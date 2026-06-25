import logging
import sqlite3
import hmac
import hashlib
import json
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from pathlib import Path

from gateway.access.zone_manager import zone_manager
from gateway.access.anti_passback import anti_passback_state
from gateway.access.code_manager import code_manager
from gateway.devices.relay_controller import relay_controller
from gateway.config import config
from gateway.database.sqlite_manager import logs_db

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter за access codes и потребители"""

    def __init__(self):
        self._attempts: Dict[str, list] = {}  # key -> [timestamps]
        self._lockouts: Dict[str, datetime] = {}  # key -> locked_until

    def check(self, key: str) -> Tuple[bool, str]:
        """Проверява дали ключът е rate-limited"""
        max_attempts = config.get('access_control.rate_limit.max_attempts', 5)
        window_minutes = config.get('access_control.rate_limit.window_minutes', 1)
        lockout_minutes = config.get('access_control.rate_limit.lockout_minutes', 5)

        locked_until = self._lockouts.get(key)
        if locked_until and datetime.now(timezone.utc) < locked_until:
            remaining = int((locked_until - datetime.now(timezone.utc)).total_seconds())
            return False, f"Твърде много опити. Изчакайте {remaining} секунди"

        now = datetime.now(timezone.utc)
        attempts = self._attempts.get(key, [])
        attempts = [t for t in attempts if (now - t).total_seconds() < window_minutes * 60]
        self._attempts[key] = attempts

        if len(attempts) >= max_attempts:
            lockout = datetime.now(timezone.utc) + timedelta(minutes=lockout_minutes)
            self._lockouts[key] = lockout
            return False, f"Твърде много опити. Изчакайте {lockout_minutes} минути"

        return True, "OK"

    def record_attempt(self, key: str):
        """Записва опит"""
        self._attempts.setdefault(key, []).append(datetime.now(timezone.utc))

    def record_success(self, key: str):
        """Изчиства опитите при успех"""
        self._attempts.pop(key, None)
        self._lockouts.pop(key, None)

    def get_status(self) -> dict:
        return {
            "max_attempts": config.get('access_control.rate_limit.max_attempts', 5),
            "window_minutes": config.get('access_control.rate_limit.window_minutes', 1),
            "lockout_minutes": config.get('access_control.rate_limit.lockout_minutes', 5),
        }


rate_limiter = RateLimiter()


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
        self.rate_limiter = rate_limiter

        log_file = config.get("logging.file", "logs/gateway.log")
        self.db_path = Path(log_file).parent / "gateway.db"
        self._init_db()

        self._zone_state_task = None

    def _init_db(self):
        """Инициализира локалната SQLite база данни (за zone_state backup и legacy logs)"""
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
            conn.execute("""
                CREATE TABLE IF NOT EXISTS zone_state_backup (
                    user_id TEXT NOT NULL,
                    zone_id TEXT NOT NULL,
                    entered_at TEXT,
                    PRIMARY KEY (user_id, zone_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS anti_passback_backup (
                    scope_key TEXT PRIMARY KEY,
                    scope TEXT,
                    scope_id TEXT,
                    zone_id TEXT,
                    timestamp TEXT,
                    scan_type TEXT
                )
            """)
            conn.commit()

    def set_zone_state(self, zone_state):
        """Задава ZoneState инстанция и възстановява от backup"""
        self.zone_state = zone_state
        self._restore_zone_state()
        self._start_zone_state_persistence()

    def _restore_zone_state(self):
        """Възстановява zone state от SQLite backup"""
        if not self.zone_state:
            return
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT user_id, zone_id, entered_at FROM zone_state_backup")
                count = 0
                for row in cursor.fetchall():
                    ts = datetime.fromisoformat(row["entered_at"])
                    user_id = row["user_id"]
                    zone_id = row["zone_id"]
                    self.zone_state._user_zones.setdefault(user_id, {})[zone_id] = ts
                    count += 1
                if count:
                    logger.info(f"Restored {count} zone state entries from backup")

                cursor = conn.execute("SELECT * FROM anti_passback_backup")
                ap_count = 0
                for row in cursor.fetchall():
                    self.anti_passback._last_scans[row["scope_key"]] = {
                        "scope_key": row["scope_key"],
                        "scope": row["scope"],
                        "scope_id": row["scope_id"],
                        "zone_id": row["zone_id"],
                        "timestamp": datetime.fromisoformat(row["timestamp"]),
                        "scan_type": row["scan_type"],
                    }
                    ap_count += 1
                if ap_count:
                    logger.info(f"Restored {ap_count} anti-passback entries from backup")
        except Exception as e:
            logger.error(f"Error restoring zone state: {e}")

    def _start_zone_state_persistence(self):
        """Стартира фонов таск за периодичен backup на zone state в SQLite.
        Безопасна за извикване преди event loop-ът да е стартирал — тогава
        запазва корутината за стартиране по-късно чрез start_zone_state_persistence()."""
        if self._zone_state_task and not self._zone_state_task.done():
            return

        async def persist_loop():
            while True:
                await asyncio.sleep(30)
                try:
                    self._save_zone_state_now()
                except Exception as e:
                    logger.error(f"Zone state persist error: {e}")

        self._zone_state_coro = persist_loop()
        try:
            loop = asyncio.get_running_loop()
            self._zone_state_task = loop.create_task(self._zone_state_coro)
            self._zone_state_coro = None
        except RuntimeError:
            logger.debug("No running event loop — zone state persistence will start later")

    def start_zone_state_persistence(self):
        """Стартира zone state persistence ако не е стартирана (за извикване от async context)"""
        if self._zone_state_task and not self._zone_state_task.done():
            return
        if self._zone_state_coro:
            try:
                self._zone_state_task = asyncio.create_task(self._zone_state_coro)
                self._zone_state_coro = None
                logger.info("Zone state persistence started (deferred)")
            except RuntimeError as e:
                logger.error(f"Cannot start zone state persistence: {e}")

    def _save_zone_state_now(self):
        """Запазва zone state и anti-passback в SQLite"""
        if not self.zone_state:
            return
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("DELETE FROM zone_state_backup")
                conn.execute("DELETE FROM anti_passback_backup")
                for user_id, zones in self.zone_state._user_zones.items():
                    for zone_id, entered_at in zones.items():
                        conn.execute("INSERT INTO zone_state_backup (user_id, zone_id, entered_at) VALUES (?, ?, ?)",
                                     (user_id, zone_id, entered_at.isoformat()))
                for scope_key, data in self.anti_passback._last_scans.items():
                    ts = data.get("timestamp")
                    conn.execute("INSERT INTO anti_passback_backup (scope_key, scope, scope_id, zone_id, timestamp, scan_type) VALUES (?, ?, ?, ?, ?, ?)",
                                 (scope_key, data.get("scope"), data.get("scope_id"), data.get("zone_id"),
                                  ts.isoformat() if ts else None, data.get("scan_type")))
                conn.commit()
        except Exception as e:
            logger.error(f"Error saving zone state: {e}")

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

        system_mode = config.get("gateway.system_mode", "normal")
        if system_mode == "emergency_unlock":
            return {"allowed": True, "message": "АВАРИЙНО ОТКЛЮЧВАНЕ", "reason": "emergency_unlock", "zone": zone.to_dict(), "door": door.to_dict()}

        if system_mode == "lockdown":
            return {"allowed": False, "message": "СИСТЕМНА БЛОКАДА", "reason": "lockdown", "zone": zone.to_dict(), "door": door.to_dict()}

        if not zone.active:
            return {"allowed": False, "message": "Зоната е деактивирана", "reason": "zone_inactive", "zone": zone.to_dict(), "door": door.to_dict()}

        schedule_ok, schedule_msg = self.zone_manager.check_schedule(zone.id)
        if not schedule_ok:
            return {"allowed": False, "message": schedule_msg, "reason": "outside_hours", "zone": zone.to_dict(), "door": door.to_dict()}

        try:
            uid_int = int(user_id)
            if uid_int not in zone.authorized_users:
                return {"allowed": False, "message": "Липсва оторизация", "reason": "not_authorized", "zone": zone.to_dict(), "door": door.to_dict()}
        except (ValueError, TypeError):
            if user_id not in [str(u) for u in zone.authorized_users]:
                return {"allowed": False, "message": "Липсва оторизация", "reason": "not_authorized", "zone": zone.to_dict(), "door": door.to_dict()}

        # Anti-passback check
        ap_config = {
            "enabled": config.get('access_control.anti_passback.enabled', False) or zone.anti_passback_enabled,
            "type": zone.anti_passback_type or config.get('access_control.anti_passback.default_type', 'soft'),
            "timeout_minutes": zone.anti_passback_timeout or config.get('access_control.anti_passback.timeout_minutes', 5),
        }
        if ap_config["enabled"] and action == "enter":
            scope = door.anti_passback_scope
            scope_id = door.anti_passback_group if scope == "group" else door.id
            ap_allowed, ap_msg = self.anti_passback.check(user_id, scope, scope_id, ap_config)
            if not ap_allowed:
                return {"allowed": False, "message": ap_msg, "reason": "anti_passback", "zone": zone.to_dict(), "door": door.to_dict()}

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
            scope = door.get("anti_passback_scope", "global")
            scope_id = door.get("anti_passback_group") if scope == "group" else door.get("id", "")
            self.anti_passback.record(user_id, scope, scope_id, zone["id"], "in")

        log = self._create_log(
            user_id=user_id, user_name=user_name, zone_id=zone["id"], zone_name=zone["name"],
            door_id=door["id"], door_name=door["name"], action=action, result="granted",
            reason="OK", method=method, terminal_id=terminal_id
        )

        return {"success": True, "message": "Достъп разрешен", "door_opened": door_opened, "log": log}

    def _create_log(self, **kwargs) -> dict:
        """Създава и записва лог и в двете бази (logs_db + gateway.db)"""
        log_data = {
            "id": f"log_{datetime.now().timestamp()}_{kwargs.get('user_id')}",
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

        secret = config.get("cluster.shared_secret", "chronos_cluster_secret")
        msg = f"{log_data['id']}|{log_data['timestamp']}|{log_data['user_id']}|{log_data['result']}"
        signature = hmac.new(str(secret).encode(), msg.encode(), hashlib.sha256).hexdigest()
        log_data["signature"] = signature

        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("""
                    INSERT INTO access_logs 
                    (id, timestamp, user_id, user_name, zone_id, zone_name, door_id, door_name, action, result, reason, method, terminal_id, signature)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    log_data["id"], log_data["timestamp"], log_data["user_id"], log_data["user_name"],
                    log_data["zone_id"], log_data["zone_name"], log_data["door_id"], log_data["door_name"],
                    log_data["action"], log_data["result"], log_data["reason"], log_data["method"],
                    log_data["terminal_id"], signature
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"SQLite save error (gateway.db): {e}")

        try:
            logs_db.add_log(log_data)
        except Exception as e:
            logger.error(f"SQLite save error (logs.db): {e}")

        return log_data

    def get_unsynced_logs(self, limit: int = 50) -> List[dict]:
        """Връща несинхронизирани логове от logs_db"""
        try:
            return logs_db.get_unsynced_logs(limit)
        except Exception:
            return []

    def mark_as_synced(self, log_ids: List[int]):
        """Маркира като синхронизирани в logs_db"""
        try:
            logs_db.mark_as_synced(log_ids)
        except Exception:
            pass

    def verify_log_signature(self, log: dict) -> bool:
        """Проверка на подписа"""
        secret = str(config.get("cluster.shared_secret", "default_secret"))
        msg = f"{log['id']}|{log['timestamp']}|{log['user_id']}|{log['result']}"
        expected = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, log.get("signature", ""))

    def get_logs(self, limit: int = 100) -> List[dict]:
        """Връща последните логове от logs_db"""
        try:
            return logs_db.get_logs(limit)
        except Exception:
            return []

    def get_active_users(self) -> List[dict]:
        return self.zone_state.get_all_active_users() if self.zone_state else []

    def reset_all_users(self):
        if self.zone_state:
            self.zone_state.reset_all()
        self.anti_passback.reset_all()
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("DELETE FROM zone_state_backup")
                conn.execute("DELETE FROM anti_passback_backup")
                conn.commit()
        except Exception as e:
            logger.error(f"Error clearing zone state backup: {e}")

    def get_status(self) -> dict:
        return {
            "active_users": len(self.get_active_users()),
            "codes": len(self.codes.codes),
            "rate_limit": self.rate_limiter.get_status(),
        }


access_controller = AccessController()