import logging
import uuid
from typing import Optional, Dict, List, Any
from datetime import datetime

from gateway.devices.sr201_relay import SR201Relay

logger = logging.getLogger(__name__)


class RelayController:
    """
    Мениджър на всички релейни устройства
    
    Поддържа:
    - SR201 Ethernet Relay
    """
    
    def __init__(self):
        self.devices: Dict[str, SR201Relay] = {}
    
    def add_device(
        self,
        device_id: Optional[str] = None,
        name: str = "",
        ip: str = "",
        port: int = 6722,
        device_type: str = "sr201",
        relay_1_duration: int = 500,
        relay_2_duration: int = 500,
        relay_1_manual: bool = False,
        relay_2_manual: bool = False,
        active: bool = True,
        mac_address: str = ""
    ) -> str:
        """
        Добавя ново устройство
        
        Returns:
            device_id на новото устройство
        """
        if not device_id:
            device_id = f"relay_{uuid.uuid4().hex[:8]}"
        
        if device_id in self.devices:
            logger.warning(f"Device {device_id} already exists, updating")
        
        if device_type == "sr201":
            relay = SR201Relay(
                device_id=device_id,
                name=name,
                ip=ip,
                port=port,
                mac_address=mac_address,
                relay_1_duration=relay_1_duration,
                relay_2_duration=relay_2_duration,
                relay_1_manual=relay_1_manual,
                relay_2_manual=relay_2_manual
            )
            self.devices[device_id] = relay
            logger.info(f"Added SR201 device: {device_id} at {ip}")
        else:
            raise ValueError(f"Unknown device type: {device_type}")
        
        return device_id
    
    def remove_device(self, device_id: str) -> bool:
        """Премахва устройство"""
        if device_id in self.devices:
            del self.devices[device_id]
            logger.info(f"Removed device: {device_id}")
            return True
        return False
    
    def get_device(self, device_id: str) -> Optional[SR201Relay]:
        """Връща устройство по ID"""
        return self.devices.get(device_id)
    
    def get_all_devices(self) -> List[Dict[str, Any]]:
        """Връща списък с всички устройства"""
        return [device.to_dict() for device in self.devices.values()]
    
    def get_device_by_ip(self, ip: str) -> Optional[SR201Relay]:
        """Връща устройство по IP"""
        for device in self.devices.values():
            if device.ip == ip:
                return device
        return None
    
    def update_device(
        self,
        device_id: str,
        name: Optional[str] = None,
        ip: Optional[str] = None,
        port: Optional[int] = None,
        relay_1_duration: Optional[int] = None,
        relay_2_duration: Optional[int] = None,
        relay_1_manual: Optional[bool] = None,
        relay_2_manual: Optional[bool] = None,
        active: Optional[bool] = None
    ) -> bool:
        """Обновява настройките на устройство"""
        device = self.devices.get(device_id)
        if not device:
            return False
        
        if name is not None:
            device.name = name
        if ip is not None:
            device.ip = ip
        if port is not None:
            device.port = port
        if relay_1_duration is not None:
            device.relay_1_duration = max(0, min(relay_1_duration, 10000))
        if relay_2_duration is not None:
            device.relay_2_duration = max(0, min(relay_2_duration, 10000))
        if relay_1_manual is not None:
            device.relay_1_manual = relay_1_manual
        if relay_2_manual is not None:
            device.relay_2_manual = relay_2_manual
        
        logger.info(f"Updated device: {device_id}")
        return True
    
    def toggle_relay_mode(self, device_id: str, relay_number: int, manual: bool) -> Dict[str, Any]:
        """Сменя режима на реле (ръчен/автоматичен)"""
        device = self.devices.get(device_id)
        if not device:
            return {"success": False, "message": "Device not found"}
        
        if relay_number == 1:
            device.relay_1_manual = manual
        elif relay_number == 2:
            device.relay_2_manual = manual
        else:
            return {"success": False, "message": "Invalid relay number"}
        
        logger.info(f"Toggled relay {relay_number} to {'manual' if manual else 'auto'} mode: {device_id}")
        return {"success": True, "message": f"Реле {relay_number}: {'Ръчен' if manual else 'Автоматичен'} режим"}
    
    def set_duration(self, device_id: str, relay_number: int, duration: int) -> Dict[str, Any]:
        """Сменя времето на релето"""
        device = self.devices.get(device_id)
        if not device:
            return {"success": False, "message": "Device not found"}
        
        duration = max(0, min(duration, 10000))
        
        if relay_number == 1:
            device.relay_1_duration = duration
        elif relay_number == 2:
            device.relay_2_duration = duration
        else:
            return {"success": False, "message": "Invalid relay number"}
        
        logger.info(f"Set relay {relay_number} duration to {duration}ms: {device_id}")
        return {"success": True, "message": f"Реле {relay_number}: {duration}ms"}
    
    async def trigger(
        self,
        device_id: str,
        relay_number: int,
        duration_ms: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Активира реле (импулс)
        
        Returns:
            {"success": bool, "message": str}
        """
        device = self.devices.get(device_id)
        if not device:
            return {
                "success": False,
                "message": f"Device {device_id} not found"
            }
        
        try:
            success = await device.pulse(relay_number, duration_ms)
            return {
                "success": success,
                "message": "Triggered" if success else "Failed"
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }
    
    async def turn_on(
        self,
        device_id: str,
        relay_number: int
    ) -> Dict[str, Any]:
        """
        Включва реле (без проверка за ръчен режим)
        """
        device = self.devices.get(device_id)
        if not device:
            return {
                "success": False,
                "message": f"Device {device_id} not found"
            }
        
        try:
            success = await device.on(relay_number)
            return {
                "success": success,
                "message": f"Реле {relay_number} включено" if success else "Грешка"
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }
    
    async def turn_off(
        self,
        device_id: str,
        relay_number: int
    ) -> Dict[str, Any]:
        """
        Изключва реле
        """
        device = self.devices.get(device_id)
        if not device:
            return {
                "success": False,
                "message": f"Device {device_id} not found"
            }
        
        try:
            success = await device.off(relay_number)
            return {
                "success": success,
                "message": f"Реле {relay_number} изключено" if success else "Грешка"
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }
    
    async def on(
        self,
        device_id: str,
        relay_number: int
    ) -> Dict[str, Any]:
        """
        Включва реле (ръчен режим)
        """
        device = self.devices.get(device_id)
        if not device:
            return {
                "success": False,
                "message": f"Device {device_id} not found"
            }
        
        if not device.relay_1_manual and relay_number == 1:
            return {
                "success": False,
                "message": "Relay 1 is not in manual mode"
            }
        if not device.relay_2_manual and relay_number == 2:
            return {
                "success": False,
                "message": "Relay 2 is not in manual mode"
            }
        
        try:
            success = await device.on(relay_number)
            return {
                "success": success,
                "message": "Relay ON" if success else "Failed"
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }
    
    async def off(
        self,
        device_id: str,
        relay_number: int
    ) -> Dict[str, Any]:
        """
        Изключва реле
        """
        device = self.devices.get(device_id)
        if not device:
            return {
                "success": False,
                "message": f"Device {device_id} not found"
            }
        
        try:
            success = await device.off(relay_number)
            return {
                "success": success,
                "message": "Relay OFF" if success else "Failed"
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }
    
    async def test_device(self, device_id: str) -> Dict[str, Any]:
        """Тества връзката с устройство"""
        device = self.devices.get(device_id)
        if not device:
            return {
                "success": False,
                "message": f"Device {device_id} not found",
                "online": False
            }
        
        try:
            status = await device.status()
            return {
                "success": status.get("online", False),
                "message": "Device online" if status.get("online") else "Device offline",
                "online": status.get("online", False),
                "status": status
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "online": False
            }
    
    async def change_ip(self, device_id: str, new_ip: str, new_netmask: str = "255.255.255.0", new_gateway: str = "192.168.1.1") -> Dict[str, Any]:
        """Сменя IP адреса на устройството"""
        device = self.devices.get(device_id)
        if not device:
            return {
                "success": False,
                "message": f"Device {device_id} not found"
            }
        
        old_ip = device.ip
        
        try:
            import socket
            import time
            import random
            session_id = str(random.randint(1000, 9999))
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((old_ip, 5111))
            
            time.sleep(0.5)
            
            # Start session - query config (#1 + session_id)
            cmd1 = f"#1{session_id};".encode()
            sock.send(cmd1)
            response1 = sock.recv(500)
            
            time.sleep(0.3)
            
            # Set new IP (#2 + session_id)
            cmd2 = f"#2{session_id},{new_ip};".encode()
            sock.send(cmd2)
            response2 = sock.recv(500)
            
            time.sleep(0.3)
            
            # Set subnet mask (#3 + session_id)
            cmd3 = f"#3{session_id},{new_netmask};".encode()
            sock.send(cmd3)
            response3 = sock.recv(500)
            
            time.sleep(0.3)
            
            # Set gateway (#4 + session_id)
            cmd4 = f"#4{session_id},{new_gateway};".encode()
            sock.send(cmd4)
            response4 = sock.recv(500)
            
            time.sleep(0.3)
            
            # Save settings (#7 + session_id)
            cmd5 = f"#7{session_id};".encode()
            sock.send(cmd5)
            response5 = sock.recv(500)
            
            sock.close()
            
            logger.info(f"IP change responses: IP={response2}, NM={response3}, GW={response4}, Save={response5}")
            
            # Check responses for OK
            r2 = response2.decode('utf-8', errors='ignore')
            r5 = response5.decode('utf-8', errors='ignore')
            
            if "OK" in r2 and "OK" in r5:
                device.ip = new_ip
                return {
                    "success": True,
                    "message": f"IP: {new_ip}, Mask: {new_netmask}, GW: {new_gateway}"
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed. IP: {r2[:20]}, Save: {r5[:20]}"
                }
        except Exception as e:
            logger.error(f"IP change error: {e}")
            return {
                "success": False,
                "message": str(e)
            }
    
    async def test_all_devices(self) -> List[Dict[str, Any]]:
        """Тества всички устройства"""
        results = []
        for device_id in self.devices:
            result = await self.test_device(device_id)
            result["device_id"] = device_id
            results.append(result)
        return results
    
    def load_from_config(self, config: List[Dict[str, Any]]):
        """Зарежда устройства от конфигурация"""
        for device_config in config:
            try:
                self.add_device(
                    device_id=device_config.get("id"),
                    name=device_config.get("name", ""),
                    ip=device_config.get("ip", ""),
                    port=device_config.get("port", 6722),
                    device_type=device_config.get("type", "sr201"),
                    relay_1_duration=device_config.get("relay_1_duration", 500),
                    relay_2_duration=device_config.get("relay_2_duration", 500),
                    relay_1_manual=device_config.get("relay_1_manual", False),
                    relay_2_manual=device_config.get("relay_2_manual", False),
                    active=device_config.get("active", True)
                )
            except Exception as e:
                logger.error(f"Error loading device from config: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Връща статус на всички устройства"""
        return {
            "total": len(self.devices),
            "devices": self.get_all_devices()
        }


relay_controller = RelayController()
