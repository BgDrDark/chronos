"""
SyncManager for synchronizing data between Gateway and Backend
"""

import asyncio
import logging
import aiohttp
from typing import Optional, Dict, Any
from datetime import datetime

from gateway.database.sqlite_manager import config_db, logs_db
from gateway.config import config

logger = logging.getLogger(__name__)


class SyncManager:
    """
    Мениджър за синхронизация между Gateway и Backend
    
    Поддържа:
    - Push на конфигурация към backend
    - Push на логове към backend
    - Pull на конфигурация от backend
    """
    
    def __init__(self, gateway_id: str = None):
        self.gateway_id = gateway_id or config.get('gateway.id', '1')
        self.backend_url = config.backend_url
        self.api_key = config.api_key
        self.sync_interval = config.get('sync.interval_minutes', 15) * 60  # Convert to seconds
        self.retry_attempts = config.get('sync.retry_attempts', 3)
        self.batch_size = config.get('sync.batch_size', 100)
        self._running = False
    
    async def start(self):
        """Стартира синхронизацията"""
        self._running = True
        logger.info(f"SyncManager started (interval: {self.sync_interval}s)")
        
        while self._running:
            try:
                # Sync logs to backend
                await self.sync_logs_to_backend()
                
                # Sync config to backend
                await self.sync_config_to_backend()
                
            except Exception as e:
                logger.error(f"Sync error: {e}")
            
            await asyncio.sleep(self.sync_interval)
    
    def stop(self):
        """Спира синхронизацията"""
        self._running = False
        logger.info("SyncManager stopped")
    
    async def sync_logs_to_backend(self):
        """Синхронизира логовете към backend"""
        try:
            unsynced_logs = logs_db.get_unsynced_logs(self.batch_size)
            if not unsynced_logs:
                logger.debug("No unsynced logs")
                return
            
            logs_to_send = []
            for log in unsynced_logs:
                logs_to_send.append({
                    'timestamp': log.get('timestamp'),
                    'user_id': log.get('user_id'),
                    'user_name': log.get('user_name'),
                    'door_id': log.get('door_id'),
                    'door_name': log.get('door_name'),
                    'zone_id': log.get('zone_id'),
                    'zone_name': log.get('zone_name'),
                    'result': log.get('result'),
                    'reason': log.get('reason'),
                    'method': log.get('method'),
                    'terminal_id': log.get('terminal_id')
                })
            
            success = await self._push_with_retry(
                f"/gateways/{self.gateway_id}/access/sync-logs",
                {'logs': logs_to_send}
            )
            
            if success:
                log_ids = [log['id'] for log in unsynced_logs if log.get('id')]
                if log_ids:
                    logs_db.mark_as_synced(log_ids)
                logger.info(f"Synced {len(logs_to_send)} logs to backend")
            else:
                logger.warning(f"Failed to sync {len(logs_to_send)} logs")
                
        except Exception as e:
            logger.error(f"Error syncing logs: {e}")
    
    async def sync_config_to_backend(self):
        """Синхронизира конфигурацията към backend"""
        try:
            from gateway.devices.relay_controller import relay_controller
            config_data = config_db.export_all_config()
            
            # Update devices with actual status from memory
            config_data['devices'] = relay_controller.get_all_devices()
            
            success = await self._push_with_retry(
                f"/gateways/{self.gateway_id}/push-config",
                config_data
            )
            
            if success:
                config_db.set_sync_meta('last_config_sync', datetime.now().isoformat())
                logger.info(f"Synced config to backend: {len(config_data.get('devices', []))} devices, "
                           f"{len(config_data.get('zones', []))} zones, "
                           f"{len(config_data.get('doors', []))} doors")
            else:
                logger.warning("Failed to sync config to backend")
                
        except Exception as e:
            logger.error(f"Error syncing config: {e}")
    
    async def pull_config_from_backend(self) -> bool:
        """Тегли конфигурацията от backend"""
        try:
            url = f"{self.backend_url}/gateways/{self.gateway_id}/config"
            headers = {"X-Kiosk-Secret": self.api_key}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        ac_config = data.get('access_control', {})
                        if ac_config:
                            # Import zones
                            zones = ac_config.get('zones', [])
                            for zone in zones:
                                config_db.save_zone(zone)
                            
                            # Import doors
                            doors = ac_config.get('doors', [])
                            for door in doors:
                                config_db.save_door(door)
                        
                        config_db.set_sync_meta('last_config_pull', datetime.now().isoformat())
                        logger.info(f"Pulled config from backend")
                        return True
                    else:
                        logger.warning(f"Failed to pull config: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error pulling config: {e}")
        
        return False
    
    async def _push_with_retry(self, endpoint: str, data: Dict[str, Any]) -> bool:
        """Пушва данни с retry логика"""
        if not self.backend_url:
            logger.warning("Backend URL not configured, skipping sync")
            return False
        
        url = f"{self.backend_url}{endpoint}"
        headers = {
            "X-Kiosk-Secret": self.api_key,
            "Content-Type": "application/json"
        }
        
        for attempt in range(self.retry_attempts):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=data, headers=headers, 
                                           timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status in (200, 201):
                            return True
                        elif response.status >= 500:
                            # Server error, retry
                            logger.warning(f"Server error {response.status}, attempt {attempt + 1}/{self.retry_attempts}")
                        else:
                            # Client error, don't retry
                            logger.warning(f"Client error {response.status}")
                            return False
                            
            except aiohttp.ClientError as e:
                logger.warning(f"Connection error (attempt {attempt + 1}/{self.retry_attempts}): {e}")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return False
            
            # Exponential backoff
            if attempt < self.retry_attempts - 1:
                await asyncio.sleep(2 ** attempt)
        
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Връща статуса на синхронизацията"""
        unsynced_count = logs_db.get_unsynced_count()
        last_config_sync = config_db.get_sync_meta('last_config_sync')
        last_config_pull = config_db.get_sync_meta('last_config_pull')
        
        return {
            'gateway_id': self.gateway_id,
            'backend_url': self.backend_url,
            'interval_seconds': self.sync_interval,
            'retry_attempts': self.retry_attempts,
            'unsynced_logs': unsynced_count,
            'last_config_sync': last_config_sync,
            'last_config_pull': last_config_pull,
            'running': self._running
        }


# Singleton instance
sync_manager: Optional[SyncManager] = None


def get_sync_manager() -> SyncManager:
    """Get or create SyncManager instance"""
    global sync_manager
    if sync_manager is None:
        sync_manager = SyncManager()
    return sync_manager
