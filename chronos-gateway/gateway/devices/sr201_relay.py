import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class SR201Relay:
    """
    Управление на SR201 Ethernet Relay устройство
    
    SR201 поддържа:
    - 2 релета
    - TCP комуникация на порт 6722
    - Команди: {n}ON, {n}OF, {n}R, 0R
    """
    
    DEFAULT_PORT = 6722
    DEFAULT_DURATION_MS = 500
    MIN_DURATION_MS = 0
    MAX_DURATION_MS = 10000
    
    def __init__(
        self,
        device_id: str,
        name: str,
        ip: str,
        port: int = DEFAULT_PORT,
        relay_1_duration: int = DEFAULT_DURATION_MS,
        relay_2_duration: int = DEFAULT_DURATION_MS,
        relay_1_manual: bool = False,
        relay_2_manual: bool = False,
        mac_address: str = ""
    ):
        self.device_id = device_id
        self.name = name
        self.ip = ip
        self.port = port
        self.mac_address = mac_address
        
        self.relay_1_duration = max(self.MIN_DURATION_MS, min(relay_1_duration, self.MAX_DURATION_MS))
        self.relay_2_duration = max(self.MIN_DURATION_MS, min(relay_2_duration, self.MAX_DURATION_MS))
        
        self.relay_1_manual = relay_1_manual
        self.relay_2_manual = relay_2_manual
        
        self._is_online = False
        self._last_status_check = None
    
    def get_duration(self, relay_number: int) -> int:
        """Връща конфигурираното време за релето"""
        if relay_number == 1:
            return self.relay_1_duration
        elif relay_number == 2:
            return self.relay_2_duration
        return self.DEFAULT_DURATION_MS
    
    async def _send_command(self, command: str, timeout: float = 3.0) -> bool:
        """Изпраща команда към SR201 през TCP"""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.ip, self.port),
                timeout=timeout
            )
            
            writer.write(command.encode())
            await writer.drain()
            
            writer.close()
            await writer.wait_closed()
            
            logger.debug(f"SR201 {self.device_id}: Sent command '{command}'")
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"SR201 {self.device_id}: Timeout sending command '{command}' to {self.ip}:{self.port}")
            return False
        except ConnectionRefusedError:
            logger.error(f"SR201 {self.device_id}: Connection refused to {self.ip}:{self.port}")
            self._is_online = False
            return False
        except Exception as e:
            logger.error(f"SR201 {self.device_id}: Error sending command '{command}': {e}")
            return False
    
    async def on(self, relay_number: int) -> bool:
        """
        Включва реле (затваря контакта)
        """
        if relay_number not in (1, 2):
            logger.error(f"SR201 {self.device_id}: Invalid relay number {relay_number}")
            return False
        
        command = f"{relay_number}1" if relay_number == 1 else "12"
        success = await self._send_command(command)
        
        if success:
            logger.info(f"SR201 {self.device_id}: Relay {relay_number} turned ON")
        
        return success
    
    async def off(self, relay_number: int) -> bool:
        """
        Изключва реле (отваря контакта)
        """
        if relay_number not in (1, 2):
            logger.error(f"SR201 {self.device_id}: Invalid relay number {relay_number}")
            return False
        
        command = f"2{relay_number}"
        success = await self._send_command(command)
        
        if success:
            logger.info(f"SR201 {self.device_id}: Relay {relay_number} turned OFF")
        
        return success
    
    async def pulse(self, relay_number: int, duration_ms: Optional[int] = None) -> bool:
        """
        Активира реле за определено време (ВКЛ → чака → ИЗКЛ)
        
        Args:
            relay_number: 1 или 2
            duration_ms: продължителност в милисекунди (по подразбиране от конфигурацията)
        """
        if relay_number not in (1, 2):
            logger.error(f"SR201 {self.device_id}: Invalid relay number {relay_number}")
            return False
        
        if duration_ms is None:
            duration_ms = self.get_duration(relay_number)
        
        duration_ms = max(self.MIN_DURATION_MS, min(duration_ms, self.MAX_DURATION_MS))
        
        logger.info(f"SR201 {self.device_id}: Pulsing relay {relay_number} for {duration_ms}ms")
        
        success_on = await self.on(relay_number)
        if not success_on:
            return False
        
        if duration_ms > 0:
            await asyncio.sleep(duration_ms / 1000.0)
        
        success_off = await self.off(relay_number)
        
        if success_off:
            logger.info(f"SR201 {self.device_id}: Relay {relay_number} pulse completed")
        
        return success_off
    
    async def trigger(self, relay_number: int, duration_ms: Optional[int] = None) -> bool:
        """
        Псевдоним на pulse() за съвместимост
        """
        return await self.pulse(relay_number, duration_ms)
    
    async def status(self) -> Dict[str, Any]:
        """
        Връща статус на устройството
        """
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.ip, self.port),
                timeout=3.0
            )
            
            writer.write(b"0R")
            await writer.drain()
            
            response = await asyncio.wait_for(reader.read(100), timeout=3.0)
            
            writer.close()
            await writer.wait_closed()
            
            self._is_online = True
            self._last_status_check = datetime.now()
            
            return {
                "online": True,
                "response": response.decode('utf-8', errors='ignore') if response else "",
                "timestamp": self._last_status_check.isoformat()
            }
            
        except Exception as e:
            self._is_online = False
            self._last_status_check = datetime.now()
            
            return {
                "online": False,
                "error": str(e),
                "timestamp": self._last_status_check.isoformat()
            }
    
    async def test_connection(self) -> bool:
        """Тества връзката с устройството"""
        result = await self.status()
        return result.get("online", False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Връща конфигурацията като речник"""
        return {
            "device_id": self.device_id,
            "id": self.device_id, # Compatibility
            "name": self.name,
            "ip": self.ip,
            "port": self.port,
            "mac_address": self.mac_address,
            "type": "sr201",
            "relay_1_duration": self.relay_1_duration,
            "relay_2_duration": self.relay_2_duration,
            "relay_1_manual": self.relay_1_manual,
            "relay_2_manual": self.relay_2_manual,
            "is_online": self._is_online,
            "online": self._is_online,
            "last_check": self._last_status_check.isoformat() if self._last_status_check else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SR201Relay':
        """Създава инстанция от речник"""
        return cls(
            device_id=data.get("device_id", ""),
            name=data.get("name", ""),
            ip=data.get("ip", ""),
            port=data.get("port", cls.DEFAULT_PORT),
            mac_address=data.get("mac_address", ""),
            relay_1_duration=data.get("relay_1_duration", cls.DEFAULT_DURATION_MS),
            relay_2_duration=data.get("relay_2_duration", cls.DEFAULT_DURATION_MS),
            relay_1_manual=data.get("relay_1_manual", False),
            relay_2_manual=data.get("relay_2_manual", False)
        )
