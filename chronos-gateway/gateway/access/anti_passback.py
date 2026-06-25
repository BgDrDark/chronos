import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


class AntiPassbackState:
    """
    Проследява последното сканиране на всеки потребител
    
    Anti-Passback типове:
    - soft: Предупреждава, но пуска
    - hard: Отказва достъп
    - timed: Отказва за X минути
    
    Обхвати:
    - global: Един общ check за всички врати/зони (по zone_id)
    - per_door: Отделно проследяване за всяка врата
    - group: Споделено проследяване за група врати
    """
    
    def __init__(self):
        # key = user_id, value = {"scope_key": ..., "zone_id": ..., "timestamp": ..., "scan_type": ...}
        self._last_scans: Dict[str, dict] = {}
    
    def _get_scope_key(self, user_id: str, scope: str, scope_id: str) -> str:
        """Генерира ключ за проследяване според обхвата"""
        if scope == "global":
            return f"{user_id}"
        elif scope == "per_door":
            return f"{user_id}:{scope_id}"
        elif scope == "group":
            return f"{user_id}:group:{scope_id}"
        return f"{user_id}"
    
    def check(
        self,
        user_id: str,
        scope: str,
        scope_id: str,
        config: dict
    ) -> Tuple[bool, str]:
        """
        Проверява anti-passback правилата
        
        Args:
            user_id: ID на потребителя
            scope: "global" | "per_door" | "group"
            scope_id: ID на вратата или групата
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
        
        scope_key = self._get_scope_key(user_id, scope, scope_id)
        last = self._last_scans.get(scope_key)
        
        if not last:
            return True, "OK"
        
        ap_type = config.get("type", "soft")
        
        if ap_type == "hard":
            return False, "Вече сте в тази зона/врата"
        
        elif ap_type == "soft":
            return True, "Warning: Повторно сканиране"
        
        elif ap_type == "timed":
            timeout = config.get("timeout_minutes", 5)
            last_time = last.get("timestamp")
            if last_time:
                minutes_since = (datetime.now(timezone.utc) - last_time).total_seconds() / 60
                if minutes_since < timeout:
                    remaining = timeout - minutes_since
                    return False, f"Изчакайте {int(remaining)} минути"
        
        return True, "OK"
    
    def check_exit(
        self,
        user_id: str,
        scope: str,
        scope_id: str
    ) -> Tuple[bool, str]:
        """
        Проверява дали потребителят може да излезе
        
        Returns:
            (allowed, message)
        """
        scope_key = self._get_scope_key(user_id, scope, scope_id)
        last = self._last_scans.get(scope_key)
        
        if not last:
            return False, "Няма запис за вход"
        
        return True, "OK"
    
    def record(
        self,
        user_id: str,
        scope: str,
        scope_id: str,
        zone_id: str,
        scan_type: str = "in"
    ):
        """
        Записва сканирането
        
        Args:
            user_id: ID на потребителя
            scope: "global" | "per_door" | "group"
            scope_id: ID на вратата или групата
            zone_id: ID на зоната
            scan_type: "in" или "out"
        """
        scope_key = self._get_scope_key(user_id, scope, scope_id)
        self._last_scans[scope_key] = {
            "scope_key": scope_key,
            "scope": scope,
            "scope_id": scope_id,
            "zone_id": zone_id,
            "timestamp": datetime.now(timezone.utc),
            "scan_type": scan_type
        }
        logger.debug(f"Recorded scan: user={user_id}, scope={scope}, scope_id={scope_id}, type={scan_type}")
    
    def get_last_scan(self, user_id: str, scope: str = "global", scope_id: str = "") -> Optional[dict]:
        """Връща последното сканиране на потребителя"""
        scope_key = self._get_scope_key(user_id, scope, scope_id)
        last = self._last_scans.get(scope_key)
        if not last:
            return None
        
        return {
            "scope_key": last.get("scope_key"),
            "scope": last.get("scope"),
            "scope_id": last.get("scope_id"),
            "zone_id": last.get("zone_id"),
            "timestamp": last.get("timestamp").isoformat() if last.get("timestamp") else None,
            "scan_type": last.get("scan_type")
        }
    
    def reset_user(self, user_id: str):
        """Ресет на потребител - премахва всички scope-ове"""
        keys_to_delete = [k for k in self._last_scans if k.startswith(f"{user_id}") or k == user_id]
        for k in keys_to_delete:
            del self._last_scans[k]
        logger.info(f"Reset anti-passback for user {user_id}: {len(keys_to_delete)} keys")
    
    def reset_all(self):
        """Ресет на всички"""
        self._last_scans.clear()
        logger.info("Reset all anti-passback states")
    
    def get_all_scans(self) -> list:
        """Връща всички записани сканирания"""
        return [
            {
                "scope_key": data.get("scope_key"),
                "scope": data.get("scope"),
                "scope_id": data.get("scope_id"),
                "zone_id": data.get("zone_id"),
                "timestamp": data.get("timestamp").isoformat() if data.get("timestamp") else None,
                "scan_type": data.get("scan_type")
            }
            for user_id, data in self._last_scans.items()
        ]


anti_passback_state = AntiPassbackState()
