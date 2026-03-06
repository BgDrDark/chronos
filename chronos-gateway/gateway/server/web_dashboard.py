from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import subprocess
import socket
import asyncio
from pathlib import Path

from gateway.config import config

logger = logging.getLogger(__name__)


async def get_mac_from_arp(ip: str) -> str:
    """Get MAC address from neighbor/ARP table"""
    try:
        if os.name == 'nt':
            subprocess.run(['ping', '-n', '1', '-w', '1000', ip], capture_output=True, timeout=3)
            result = subprocess.run(['arp', '-a', ip], capture_output=True, text=True, timeout=5)
            for line in result.stdout.split('\n'):
                if ip in line:
                    parts = line.split()
                    for part in parts:
                        if '-' in part and len(part) == 17:
                            return part.upper()
        else:
            subprocess.run(['ping', '-c', '1', '-W', '1', ip], capture_output=True, timeout=3)
            result = subprocess.run(['ip', 'neigh', 'show', ip], capture_output=True, text=True, timeout=5)
            for line in result.stdout.split('\n'):
                if ip in line:
                    parts = line.split()
                    for part in parts:
                        if ':' in part and len(part) == 17:
                            return part.upper()
    except Exception as e:
        logger.debug(f"MAC lookup failed for {ip}: {e}")
    return ""

BASE_DIR = Path(__file__).parent.parent.parent
STATIC_DIR = BASE_DIR / "static"


class WebDashboard:
    """
    Web базиран dashboard за мониторинг
    
    Функционалност:
    - Преглед на активните устройства
    - Управление на принтери
    - Стартиране/спиране на service
    """
    
    def __init__(self, gateway_service):
        self.gateway = gateway_service
        self.app = FastAPI(title="Chronos Gateway Dashboard")
        
        if STATIC_DIR.exists():
            self.app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
        
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self._setup_routes()
    
    def _get_cluster_peers(self) -> list:
        """Връща списък с peers в клъстера"""
        try:
            from gateway.cluster.discovery import discovery_manager
            peers = []
            for ip, peer in discovery_manager.peers.items():
                peers.append({
                    "ip": ip,
                    "hostname": peer.hostname,
                    "role": peer.role,
                    "score": peer.score,
                    "priority": peer.priority,
                    "last_seen": peer.last_seen.isoformat()
                })
            return peers
        except Exception as e:
            logger.debug(f"Error getting cluster peers: {e}")
            return []
    
    def _setup_routes(self):
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard(request: Request):
            """Главна страница"""
            html_path = STATIC_DIR / "index.html"
            if html_path.exists():
                return HTMLResponse(content=html_path.read_text(encoding='utf-8'))
            return HTMLResponse(content=self._get_default_html())
        
        @self.app.get("/api/status")
        async def get_status():
            """Общ статус на gateway"""
            from gateway.core.hardware_id import get_mac_address
            
            terminals_status = self.gateway.terminal_manager.get_status(
                config.heartbeat_timeout
            )
            printers_status = self.gateway.printer_manager.get_status()
            
            return {
                "gateway": {
                    "id": config.gateway_id,
                    "alias": config.alias,
                    "ip_address": self.gateway.get_local_ip(),
                    "mac_address": get_mac_address(),
                    "hardware_uuid": config.hardware_uuid,
                    "status": "running",
                    "uptime": self.gateway.get_uptime(),
                    "registered": config.gateway_id != "auto",
                    "cluster_enabled": config.get("cluster.enabled", False),
                    "cluster_role": self.gateway.cluster_manager.role if config.get("cluster.enabled") else "standalone",
                    "terminal_port": config.terminal_port,
                    "web_port": config.web_port,
                    "cluster_peers": self._get_cluster_peers() if config.get("cluster.enabled") else []
                },
                "terminals": terminals_status,
                "printers": printers_status,
            }

        @self.app.post("/api/register")
        async def trigger_registration():
            """Ръчно задействане на регистрация в бакенда"""
            success = await self.gateway.register_with_backend()
            return JSONResponse(content={"success": success, "status": "registered" if success else "failed"})

        @self.app.post("/api/cluster/toggle")
        async def toggle_cluster(data: dict):
            """Включване/Изключване на клъстерния режим"""
            enabled = data.get("enabled", False)
            config.set("cluster.enabled", enabled)
            logger.warning(f"Cluster mode {'enabled' if enabled else 'disabled'} via dashboard")
            return {"status": "ok", "enabled": enabled}

        @self.app.post("/api/restart")
        async def restart_service():
            """Рестартиране на гейтуея"""
            logger.warning("Restart requested via Web Dashboard...")
            # Използваме малко забавяне, за да върнем отговора към браузъра преди да спрем
            async def shutdown():
                await asyncio.sleep(1)
                import os
                import signal
                os.kill(os.getpid(), signal.SIGTERM)
            
            asyncio.create_task(shutdown())
            return {"status": "restarting"}
        
        @self.app.get("/api/terminals")
        async def get_terminals():
            """Списък с терминали"""
            return JSONResponse(
                content=self.gateway.terminal_manager.get_all_terminals()
            )
        
        @self.app.post("/api/terminal/config")
        async def update_terminal_config(data: dict):
            """Обновяване конфигурацията на терминал (свързване с врата)"""
            from gateway.access import zone_manager
            
            hardware_uuid = data.get("hardware_uuid")
            door_id = data.get("door_id")
            mode = data.get("mode", "access")
            
            if not hardware_uuid:
                return JSONResponse(content={"status": "error", "message": "hardware_uuid is required"}, status_code=400)
            
            # Намираме вратата и обновяваме нейния terminal_id
            doors = zone_manager.get_all_doors()
            found = False
            for door in doors:
                if door['id'] == door_id:
                    door['terminal_id'] = hardware_uuid
                    door['terminal_mode'] = mode
                    found = True
                    # Запазваме промяната обратно в мениджъра
                    zone_manager.update_door(door['id'], door)
                elif door.get('terminal_id') == hardware_uuid:
                    # Разкачаме старата връзка ако има такава
                    door['terminal_id'] = None
                    zone_manager.update_door(door['id'], door)
            
            if not found and door_id:
                return JSONResponse(content={"status": "error", "message": "Door not found"}, status_code=404)
            
            return JSONResponse(content={"status": "updated", "hardware_uuid": hardware_uuid, "door_id": door_id})

        @self.app.get("/api/printers")
        async def get_printers():
            """Списък с принтери"""
            return JSONResponse(
                content=self.gateway.printer_manager.get_all_printers()
            )
        
        @self.app.post("/api/printers")
        async def add_printer(data: dict):
            """Добавяне на принтер"""
            import uuid
            
            printer_id = uuid.uuid4().hex[:8]
            
            self.gateway.printer_manager.add_printer(
                printer_id=printer_id,
                name=data.get("name"),
                printer_type=data.get("type", "network"),
                ip_address=data.get("ip_address"),
                port=data.get("port", 9100),
                protocol=data.get("protocol", "raw"),
                windows_name=data.get("windows_name"),
                is_default=data.get("is_default", False),
            )
            
            return JSONResponse(
                content={"status": "created", "id": printer_id},
                status_code=201
            )
        
        @self.app.post("/api/printers/{printer_id}/test")
        async def test_printer(printer_id: str):
            """Тест на принтер"""
            result = self.gateway.printer_manager.test_printer(printer_id)
            return JSONResponse(content=result)
        
        @self.app.post("/api/printers/{printer_id}/set-default")
        async def set_default_printer(printer_id: str):
            """Задаване като подразбиращ принтер"""
            success = self.gateway.printer_manager.set_default(printer_id)
            return JSONResponse(content={"status": "ok" if success else "error"})
        
        @self.app.delete("/api/printers/{printer_id}")
        async def delete_printer(printer_id: str):
            """Премахване на принтер"""
            success = self.gateway.printer_manager.remove_printer(printer_id)
            return JSONResponse(content={"status": "deleted" if success else "not_found"})
        
        @self.app.post("/api/printers/{printer_id}")
        async def update_printer(printer_id: str, data: dict):
            """Редакция на принтер"""
            printer = self.gateway.printer_manager.get_printer(printer_id)
            if not printer:
                return JSONResponse(
                    content={"status": "error", "message": "Printer not found"},
                    status_code=404
                )
            
            if "name" in data:
                printer["name"] = data["name"]
            if "ip_address" in data:
                printer["ip_address"] = data["ip_address"]
            if "port" in data:
                printer["port"] = data["port"]
            
            return JSONResponse(content={"status": "updated"})
        
        @self.app.get("/api/logs")
        async def get_logs(lines: int = 100):
            """Получаване на логове"""
            log_file = BASE_DIR / "logs" / "gateway.log"
            if log_file.exists():
                with open(log_file, 'r') as f:
                    all_lines = f.readlines()
                    return JSONResponse(content=all_lines[-lines:])
            return JSONResponse(content=[])
        
        @self.app.get("/access/hardware")
        async def get_hardware():
            from gateway.devices.relay_controller import relay_controller
            return JSONResponse(content=relay_controller.get_all_devices())
        
        @self.app.post("/access/hardware")
        async def add_hardware(data: dict):
            from gateway.devices.relay_controller import relay_controller
            try:
                device_id = relay_controller.add_device(
                    device_id=data.get("id"),
                    name=data.get("name", ""),
                    ip=data.get("ip", ""),
                    port=data.get("port", 6722),
                    device_type=data.get("type", "sr201"),
                    mac_address=data.get("mac_address", ""),
                    relay_1_duration=data.get("relay_1_duration", 500),
                    relay_2_duration=data.get("relay_2_duration", 500),
                    relay_1_manual=data.get("relay_1_manual", False),
                    relay_2_manual=data.get("relay_2_manual", False),
                    active=data.get("active", True)
                )
                return JSONResponse(content={"status": "created", "id": device_id}, status_code=201)
            except Exception as e:
                return JSONResponse(content={"status": "error", "message": str(e)}, status_code=400)
        
        @self.app.delete("/access/hardware/{device_id}")
        async def delete_hardware(device_id: str):
            from gateway.devices.relay_controller import relay_controller
            success = relay_controller.remove_device(device_id)
            return JSONResponse(content={"status": "deleted" if success else "not_found"})
        
        @self.app.post("/access/hardware/{device_id}/trigger")
        async def trigger_hardware(device_id: str, data: dict):
            from gateway.devices.relay_controller import relay_controller
            result = await relay_controller.trigger(device_id, data.get("relay_number", 1), data.get("duration_ms"))
            return JSONResponse(content=result)
        
        @self.app.post("/access/hardware/{device_id}/on")
        async def turn_on_hardware(device_id: str, data: dict):
            from gateway.devices.relay_controller import relay_controller
            result = await relay_controller.turn_on(device_id, data.get("relay_number", 1))
            return JSONResponse(content=result)
        
        @self.app.post("/access/hardware/{device_id}/off")
        async def turn_off_hardware(device_id: str, data: dict):
            from gateway.devices.relay_controller import relay_controller
            result = await relay_controller.turn_off(device_id, data.get("relay_number", 1))
            return JSONResponse(content=result)
        
        @self.app.post("/access/hardware/{device_id}/test")
        async def test_hardware(device_id: str):
            from gateway.devices.relay_controller import relay_controller
            result = await relay_controller.test_device(device_id)
            return JSONResponse(content=result)
        
        @self.app.post("/access/scan/{ip_address}")
        async def scan_ip(ip_address: str):
            import socket
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((ip_address, 6722))
                sock.close()
                
                if result == 0:
                    mac_address = await get_mac_from_arp(ip_address)
                    return JSONResponse(content={"success": True, "online": True, "mac_address": mac_address})
                return JSONResponse(content={"success": False, "online": False, "mac_address": None})
            except Exception as e:
                return JSONResponse(content={"success": False, "error": str(e)})
        
        @self.app.post("/access/scan-network")
        async def scan_network():
            """Сканира мрежата за SR201 устройства"""
            import asyncio
            import socket
            import logging
            
            logger = logging.getLogger(__name__)
            
            gateway_ip = self.gateway.get_local_ip()
            subnet = gateway_ip.rsplit('.', 1)[0]
            
            logger.info(f"Starting network scan from {gateway_ip}, subnet {subnet}.0/24")
            
            def check_port_sync(host: str, port: int = 6722, timeout: float = 0.5) -> dict | None:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(timeout)
                    result = sock.connect_ex((host, port))
                    sock.close()
                    if result == 0:
                        return {'ip': host, 'online': True}
                except:
                    pass
                return None
            
            loop = asyncio.get_event_loop()
            
            # Run in thread pool for true parallelism
            tasks = []
            for i in range(1, 255):
                tasks.append(loop.run_in_executor(None, check_port_sync, f"{subnet}.{i}"))
            
            results = await asyncio.gather(*tasks)
            
            # Count online hosts
            online_count = sum(1 for r in results if r and r.get('online'))
            logger.info(f"Found {online_count} hosts with port 6722 open")
            
            # Check MAC for found devices
            found_devices = []
            for r in results:
                if r and r.get('online'):
                    mac = await get_mac_from_arp(r['ip'])
                    logger.debug(f"Host {r['ip']} MAC: {mac}")
                    # Show all hosts with port 6722 as potential SR201
                    is_sr201 = mac and mac.upper().startswith('00:FF:B0')
                    found_devices.append({
                        'ip': r['ip'],
                        'mac': mac.upper() if mac else '',
                        'is_sr201': is_sr201
                    })
            
            logger.info(f"Found {len(found_devices)} devices with port 6722 open")
            
            return JSONResponse(content={
                "success": True, 
                "devices": found_devices,
                "debug": {
                    "gateway_ip": gateway_ip,
                    "subnet": f"{subnet}.0/24",
                    "online_hosts": online_count
                }
            })
        
        @self.app.post("/access/hardware/{ip_or_device_id}/test")
        async def test_hardware_by_ip(ip_or_device_id: str):
            import socket
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((ip_or_device_id, 6722))
                sock.close()
                
                if result == 0:
                    mac_address = await get_mac_from_arp(ip_or_device_id)
                    return JSONResponse(content={"success": True, "online": True, "mac_address": mac_address})
                return JSONResponse(content={"success": False, "online": False, "mac_address": None})
            except Exception as e:
                return JSONResponse(content={"success": False, "error": str(e)})
        
        @self.app.post("/access/hardware/{device_id}/change-ip")
        async def change_hardware_ip(device_id: str, data: dict):
            from gateway.devices.relay_controller import relay_controller
            new_ip = data.get("new_ip", "")
            new_netmask = data.get("new_netmask", "255.255.255.0")
            new_gateway = data.get("new_gateway", "192.168.1.1")
            if not new_ip:
                return JSONResponse(content={"success": False, "message": "New IP required"})
            
            result = await relay_controller.change_ip(device_id, new_ip, new_netmask, new_gateway)
            return JSONResponse(content=result)
        
        @self.app.post("/access/hardware/{device_id}/mode")
        async def toggle_relay_mode(device_id: str, data: dict):
            from gateway.devices.relay_controller import relay_controller
            relay_number = data.get("relay_number", 1)
            manual = data.get("manual", False)
            
            result = relay_controller.toggle_relay_mode(device_id, relay_number, manual)
            return JSONResponse(content=result)
        
        @self.app.post("/access/hardware/{device_id}/duration")
        async def set_relay_duration(device_id: str, data: dict):
            from gateway.devices.relay_controller import relay_controller
            relay_number = data.get("relay_number", 1)
            duration = data.get("duration", 500)
            
            result = relay_controller.set_duration(device_id, relay_number, duration)
            return JSONResponse(content=result)
        
        @self.app.get("/access/zones")
        async def get_zones():
            from gateway.access import zone_manager
            return JSONResponse(content=zone_manager.get_all_zones())
        
        @self.app.post("/access/zones")
        async def add_zone(data: dict):
            from gateway.access import zone_manager
            zone_id = zone_manager.add_zone(data)
            return JSONResponse(content={"status": "created", "id": zone_id}, status_code=201)
        
        @self.app.delete("/access/zones/{zone_id}")
        async def delete_zone(zone_id: str):
            from gateway.access import zone_manager
            success = zone_manager.remove_zone(zone_id)
            return JSONResponse(content={"status": "deleted" if success else "not_found"})
        
        @self.app.get("/access/doors")
        async def get_doors():
            from gateway.access import zone_manager
            return JSONResponse(content=zone_manager.get_all_doors())
        
        @self.app.post("/access/doors")
        async def add_door(data: dict):
            from gateway.access import zone_manager
            door_id = zone_manager.add_door(data)
            return JSONResponse(content={"status": "created", "id": door_id}, status_code=201)
        
        @self.app.delete("/access/doors/{door_id}")
        async def delete_door(door_id: str):
            from gateway.access import zone_manager
            success = zone_manager.remove_door(door_id)
            return JSONResponse(content={"status": "deleted" if success else "not_found"})
        
        @self.app.post("/access/doors/{door_id}/trigger")
        async def trigger_door(door_id: str):
            from gateway.access import zone_manager
            from gateway.devices.relay_controller import relay_controller
            door = zone_manager.get_door(door_id)
            if not door:
                return JSONResponse(content={"status": "error", "message": "Door not found"}, status_code=404)
            result = await relay_controller.trigger(door.device_id, door.relay_number)
            return JSONResponse(content=result)
        
        @self.app.get("/access/codes")
        async def get_codes():
            from gateway.access import code_manager
            return JSONResponse(content={"codes": code_manager.get_codes()})
        
        @self.app.post("/access/codes/generate")
        async def generate_code(data: dict):
            from gateway.access import code_manager
            code = code_manager.create_code(data)
            return JSONResponse(content={"code": code})
        
        @self.app.post("/access/codes/{code}/revoke")
        async def revoke_code(code: str):
            from gateway.access import code_manager
            success = code_manager.revoke_code(code)
            return JSONResponse(content={"status": "revoked" if success else "not_found"})
        
        @self.app.delete("/access/codes/{code}")
        async def delete_code(code: str):
            from gateway.access import code_manager
            success = code_manager.delete_code(code)
            return JSONResponse(content={"status": "deleted" if success else "not_found"})
        
        @self.app.get("/access/logs")
        async def get_access_logs(limit: int = 100):
            from gateway.access import access_controller
            return JSONResponse(content={"logs": access_controller.get_logs(limit)})
        
        @self.app.get("/access/state")
        async def get_access_state():
            from gateway.access import access_controller
            users = access_controller.get_active_users()
            return JSONResponse(content={"users": users})
    
    def _get_default_html(self) -> str:
        """Default HTML ако липсва файл"""
        return """
<!DOCTYPE html>
<html lang="bg">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chronos Gateway</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100">
    <div class="container mx-auto p-8">
        <h1 class="text-2xl font-bold mb-4">Chronos Gateway Dashboard</h1>
        <p>Loading...</p>
    </div>
    <script>
        fetch('/api/status').then(r => r.json()).then(console.log);
    </script>
</body>
</html>
"""
