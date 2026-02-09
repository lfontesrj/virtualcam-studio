# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for VirtualCam Studio (Optimized).
Run with: pyinstaller virtualcam_studio.spec --noconfirm
"""

import os

block_cipher = None

# Paths
src_dir = os.path.join(os.getcwd(), 'src')
assets_dir = os.path.join(os.getcwd(), 'assets')

# Find customtkinter path for theme data
import importlib
ctk_spec = importlib.util.find_spec('customtkinter')
ctk_datas = []
if ctk_spec and ctk_spec.origin:
    ctk_path = os.path.dirname(ctk_spec.origin)
    ctk_datas = [(ctk_path, 'customtkinter')]

a = Analysis(
    ['src/main.py'],
    pathex=[src_dir],
    binaries=[],
    datas=[
        ('assets/templates/*.png', 'assets/templates'),
        ('assets/sample_ticker.txt', 'assets'),
        ('assets/sample_indicators.txt', 'assets'),
        ('assets/sample_indicators.json', 'assets'),
        ('drivers/install_virtualcam.bat', 'drivers'),
        ('drivers/uninstall_virtualcam.bat', 'drivers'),
        ('drivers/install_obs_silent.ps1', 'drivers'),
        ('LICENSE', '.'),
    ] + ctk_datas,
    hiddenimports=[
        'cv2',
        'numpy',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'customtkinter',
        'pyvirtualcam',
        'pyvirtualcam.camera',
        'first_run',
        'camera_manager',
        'compositor',
        'main_window',
        'settings',
        'template_generator',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Aggressive exclusions to reduce size
    excludes=[
        # PyQt5 / Qt (no longer used)
        'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'sip', 'sipbuild',
        # Heavy scientific libs
        'scipy', 'pandas', 'matplotlib', 'seaborn', 'plotly',
        'sklearn', 'tensorflow', 'torch', 'torchvision',
        # Testing
        'pytest', 'unittest', 'doctest',
        # Dev tools
        'IPython', 'jupyter', 'notebook', 'ipykernel',
        'setuptools', 'pip', 'wheel', 'distutils',
        # Unused stdlib
        'xmlrpc', 'pydoc', 'pdb', 'profile', 'cProfile',
        'lib2to3', 'ensurepip', 'venv',
        'multiprocessing', 'concurrent',
        'asyncio', 'aiohttp',
        'email', 'html.parser', 'http.server',
        'ftplib', 'imaplib', 'smtplib', 'poplib',
        'telnetlib', 'turtle', 'turtledemo',
        'curses', 'idlelib',
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
    [],
    exclude_binaries=True,
    name='VirtualCamStudio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,   # Strip debug symbols
    upx=True,     # UPX compression
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=True,
    upx=True,
    upx_exclude=[
        'vcruntime140.dll',
        'python3*.dll',
        'ucrtbase.dll',
    ],
    name='VirtualCamStudio',
)
