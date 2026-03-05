import asyncio
import logging
from typing import Optional

from gateway.config import config
from gateway.cluster.discovery import discovery_manager

logger = logging.getLogger(__name__)

class ClusterManager:
    """
    Управлява състоянието на клъстера и ролята на текущия гейтуей.
    """
    def __init__(self, gateway_service):
        self.gateway = gateway_service
        self.role = "master" # Default
        self._running = False
        self.master_ip: Optional[str] = None

    async def start(self):
        if not config.get("cluster.enabled", False):
            logger.info("Cluster mode disabled in config.")
            return

        self._running = True
        # Стартираме discovery под-системата
        asyncio.create_task(discovery_manager.start())
        
        # Стартираме цикъла за следене на ролята
        await self._monitor_loop()

    async def _monitor_loop(self):
        """Периодично проверява дали трябва да сме Master или Slave"""
        sync_counter = 0
        
        while self._running:
            try:
                is_leader = discovery_manager.is_leader()
                new_role = "master" if is_leader else "slave"
                
                if new_role != self.role:
                    logger.warning(f"CLUSTER ROLE CHANGE: {self.role.upper()} -> {new_role.upper()}")
                    self.role = new_role
                    await self._handle_role_change()

                # Ако сме Slave, синхронизираме със Master-а
                if self.role == "slave":
                    self.master_ip = self._find_master_ip()
                    if self.master_ip:
                        await self.sync_offline_logs()
                        await self.sync_zone_state()
                else:
                    self.master_ip = None
                    # Ако сме Master, изпращаме конфигурация на всеки 60 сек
                    sync_counter += 5
                    if sync_counter >= 60:
                        await self.sync_config_to_slaves()
                        sync_counter = 0

            except Exception as e:
                logger.error(f"Cluster monitor error: {e}")
            
            await asyncio.sleep(5)

    async def sync_offline_logs(self):
        """Изпраща локално натрупани логове от SQLite към Master-а"""
        from gateway.access.controller import access_controller
        
        # 1. Вземаме несинхронизираните записи от базата
        unsynced = access_controller.get_unsynced_logs(limit=50)
        if not unsynced:
            return

        master_url = self.get_master_url()
        if not master_url:
            return

        import aiohttp
        url = f"{master_url}/cluster/sync-logs"
        headers = {"X-Cluster-Secret": config.get("cluster.shared_secret")}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=unsynced, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        res_data = await response.json()
                        synced_ids = res_data.get("synced_ids", [])
                        
                        # 2. Маркираме само потвърдените записи в SQLite
                        if synced_ids:
                            access_controller.mark_as_synced(synced_ids)
                            logger.info(f"Successfully synced and verified {len(synced_ids)} logs to Master")
        except Exception as e:
            logger.debug(f"Failed to sync logs to Master: {e}")
    
    async def sync_zone_state(self):
        """Синхронизира зона state между Masters"""
        from gateway.access import zone_manager, access_controller
        
        if not access_controller.zone_state:
            return
        
        # 1. Вземаме локалния state
        local_state = access_controller.zone_state.export_state()
        
        master_url = self.get_master_url()
        if not master_url:
            return
        
        import aiohttp
        url = f"{master_url}/cluster/sync-state"
        headers = {"X-Cluster-Secret": config.get("cluster.shared_secret")}
        
        try:
            async with aiohttp.ClientSession() as session:
                # Първо взимаме state от Master
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        master_state = await response.json()
                        # Обединяваме state-овете
                        count = access_controller.zone_state.merge_state(master_state)
                        if count > 0:
                            logger.info(f"Merged {count} zone states from Master")
                
                # После изпращаме нашия state
                async with session.post(url, json=local_state, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.debug(f"Zone state sync: {result}")
        except Exception as e:
            logger.debug(f"Failed to sync zone state: {e}")
    
    async def sync_config_to_slaves(self):
        """Изпраща конфигурацията на всички Slave-ове"""
        from gateway.access import zone_manager
        
        if self.role != "master":
            return
        
        # 1. Вземаме конфигурацията
        config_data = zone_manager.export_config()
        
        import aiohttp
        
        for ip, peer in discovery_manager.peers.items():
            if peer.role == "slave":
                try:
                    url = f"http://{ip}:{config.web_port}/cluster/config"
                    headers = {"X-Cluster-Secret": config.get("cluster.shared_secret")}
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.post(url, json=config_data, headers=headers, timeout=10) as response:
                            if response.status == 200:
                                result = await response.json()
                                logger.info(f"Sent config to slave {ip}: {result}")
                except Exception as e:
                    logger.debug(f"Failed to send config to slave {ip}: {e}")

    def _find_master_ip(self) -> Optional[str]:
        """Намира IP на текущия Master в мрежата"""
        for ip, peer in discovery_manager.peers.items():
            if peer.role == "master":
                return ip
        return None

    async def _handle_role_change(self):
        """Действия при смяна на ролята"""
        if self.role == "master":
            # Master трябва да се регистрира в бакенда и да праща heartbeat
            logger.info("Promoted to MASTER. Starting backend synchronization...")
            await self.gateway.register_with_backend()
        else:
            # Slave спира директната синхронизация с бакенда (Master-ът ще я прави)
            logger.info("Demoted to SLAVE. Redirecting requests to Master.")

    def is_master(self) -> bool:
        return self.role == "master" or not config.get("cluster.enabled", False)

    def get_master_url(self) -> Optional[str]:
        """Връща URL към API на Master-а"""
        if self.is_master():
            return None
        if self.master_ip:
            return f"http://{self.master_ip}:{config.terminal_port}"
        return None

    def stop(self):
        self._running = False
        discovery_manager.stop()
