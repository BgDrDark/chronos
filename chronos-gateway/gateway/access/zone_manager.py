import logging
import uuid
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from gateway.access.zone_state import Zone, Door

logger = logging.getLogger(__name__)


class ZoneManager:
    """
    Мениджър на зоните и вратите
    
    Управлява:
    - Зони (Zone)
    - Врати (Door)
    - Зависимости между зони
    - Работно време
    """
    
    def __init__(self):
        self.zones: Dict[str, Zone] = {}
        self.doors: Dict[str, Door] = {}
    
    def add_zone(self, zone_data: dict) -> str:
        """Добавя нова зона"""
        zone_id = zone_data.get("id")
        if not zone_id:
            zone_id = f"zone_{uuid.uuid4().hex[:8]}"
        
        if zone_id in self.zones:
            logger.warning(f"Zone {zone_id} already exists, updating")
        
        zone = Zone.from_dict(zone_data)
        zone.id = zone_id
        self.zones[zone_id] = zone
        
        logger.info(f"Added zone: {zone_id} - {zone.name}")
        return zone_id
    
    def remove_zone(self, zone_id: str) -> bool:
        """Премахва зона"""
        if zone_id not in self.zones:
            return False
        
        del self.zones[zone_id]
        
        for door in list(self.doors.values()):
            if door.zone_id == zone_id:
                del self.doors[door.id]
        
        logger.info(f"Removed zone: {zone_id}")
        return True
    
    def update_zone(self, zone_id: str, zone_data: dict) -> bool:
        """Обновява зона"""
        if zone_id not in self.zones:
            return False
        
        zone = Zone.from_dict(zone_data)
        zone.id = zone_id
        self.zones[zone_id] = zone
        
        logger.info(f"Updated zone: {zone_id}")
        return True
    
    def get_zone(self, zone_id: str) -> Optional[Zone]:
        """Връща зона по ID"""
        return self.zones.get(zone_id)
    
    def get_all_zones(self) -> List[dict]:
        """Връща списък със зони"""
        return [zone.to_dict() for zone in self.zones.values()]
    
    def get_active_zones(self) -> List[dict]:
        """Връща само активните зони"""
        return [zone.to_dict() for zone in self.zones.values() if zone.active]
    
    def add_door(self, door_data: dict) -> str:
        """Добавя нова врата"""
        door_id = door_data.get("id")
        if not door_id:
            door_id = f"door_{uuid.uuid4().hex[:8]}"
        
        if door_id in self.doors:
            logger.warning(f"Door {door_id} already exists, updating")
        
        door = Door.from_dict(door_data)
        door.id = door_id
        self.doors[door_id] = door
        
        logger.info(f"Added door: {door_id} - {door.name}")
        return door_id
    
    def remove_door(self, door_id: str) -> bool:
        """Премахва врата"""
        if door_id not in self.doors:
            return False
        
        del self.doors[door_id]
        logger.info(f"Removed door: {door_id}")
        return True
    
    def update_door(self, door_id: str, door_data: dict) -> bool:
        """Обновява врата"""
        if door_id not in self.doors:
            return False
        
        door = Door.from_dict(door_data)
        door.id = door_id
        self.doors[door_id] = door
        
        logger.info(f"Updated door: {door_id}")
        return True
    
    def get_door(self, door_id: str) -> Optional[Door]:
        """Връща врата по ID"""
        return self.doors.get(door_id)
    
    def get_all_doors(self) -> List[dict]:
        """Връща списък с вратите"""
        return [door.to_dict() for door in self.doors.values()]
    
    def get_active_doors(self) -> List[dict]:
        """Връща само активните врати"""
        return [door.to_dict() for door in self.doors.values() if door.active]
    
    def get_zone_by_door(self, door_id: str) -> Optional[Zone]:
        """Връща зоната на дадена врата"""
        door = self.doors.get(door_id)
        if not door:
            return None
        return self.zones.get(door.zone_id)
    
    def get_zone_by_terminal(self, terminal_id: str) -> Optional[Zone]:
        """Връща зоната по terminal_id"""
        for door in self.doors.values():
            if door.terminal_id == terminal_id:
                return self.zones.get(door.zone_id)
        return None
    
    def get_door_by_terminal(self, terminal_id: str) -> Optional[Door]:
        """Връща вратата по terminal_id"""
        for door in self.doors.values():
            if door.terminal_id == terminal_id:
                return door
        return None
    
    def get_doors_by_zone(self, zone_id: str) -> List[Door]:
        """Връща всички врати в дадена зона"""
        return [door for door in self.doors.values() if door.zone_id == zone_id]
    
    def check_schedule(self, zone_id: str) -> Tuple[bool, str]:
        """Проверява работното време на зоната"""
        zone = self.zones.get(zone_id)
        if not zone:
            return False, "Зоната не съществува"
        
        if not zone.active:
            return False, "Зоната е деактивирана"
        
        return zone.is_within_hours()
    
    def check_dependencies(self, user_id: str, zone_id: str, zone_state) -> Tuple[bool, str]:
        """
        Проверява зависимостите на зоната
        
        Args:
            user_id: ID на потребителя
            zone_id: ID на зоната
            zone_state: инстанция на ZoneState
        """
        zone = self.zones.get(zone_id)
        if not zone:
            return False, "Зоната не съществува"
        
        if zone.level == 1:
            return True, "OK"
        
        return zone_state.check_access(user_id, zone)
    
    def validate_zone_dependencies(self, zone_data: dict) -> Tuple[bool, str]:
        """
        Валидира зависимостите на зоната при създаване/редактиране
        
        Returns:
            (valid, error_message)
        """
        zone_id = zone_data.get("id", "")
        depends_on = zone_data.get("depends_on", [])
        level = zone_data.get("level", 1)
        
        if level == 1:
            return True, "OK"
        
        if not depends_on:
            return False, f"Зона с level {level} трябва да има depends_on"
        
        for dep_id in depends_on:
            if dep_id not in self.zones:
                return False, f"Зависимата зона {dep_id} не съществува"
            
            dep_zone = self.zones[dep_id]
            if dep_zone.level >= level:
                return False, f"Зависимата зона {dep_id} има level {dep_zone.level}, който е >= на {level}"
        
        return True, "OK"
    
    def load_from_config(self, zones_config: List[dict], doors_config: List[dict]):
        """Зарежда зони и врати от конфигурация"""
        for zone_data in zones_config:
            try:
                self.add_zone(zone_data)
            except Exception as e:
                logger.error(f"Error loading zone from config: {e}")
        
        for door_data in doors_config:
            try:
                self.add_door(door_data)
            except Exception as e:
                logger.error(f"Error loading door from config: {e}")
    
    def get_status(self) -> dict:
        """Връща статус"""
        return {
            "zones": {
                "total": len(self.zones),
                "active": sum(1 for z in self.zones.values() if z.active),
                "list": self.get_all_zones()
            },
            "doors": {
                "total": len(self.doors),
                "active": sum(1 for d in self.doors.values() if d.active),
                "list": self.get_all_doors()
            }
        }
    
    def export_config(self) -> dict:
        """
        Експортира цялата конфигурация (зони + врати) за синхронизация
        """
        from datetime import datetime
        
        return {
            "version": 1,
            "timestamp": datetime.utcnow().isoformat(),
            "zones": self.get_all_zones(),
            "doors": self.get_all_doors()
        }
    
    def import_config(self, config: dict, merge: bool = False) -> dict:
        """
        Импортира конфигурация от друг Gateway
        
        Args:
            config: Експортираната конфигурация
            merge: Ако True, обединява; ако False, замества
            
        Returns:
            Брой обновени зони/врати
        """
        if config.get("version") != 1:
            logger.warning(f"Unknown config version: {config.get('version')}")
            return {"zones": 0, "doors": 0}
        
        count = {"zones": 0, "doors": 0}
        
        zones = config.get("zones", [])
        doors = config.get("doors", [])
        
        if not merge:
            # Заместваме изцяло
            self.zones.clear()
            self.doors.clear()
        
        for zone_data in zones:
            zone_id = zone_data.get("id")
            if zone_id:
                self.add_zone(zone_data)
                count["zones"] += 1
        
        for door_data in doors:
            door_id = door_data.get("id")
            if door_id:
                self.add_door(door_data)
                count["doors"] += 1
        
        logger.info(f"Imported config: {count['zones']} zones, {count['doors']} doors")
        return count


zone_manager = ZoneManager()
