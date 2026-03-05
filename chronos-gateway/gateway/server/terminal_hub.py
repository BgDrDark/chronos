from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Header
from fastapi.responses import JSONResponse
from typing import Optional, List
import logging
import asyncio
import json
from datetime import datetime

from gateway.config import config
from gateway.devices.terminal_manager import TerminalManager
from gateway.devices.printer_manager import PrinterManager
from gateway.devices.relay_controller import relay_controller
from gateway.access import zone_manager, zone_state, access_controller

logger = logging.getLogger(__name__)


class TerminalHub:
    """
    HTTP/WebSocket сървър за терминалите
    
    Endpoint-ове:
    - POST /register   - Регистрация на терминал
    - POST /scan      - QR сканиране
    - WS  /ws/{terminal_id} - WebSocket връзка
    - GET  /health    - Health check
    - GET  /config    - Конфигурация за терминал
    """
    
    def __init__(self, terminal_manager: TerminalManager, printer_manager: PrinterManager, cluster_manager=None):
        self.terminal_manager = terminal_manager
        self.printer_manager = printer_manager
        self.relay_controller = relay_controller
        self.cluster_manager = cluster_manager
        self.app = FastAPI(title="Chronos Terminal Hub")
        self.websockets: dict = {}
        
        access_controller.set_zone_state(zone_state)
        
        self._setup_routes()
    
    def _setup_routes(self):
        
        @self.app.get("/health")
        async def health_check():
            """Health check"""
            return {
                "status": "ok",
                "timestamp": datetime.now().isoformat(),
                "gateway_id": config.gateway_id,
            }
        
        @self.app.get("/config")
        async def get_config():
            """Конфигурация за терминала"""
            default_printer = self.printer_manager.get_default_printer()
            
            return {
                "backend_url": config.backend_url,
                "gateway_id": config.gateway_id,
                "printer": {
                    "id": default_printer["id"] if default_printer else None,
                    "name": default_printer["name"] if default_printer else None,
                } if default_printer else None,
            }
        
        @self.app.post("/register")
        async def register_terminal(data: dict, request: Request):
            """Регистрация на терминал"""
            terminal_id = data.get("hardware_uuid")
            client_ip = request.client.host
            
            device_info = {
                "device_name": data.get("device_name"),
                "device_type": data.get("device_type", "tablet"),
                "device_model": data.get("device_model"),
                "os_version": data.get("os_version"),
                "ip_address": client_ip,
            }
            
            terminal = self.terminal_manager.register(terminal_id, device_info)
            
            logger.info(f"Terminal registered: {terminal_id} from {client_ip}")
            
            return {
                "status": "registered",
                "terminal_id": terminal_id,
                "gateway_id": config.gateway_id,
            }
        
        @self.app.post("/scan")
        async def handle_scan(
            data: dict,
            x_terminal_id: Optional[str] = Header(None, alias="X-Terminal-Id")
        ):
            """QR сканиране за присъствие"""
            if not x_terminal_id:
                return {"status": "error", "message": "Missing X-Terminal-Id header"}
            
            self.terminal_manager.update_heartbeat(x_terminal_id)
            
            result = await self._proxy_to_backend("/kiosk/scan", data)
            
            if result.get("status") == "success":
                self.terminal_manager.increment_scans(x_terminal_id)
            
            return result
        
        @self.app.post("/production/scan")
        async def handle_production_scan(
            data: dict,
            x_terminal_id: Optional[str] = Header(None, alias="X-Terminal-Id")
        ):
            """QR сканиране за производство"""
            if not x_terminal_id:
                return {"status": "error", "message": "Missing X-Terminal-Id header"}
            
            self.terminal_manager.update_heartbeat(x_terminal_id)
            
            result = await self._proxy_to_backend("/production/scan", data)
            
            return result
        
        @self.app.post("/production/print-label")
        async def print_production_label(
            data: dict,
            x_terminal_id: Optional[str] = Header(None, alias="X-Terminal-Id")
       ):
            """Принтиране на етикет за производство"""
            if not x_terminal_id:
                return {"status": "error", "message": "Missing X-Terminal-Id header"}
            
            self.terminal_manager.update_heartbeat(x_terminal_id)
            
            printer_id = data.get("printer_id")
            label_data = data.get("label_data")
            
            if not printer_id or not label_data:
                return {"status": "error", "message": "Missing printer_id or label_data"}
            
            # Get printer and print
            success = self.printer_manager.print_data(printer_id, label_data.encode())
            
            if success:
                self.terminal_manager.increment_scans(x_terminal_id)
                return {"status": "success", "message": "Label printed"}
            else:
                return {"status": "error", "message": "Print failed"}
        
        @self.app.post("/terminal/identify")
        async def terminal_identify(data: dict):
            """Идентификация на служител"""
            result = await self._proxy_to_backend("/terminal/identify", data)
            return result
        
        @self.app.get("/terminal/workstations")
        async def get_workstations():
            """Списък със станции"""
            result = await self._proxy_to_backend("/terminal/workstations", {}, method="GET")
            return result
        
        @self.app.get("/terminal/workstations/{workstation_id}/orders")
        async def get_workstation_orders(workstation_id: int):
            """Поръчки за станция"""
            result = await self._proxy_to_backend(
                f"/terminal/workstations/{workstation_id}/orders", 
                {}, 
                method="GET"
            )
            return result
        
        @self.app.get("/terminal/orders/{order_id}/tasks")
        async def get_order_tasks(order_id: int):
            """Задачи за поръчка"""
            result = await self._proxy_to_backend(
                f"/terminal/orders/{order_id}/tasks",
                {},
                method="GET"
            )
            return result
        
        @self.app.post("/terminal/session/start")
        async def session_start(data: dict):
            """Старт на сесия"""
            result = await self._proxy_to_backend("/terminal/session/start", data)
            return result
        
        @self.app.post("/terminal/session/end")
        async def session_end(data: dict):
            """Край на сесия"""
            result = await self._proxy_to_backend("/terminal/session/end", data)
            return result
        
        @self.app.get("/terminal/session/status")
        async def session_status(terminal_id: str):
            """Статус на сесия"""
            result = await self._proxy_to_backend(
                f"/terminal/session/status?terminal_id={terminal_id}",
                {},
                method="GET"
            )
            return result
        
        @self.app.post("/terminal/task/start")
        async def task_start(data: dict):
            """Старт на задача"""
            result = await self._proxy_to_backend("/terminal/task/start", data)
            return result
        
        @self.app.post("/terminal/task/complete")
        async def task_complete(data: dict):
            """Завършване на задача"""
            result = await self._proxy_to_backend("/terminal/task/complete", data)
            return result
        
        @self.app.post("/terminal/task/scrap")
        async def task_scrap(data: dict):
            """Добавяне на брак"""
            result = await self._proxy_to_backend("/terminal/task/scrap", data)
            return result
        
        @self.app.post("/heartbeat")
        async def terminal_heartbeat(
            data: dict,
            x_terminal_id: Optional[str] = Header(None, alias="X-Terminal-Id")
        ):
            """Heartbeat от терминал"""
            if x_terminal_id:
                self.terminal_manager.update_heartbeat(x_terminal_id)
            
            return {"status": "ok", "timestamp": datetime.now().isoformat()}
        
        @self.app.post("/unregister")
        async def unregister_terminal(
            x_terminal_id: Optional[str] = Header(None, alias="X-Terminal-Id")
        ):
            """Премахване на терминал"""
            if x_terminal_id:
                self.terminal_manager.unregister(x_terminal_id)
            
            return {"status": "unregistered"}
        
        @self.app.websocket("/ws/{terminal_id}")
        async def websocket_endpoint(websocket: WebSocket, terminal_id: str):
            """WebSocket за realtime комуникация"""
            await websocket.accept()
            self.websockets[terminal_id] = websocket
            
            logger.info(f"WebSocket connected: {terminal_id}")
            
            try:
                while True:
                    data = await websocket.receive_text()
                    await self._handle_websocket_message(terminal_id, data)
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: {terminal_id}")
            finally:
                self.websockets.pop(terminal_id, None)
        
        @self.app.get("/access/hardware")
        async def get_hardware_devices():
            """Списък с хардуерни устройства"""
            return JSONResponse(content=self.relay_controller.get_all_devices())
        
        @self.app.post("/access/hardware")
        async def add_hardware_device(data: dict):
            """Добавяне на хардуерно устройство"""
            try:
                device_id = self.relay_controller.add_device(
                    device_id=data.get("id"),
                    name=data.get("name", ""),
                    ip=data.get("ip", ""),
                    port=data.get("port", 6722),
                    device_type=data.get("type", "sr201"),
                    relay_1_duration=data.get("relay_1_duration", 500),
                    relay_2_duration=data.get("relay_2_duration", 500),
                    relay_1_manual=data.get("relay_1_manual", False),
                    relay_2_manual=data.get("relay_2_manual", False),
                    active=data.get("active", True)
                )
                return JSONResponse(
                    content={"status": "created", "id": device_id},
                    status_code=201
                )
            except Exception as e:
                logger.error(f"Error adding hardware device: {e}")
                return JSONResponse(
                    content={"status": "error", "message": str(e)},
                    status_code=400
                )
        
        @self.app.get("/access/hardware/{device_id}")
        async def get_hardware_device(device_id: str):
            """Информация за устройство"""
            device = self.relay_controller.get_device(device_id)
            if not device:
                return JSONResponse(
                    content={"status": "error", "message": "Device not found"},
                    status_code=404
                )
            return JSONResponse(content=device.to_dict())
        
        @self.app.put("/access/hardware/{device_id}")
        async def update_hardware_device(device_id: str, data: dict):
            """Обновяване на устройство"""
            success = self.relay_controller.update_device(
                device_id=device_id,
                name=data.get("name"),
                ip=data.get("ip"),
                port=data.get("port"),
                relay_1_duration=data.get("relay_1_duration"),
                relay_2_duration=data.get("relay_2_duration"),
                relay_1_manual=data.get("relay_1_manual"),
                relay_2_manual=data.get("relay_2_manual"),
                active=data.get("active")
            )
            if not success:
                return JSONResponse(
                    content={"status": "error", "message": "Device not found"},
                    status_code=404
                )
            return JSONResponse(content={"status": "updated"})
        
        @self.app.delete("/access/hardware/{device_id}")
        async def delete_hardware_device(device_id: str):
            """Изтриване на устройство"""
            success = self.relay_controller.remove_device(device_id)
            if not success:
                return JSONResponse(
                    content={"status": "error", "message": "Device not found"},
                    status_code=404
                )
            return JSONResponse(content={"status": "deleted"})
        
        @self.app.post("/access/hardware/{device_id}/test")
        async def test_hardware_device(device_id: str):
            """Тест на устройство"""
            result = await self.relay_controller.test_device(device_id)
            return JSONResponse(content=result)
        
        @self.app.post("/access/hardware/{device_id}/test-all")
        async def test_all_hardware_devices():
            """Тест на всички устройства"""
            results = await self.relay_controller.test_all_devices()
            return JSONResponse(content=results)
        
        @self.app.post("/access/hardware/{device_id}/trigger")
        async def trigger_relay(device_id: str, data: dict):
            """Активиране на реле"""
            relay_number = data.get("relay_number", 1)
            duration_ms = data.get("duration_ms")
            
            result = await self.relay_controller.trigger(device_id, relay_number, duration_ms)
            return JSONResponse(content=result)
        
        @self.app.post("/access/hardware/{device_id}/on")
        async def relay_on(device_id: str, data: dict):
            """Ръчно включване на реле"""
            relay_number = data.get("relay_number", 1)
            result = await self.relay_controller.on(device_id, relay_number)
            return JSONResponse(content=result)
        
        @self.app.post("/access/hardware/{device_id}/off")
        async def relay_off(device_id: str, data: dict):
            """Ръчно изключване на реле"""
            relay_number = data.get("relay_number", 1)
            result = await self.relay_controller.off(device_id, relay_number)
            return JSONResponse(content=result)
        
        @self.app.get("/access/zones")
        async def get_zones():
            """Списък със зони"""
            return JSONResponse(content=zone_manager.get_all_zones())
        
        @self.app.post("/access/zones")
        async def add_zone(data: dict):
            """Добавяне на зона"""
            valid, msg = zone_manager.validate_zone_dependencies(data)
            if not valid:
                return JSONResponse(content={"status": "error", "message": msg}, status_code=400)
            
            zone_id = zone_manager.add_zone(data)
            return JSONResponse(content={"status": "created", "id": zone_id}, status_code=201)
        
        @self.app.get("/access/zones/{zone_id}")
        async def get_zone(zone_id: str):
            """Информация за зона"""
            zone = zone_manager.get_zone(zone_id)
            if not zone:
                return JSONResponse(content={"status": "error", "message": "Zone not found"}, status_code=404)
            return JSONResponse(content=zone.to_dict())
        
        @self.app.put("/access/zones/{zone_id}")
        async def update_zone(zone_id: str, data: dict):
            """Обновяване на зона"""
            valid, msg = zone_manager.validate_zone_dependencies(data)
            if not valid:
                return JSONResponse(content={"status": "error", "message": msg}, status_code=400)
            
            success = zone_manager.update_zone(zone_id, data)
            if not success:
                return JSONResponse(content={"status": "error", "message": "Zone not found"}, status_code=404)
            return JSONResponse(content={"status": "updated"})
        
        @self.app.delete("/access/zones/{zone_id}")
        async def delete_zone(zone_id: str):
            """Изтриване на зона"""
            success = zone_manager.remove_zone(zone_id)
            if not success:
                return JSONResponse(content={"status": "error", "message": "Zone not found"}, status_code=404)
            return JSONResponse(content={"status": "deleted"})
        
        @self.app.get("/access/doors")
        async def get_doors():
            """Списък с врати"""
            return JSONResponse(content=zone_manager.get_all_doors())
        
        @self.app.post("/access/doors")
        async def add_door(data: dict):
            """Добавяне на врата"""
            door_id = zone_manager.add_door(data)
            return JSONResponse(content={"status": "created", "id": door_id}, status_code=201)
        
        @self.app.get("/access/doors/{door_id}")
        async def get_door(door_id: str):
            """Информация за врата"""
            door = zone_manager.get_door(door_id)
            if not door:
                return JSONResponse(content={"status": "error", "message": "Door not found"}, status_code=404)
            return JSONResponse(content=door.to_dict())
        
        @self.app.put("/access/doors/{door_id}")
        async def update_door(door_id: str, data: dict):
            """Обновяване на врата"""
            success = zone_manager.update_door(door_id, data)
            if not success:
                return JSONResponse(content={"status": "error", "message": "Door not found"}, status_code=404)
            return JSONResponse(content={"status": "updated"})
        
        @self.app.delete("/access/doors/{door_id}")
        async def delete_door(door_id: str):
            """Изтриване на врата"""
            success = zone_manager.remove_door(door_id)
            if not success:
                return JSONResponse(content={"status": "error", "message": "Door not found"}, status_code=404)
            return JSONResponse(content={"status": "deleted"})
        
        @self.app.post("/access/doors/{door_id}/trigger")
        async def trigger_door(door_id: str):
            """Ръчно отваряне на врата"""
            door = zone_manager.get_door(door_id)
            if not door:
                return JSONResponse(content={"status": "error", "message": "Door not found"}, status_code=404)
            
            result = await self.relay_controller.trigger(door.device_id, door.relay_number)
            return JSONResponse(content=result)
        
        @self.app.post("/access/verify")
        async def verify_access(data: dict):
            """Проверка на достъп (с поддръжка за клъстер)"""
            if self.cluster_manager and not self.cluster_manager.is_master():
                master_url = self.cluster_manager.get_master_url()
                if master_url:
                    return await self._proxy_to_master("/access/verify", data)
            
            user_id = data.get("user_id", "")
            terminal_id = data.get("terminal_id", "")
            action = data.get("action", "enter")
            
            result = await access_controller.check_access(user_id, terminal_id, action)
            return JSONResponse(content=result)
        
        @self.app.post("/access/scan")
        async def access_scan(data: dict):
            """Сканиране за достъп (с поддръжка за клъстер)"""
            if self.cluster_manager and not self.cluster_manager.is_master():
                master_url = self.cluster_manager.get_master_url()
                if master_url:
                    return await self._proxy_to_master("/access/scan", data)

            user_id = data.get("user_id", "")
            user_name = data.get("user_name", "")
            terminal_id = data.get("terminal_id", "")
            method = data.get("method", "qr_scan")
            
            result = await access_controller.grant_access(
                user_id=user_id,
                user_name=user_name,
                terminal_id=terminal_id,
                method=method,
                action="enter"
            )
            return JSONResponse(content=result)

        @self.app.post("/cluster/check-access")
        async def cluster_check_access(data: dict, x_secret: str = Header(None, alias="X-Cluster-Secret")):
            """Вътрешен ендпоинт за Slave устройства"""
            if x_secret != config.get("cluster.shared_secret"):
                return JSONResponse(content={"status": "error", "message": "Unauthorized cluster request"}, status_code=401)
            
            # Изпълняваме локално на Master-а
            return await access_scan(data)

        @self.app.post("/cluster/sync-logs")
        async def cluster_sync_logs(logs: List[dict], x_secret: str = Header(None, alias="X-Cluster-Secret")):
            """Приема натрупани логове от Slave устройства с верификация на подписа"""
            if x_secret != config.get("cluster.shared_secret"):
                return JSONResponse(content={"status": "error", "message": "Unauthorized cluster request"}, status_code=401)
            
            count = 0
            for log in logs:
                # 1. Проверка на подписа (Integrity Check)
                if not access_controller.verify_log_signature(log):
                    logger.warning(f"Invalid log signature for log ID: {log.get('id')}. Potential tampering detected!")
                    continue

                # 2. Обновяване на състоянието на Master-а
                user_id = log.get("user_id")
                zone_id = log.get("zone_id")
                action = log.get("action")
                result = log.get("result")

                if result == "granted" and user_id and zone_id:
                    if action == "enter":
                        access_controller.zone_state.enter_zone(user_id, zone_id)
                        access_controller.anti_passback.record(user_id, zone_id, "in")
                    else:
                        access_controller.zone_state.leave_zone(user_id, zone_id)
                        access_controller.anti_passback.record(user_id, zone_id, "out")
                
                # 3. Запис в локалната база на Master-а
                access_controller._create_log(**log)
                count += 1
            
            logger.info(f"Verified and synced {count} logs from cluster peer")
            return {"status": "success", "synced_ids": [l.get("id") for l in logs]}
        
        @self.app.post("/cluster/sync-state")
        async def cluster_sync_state(state: dict, x_secret: str = Header(None, alias="X-Cluster-Secret")):
            """Синхронизира зона state между Masters"""
            if x_secret != config.get("cluster.shared_secret"):
                return JSONResponse(content={"status": "error", "message": "Unauthorized cluster request"}, status_code=401)
            
            if not access_controller.zone_state:
                return {"status": "error", "message": "Zone state not initialized"}
            
            # Merge the state (keeps newer entries)
            count = access_controller.zone_state.merge_state(state)
            
            return {
                "status": "success", 
                "imported": count,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        @self.app.get("/cluster/state")
        async def cluster_get_state(x_secret: str = Header(None, alias="X-Cluster-Secret")):
            """Връща локалния зона state за синхронизация"""
            if x_secret != config.get("cluster.shared_secret"):
                return JSONResponse(content={"status": "error", "message": "Unauthorized cluster request"}, status_code=401)
            
            if not access_controller.zone_state:
                return {"status": "error", "message": "Zone state not initialized"}
            
            return access_controller.zone_state.export_state()
        
        @self.app.post("/cluster/config")
        async def cluster_receive_config(config_data: dict, x_secret: str = Header(None, alias="X-Cluster-Secret")):
            """Получава конфигурация от Master"""
            if x_secret != config.get("cluster.shared_secret"):
                return JSONResponse(content={"status": "error", "message": "Unauthorized cluster request"}, status_code=401)
            
            result = zone_manager.import_config(config_data, merge=True)
            
            return {
                "status": "success",
                "imported": result
            }
        
        @self.app.get("/cluster/peers")
        async def cluster_get_peers(x_secret: str = Header(None, alias="X-Cluster-Secret")):
            """Връща списък с всички peers в клъстера"""
            if x_secret != config.get("cluster.shared_secret"):
                return JSONResponse(content={"status": "error", "message": "Unauthorized cluster request"}, status_code=401)
            
            from gateway.cluster.discovery import discovery_manager
            return {
                "local_ip": discovery_manager.get_local_ip(),
                "peers": [
                    {
                        "ip": ip,
                        "hostname": peer.hostname,
                        "role": peer.role,
                        "score": peer.score,
                        "priority": peer.priority,
                        "last_seen": peer.last_seen.isoformat()
                    }
                    for ip, peer in discovery_manager.peers.items()
                ]
            }
        
        @self.app.post("/access/exit")
        async def access_exit(data: dict):
            """Изход от зона"""
            user_id = data.get("user_id", "")
            terminal_id = data.get("terminal_id", "")
            
            result = await access_controller.check_access(user_id, terminal_id, "exit")
            if result["allowed"]:
                if access_controller.zone_state:
                    access_controller.zone_state.leave_zone(user_id, result["zone"]["id"])
                    access_controller.anti_passback.record(user_id, result["zone"]["id"], "out")
            
            return JSONResponse(content=result)
        
        @self.app.get("/access/state")
        async def get_access_state():
            """Активни потребители"""
            users = access_controller.get_active_users()
            return JSONResponse(content={"users": users})
        
        @self.app.get("/access/state/{user_id}")
        async def get_user_state(user_id: str):
            """Състояние на потребител"""
            state = access_controller.get_user_state(user_id)
            return JSONResponse(content=state)
        
        @self.app.post("/access/state/reset")
        async def reset_access_state():
            """Ресет на всички потребители"""
            access_controller.reset_all_users()
            return JSONResponse(content={"status": "reset"})
        
        @self.app.get("/access/logs")
        async def get_access_logs(limit: int = 100):
            """Логове за достъп"""
            logs = access_controller.get_logs(limit)
            return JSONResponse(content={"logs": logs})
        
        @self.app.get("/access/codes")
        async def get_codes():
            """Списък с кодове"""
            codes = code_manager.get_codes()
            return JSONResponse(content={"codes": codes})
        
        @self.app.post("/access/codes")
        async def create_code(data: dict):
            """Създаване на код"""
            code = code_manager.create_code(data)
            return JSONResponse(content={"status": "created", "code": code}, status_code=201)
        
        @self.app.post("/access/codes/generate")
        async def generate_code(data: dict):
            """Генериране на код"""
            code = code_manager.create_code(data)
            return JSONResponse(content={"code": code})
        
        @self.app.get("/access/codes/{code}")
        async def get_code(code: str):
            """Информация за код"""
            access_code = code_manager.get_code(code)
            if not access_code:
                return JSONResponse(content={"status": "error", "message": "Code not found"}, status_code=404)
            return JSONResponse(content=access_code.to_dict())
        
        @self.app.post("/access/codes/{code}/revoke")
        async def revoke_code(code: str):
            """Отнемане на код"""
            success = code_manager.revoke_code(code)
            if not success:
                return JSONResponse(content={"status": "error", "message": "Code not found"}, status_code=404)
            return JSONResponse(content={"status": "revoked"})
        
        @self.app.delete("/access/codes/{code}")
        async def delete_code(code: str):
            """Изтриване на код"""
            success = code_manager.delete_code(code)
            if not success:
                return JSONResponse(content={"status": "error", "message": "Code not found"}, status_code=404)
            return JSONResponse(content={"status": "deleted"})
    
    async def _proxy_to_master(self, endpoint: str, data: dict) -> dict:
        """Пренасочва заявка към Master гейтуея в клъстера"""
        if not self.cluster_manager:
            return {"status": "error", "message": "Cluster manager not initialized"}
            
        master_url = self.cluster_manager.get_master_url()
        if not master_url:
            # Fallback към локално взимане на решения, ако няма Master (Phase 2 - Failover)
            return await access_controller.grant_access(**data)

        import aiohttp
        url = f"{master_url}/cluster/check-access"
        headers = {
            "X-Cluster-Secret": config.get("cluster.shared_secret"),
            "Content-Type": "application/json",
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers, timeout=5) as response:
                    return await response.json()
        except Exception as e:
            logger.error(f"Cluster Master proxy error: {e}")
            # Fallback - автономно решение при отпадане на Master
            return await access_controller.grant_access(**data)

    async def _proxy_to_backend(self, endpoint: str, data: dict = None, method: str = "POST") -> dict:
        """Проксиране на заявка към бекенд"""
        import aiohttp
        
        url = f"{config.backend_url}{endpoint}"
        headers = {
            "X-Kiosk-Secret": config.api_key,
            "Content-Type": "application/json",
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                if method == "GET":
                    async with session.get(url, headers=headers) as response:
                        return await response.json()
                else:
                    async with session.post(url, json=data, headers=headers) as response:
                        return await response.json()
        except Exception as e:
            logger.error(f"Backend proxy error: {e}")
            return {
                "status": "error",
                "message": f"Failed to connect to backend: {str(e)}"
            }
    
    async def _handle_websocket_message(self, terminal_id: str, message: str):
        """Обработка на WebSocket съобщение"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "heartbeat":
                self.terminal_manager.update_heartbeat(terminal_id)
            
            elif msg_type == "print_status":
                printer_id = data.get("printer_id")
                # Handle print status update
                pass
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from terminal {terminal_id}")
    
    async def broadcast_to_terminals(self, message: dict):
        """Изпраща съобщение до всички свързани терминали"""
        for terminal_id, ws in self.websockets.items():
            try:
                await ws.send_json(message)
            except:
                pass
