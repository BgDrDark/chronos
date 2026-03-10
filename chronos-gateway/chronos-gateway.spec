# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Chronos Gateway (Windows)

Build command:
    pyinstaller chronos-gateway.spec
"""

import os
import sys

block_cipher = None

# Get the directory where this spec file is located  
spec_dir = os.path.dirname(os.path.abspath(SPECPATH))
# main.py is directly in chronos-gateway folder
gateway_dir = spec_dir

a = Analysis(
    [os.path.join(gateway_dir, 'main.py')],
    pathex=[spec_dir, gateway_dir],
    binaries=[],
    datas=[
        (os.path.join(spec_dir, 'config.yaml'), '.'),
    ],
    hiddenimports=[
        # Core
        'aiohttp', 'aiohttp.web', 'aiohttp.helpers',
        'fastapi', 'uvicorn', 'uvicorn.logging', 'uvicorn.loops',
        'uvicorn.protocols', 'uvicorn.protocols.http',
        'uvicorn.protocols.websockets',
        
        # Gateway modules
        'gateway.config',
        'gateway.core.hardware_id',
        'gateway.devices.terminal_manager',
        'gateway.devices.printer_manager',
        'gateway.devices.relay_controller',
        'gateway.devices.sr201_relay',
        'gateway.cluster.manager',
        'gateway.cluster.discovery',
        'gateway.cluster.scorer',
        'gateway.sync.sync_manager',
        'gateway.access.controller',
        'gateway.access.zone_manager',
        'gateway.access.code_manager',
        'gateway.access.zone_state',
        'gateway.access.anti_passback',
        'gateway.server.web_dashboard',
        'gateway.server.terminal_hub',
        'gateway.database.sqlite_manager',
        
        # Database
        'sqlite3',
        
        # Serial
        'serial', 'serial.tools.list_ports',
        
        # Utils
        'json', 'hashlib', 'hmac', 'secrets', 'logging',
        'datetime', 'asyncio', 'threading', 'socket',
        'pathlib', 'urllib', 'urllib.request', 'urllib.parse',
        'http.client', 'http.server',
        
        # Websockets
        'websockets', 'websockets.server', 'websockets.client',
        
        # YAML
        'yaml', 'yaml.safe_load', 'yaml.safe_dump',
        
        # Requests
        'requests', 'requests.adapters',
        
        # Cryptography  
        'cryptography', 'cryptography.fernet',
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
    name='ChronosGateway',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ChronosGateway',
)
