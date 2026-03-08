import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Zone:
    """Зона за контрол на достъп"""
    id: str
    name: str
    level: int = 1
    depends_on: List[str] = field(default_factory=list)
    authorized_users: List[int] = field(default_factory=list) # List of user IDs
    required_hours_start: str = "00:00"
    required_hours_end: str = "23:59"
    anti_passback_enabled: bool = False
    anti_passback_type: str = "soft"
    anti_passback_timeout: int = 5
    description: str = ""
    active: bool = True
    
    # ... (is_within_hours stays same)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "level": self.level,
            "depends_on": self.depends_on,
            "authorized_users": self.authorized_users,
            "required_hours": {
                "start": self.required_hours_start,
                "end": self.required_hours_end
            },
            "anti_passback": {
                "enabled": self.anti_passback_enabled,
                "type": self.anti_passback_type,
                "timeout_minutes": self.anti_passback_timeout
            },
            "description": self.description,
            "active": self.active
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Zone':
        # Support both nested (API) and flat (SQLite) formats
        hours = data.get("required_hours", {})
        ap = data.get("anti_passback", {})
        
        req_start = hours.get("start") or data.get("required_hours_start", "00:00")
        req_end = hours.get("end") or data.get("required_hours_end", "23:59")
        
        # Handle anti_passback fields
        if "enabled" in ap:
            ap_enabled = ap["enabled"]
        elif "anti_passback_enabled" in data:
            ap_enabled = bool(data["anti_passback_enabled"])
        else:
            ap_enabled = False
            
        ap_type = ap.get("type") or data.get("anti_passback_type", "soft")
        ap_timeout = ap.get("timeout_minutes") or data.get("anti_passback_timeout", 5)

        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            level=data.get("level", 1),
            depends_on=data.get("depends_on") if isinstance(data.get("depends_on"), list) else [],
            authorized_users=data.get("authorized_users") if isinstance(data.get("authorized_users"), list) else [],
            required_hours_start=req_start,
            required_hours_end=req_end,
            anti_passback_enabled=ap_enabled,
            anti_passback_type=ap_type,
            anti_passback_timeout=ap_timeout,
            description=data.get("description", ""),
            active=bool(data.get("active", True))
        )


@dataclass
class Door:
    """Врата за контрол на достъп"""
    id: str
    name: str
    zone_id: str
    device_id: str
    relay_number: int = 1
    terminal_id: str = ""
    description: str = ""
    active: bool = True
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "zone_id": self.zone_id,
            "device_id": self.device_id,
            "relay_number": self.relay_number,
            "terminal_id": self.terminal_id,
            "description": self.description,
            "active": self.active
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Door':
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            zone_id=data.get("zone_id", ""),
            device_id=data.get("device_id", ""),
            relay_number=data.get("relay_number", 1),
            terminal_id=data.get("terminal_id", ""),
            description=data.get("description", ""),
            active=data.get("active", True)
        )


class ZoneState:
    """
    Проследява текущата зона на всеки потребител
    
    Съхранява информация за това кой потребител в коя зона е влязъл
    """
    
    def __init__(self):
        self._user_zones: Dict[str, Dict[str, datetime]] = {}
    
    def check_access(self, user_id: str, target_zone: Zone) -> Tuple[bool, str]:
        """
        Проверява дали потребителят има достъп до зоната

        Returns:
            (allowed, reason)
        """
        # 1. Проверка за оторизация - потребителят ТРЯБВА да е в списъка
        try:
            uid_int = int(user_id)
            if uid_int not in target_zone.authorized_users:
                return False, f"Потребител {user_id} няма оторизация за тази зона"
        except (ValueError, TypeError):
            # Ако не е число (напр. гост код), отказваме достъп, ако не е в списъка (като string)
            if user_id not in [str(u) for u in target_zone.authorized_users]:
                 return False, "Липсва специфична оторизация за този код"

        if target_zone.level == 1:
            return True, "OK"

        
        user_zones = self._user_zones.get(user_id, {})
        
        for dep_zone_id in target_zone.depends_on:
            if dep_zone_id not in user_zones:
                return False, f"Липсва достъп до: {dep_zone_id}"
        
        return True, "OK"
    
    def enter_zone(self, user_id: str, zone_id: str):
        """Потребител влиза в зона"""
        if user_id not in self._user_zones:
            self._user_zones[user_id] = {}
        
        self._user_zones[user_id][zone_id] = datetime.utcnow()
        logger.info(f"User {user_id} entered zone {zone_id}")
    
    def leave_zone(self, user_id: str, zone_id: str):
        """Потребител напуска зона"""
        if user_id in self._user_zones:
            self._user_zones[user_id].pop(zone_id, None)
            logger.info(f"User {user_id} left zone {zone_id}")
    
    def get_user_zones(self, user_id: str) -> List[str]:
        """Връща списък със зоните на потребителя"""
        user_zones = self._user_zones.get(user_id, {})
        return list(user_zones.keys())
    
    def get_user_zone_details(self, user_id: str) -> List[dict]:
        """Връща детайли за зоните на потребителя"""
        user_zones = self._user_zones.get(user_id, {})
        return [
            {"zone_id": zone_id, "entered_at": ts.isoformat()}
            for zone_id, ts in user_zones.items()
        ]
    
    def reset_user(self, user_id: str):
        """Ресет на потребител"""
        if user_id in self._user_zones:
            del self._user_zones[user_id]
            logger.info(f"Reset user {user_id} zones")
    
    def reset_all(self):
        """Ресет на всички потребители"""
        self._user_zones.clear()
        logger.info("Reset all user zones")
    
    def get_all_active_users(self) -> List[dict]:
        """Връща всички активни потребители"""
        result = []
        for user_id, zones in self._user_zones.items():
            for zone_id, entered_at in zones.items():
                result.append({
                    "user_id": user_id,
                    "zone_id": zone_id,
                    "entered_at": entered_at.isoformat()
                })
        return result
    
    def is_user_in_zone(self, user_id: str, zone_id: str) -> bool:
        """Проверява дали потребителят е в дадена зона"""
        user_zones = self._user_zones.get(user_id, {})
        return zone_id in user_zones
    
    def export_state(self) -> dict:
        """
        Експортира цялата зона state за синхронизация между Masters
        """
        exported = {}
        for user_id, zones in self._user_zones.items():
            exported[user_id] = {
                zone_id: ts.isoformat()
                for zone_id, ts in zones.items()
            }
        
        return {
            "version": 1,
            "timestamp": datetime.utcnow().isoformat(),
            "user_zones": exported
        }
    
    def import_state(self, state: dict, force: bool = False) -> int:
        """
        Импортира зона state от друг Master
        
        Args:
            state: Експортирания state
            force: Ако True, замества изцяло
            
        Returns:
            Брой обновени записи
        """
        if state.get("version") != 1:
            logger.warning(f"Unknown zone state version: {state.get('version')}")
            return 0
        
        imported_timestamp = datetime.fromisoformat(state["timestamp"])
        
        # Проверка дали state-а е по-нов
        # (опростено - приемаме всичко)
        
        user_zones = state.get("user_zones", {})
        count = 0
        
        for user_id, zones in user_zones.items():
            if force or user_id not in self._user_zones:
                self._user_zones[user_id] = {
                    zone_id: datetime.fromisoformat(ts)
                    for zone_id, ts in zones.items()
                }
                count += 1
        
        logger.info(f"Imported zone state: {count} users")
        return count
    
    def merge_state(self, state: dict) -> int:
        """
        Обединява зона state с приоритет на по-новите записи
        """
        if state.get("version") != 1:
            return 0
        
        imported_timestamp = datetime.fromisoformat(state["timestamp"])
        user_zones = state.get("user_zones", {})
        count = 0
        
        for user_id, zones in user_zones.items():
            if user_id not in self._user_zones:
                # Нов потребител - директно добавяме
                self._user_zones[user_id] = {
                    zone_id: datetime.fromisoformat(ts)
                    for zone_id, ts in zones.items()
                }
                count += 1
            else:
                # Обединяваме - запазваме по-новите записи
                for zone_id, ts_str in zones.items():
                    ts = datetime.fromisoformat(ts_str)
                    existing = self._user_zones[user_id].get(zone_id)
                    if existing is None or ts > existing:
                        self._user_zones[user_id][zone_id] = ts
                        count += 1
        
        logger.info(f"Merged zone state: {count} updates")
        return count
