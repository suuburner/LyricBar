# -*- mode: python ; coding: utf-8 -*-
# LyricBar PyInstaller Spec File
# This file defines how to bundle LyricBar into a standalone executable

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('themes', 'themes'),
        ('resources', 'resources'),
        ('images', 'images'),
        ('settings.yaml', '.'),
        ('webnowplaying.js', '.'),
        ('README.md', '.'),
    ],
    hiddenimports=[
        'winrt.windows.media.control',
        'winrt.windows.foundation',
        'winrt.windows.foundation.collections',
        'winrt',
        'regex',
        'pylrc',
        'syncedlyrics',
        'websocket_server',
        'yaml',
        'syrics',
        'PyQt5',
        'psutil',
        'win32gui',
        'win32process',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'pandas',
        'notebook',
        'IPython',
        'jupyter',
        'tkinter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],  # Don't bundle binaries in the exe
    exclude_binaries=True,  # Create folder-based distribution
    name='LyricBar',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Hide console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icon.ico',
)

# Create folder with all dependencies and data files
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LyricBar'
)
