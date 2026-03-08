# -*- mode: python ; coding: utf-8 -*-

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
        'uvicorn.logging',
        'uvicorn.loops.auto',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan.on',
        'fastapi.middleware.cors',
        'starlette.middleware.cors',
        'jinja2',
        'psutil',
        'sqlite3',
        'yaml',
        'aiohttp',
        'pydantic',
        'pydantic_core._pydantic_core', # Важно за Pydantic v2
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
    console=True, # Променено на True за дебъгване, може да се смени на False за "тих" режим
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='static/favicon.ico' if os.path.exists('static/favicon.ico') else None
)
