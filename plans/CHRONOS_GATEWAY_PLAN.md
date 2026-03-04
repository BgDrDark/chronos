# Chronos Gateway - Имплементационен План

## Преглед

Този документ описва пълната имплементация на **Chronos Gateway** - Windows service, който служи като gateway между терминалите в цеха и бекенда.

### Архитектура

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CHRONOS SYSTEM ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────┐    mTLS          ┌──────────┐    mTLS         ┌──────────┐ │
│   │Terminal │ ◄───────────────►│  Gateway │◄────────────────►│  Backend │ │
│   │ (PWA)   │                  │ (Windows)│                  │ (Chronos)│ │
│   └────┬────┘                  └────┬─────┘                  └────┬─────┘ │
│        │                            │                            │        │
│        │  QR Scan                  │  Print                    │        │
│        │  Heartbeat               │  Queue                    │        │
│        │  Status                  │  Monitor                  │        │
│        ▼                            ▼                            ▼        │
│   ┌───────────────────────────────────────────────────────────────────┐  │
│   │                     POSTGRESQL DATABASE                             │  │
│   │   gateways | terminals | printers | time_logs | users | ...        │  │
│   └───────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Част 1: База Данни

### 1.1 Нови модели

```python
# backend/database/models.py

class Gateway(Base):
    """Gateway устройство - инсталирано на Windows машина в локалната мрежа"""
    __tablename__ = "gateways"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # GATEWAY-001
    
    # Hardware-bound идентификатор (не може да се копира)
    hardware_uuid = Column(String(64), unique=True, nullable=False)
    
    # Потребителски псевдоним
    alias = Column(String(100), nullable=True)
    
    # Мрежова информация
    ip_address = Column(String(50), nullable=True)
    local_hostname = Column(String(100), nullable=True)
    
    # Конфигурация
    terminal_port = Column(Integer, default=8080)
    web_port = Column(Integer, default=8888)
    
    # Статус
    is_active = Column(Boolean, default=True)
    last_heartbeat = Column(DateTime, nullable=True)
    registered_at = Column(DateTime, default=datetime.utcnow)
    
    # Връзка към компания
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    
    # Релации
    terminals = relationship("Terminal", back_populates="gateway")
    printers = relationship("Printer", back_populates="gateway")


class Terminal(Base):
    """Терминал - таблет/киоск свързан към gateway"""
    __tablename__ = "terminals"

    id = Column(Integer, primary_key=True, index=True)
    hardware_uuid = Column(String(64), unique=True, nullable=False)
    
    # Информация за устройството
    device_name = Column(String(100), nullable=True)
    device_type = Column(String(50))  # "tablet", "kiosk", "raspberry"
    device_model = Column(String(100), nullable=True)
    os_version = Column(String(50), nullable=True)
    
    # Gateway асоциация
    gateway_id = Column(Integer, ForeignKey("gateways.id"), nullable=True)
    gateway = relationship("Gateway", back_populates="terminals")
    
    # Статус
    is_active = Column(Boolean, default=True)
    last_seen = Column(DateTime, nullable=True)
    total_scans = Column(Integer, default=0)
    
    # Потребителски настройки
    alias = Column(String(100), nullable=True)


class Printer(Base):
    """Принтер свързан към gateway"""
    __tablename__ = "printers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    printer_type = Column(String(20))  # "network", "usb", "windows"
    
    # Мрежова конфигурация
    ip_address = Column(String(50), nullable=True)
    port = Column(Integer, default=9100)  # RAW port
    protocol = Column(String(20))  # "raw", "lpd", "ipp"
    
    # Windows споделен принтер
    windows_share_name = Column(String(100), nullable=True)
    
    # Информация за принтера
    manufacturer = Column(String(50), nullable=True)
    model = Column(String(100), nullable=True)
    
    # Gateway асоциация
    gateway_id = Column(Integer, ForeignKey("gateways.id"))
    gateway = relationship("Gateway", back_populates="printers")
    
    # Статус
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    last_test = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)


class GatewayHeartbeat(Base):
    """История на heartbeat събития"""
    __tablename__ = "gateway_heartbeats"

    id = Column(Integer, primary_key=True)
    gateway_id = Column(Integer, ForeignKey("gateways.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20))  # "online", "offline"
    cpu_usage = Column(Float, nullable=True)
    memory_usage = Column(Float, nullable=True)
    terminal_count = Column(Integer, default=0)
    printer_count = Column(Integer, default=0)
```

### 1.2 API Endpoints

```
# backend/routers/gateway.py

# Gateway CRUD
POST   /api/gateways/register         # Регистрация на нов gateway
GET    /api/gateways                  # Списък с всички gateways
GET    /api/gateways/{id}             # Детайли за gateway
PATCH  /api/gateways/{id}             # Промяна на alias
DELETE /api/gateways/{id}             # Деактивиране на gateway
POST   /api/gateways/{id}/heartbeat   # Heartbeat от gateway

# Terminals
GET    /api/gateways/{id}/terminals   # Терминали за този gateway
GET    /api/terminals                 # Всички терминали (филтрирани)
GET    /api/terminals/{id}             # Детайли за терминал

# Printers
GET    /api/gateways/{id}/printers    # Принтери за този gateway
POST   /api/gateways/{id}/printers    # Добавяне на принтер
PATCH  /api/gateways/{id}/printers/{printer_id}  # Редакция
DELETE /api/gateways/{id}/printers/{printer_id}  # Премахване
POST   /api/gateways/{id}/printers/{printer_id}/test  # Тест принтиране
POST   /api/gateways/{id}/printers/{printer_id}/set-default  # Задаване като подразбиращ
```

---

## Част 2: Gateway Service (Windows)

### 2.1 Структура на проекта

```
chronos-gateway/
├── gateway/
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   ├── service.py              # Windows service wrapper
│   ├── config.py               # Configuration management
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── hardware_id.py      # Hardware UUID generation
│   │   ├── certificate.py      # mTLS certificate management
│   │   └── encryption.py       # Payload encryption
│   │
│   ├── server/
│   │   ├── __init__.py
│   │   ├── terminal_hub.py     # Terminal communication (port 8080)
│   │   ├── web_dashboard.py    # Web UI (port 8888)
│   │   ├── api_proxy.py        # Backend proxy
│   │   └── websocket.py         # Real-time updates
│   │
│   ├── devices/
│   │   ├── __init__.py
│   │   ├── terminal_manager.py # Terminal registry & heartbeat
│   │   └── printer_manager.py  # Printer management
│   │
│   ├── printer/
│   │   ├── __init__.py
│   │   ├── base.py              # Base printer class
│   │   ├── network.py           # Network printer (RAW/LPD)
│   │   ├── usb.py               # USB printer
│   │   └── windows.py           # Windows print spooler
│   │
│   └── storage/
│       ├── __init__.py
│       └── database.py          # Local SQLite for offline buffer
│
├── static/
│   ├── index.html               # Dashboard
│   ├── styles.css
│   └── app.js
│
├── certs/                       # Certificates (generated)
│   ├── gateway.pem
│   ├── gateway-key.pem
│   └── ca-chain.pem
│
├── logs/                        # Application logs
├── data/                        # Local SQLite
│
├── config.yaml                  # Configuration
├── requirements.txt
├── pyproject.toml
└── setup.py
```

### 2.2 Hardware UUID Generation

```python
# gateway/core/hardware_id.py

import hashlib
import uuid
import platform
import subprocess
import re

def get_hardware_uuid() -> str:
    """
    Генерира уникален хардуерен идентификатор базиран на:
    - Motherboard serial
    - CPU ID
    - BIOS UUID
    - Primary MAC address
    
    Това UUID е обвързано с хардуера и не може да се копира.
    """
    
    components = []
    
    # 1. Motherboard serial
    mb_serial = _get_wmi_info("Win32_BaseBoard", "SerialNumber")
    if mb_serial:
        components.append(mb_serial)
    
    # 2. BIOS UUID
    bios_uuid = _get_wmi_info("Win32_ComputerSystemProduct", "UUID")
    if bios_uuid:
        components.append(bios_uuid)
    
    # 3. CPU ID
    cpu_id = _get_cpu_id()
    if cpu_id:
        components.append(cpu_id)
    
    # 4. Primary MAC address
    mac = _get_primary_mac()
    if mac:
        components.append(mac)
    
    if not components:
        # Fallback: generate random but store for future
        return _get_or_create_fallback_uuid()
    
    # Generate SHA-256 hash
    combined = "|".join(components)
    hw_uuid = hashlib.sha256(combined.encode()).hexdigest()[:64]
    
    return hw_uuid


def _get_wmi_info(wmi_class: str, attribute: str) -> str:
    """Извлича информация от WMI"""
    try:
        result = subprocess.run(
            ["powershell", "-Command", 
             f"Get-WmiObject -Class {wmi_class} | "
             f"Select-Object -ExpandProperty {attribute}"],
            capture_output=True, text=True, timeout=5
        )
        value = result.stdout.strip()
        if value and value != "None":
            return value
    except:
        pass
    return None


def _get_cpu_id() -> str:
    """CPU ID чрез WMI"""
    return _get_wmi_info("Win32_Processor", "ProcessorId")


def _get_primary_mac() -> str:
    """Първи MAC адрес"""
    try:
        result = subprocess.run(
            ["powershell", "-Command", 
             "Get-NetAdapter | Where-Object Status -eq 'Up' | "
             "Select-Object -First 1 -ExpandProperty MacAddress"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except:
        return None


def _get_or_create_fallback_uuid() -> str:
    """Fallback: генерира и запазва UUID"""
    config_dir = Path(os.environ.get('PROGRAMDATA', 'C:\\ProgramData')) / 'ChronosGateway'
    config_dir.mkdir(parents=True, exist_ok=True)
    uuid_file = config_dir / 'machine.uuid'
    
    if uuid_file.exists():
        return uuid_file.read_text().strip()
    
    new_uuid = uuid.uuid4().hex
    uuid_file.write_text(new_uuid)
    return new_uuid
```

### 2.3 Terminal Hub (Port 8080)

```python
# gateway/server/terminal_hub.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import asyncio
import json
from datetime import datetime

class TerminalHub:
    """
    HTTP/WebSocket сървър за терминалите
    
    Endpoint-ове:
    - POST /register   - Регистрация на терминал
    - POST /scan      - QR сканиране
    - WS  /ws/{terminal_id} - WebSocket връзка
    - GET  /health    - Health check
    """
    
    def __init__(self, config: dict):
        self.app = FastAPI(title="Chronos Terminal Hub")
        self.config = config
        self.terminals: Dict[str, dict] = {}  # terminal_id -> info
        self.websockets: Dict[str, WebSocket] = {}
        
        self._setup_routes()
    
    def _setup_routes(self):
        @self.app.post("/register")
        async def register_terminal(data: dict):
            """Регистрация на терминал"""
            terminal_id = data.get("hardware_uuid")
            device_info = {
                "terminal_id": terminal_id,
                "device_name": data.get("device_name"),
                "device_type": data.get("device_type"),
                "os_version": data.get("os_version"),
                "registered_at": datetime.utcnow().isoformat(),
                "ip_address": data.get("ip_address"),
            }
            self.terminals[terminal_id] = device_info
            return {"status": "registered", "terminal_id": terminal_id}
        
        @self.app.post("/scan")
        async def handle_scan(data: dict):
            """Препраща сканиране към backend"""
            # Forward to backend via API proxy
            result = await self._proxy_to_backend("/kiosk/scan", data)
            return result
        
        @self.app.post("/heartbeat")
        async def terminal_heartbeat(data: dict):
            """Heartbeat от терминал"""
            terminal_id = data.get("terminal_id")
            if terminal_id in self.terminals:
                self.terminals[terminal_id]["last_heartbeat"] = datetime.utcnow()
            return {"status": "ok"}
        
        @self.app.get("/config")
        async def get_config():
            """Конфигурация за терминала"""
            return {
                "backend_url": self.config["backend"]["url"],
                "gateway_id": self.config["gateway"]["id"],
                "printer_id": self.config.get("default_printer_id"),
            }
        
        @self.app.websocket("/ws/{terminal_id}")
        async def websocket_endpoint(websocket: WebSocket, terminal_id: str):
            """WebSocket за realtime комуникация"""
            await websocket.accept()
            self.websockets[terminal_id] = websocket
            try:
                while True:
                    data = await websocket.receive_text()
                    await self._handle_websocket_message(terminal_id, data)
            except WebSocketDisconnect:
                self.websockets.pop(terminal_id, None)
    
    async def _proxy_to_backend(self, endpoint: str, data: dict) -> dict:
        """Проксиране на заявка към бекенд"""
        # Implementation in api_proxy.py
        pass
    
    async def start(self):
        """Стартиране на сървъра"""
        import uvicorn
        config = uvicorn.Config(
            self.app, 
            host="0.0.0.0", 
            port=self.config["gateway"]["terminal_port"]
        )
        await config.serve()
```

### 2.4 Printer Manager

```python
# gateway/devices/printer_manager.py

import socket
import win32print
import win32api
from typing import Optional
from enum import Enum

class PrinterProtocol(Enum):
    RAW = "raw"
    LPD = "lpd"
    IPP = "ipp"

class PrinterManager:
    """
    Управление на принтери
    
    Поддържа:
    - Network printers (RAW, LPD)
    - USB printers
    - Windows shared printers
    """
    
    def __init__(self):
        self.printers: dict = {}  # printer_id -> config
    
    def add_printer(self, printer_id: str, config: dict):
        """Добавяне на принтер"""
        self.printers[printer_id] = {
            "name": config["name"],
            "type": config["type"],  # network, usb, windows
            "ip_address": config.get("ip_address"),
            "port": config.get("port", 9100),
            "protocol": config.get("protocol", "raw"),
            "windows_name": config.get("windows_name"),
            "is_default": config.get("is_default", False),
        }
    
    def print_receipt(self, printer_id: str, data: bytes) -> bool:
        """Принтиране на receipt"""
        printer = self.printers.get(printer_id)
        if not printer:
            raise ValueError(f"Printer {printer_id} not found")
        
        if printer["type"] == "network":
            return self._print_network(printer, data)
        elif printer["type"] == "usb":
            return self._print_usb(printer, data)
        elif printer["type"] == "windows":
            return self._print_windows(printer, data)
        
        raise ValueError(f"Unknown printer type: {printer['type']}")
    
    def _print_network(self, printer: dict, data: bytes) -> bool:
        """Принтиране към мрежов принтер"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(10)
                sock.connect((printer["ip_address"], printer["port"]))
                sock.sendall(data)
            return True
        except Exception as e:
            print(f"Network print error: {e}")
            return False
    
    def _print_windows(self, printer: dict, data: bytes) -> bool:
        """Принтиране чрез Windows Print Spooler"""
        try:
            hprinter = win32print.OpenPrinter(printer["windows_name"])
            try:
                job = win32print.StartDocPrinter(hprinter, 1, ("Receipt", None, "RAW"))
                try:
                    win32print.WritePrinter(hprinter, data)
                finally:
                    win32print.EndDocPrinter(hprinter)
            finally:
                win32print.ClosePrinter(hprinter)
            return True
        except Exception as e:
            print(f"Windows print error: {e}")
            return False
    
    def test_printer(self, printer_id: str) -> dict:
        """Тест на принтер"""
        printer = self.printers.get(printer_id)
        if not printer:
            return {"status": "error", "message": "Printer not found"}
        
        # Test pattern
        test_data = b"\x1B@\x1B\x61\x01Test Print\x1B\x64\x03\n"
        
        success = False
        try:
            if printer["type"] == "network":
                success = self._print_network(printer, test_data)
            elif printer["type"] == "windows":
                success = self._print_windows(printer, test_data)
        except Exception as e:
            return {"status": "error", "message": str(e)}
        
        return {"status": "success" if success else "error"}
```

### 2.5 Activity Monitor

```python
# gateway/devices/activity_monitor.py

import asyncio
from datetime import datetime, timedelta
from typing import Dict

class ActivityMonitor:
    """
    Мониторинг на активността на терминалите
    
    - Проследява heartbeat
    - Открива offline устройства
    - Поддържа списък на активните устройства
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.heartbeat_timeout = config.get("activity", {}).get("timeout", 120)
        
        # terminal_id -> last_heartbeat
        self.terminal_heartbeats: Dict[str, datetime] = {}
        
        # terminal_id -> status
        self.terminal_status: Dict[str, str] = {}  # "online", "offline"
    
    async def start(self):
        """Стартира мониторинга"""
        while True:
            await self._check_heartbeats()
            await asyncio.sleep(10)  # Check every 10 seconds
    
    async def _check_heartbeats(self):
        """Проверява статус на всички терминали"""
        now = datetime.utcnow()
        
        for terminal_id, last_heartbeat in self.terminal_heartbeats.items():
            time_diff = (now - last_heartbeat).total_seconds()
            
            if time_diff > self.heartbeat_timeout:
                if self.terminal_status.get(terminal_id) != "offline":
                    self.terminal_status[terminal_id] = "offline"
                    await self._notify_status_change(terminal_id, "offline")
            else:
                if self.terminal_status.get(terminal_id) != "online":
                    self.terminal_status[terminal_id] = "online"
                    await self._notify_status_change(terminal_id, "online")
    
    async def _notify_status_change(self, terminal_id: str, status: str):
        """Уведомява при промяна на статус"""
        print(f"Terminal {terminal_id} is now {status}")
        # TODO: Send to backend, update websocket
    
    def update_heartbeat(self, terminal_id: str):
        """Обновява heartbeat за терминал"""
        self.terminal_heartbeats[terminal_id] = datetime.utcnow()
    
    def get_status(self) -> dict:
        """Връща текущия статус"""
        return {
            "total": len(self.terminal_heartbeats),
            "online": sum(1 for s in self.terminal_status.values() if s == "online"),
            "offline": sum(1 for s in self.terminal_status.values() if s == "offline"),
            "terminals": self.terminal_status.copy()
        }
```

---

## Част 3: Web Dashboard (Port 8888)

### 3.1 Dashboard API

```python
# gateway/server/web_dashboard.py

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

class WebDashboard:
    """
    Web базиран dashboard за мониторинг
    
    Функционалност:
    - Преглед на активните устройства
    - Управление на принтери
    - Стартиране/спиране на service
    """
    
    def __init__(self, gateway_service):
        self.gateway = gateway_service
        self.app = FastAPI(title="Chronos Gateway Dashboard")
        
        self._setup_routes()
    
    def _setup_routes(self):
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard():
            return self._render_dashboard()
        
        @self.app.get("/api/status")
        async def get_status():
            """Общ статус на gateway"""
            return {
                "gateway": {
                    "id": self.gateway.config.get("gateway", {}).get("id"),
                    "alias": self.gateway.config.get("gateway", {}).get("alias"),
                    "ip_address": self.gateway.config.get("network", {}).get("ip"),
                    "status": "running",  # TODO: check actual status
                    "uptime": self.gateway.get_uptime(),
                },
                "terminals": self.gateway.activity_monitor.get_status(),
                "printers": self.gateway.printer_manager.get_printers_list(),
            }
        
        @self.app.get("/api/terminals")
        async def get_terminals():
            """Списък с терминали"""
            return self.gateway.terminal_manager.get_all_terminals()
        
        @self.app.get("/api/printers")
        async def get_printers():
            """Списък с принтери"""
            return self.gateway.printer_manager.get_printers_list()
        
        @self.app.post("/api/printers")
        async def add_printer(data: dict):
            """Добавяне на принтер"""
            return self.gateway.printer_manager.add_printer(
                name=data["name"],
                printer_type=data["type"],
                ip_address=data.get("ip_address"),
                port=data.get("port", 9100),
                windows_name=data.get("windows_name"),
            )
        
        @self.app.post("/api/printers/{printer_id}/test")
        async def test_printer(printer_id: str):
            """Тест на принтер"""
            return self.gateway.printer_manager.test_printer(printer_id)
        
        @self.app.post("/api/printers/{printer_id}/set-default")
        async def set_default_printer(printer_id: str):
            """Задаване като подразбиращ принтер"""
            return self.gateway.printer_manager.set_default(printer_id)
        
        @self.app.delete("/api/printers/{printer_id}")
        async def delete_printer(printer_id: str):
            """Премахване на принтер"""
            return self.gateway.printer_manager.remove_printer(printer_id)
        
        @self.app.get("/api/logs")
        async def get_logs(lines: int = 100):
            """Получаване на логове"""
            return self.gateway.get_logs(lines)
```

### 3.2 Dashboard HTML Structure

```html
<!-- static/index.html -->

<!DOCTYPE html>
<html lang="bg">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chronos Gateway Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        // Refresh status every 10 seconds
        setInterval(loadStatus, 10000);
    </script>
</head>
<body class="bg-gray-100">
    <!-- Header -->
    <header class="bg-blue-600 text-white p-4">
        <div class="container mx-auto flex justify-between items-center">
            <h1 class="text-xl font-bold">Chronos Gateway</h1>
            <div class="flex items-center gap-4">
                <span id="gateway-status" class="px-3 py-1 rounded-full bg-green-500">Active</span>
                <button onclick="restartService()" class="bg-blue-700 px-4 py-2 rounded">Restart</button>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="container mx-auto p-4">
        <!-- Stats Cards -->
        <div class="grid grid-cols-4 gap-4 mb-6">
            <div class="bg-white p-4 rounded shadow">
                <div class="text-gray-500">Active Terminals</div>
                <div class="text-3xl font-bold text-green-600" id="active-terminals">0</div>
            </div>
            <div class="bg-white p-4 rounded shadow">
                <div class="text-gray-500">Offline Terminals</div>
                <div class="text-3xl font-bold text-red-600" id="offline-terminals">0</div>
            </div>
            <div class="bg-white p-4 rounded shadow">
                <div class="text-gray-500">Total Terminals</div>
                <div class="text-3xl font-bold" id="total-terminals">0</div>
            </div>
            <div class="bg-white p-4 rounded shadow">
                <div class="text-gray-500">Printers</div>
                <div class="text-3xl font-bold" id="total-printers">0</div>
            </div>
        </div>

        <!-- Gateway List -->
        <div class="bg-white rounded shadow mb-6">
            <div class="p-4 border-b flex justify-between items-center">
                <h2 class="text-lg font-semibold">Gateways</h2>
            </div>
            <div id="gateway-list" class="divide-y">
                <!-- Gateway items will be rendered here -->
            </div>
        </div>
    </main>

    <!-- Gateway Detail Modal -->
    <div id="gateway-modal" class="fixed inset-0 bg-black bg-opacity-50 hidden">
        <div class="bg-white rounded-lg shadow-xl max-w-2xl mx-auto mt-20">
            <!-- Modal content -->
        </div>
    </div>

    <!-- Add Printer Modal -->
    <div id="printer-modal" class="fixed inset-0 bg-black bg-opacity-50 hidden">
        <div class="bg-white rounded-lg shadow-xl max-w-md mx-auto mt-20 p-6">
            <h3 class="text-lg font-semibold mb-4">Add Printer</h3>
            <form id="printer-form">
                <!-- Form fields -->
            </form>
        </div>
    </div>
</body>
</html>
```

---

## Част 4: Инсталация

### 4.1 Конфигурационен файл

```yaml
# config.yaml

# Gateway Configuration
gateway:
  id: "auto"  # Will be assigned by backend
  alias: ""   # User-defined alias
  hardware_uuid: ""  # Auto-generated

# Network Configuration  
network:
  ip: "0.0.0.0"  # Auto-detect
  terminal_port: 8080
  web_port: 8888

# Backend Configuration
backend:
  url: "https://chronos.yourcompany.com"
  api_key: ""  # Will be assigned on registration
  verify_ssl: true

# mTLS Configuration
mtls:
  enabled: false
  cert_file: "certs/gateway.pem"
  key_file: "certs/gateway-key.pem"
  ca_file: "certs/ca-chain.pem"

# Activity Monitoring
activity:
  heartbeat_interval: 30  # seconds
  timeout: 120  # seconds (offline threshold)

# Logging
logging:
  level: "INFO"
  file: "logs/gateway.log"
  max_size: "10MB"
  backup_count: 5

# Printers (pre-configured)
printers: []
```

### 4.2 PyInstaller Configuration

```python
# pyinstaller_spec.py

block_cipher = None

a = Analysis(
    ['gateway/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('static', 'static'),
        ('config.yaml', '.'),
    ],
    hiddenimports=[
        'uvicorn',
        'fastapi',
        'websockets',
        'win32print',
        'win32api',
        'jinja2',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ChronosGateway',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to False for production
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
```

### 4.3 Inno Setup Script

```iss
[Setup]
AppName=Chronos Gateway
AppVersion=1.0.0
DefaultDirName={autopf}\ChronosGateway
DefaultGroupName=Chronos Gateway
OutputBaseFilename=ChronosGateway-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Languages]
Name: "bulgarian"; MessagesFile: "compiler:Languages\Bulgarian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "startup"; Description: "Start with Windows"; GroupDescription: "Other:"

[Files]
Source: "dist\ChronosGateway.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "config.yaml"; DestDir: "{app}"; Flags: ignoreversion
Source: "static\*"; DestDir: "{app}\static"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Chronos Gateway"; Filename: "{app}\ChronosGateway.exe"
Name: "{commondesktop}\Chronos Gateway"; Filename: "{app}\ChronosGateway.exe"

[Run]
Filename: "{app}\ChronosGateway.exe"; Parameters: "--install-service"; Flags: runhidden waituntilterminated

[UninstallRun]
Filename: "{app}\ChronosGateway.exe"; Parameters: "--uninstall-service"; Flags: runhidden

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
```

---

## Част 5: Signalност

### 5.1 mTLS Implementation

```python
# gateway/core/certificate.py

import ssl
import certifi

def create_ssl_context(config: dict) -> ssl.SSLContext:
    """Създава SSL контекст за mTLS"""
    
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    
    # Load CA certificate
    ca_file = config.get("mtls", {}).get("ca_file", "certs/ca-chain.pem")
    ctx.load_verify_locations(ca_file)
    
    # Load client certificate
    cert_file = config.get("mtls", {}).get("cert_file")
    key_file = config.get("mtls", {}).get("key_file")
    
    if cert_file and key_file:
        ctx.load_cert_chain(cert_file, key_file)
        ctx.verify_mode = ssl.CERT_REQUIRED
    else:
        ctx.verify_mode = ssl.CERT_NONE
    
    return ctx
```

---

## Част 6: Frontend Integration

### 6.1 GraphQL Schema Additions

```python
# backend/graphql/types.py

@strawberry.type
class Gateway:
    id: int
    name: str
    hardware_uuid: str
    alias: Optional[str]
    ip_address: Optional[str]
    local_hostname: Optional[str]
    terminal_port: int
    web_port: int
    is_active: bool
    last_heartbeat: Optional[datetime]
    registered_at: datetime
    
    terminals: List["Terminal"]
    printers: List["Printer"]


@strawberry.type
class Terminal:
    id: int
    hardware_uuid: str
    device_name: Optional[str]
    device_type: str
    gateway: Optional[Gateway]
    is_active: bool
    last_seen: Optional[datetime]
    total_scans: int
    alias: Optional[str]


@strawberry.type
class Printer:
    id: int
    name: str
    printer_type: str
    ip_address: Optional[str]
    port: int
    protocol: str
    gateway: Gateway
    is_active: bool
    is_default: bool
    last_test: Optional[datetime]
    last_error: Optional[str]
```

---

## Имплементационни Стъпки

| Стъпка | Описание | Приоритет |
|--------|----------|-----------|
| 1 | Създаване на database models | Висок |
| 2 | Създаване на API endpoints | Висок |
| 3 | Gateway hardware UUID | Висок |
| 4 | Terminal Hub сървър | Висок |
| 5 | Printer Manager | Висок |
| 6 | Activity Monitor | Среден |
| 7 | Web Dashboard | Среден |
| 8 | Backend proxy | Среден |
| 9 | mTLS certificates | Среден |
| 10 | PyInstaller build | Среден |
| 11 | Inno Setup installer | Среден |
| 12 | Frontend UI интеграция | Нисък |

---

## Забележки

- Всички времена са в UTC, освен ако не е указано друго
- Използва се Europe/Sofia timezone за display
- Логовете се ротират автоматично
- Database migrations трябва да се направят преди deployment
