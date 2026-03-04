import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AntiPassbackState:
    """
    Проследява последното сканиране на всеки потребител
    
    Anti-Passback типове:
    - soft: Предупреждава, но пуска
    - hard: Отказва достъп
    - timed: Отказва за X минути
    """
    
    def __init__(self):
        self._last_scans: Dict[str, dict] = {}
    
    def check(
        self,
        user_id: str,
        zone_id: str,
        config: dict
    ) -> Tuple[bool, str]:
        """
        Проверява anti-passback правилата
        
        Args:
            user_id: ID на потребителя
            zone_id: ID на зоната
            config: {
                "enabled": bool,
                "type": "soft" | "hard" | "timed",
                "timeout_minutes": int
            }
        
        Returns:
            (allowed, message)
        """
        if not config.get("enabled", False):
            return True, "OK"
        
        last = self._last_scans.get(user_id)
        
        if not last:
            return True, "OK"
        
        if last.get("zone_id") == zone_id:
            ap_type = config.get("type", "soft")
            
            if ap_type == "hard":
                return False, "Вече сте в тази зона"
            
            elif ap_type == "soft":
                return True, "Warning: Повторно сканиране"
            
            elif ap_type == "timed":
                timeout = config.get("timeout_minutes", 5)
                last_time = last.get("timestamp")
                if last_time:
                    minutes_since = (datetime.utcnow() - last_time).total_seconds() / 60
                    if minutes_since < timeout:
                        remaining = timeout - minutes_since
                        return False, f"Изчакайте {int(remaining)} минути"
        
        return True, "OK"
    
    def check_exit(
        self,
        user_id: str,
        zone_id: str
    ) -> Tuple[bool, str]:
        """
        Проверява дали потребителят може да излезе от зоната
        
        Returns:
            (allowed, message)
        """
        last = self._last_scans.get(user_id)
        
        if not last:
            return False, "Не сте влязъл в тази зона"
        
        if last.get("zone_id") == zone_id:
            return True, "OK"
        
        return False, "Не сте в тази зона"
    
    def record(
        self,
        user_id: str,
        zone_id: str,
        scan_type: str = "in"
    ):
        """
        Записва сканирането
        
        Args:
            user_id: ID на потребителя
            zone_id: ID на зоната
            scan_type: "in" или "out"
        """
        self._last_scans[user_id] = {
            "zone_id": zone_id,
            "timestamp": datetime.utcnow(),
            "scan_type": scan_type
        }
        logger.debug(f"Recorded scan: user={user_id}, zone={zone_id}, type={scan_type}")
    
    def get_last_scan(self, user_id: str) -> Optional[dict]:
        """Връща последното сканиране на потребителя"""
        last = self._last_scans.get(user_id)
        if not last:
            return None
        
        return {
            "zone_id": last.get("zone_id"),
            "timestamp": last.get("timestamp").isoformat() if last.get("timestamp") else None,
            "scan_type": last.get("scan_type")
        }
    
    def reset_user(self, user_id: str):
        """Ресет на потребител"""
        if user_id in self._last_scans:
            del self._last_scans[user_id]
            logger.info(f"Reset anti-passback for user {user_id}")
    
    def reset_all(self):
        """Ресет на всички"""
        self._last_scans.clear()
        logger.info("Reset all anti-passback states")
    
    def get_all_scans(self) -> list:
        """Връща всички записани сканирания"""
        return [
            {
                "user_id": user_id,
                "zone_id": data.get("zone_id"),
                "timestamp": data.get("timestamp").isoformat() if data.get("timestamp") else None,
                "scan_type": data.get("scan_type")
            }
            for user_id, data in self._last_scans.items()
        ]


anti_passback_state = AntiPassbackState()
