import logging
import sqlite3
import hmac
import hashlib
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

from gateway.access.zone_manager import zone_manager
from gateway.access.anti_passback import anti_passback_state
from gateway.access.code_manager import code_manager
from gateway.devices.relay_controller import relay_controller
from gateway.config import config

logger = logging.getLogger(__name__)


class AccessController:
    """
    Главен контролер за контрол на достъп с SQLite Persistence
    """
    
    def __init__(self):
        self.zone_manager = zone_manager
        self.zone_state = None
        self.anti_passback = anti_passback_state
        self.codes = code_manager
        self.relays = relay_controller
        
        # Път до базата данни (в папката с логове)
        log_file = config.get("logging.file", "logs/gateway.log")
        self.db_path = Path(log_file).parent / "gateway.db"
        self._init_db()
    
    def _init_db(self):
        """Инициализира локалната SQLite база данни"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS access_logs (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    user_id TEXT,
                    user_name TEXT,
                    zone_id TEXT,
                    zone_name TEXT,
                    door_id TEXT,
                    door_name TEXT,
                    action TEXT,
                    result TEXT,
                    reason TEXT,
                    method TEXT,
                    terminal_id TEXT,
                    synced INTEGER DEFAULT 0,
                    signature TEXT
                )
            """)
            conn.commit()

    def set_zone_state(self, zone_state):
        """Задава ZoneState инстанция"""
        self.zone_state = zone_state
    
    async def check_access(
        self,
        user_id: str,
        terminal_id: str,
        action: str = "enter"
    ) -> dict:
        """Проверява достъпа на потребителя"""
        door = self.zone_manager.get_door_by_terminal(terminal_id)
        if not door:
            return {"allowed": False, "message": "Терминалът не е свързан с врата", "reason": "no_door", "zone": None, "door": None}
        
        zone = self.zone_manager.get_zone(door.zone_id)
        if not zone:
            return {"allowed": False, "message": "Вратата не е свързана със зона", "reason": "no_zone", "zone": None, "door": door.to_dict()}
        
        # Emergency Mode Checks
        system_mode = config.get("gateway.system_mode", "normal")
        if system_mode == "emergency_unlock":
            return {"allowed": True, "message": "АВАРИЙНО ОТКЛЮЧВАНЕ", "reason": "emergency_unlock", "zone": zone.to_dict(), "door": door.to_dict()}
        
        if system_mode == "lockdown":
            return {"allowed": False, "message": "СИСТЕМНА БЛОКАДА", "reason": "lockdown", "zone": zone.to_dict(), "door": door.to_dict()}

        if not zone.active:
            return {"allowed": False, "message": "Зоната е деактивирана", "reason": "zone_inactive", "zone": zone.to_dict(), "door": door.to_dict()}
        
        # Обичайни проверки
        schedule_ok, schedule_msg = self.zone_manager.check_schedule(zone.id)
        if not schedule_ok:
            return {"allowed": False, "message": schedule_msg, "reason": "outside_hours", "zone": zone.to_dict(), "door": door.to_dict()}
        
        # Проверка за оторизация (рестриктивна логика)
        try:
            uid_int = int(user_id)
            if uid_int not in zone.authorized_users:
                return {"allowed": False, "message": "Липсва оторизация", "reason": "not_authorized", "zone": zone.to_dict(), "door": door.to_dict()}
        except:
            if user_id not in [str(u) for u in zone.authorized_users]:
                return {"allowed": False, "message": "Липсва оторизация", "reason": "not_authorized", "zone": zone.to_dict(), "door": door.to_dict()}

        return {"allowed": True, "message": "Достъп разрешен", "reason": "OK", "zone": zone.to_dict(), "door": door.to_dict()}
    
    async def grant_access(
        self,
        user_id: str,
        user_name: str,
        terminal_id: str,
        method: str = "qr_scan",
        action: str = "enter"
    ) -> dict:
        """Разрешава достъп и отваря вратата"""
        access_check = await self.check_access(user_id, terminal_id, action)
        
        if not access_check["allowed"]:
            log = self._create_log(
                user_id=user_id, user_name=user_name,
                zone_id=access_check["zone"]["id"] if access_check["zone"] else None,
                zone_name=access_check["zone"]["name"] if access_check["zone"] else None,
                door_id=access_check["door"]["id"] if access_check["door"] else None,
                door_name=access_check["door"]["name"] if access_check["door"] else None,
                action=action, result="denied", reason=access_check["reason"], method=method, terminal_id=terminal_id
            )
            return {"success": False, "message": access_check["message"], "door_opened": False, "log": log}
        
        door = access_check["door"]
        zone = access_check["zone"]
        
        result = await self.relays.trigger(door["device_id"], door["relay_number"])
        door_opened = result.get("success", False)
        
        if action == "enter" and self.zone_state:
            self.zone_state.enter_zone(user_id, zone["id"])
            self.anti_passback.record(user_id, zone["id"], "in")
        
        log = self._create_log(
            user_id=user_id, user_name=user_name, zone_id=zone["id"], zone_name=zone["name"],
            door_id=door["id"], door_name=door["name"], action=action, result="granted",
            reason="OK", method=method, terminal_id=terminal_id
        )
        
        return {"success": True, "message": "Достъп разрешен", "door_opened": door_opened, "log": log}

    def _create_log(self, **kwargs) -> dict:
        """Създава и записва лог в SQLite"""
        log_id = f"log_{datetime.now().timestamp()}_{kwargs.get('user_id')}"
        log_data = {
            "id": log_id,
            "timestamp": datetime.now().isoformat(),
            "user_id": kwargs.get("user_id"),
            "user_name": kwargs.get("user_name"),
            "zone_id": kwargs.get("zone_id"),
            "zone_name": kwargs.get("zone_name"),
            "door_id": kwargs.get("door_id"),
            "door_name": kwargs.get("door_name"),
            "action": kwargs.get("action"),
            "result": kwargs.get("result"),
            "reason": kwargs.get("reason"),
            "method": kwargs.get("method"),
            "terminal_id": kwargs.get("terminal_id"),
            "synced": 0
        }
        
        # Подписване
        secret = config.get("cluster.shared_secret", "chronos_cluster_secret")
        msg = f"{log_id}|{log_data['timestamp']}|{log_data['user_id']}|{log_data['result']}"
        signature = hmac.new(str(secret).encode(), msg.encode(), hashlib.sha256).hexdigest()
        log_data["signature"] = signature

        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("""
                    INSERT INTO access_logs 
                    (id, timestamp, user_id, user_name, zone_id, zone_name, door_id, door_name, action, result, reason, method, terminal_id, signature)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    log_id, log_data["timestamp"], log_data["user_id"], log_data["user_name"],
                    log_data["zone_id"], log_data["zone_name"], log_data["door_id"], log_data["door_name"],
                    log_data["action"], log_data["result"], log_data["reason"], log_data["method"],
                    log_data["terminal_id"], signature
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"SQLite save error: {e}")

        return log_data

    def get_unsynced_logs(self, limit: int = 50) -> List[dict]:
        """Връща несинхронизирани логове"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM access_logs WHERE synced = 0 LIMIT ?", (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except: return []

    def mark_as_synced(self, log_ids: List[str]):
        """Маркира като синхронизирани"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.executemany("UPDATE access_logs SET synced = 1 WHERE id = ?", [(lid,) for lid in log_ids])
                conn.commit()
        except: pass

    def verify_log_signature(self, log: dict) -> bool:
        """Проверка на подписа"""
        secret = str(config.get("cluster.shared_secret", "default_secret"))
        msg = f"{log['id']}|{log['timestamp']}|{log['user_id']}|{log['result']}"
        expected = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, log.get("signature", ""))

    def get_logs(self, limit: int = 100) -> List[dict]:
        """Връща последните логове от базата"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM access_logs ORDER BY timestamp DESC LIMIT ?", (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except: return []

    def get_active_users(self) -> List[dict]:
        return self.zone_state.get_all_active_users() if self.zone_state else []

    def reset_all_users(self):
        if self.zone_state: self.zone_state.reset_all()
        self.anti_passback.reset_all()

    def get_status(self) -> dict:
        return {
            "active_users": len(self.get_active_users()),
            "total_logs": 0, # Може да се изчисли с COUNT(*)
            "codes": len(self.codes.codes)
        }

access_controller = AccessController()
