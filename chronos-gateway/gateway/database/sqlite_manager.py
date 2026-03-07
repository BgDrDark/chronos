"""
SQLite Database Manager for Chronos Gateway
Manages local SQLite databases for configuration and logs
"""

import sqlite3
import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
CONFIG_DB_PATH = BASE_DIR / 'config' / 'config.db'
LOGS_DB_PATH = BASE_DIR / 'config' / 'logs.db'


class SQLiteManager:
    """Base class for SQLite operations"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    @contextmanager
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_db(self):
        """Initialize database - to be implemented by subclasses"""
        raise NotImplementedError


class ConfigDatabaseManager(SQLiteManager):
    """Manages config.db - zones, doors, devices, terminals, printers"""
    
    def __init__(self):
        super().__init__(CONFIG_DB_PATH)
    
    def _init_db(self):
        """Create tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Devices (SR201)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    ip TEXT,
                    port INTEGER DEFAULT 6722,
                    mac_address TEXT,
                    relay_1_duration INTEGER DEFAULT 500,
                    relay_2_duration INTEGER DEFAULT 500,
                    relay_1_manual INTEGER DEFAULT 0,
                    relay_2_manual INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Zones
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS zones (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    level INTEGER DEFAULT 0,
                    depends_on TEXT,
                    anti_passback_enabled INTEGER DEFAULT 0,
                    anti_passback_type TEXT DEFAULT 'soft',
                    anti_passback_timeout INTEGER DEFAULT 5,
                    required_hours_start TEXT,
                    required_hours_end TEXT,
                    active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Doors
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS doors (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    zone_id TEXT,
                    device_id TEXT,
                    relay_number INTEGER DEFAULT 1,
                    terminal_id TEXT,
                    description TEXT,
                    active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Terminals
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS terminals (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    ip_address TEXT,
                    device_type TEXT,
                    status TEXT DEFAULT 'offline',
                    last_seen TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Printers
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS printers (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    ip_address TEXT,
                    port INTEGER DEFAULT 9100,
                    is_default INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Access codes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS access_codes (
                    code TEXT PRIMARY KEY,
                    user_id TEXT,
                    used INTEGER DEFAULT 0,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Sync metadata
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            logger.info("Config database initialized")
    
    # ========== DEVICES ==========
    
    def get_all_devices(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM devices")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM devices WHERE id = ?", (device_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def save_device(self, device: Dict[str, Any]) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO devices 
                (id, name, ip, port, mac_address, relay_1_duration, relay_2_duration, 
                 relay_1_manual, relay_2_manual, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                device.get('id'), device.get('name'), device.get('ip'), device.get('port', 6722),
                device.get('mac_address'), device.get('relay_1_duration', 500), 
                device.get('relay_2_duration', 500), 
                1 if device.get('relay_1_manual') else 0,
                1 if device.get('relay_2_manual') else 0
            ))
            return True
    
    def delete_device(self, device_id: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM devices WHERE id = ?", (device_id,))
            return cursor.rowcount > 0
    
    # ========== ZONES ==========
    
    def get_all_zones(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM zones")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_zone(self, zone_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM zones WHERE id = ?", (zone_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def save_zone(self, zone: Dict[str, Any]) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO zones 
                (id, name, level, depends_on, anti_passback_enabled, anti_passback_type,
                 anti_passback_timeout, required_hours_start, required_hours_end, active, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                zone.get('id'), zone.get('name'), zone.get('level', 0), zone.get('depends_on'),
                1 if zone.get('anti_passback_enabled') else 0, zone.get('anti_passback_type', 'soft'),
                zone.get('anti_passback_timeout', 5), zone.get('required_hours_start'),
                zone.get('required_hours_end'), 1 if zone.get('active', True) else 0
            ))
            return True
    
    def delete_zone(self, zone_id: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM zones WHERE id = ?", (zone_id,))
            return cursor.rowcount > 0
    
    # ========== DOORS ==========
    
    def get_all_doors(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM doors")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_door(self, door_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM doors WHERE id = ?", (door_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def save_door(self, door: Dict[str, Any]) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO doors 
                (id, name, zone_id, device_id, relay_number, terminal_id, description, active, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                door.get('id'), door.get('name'), door.get('zone_id'), door.get('device_id'),
                door.get('relay_number', 1), door.get('terminal_id'), door.get('description'),
                1 if door.get('active', True) else 0
            ))
            return True
    
    def delete_door(self, door_id: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM doors WHERE id = ?", (door_id,))
            return cursor.rowcount > 0
    
    # ========== TERMINALS ==========
    
    def get_all_terminals(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM terminals")
            return [dict(row) for row in cursor.fetchall()]
    
    def save_terminal(self, terminal: Dict[str, Any]) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO terminals 
                (id, name, ip_address, device_type, status, last_seen)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                terminal.get('id'), terminal.get('name'), terminal.get('ip_address'),
                terminal.get('device_type'), terminal.get('status', 'offline'),
                terminal.get('last_seen')
            ))
            return True
    
    # ========== PRINTERS ==========
    
    def get_all_printers(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM printers")
            return [dict(row) for row in cursor.fetchall()]
    
    def save_printer(self, printer: Dict[str, Any]) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO printers 
                (id, name, ip_address, port, is_default)
                VALUES (?, ?, ?, ?, ?)
            """, (
                printer.get('id'), printer.get('name'), printer.get('ip_address'),
                printer.get('port', 9100), 1 if printer.get('is_default') else 0
            ))
            return True
    
    # ========== SYNC META ==========
    
    def get_sync_meta(self, key: str) -> Optional[str]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM sync_meta WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row['value'] if row else None
    
    def set_sync_meta(self, key: str, value: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO sync_meta (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, value))
    
    # ========== EXPORT FOR SYNC ==========
    
    def export_all_config(self) -> Dict[str, Any]:
        """Export all config for sync"""
        return {
            'devices': self.get_all_devices(),
            'zones': self.get_all_zones(),
            'doors': self.get_all_doors(),
            'terminals': self.get_all_terminals(),
            'printers': self.get_all_printers()
        }
    
    def import_config(self, config: Dict[str, Any]):
        """Import config from backend"""
        for device in config.get('devices', []):
            self.save_device(device)
        for zone in config.get('zones', []):
            self.save_zone(zone)
        for door in config.get('doors', []):
            self.save_door(door)
        for terminal in config.get('terminals', []):
            self.save_terminal(terminal)
        for printer in config.get('printers', []):
            self.save_printer(printer)


class LogsDatabaseManager(SQLiteManager):
    """Manages logs.db - access logs"""
    
    def __init__(self):
        super().__init__(LOGS_DB_PATH)
    
    def _init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS access_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id TEXT,
                    user_name TEXT,
                    door_id TEXT,
                    door_name TEXT,
                    zone_id TEXT,
                    zone_name TEXT,
                    result TEXT,
                    reason TEXT,
                    method TEXT,
                    terminal_id TEXT,
                    gateway_id TEXT,
                    synced INTEGER DEFAULT 0
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON access_logs(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_user ON access_logs(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_door ON access_logs(door_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_synced ON access_logs(synced)")
            
            logger.info("Logs database initialized")
    
    def add_log(self, log: Dict[str, Any]) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO access_logs 
                (user_id, user_name, door_id, door_name, zone_id, zone_name, 
                 result, reason, method, terminal_id, gateway_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log.get('user_id'), log.get('user_name'), log.get('door_id'),
                log.get('door_name'), log.get('zone_id'), log.get('zone_name'),
                log.get('result'), log.get('reason'), log.get('method'),
                log.get('terminal_id'), log.get('gateway_id')
            ))
            return cursor.lastrowid
    
    def get_unsynced_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM access_logs 
                WHERE synced = 0 
                ORDER BY timestamp ASC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def mark_as_synced(self, log_ids: List[int]):
        if not log_ids:
            return
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ','.join('?' * len(log_ids))
            cursor.execute(f"""
                UPDATE access_logs 
                SET synced = 1 
                WHERE id IN ({placeholders})
            """, log_ids)
    
    def get_logs(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM access_logs 
                ORDER BY timestamp DESC 
                LIMIT ? OFFSET ?
            """, (limit, offset))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_logs_count(self) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM access_logs")
            return cursor.fetchone()['count']
    
    def get_unsynced_count(self) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM access_logs WHERE synced = 0")
            return cursor.fetchone()['count']


# Singleton instances
config_db = ConfigDatabaseManager()
logs_db = LogsDatabaseManager()
