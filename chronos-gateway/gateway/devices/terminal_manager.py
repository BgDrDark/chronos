from typing import Dict, Optional
from datetime import datetime
import asyncio

class TerminalManager:
    """
    Управление на терминалите
    
    - Регистрация на терминали
    - Heartbeat tracking
    - Статус мониторинг
    """
    
    def __init__(self):
        self.terminals: Dict[str, dict] = {}
        self.heartbeats: Dict[str, datetime] = {}
    
    def register(self, terminal_id: str, device_info: dict) -> dict:
        """Регистрира терминал"""
        self.terminals[terminal_id] = {
            "terminal_id": terminal_id,
            "device_name": device_info.get("device_name"),
            "device_type": device_info.get("device_type", "tablet"),
            "device_model": device_info.get("device_model"),
            "os_version": device_info.get("os_version"),
            "ip_address": device_info.get("ip_address"),
            "registered_at": datetime.utcnow(),
            "last_seen": datetime.utcnow(),
            "total_scans": 0,
        }
        self.heartbeats[terminal_id] = datetime.utcnow()
        return self.terminals[terminal_id]
    
    def unregister(self, terminal_id: str):
        """Премахва терминал"""
        self.terminals.pop(terminal_id, None)
        self.heartbeats.pop(terminal_id, None)
    
    def update_heartbeat(self, terminal_id: str):
        """Обновява heartbeat"""
        if terminal_id in self.terminals:
            self.heartbeats[terminal_id] = datetime.utcnow()
            self.terminals[terminal_id]["last_seen"] = datetime.utcnow()
    
    def increment_scans(self, terminal_id: str):
        """Увеличава брояча на сканирания"""
        if terminal_id in self.terminals:
            self.terminals[terminal_id]["total_scans"] += 1
    
    def get_terminal(self, terminal_id: str) -> Optional[dict]:
        """Връща информация за терминал"""
        return self.terminals.get(terminal_id)
    
    def get_all_terminals(self) -> list:
        """Връща всички терминали"""
        return list(self.terminals.values())
    
    def get_status(self, timeout_seconds: int = 120) -> dict:
        """Връща статус на всички терминали"""
        now = datetime.utcnow()
        
        active = []
        offline = []
        
        for terminal_id, terminal in self.terminals.items():
            last_heartbeat = self.heartbeats.get(terminal_id)
            if last_heartbeat:
                elapsed = (now - last_heartbeat).total_seconds()
                if elapsed > timeout_seconds:
                    offline.append(terminal_id)
                    terminal["status"] = "offline"
                else:
                    active.append(terminal_id)
                    terminal["status"] = "online"
            else:
                offline.append(terminal_id)
                terminal["status"] = "offline"
        
        return {
            "total": len(self.terminals),
            "active": len(active),
            "offline": len(offline),
            "terminals": self.terminals
        }
    
    def cleanup_offline(self, timeout_seconds: int = 300):
        """Премахва офлайн терминали"""
        now = datetime.now()
        to_remove = []
        
        for terminal_id, last_heartbeat in self.heartbeats.items():
            elapsed = (now - last_heartbeat).total_seconds()
            if elapsed > timeout_seconds:
                to_remove.append(terminal_id)
        
        for terminal_id in to_remove:
            self.unregister(terminal_id)
        
        return len(to_remove)
