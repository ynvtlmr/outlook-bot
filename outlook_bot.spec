# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Helper to find libs
# Customtkinter needs to bundle its json/theme files
datas = collect_data_files('customtkinter')

# Add our own data files
# We want src/apple_scripts -> src/apple_scripts in the bundle
datas += [
    ('src/apple_scripts', 'src/apple_scripts'),
    ('system_prompt.txt', '.'), 
    ('config.yaml', '.'),
    ('.env.example', '.')
]

a = Analysis(
    ['src/gui.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['google.genai', 'customtkinter', 'PIL'],
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
    name='OutlookBot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

app = BUNDLE(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='OutlookBot.app',
    icon=None,
    bundle_identifier='com.yaniv.outlookbot',
)
