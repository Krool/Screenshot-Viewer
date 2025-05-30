# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['game_screenshots.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('steam_games_cache.json', '.'),
        ('custom_games_cache.json', '.'),
        ('app_icon.ico', '.'),
    ],
    hiddenimports=[],
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
    name='Game Screenshot Viewer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='app_icon.ico',
)
