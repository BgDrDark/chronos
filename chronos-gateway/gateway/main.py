import asyncio
import logging
import signal
import sys
import os
import socket
from pathlib import Path
from datetime import datetime

from gateway.config import config
from gateway.core.hardware_id import get_hardware_uuid
from gateway.devices.terminal_manager import TerminalManager
from gateway.devices.printer_manager import PrinterManager
from gateway.cluster.manager import ClusterManager

BASE_DIR = Path(__file__).parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "gateway.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GatewayService:
    """
    Главен Gateway service
    
    Управлява:
    - Terminal Hub (port 1424)
    - Web Dashboard (port 8889)
    - Heartbeat мониторинг
    - Комуникация с бекенд
    """
    
    def __init__(self):
        self.terminal_manager = TerminalManager()
        self.printer_manager = PrinterManager()
        self.cluster_manager = ClusterManager(self)
        self.start_time = datetime.now()
        self._running = False
        self._registered = False
        
        self._ensure_hardware_uuid()
        self._load_printers_from_config()
    
    def _ensure_hardware_uuid(self):
        """Инициализира hardware UUID ако липсва"""
        if not config.hardware_uuid:
            hw_uuid = get_hardware_uuid()
            config.hardware_uuid = hw_uuid
            logger.info(f"Generated hardware UUID: {hw_uuid}")
    
    async def register_with_backend(self):
        """Регистрира gateway-а в бекенда"""
        if not config.backend_url:
            logger.warning("Backend URL not configured. Running in local mode.")
            return False
        
        import aiohttp
        
        async def try_register(base_url: str) -> bool:
            url = f"{base_url}/gateways/register"
            
            if not base_url:
                logger.warning("Could not register with backend: Empty backend_url")
                return False
            
            data = {
                "hardware_uuid": config.hardware_uuid,
                "ip_address": self.get_local_ip(),
                "local_hostname": socket.gethostname(),
                "terminal_port": config.terminal_port,
                "web_port": config.web_port,
            }
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=data, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status == 200:
                            result = await response.json()
                            api_key = result.get("api_key")
                            if api_key:
                                config.set("backend.api_key", api_key)
                                if result.get("id"):
                                    gateway_id = str(result.get("id"))
                                    config.set("gateway.id", gateway_id)
                                    logger.info(f"Registered with backend. Persistent Gateway ID: {gateway_id}")
                                return True
                        elif response.status == 400:
                            result = await response.json()
                            detail = result.get("detail", {})
                            if isinstance(detail, dict):
                                msg = detail.get("message", "")
                                gateway_id = detail.get("id")
                                api_key = detail.get("api_key")
                            else:
                                msg = detail
                                gateway_id = None
                                api_key = None

                            if "вече" in msg.lower():
                                if gateway_id:
                                    config.set("gateway.id", str(gateway_id))
                                if api_key:
                                    config.set("backend.api_key", api_key)
                                logger.info(f"Gateway already registered. Found ID: {gateway_id}")
                                return True
                        logger.warning(f"Registration failed: HTTP {response.status} (URL: {url})")
            except asyncio.TimeoutError:
                logger.warning(f"Could not register with backend: Timeout after 10s (URL: {url})")
            except aiohttp.ClientConnectorError as e:
                logger.warning(f"Could not register with backend: Connection failed (URL: {url}) - {type(e).__name__}: {e}")
            except Exception as e:
                logger.warning(f"Could not register with backend: {type(e).__name__}: {e} (URL: {url})", exc_info=True)
            return False
        
        if await try_register(config.backend_url):
            self._registered = True
            return True
        
        if config.fallback_url:
            logger.info(f"Primary backend failed, trying fallback: {config.fallback_url}")
            if await try_register(config.fallback_url):
                self._registered = True
                return True
        
        return False
    
    def _load_printers_from_config(self):
        """Зарежда принтери от конфигурацията"""
        printers = config.get('printers', [])
        for p in printers:
            self.printer_manager.add_printer(
                printer_id=p.get('id', p.get('name', 'unknown')),
                name=p.get('name'),
                printer_type=p.get('type', 'network'),
                ip_address=p.get('ip_address'),
                port=p.get('port', 9100),
                protocol=p.get('protocol', 'raw'),
                windows_name=p.get('windows_name'),
                is_default=p.get('is_default', False),
            )
    
    def get_local_ip(self) -> str:
        """Връща локалния IP адрес"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def get_uptime(self) -> str:
        """Връща uptime"""
        delta = datetime.now() - self.start_time
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}h {minutes}m {seconds}s"
    
    async def start_heartbeat(self):
        """Стартира heartbeat мониторинг"""
        logger.info("Starting heartbeat monitor")
        
        while self._running:
            try:
                await self._send_heartbeat()
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
            
            await asyncio.sleep(config.heartbeat_interval)
    
    async def _send_heartbeat(self):
        """Изпраща heartbeat към бекенд"""
        if config.gateway_id == "auto" or not self.cluster_manager.is_master():
            return
        
        import aiohttp
        
        terminals_status = self.terminal_manager.get_status(config.heartbeat_timeout)
        printers_status = self.printer_manager.get_status()
        
        data = {
            "status": "online",
            "terminal_count": terminals_status["total"],
            "printer_count": printers_status["total"],
        }
        
        async def try_heartbeat(base_url: str) -> bool:
            url = f"{base_url}/gateways/{config.gateway_id}/heartbeat"
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=data) as response:
                        if response.status == 200:
                            logger.debug("Heartbeat sent successfully")
                            return True
                        else:
                            logger.warning(f"Heartbeat failed: {response.status}")
            except Exception as e:
                logger.debug(f"Heartbeat skipped (backend unreachable): {e}")
            return False
        
        if not await try_heartbeat(config.backend_url):
            if config.fallback_url:
                await try_heartbeat(config.fallback_url)

    async def sync_config_from_backend(self):
        """Периодично изтегляне на конфигурация (зони, врати) от бакенда"""
        if config.gateway_id == "auto" or not self.cluster_manager.is_master():
            return

        import aiohttp
        from gateway.access import zone_manager

        headers = {"X-Kiosk-Secret": config.api_key}

        async def try_sync(base_url: str) -> bool:
            url = f"{base_url}/gateways/{config.gateway_id}/config"
            
            if not base_url:
                logger.error(f"Error syncing config: Empty base_url (Gateway ID: {config.gateway_id})")
                return False
            
            if not config.api_key:
                logger.warning(f"Error syncing config: No API key configured (Gateway ID: {config.gateway_id})")
                return False
            
            logger.info(f"Syncing config: {url} (Gateway ID: {config.gateway_id})")
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            mode = data.get("system_mode", "normal")
                            if mode != config.get("gateway.system_mode"):
                                config.set("gateway.system_mode", mode)
                                logger.warning(f"SYSTEM MODE CHANGED TO: {mode.upper()}")

                            ac_config = data.get("access_control", {})
                            
                            if ac_config:
                                zones = ac_config.get("zones", [])
                                doors = ac_config.get("doors", [])
                                zone_manager.load_from_config(zones, doors)
                                logger.info(f"Synced configuration from backend: {len(zones)} zones, {len(doors)} doors")
                            return True
                        elif response.status == 401:
                            logger.error(f"Config sync failed: Unauthorized (Gateway ID: {config.gateway_id}) - check API key")
                        elif response.status == 404:
                            logger.error(f"Config sync failed: Gateway not found (Gateway ID: {config.gateway_id})")
                        else:
                            logger.warning(f"Config sync failed: HTTP {response.status} (Gateway ID: {config.gateway_id})")
            except asyncio.TimeoutError:
                logger.error(f"Error syncing config: Timeout after 10s (URL: {url})")
            except aiohttp.ClientConnectorError as e:
                logger.error(f"Error syncing config: Connection failed (URL: {url}) - {type(e).__name__}: {e}")
            except Exception as e:
                logger.error(f"Error syncing config: {type(e).__name__}: {e} (URL: {url})", exc_info=True)
            return False

        while self._running:
            success = await try_sync(config.backend_url)
            if not success and config.fallback_url:
                logger.info(f"Primary backend failed, trying fallback for config sync")
                await try_sync(config.fallback_url)
            
            await asyncio.sleep(300) # Every 5 minutes
    
    async def cleanup_offline_terminals(self):
        """Премахва офлайн терминали"""
        while self._running:
            await asyncio.sleep(60)
            removed = self.terminal_manager.cleanup_offline(300)
            if removed:
                logger.info(f"Cleaned up {removed} offline terminals")
    
    def stop(self):
        """Спира service-а"""
        logger.info("Stopping gateway service")
        self._running = False
    
    def run(self):
        """Стартира service-а"""
        logger.info("Starting Chronos Gateway")
        logger.info(f"Hardware UUID: {config.hardware_uuid}")
        logger.info(f"Local IP: {self.get_local_ip()}")
        
        self._running = True
        
        from gateway.server.terminal_hub import TerminalHub
        from gateway.server.web_dashboard import WebDashboard
        
        terminal_hub = TerminalHub(self.terminal_manager, self.printer_manager, self.cluster_manager)
        web_dashboard = WebDashboard(self)
        
        import uvicorn
        
        self._stop_event = asyncio.Event()
        
        async def run_terminal_hub():
            config_terminal = uvicorn.Config(
                terminal_hub.app,
                host="0.0.0.0",
                port=config.terminal_port,
                log_level="info"
            )
            server = uvicorn.Server(config_terminal)
            
            # Таск за спиране на сървъра при стоп събитие
            async def watch_stop():
                await self._stop_event.wait()
                server.should_exit = True
            
            stop_task = asyncio.create_task(watch_stop())
            await server.serve()
            stop_task.cancel()
        
        async def run_web_dashboard():
            config_web = uvicorn.Config(
                web_dashboard.app,
                host="0.0.0.0",
                port=config.web_port,
                log_level="info"
            )
            server = uvicorn.Server(config_web)
            
            # Таск за спиране на сървъра при стоп събитие
            async def watch_stop():
                await self._stop_event.wait()
                server.should_exit = True
            
            stop_task = asyncio.create_task(watch_stop())
            await server.serve()
            stop_task.cancel()
        
        async def run_all():
            # Initial registration attempt (only if leader/master)
            if self.cluster_manager.is_master():
                await self.register_with_backend()
            
            from gateway.devices.relay_controller import relay_controller
            
            # Старт на всички под-системи като таскове
            tasks = [
                asyncio.create_task(run_terminal_hub()),
                asyncio.create_task(run_web_dashboard()),
                asyncio.create_task(self.cluster_manager.start()),
                asyncio.create_task(self.start_heartbeat()),
                asyncio.create_task(self.sync_config_from_backend()),
                asyncio.create_task(self.cleanup_offline_terminals()),
                asyncio.create_task(relay_controller.start_background_checks()),
            ]
            
            # Изчакваме събитие за стоп
            await self._stop_event.wait()
            logger.info("Graceful shutdown initiated...")
            
            # Изчакваме малко сървърите да спрат сами (те слушат за should_exit през watch_stop)
            await asyncio.sleep(1)
            
            # Канселираме останалите таскове (heartbeat, sync и т.н.)
            for task in tasks:
                if not task.done():
                    task.cancel()
            
            # Изчакваме всички да приключат и игнорираме грешки от канселиране
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info("All tasks settled")
        
        # Закачаме сигналния хендлър към цикъла
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        def handle_signal():
            logger.info("Shutdown signal received")
            self.stop()
            self._stop_event.set()

        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, handle_signal)

        try:
            loop.run_until_complete(run_all())
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            self.stop()


def main():
    service = GatewayService()
    service.run()


if __name__ == "__main__":
    main()
