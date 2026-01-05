# -*- mode: python ; coding: utf-8 -*-
# Using --onedir mode for faster startup (avoids extraction on each launch)

block_cipher = None

a = Analysis(
    ['run.py'],
    pathex=['src'],
    binaries=[],
    datas=[('src/photonflow', 'photonflow')],
    hiddenimports=[
        'uvicorn.logging', 
        'uvicorn.loops', 
        'uvicorn.loops.auto', 
        'uvicorn.protocols', 
        'uvicorn.protocols.http', 
        'uvicorn.protocols.http.auto', 
        'uvicorn.protocols.websockets', 
        'uvicorn.protocols.websockets.auto', 
        'uvicorn.lifespan', 
        'uvicorn.lifespan.on',
        'engineio.async_drivers.asgi',
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

# --onedir mode: EXE without bundled binaries/datas
exe = EXE(
    pyz,
    a.scripts,
    [],  # No binaries bundled in exe
    exclude_binaries=True,  # Key for onedir mode
    name='photonflow-server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='../src-tauri/icons/icon.ico',
)

# Collect all files into a directory
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='photonflow-server',
)
