"""
Хардуерна абстракция за контролери на врати: OSDP, Wiegand, Virtual.

OSDP — RS-485 протокол (IEEE 1795.1)
Wiegand — стандартен 26/34-bit паралелен интерфейс
Virtual — емулация за тестове без физически хардуер

Всички драйвери имплементират `DoorDriver` protocol class.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Callable, Dict, Any, List

logger = logging.getLogger(__name__)


@dataclass
class CardData:
    """Данни от карта/ключодържател"""
    raw: str
    facility_code: Optional[int] = None
    card_number: Optional[int] = None
    bit_length: int = 26
    wiegand_format: str = "26bit"
    timestamp: float = 0.0


@dataclass
class ReaderState:
    """Състояние на четец"""
    online: bool = False
    last_card: Optional[CardData] = None
    last_activity: float = 0.0
    tamper: bool = False
    door_open: bool = False
    voltage: float = 12.0


class DoorDriver(ABC):
    """Abstract base class за хардуерен драйвер на врата"""

    def __init__(self, door_id: str, config: dict):
        self.door_id = door_id
        self.config = config
        self._reader_state = ReaderState()
        self._on_card: Optional[Callable[[CardData], None]] = None

    @abstractmethod
    async def connect(self) -> bool:
        """Свързване с хардуера"""

    @abstractmethod
    async def disconnect(self):
        """Прекъсване на връзката"""

    @abstractmethod
    async def unlock(self, duration: float = 5.0) -> bool:
        """Отключва вратата за N секунди"""

    @abstractmethod
    async def lock(self) -> bool:
        """Заключва вратата"""

    @abstractmethod
    async def get_state(self) -> ReaderState:
        """Връща текущото състояние на четеца"""

    @abstractmethod
    async def beep(self, duration: float = 0.5) -> bool:
        """Звуков сигнал на четеца"""

    @abstractmethod
    async def led(self, color: str = "green", on: bool = True) -> bool:
        """LED индикация на четеца"""

    def on_card(self, callback: Callable[[CardData], None]):
        """Регистрира callback при разчитане на карта"""
        self._on_card = callback

    @property
    def is_online(self) -> bool:
        return self._reader_state.online


class VirtualDriver(DoorDriver):
    """Virtual емулация — не изисква физически хардуер"""

    def __init__(self, door_id: str, config: dict):
        super().__init__(door_id, config)
        self._locked = True

    async def connect(self) -> bool:
        self._reader_state.online = True
        self._reader_state.last_activity = time.time()
        logger.info(f"[VirtualDriver:{self.door_id}] Connected")
        return True

    async def disconnect(self):
        self._reader_state.online = False
        logger.info(f"[VirtualDriver:{self.door_id}] Disconnected")

    async def unlock(self, duration: float = 5.0) -> bool:
        self._locked = False
        self._reader_state.door_open = True
        logger.info(f"[VirtualDriver:{self.door_id}] Unlocked for {duration}s")
        asyncio.ensure_future(self._auto_lock(duration))
        return True

    async def _auto_lock(self, delay: float):
        await asyncio.sleep(delay)
        self._locked = True
        self._reader_state.door_open = False

    async def lock(self) -> bool:
        self._locked = True
        self._reader_state.door_open = False
        logger.info(f"[VirtualDriver:{self.door_id}] Locked")
        return True

    async def get_state(self) -> ReaderState:
        return self._reader_state

    async def beep(self, duration: float = 0.5) -> bool:
        logger.info(f"[VirtualDriver:{self.door_id}] Beep {duration}s")
        return True

    async def led(self, color: str = "green", on: bool = True) -> bool:
        logger.info(f"[VirtualDriver:{self.door_id}] LED {color} {'ON' if on else 'OFF'}")
        return True


class WiegandDriver(DoorDriver):
    """
    Wiegand протокол — 26/34/37/40-bit формати.

    Конфигурация:
        device: /dev/ttyUSB0 или tcp://host:port
        bit_length: 26 (default), 34, 37, 40
        beep_pin: GPIO пин за бузер
        lock_pin: GPIO пин за реле
        door_sensor_pin: GPIO пин за сензор врата
    """

    def __init__(self, door_id: str, config: dict):
        super().__init__(door_id, config)
        self._device = config.get("device", "/dev/ttyUSB0")
        self._bit_length = config.get("bit_length", 26)
        self._reader: Optional[Any] = None

    async def connect(self) -> bool:
        try:
            from serial import Serial
            self._reader = Serial(self._device, 9600, timeout=1)
            self._reader_state.online = True
            self._reader_state.last_activity = time.time()
            logger.info(f"[WiegandDriver:{self.door_id}] Connected to {self._device}")
            asyncio.ensure_future(self._read_loop())
            return True
        except Exception as e:
            logger.error(f"[WiegandDriver:{self.door_id}] Connection failed: {e}")
            return False

    async def disconnect(self):
        self._reader_state.online = False
        if self._reader:
            self._reader.close()

    async def _read_loop(self):
        """Чете Wiegand данни от RS-485 конвертор"""
        while self._reader_state.online and self._reader:
            try:
                data = await asyncio.get_event_loop().run_in_executor(
                    None, self._reader.readline
                )
                if data:
                    raw = data.decode("utf-8", errors="replace").strip()
                    card = self._parse_wiegand(raw)
                    if card and self._on_card:
                        self._on_card(card)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug(f"[WiegandDriver:{self.door_id}] Read error: {e}")
                await asyncio.sleep(0.1)

    def _parse_wiegand(self, raw: str) -> Optional[CardData]:
        """Парсинг на Wiegand raw данни"""
        try:
            bits = raw.replace(" ", "")
            bit_len = len(bits)
            if bit_len not in (26, 34, 37, 40):
                logger.debug(f"[WiegandDriver:{self.door_id}] Unknown bit length: {bit_len}")
                return None

            card_number = int(bits[-bit_len + 1:-1] if bit_len == 26 else bits[-bit_len + 1:-1], 2)
            facility = int(bits[1:9], 2) if bit_len == 26 else None

            return CardData(
                raw=raw,
                facility_code=facility,
                card_number=card_number,
                bit_length=bit_len,
                wiegand_format=f"{bit_len}bit",
                timestamp=time.time()
            )
        except Exception as e:
            logger.debug(f"[WiegandDriver:{self.door_id}] Parse error: {e}")
            return None

    async def unlock(self, duration: float = 5.0) -> bool:
        """Импулс към релето"""
        try:
            if self._reader:
                self._reader_state.door_open = True
                asyncio.ensure_future(self._auto_lock(duration))
                return True
        except Exception as e:
            logger.error(f"[WiegandDriver:{self.door_id}] Unlock failed: {e}")
        return False

    async def _auto_lock(self, delay: float):
        await asyncio.sleep(delay)
        self._reader_state.door_open = False

    async def lock(self) -> bool:
        self._reader_state.door_open = False
        return True

    async def get_state(self) -> ReaderState:
        return self._reader_state

    async def beep(self, duration: float = 0.5) -> bool:
        return True

    async def led(self, color: str = "green", on: bool = True) -> bool:
        return True


class OSDPMessage:
    """OSDP frame — command/response пакет"""

    def __init__(self, address: int = 0x7F, command: int = 0x60, data: bytes = b""):
        self.address = address
        self.command = command
        self.data = data

    def encode(self) -> bytes:
        """Кодира съобщение в OSDP формат (без CRC)"""
        payload = bytes([self.address, 0x04 | (0x04 if len(self.data) > 0 else 0x00), self.command])
        payload += self.data
        payload += bytes([0x00, 0x00])  # CRC placeholder
        return payload

    @classmethod
    def decode(cls, raw: bytes) -> Optional["OSDPMessage"]:
        if len(raw) < 4:
            return None
        return cls(address=raw[0], command=raw[2], data=raw[3:-2])


class OSDPDriver(DoorDriver):
    """
    OSDP протокол (IEEE 1795.1) — RS-485 мулти-дроп.
    Поддържа POLL, READER_LED, READER_BUZZER, OUTPUT_CONTROL, etc.

    Конфигурация:
        device: /dev/ttyAMA0 или tcp://host:port
        address: OSDP адрес (0x00-0x7F)
        baud: 9600 (default), 19200, 38400, 57600, 115200
        use_crc: true (default)
        use_secure_channel: false (default)
    """

    CMD_POLL = 0x60
    CMD_LED = 0x69
    CMD_BUZZER = 0x6A
    CMD_OUTPUT = 0x65
    CMD_READER = 0x77
    REPLY_ACK = 0x40
    REPLY_NAK = 0x4F
    REPLY_READER = 0x77

    def __init__(self, door_id: str, config: dict):
        super().__init__(door_id, config)
        self._device = config.get("device", "/dev/ttyAMA0")
        self._address = config.get("address", 0x7F)
        self._baud = config.get("baud", 9600)
        self._reader: Optional[Any] = None

    async def connect(self) -> bool:
        try:
            from serial import Serial
            self._reader = Serial(self._device, self._baud, timeout=0.1)
            self._reader_state.online = True
            self._reader_state.last_activity = time.time()
            logger.info(f"[OSDPDriver:{self.door_id}] Connected to {self._device} @ {self._baud}")
            asyncio.ensure_future(self._poll_loop())
            return True
        except Exception as e:
            logger.error(f"[OSDPDriver:{self.door_id}] Connection failed: {e}")
            return False

    async def disconnect(self):
        self._reader_state.online = False
        if self._reader:
            self._reader.close()

    async def _poll_loop(self):
        while self._reader_state.online and self._reader:
            try:
                msg = OSDPMessage(address=self._address, command=self.CMD_POLL)
                await asyncio.get_event_loop().run_in_executor(
                    None, self._send_raw, msg.encode()
                )
                reply = await asyncio.get_event_loop().run_in_executor(
                    None, self._reader.read, 16
                )
                if reply:
                    parsed = OSDPMessage.decode(reply)
                    if parsed and parsed.command == self.REPLY_READER and self._on_card:
                        card_number = int.from_bytes(parsed.data[:4], "little")
                        card = CardData(
                            raw=parsed.data.hex(),
                            card_number=card_number,
                            bit_length=0,
                            wiegand_format="osdp",
                            timestamp=time.time()
                        )
                        self._on_card(card)
                self._reader_state.last_activity = time.time()
            except Exception as e:
                logger.debug(f"[OSDPDriver:{self.door_id}] Poll error: {e}")
            await asyncio.sleep(0.2)

    async def _send_raw(self, data: bytes):
        if self._reader and self._reader.is_open:
            self._reader.write(data)
            self._reader.flush()

    async def unlock(self, duration: float = 5.0) -> bool:
        msg = OSDPMessage(address=self._address, command=self.CMD_OUTPUT, data=bytes([0x01, 0x01]))
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_raw, msg.encode())
            await loop.run_in_executor(None, self._reader.read, 8)
            self._reader_state.door_open = True
            asyncio.ensure_future(self._auto_lock(duration))
            return True
        except Exception as e:
            logger.error(f"[OSDPDriver:{self.door_id}] Unlock failed: {e}")
        return False

    async def _auto_lock(self, delay: float):
        await asyncio.sleep(delay)
        msg = OSDPMessage(address=self._address, command=self.CMD_OUTPUT, data=bytes([0x01, 0x00]))
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_raw, msg.encode())
        except Exception:
            pass
        self._reader_state.door_open = False

    async def lock(self) -> bool:
        msg = OSDPMessage(address=self._address, command=self.CMD_OUTPUT, data=bytes([0x01, 0x00]))
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_raw, msg.encode())
            self._reader_state.door_open = False
            return True
        except Exception as e:
            logger.error(f"[OSDPDriver:{self.door_id}] Lock failed: {e}")
        return False

    async def get_state(self) -> ReaderState:
        return self._reader_state

    async def beep(self, duration: float = 0.5) -> bool:
        duration_10ms = max(1, int(duration * 100))
        msg = OSDPMessage(address=self._address, command=self.CMD_BUZZER, data=bytes([0x01, duration_10ms]))
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_raw, msg.encode())
            return True
        except Exception as e:
            logger.error(f"[OSDPDriver:{self.door_id}] Beep failed: {e}")
        return False

    async def led(self, color: str = "green", on: bool = True) -> bool:
        color_code = 0x01 if color == "green" else 0x02 if color == "red" else 0x03
        if not on:
            color_code = 0x00
        msg = OSDPMessage(address=self._address, command=self.CMD_LED,
                          data=bytes([0x01, color_code, 0x64, 0x00, 0x64, 0x00]))
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_raw, msg.encode())
            return True
        except Exception as e:
            logger.error(f"[OSDPDriver:{self.door_id}] LED failed: {e}")
        return False


def create_driver(door_id: str, config: dict) -> DoorDriver:
    """
    Фабрика за драйвъри.

    config.protocol = "virtual" | "wiegand" | "osdp"
    """
    protocol = config.get("protocol", "virtual").lower()
    if protocol == "wiegand":
        return WiegandDriver(door_id, config)
    elif protocol == "osdp":
        return OSDPDriver(door_id, config)
    else:
        return VirtualDriver(door_id, config)
