# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Chronos Gateway (Windows)

Build command:
    pyinstaller chronos-gateway.spec

Output will be in dist/chronos-gateway/
"""

import sys
from pathlib import Path

# Get the gateway directory
gateway_dir = Path(SPECPATH).parent / "gateway"

block_cipher = None

a = Analysis(
    [str(gateway_dir / "main.py")],
    pathex=[str(Path(SPECPATH).parent)],
    binaries=[],
    datas=[
        # Include config.yaml
        (str(Path(SPECPATH).parent / "config.yaml"), "."),
    ],
    hiddenimports=[
        # Core dependencies
        "aiohttp",
        "aiohttp.web",
        "aiohttp.helpers",
        "fastapi",
        "uvicorn",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        
        # Gateway modules
        "gateway.config",
        "gateway.core.hardware_id",
        "gateway.devices.terminal_manager",
        "gateway.devices.printer_manager",
        "gateway.devices.relay_controller",
        "gateway.devices.sr201_relay",
        "gateway.cluster.manager",
        "gateway.cluster.discovery",
        "gateway.cluster.scorer",
        "gateway.sync.sync_manager",
        "gateway.access.controller",
        "gateway.access.zone_manager",
        "gateway.access.code_manager",
        "gateway.access.zone_state",
        "gateway.access.anti_passback",
        "gateway.server.web_dashboard",
        "gateway.server.terminal_hub",
        
        # Database
        "sqlite3",
        
        # Serial communication
        "serial",
        "serial.tools.list_ports",
        
        # Utilities
        "json",
        "hashlib",
        "hmac",
        "secrets",
        "logging",
        "datetime",
        "asyncio",
        "threading",
        "socket",
        "pathlib",
        "urllib",
        "urllib.request",
        "urllib.parse",
        "http.client",
        "http.server",
        "websockets",
        "websockets.server",
        "websockets.client",
        "websockets.sync.server",
        
        # YAML
        "yaml",
        "yaml.safe_load",
        "yaml.safe_dump",
        
        # Cryptography
        "cryptography",
        "cryptography.fernet",
        
        # HTTP
        "requests",
        "requests.adapters",
        
        # Windows specific
        "winreg",
        "wmi",
        
        # Multiprocessing
        "multiprocessing",
        "multiprocessing.spawn",
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
    [],
    exclude_binaries=True,
    name="ChronosGateway",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Set to False for production (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here: "icon.ico"
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ChronosGateway",
)
