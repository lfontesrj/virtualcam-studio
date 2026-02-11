# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for VirtualCam Studio (Optimized + Debug).
Run with: pyinstaller virtualcam_studio.spec --noconfirm
"""

import os
import sys

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

# Find darkdetect (dependency of customtkinter)
dd_spec = importlib.util.find_spec('darkdetect')
dd_datas = []
if dd_spec and dd_spec.origin:
    dd_path = os.path.dirname(dd_spec.origin)
    dd_datas = [(dd_path, 'darkdetect')]

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
    ] + ctk_datas + dd_datas,
    hiddenimports=[
        # Core dependencies
        'cv2',
        'numpy',
        'numpy.core',
        'numpy.core._methods',
        'numpy.core._exceptions',
        'numpy.core.multiarray',
        'numpy.core.umath',
        'numpy.core._multiarray_umath',
        'numpy.lib',
        'numpy.lib.format',
        'numpy.random',
        'numpy.fft',
        'numpy.linalg',
        # GUI
        'tkinter',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'tkinter.colorchooser',
        'customtkinter',
        'darkdetect',
        # Image handling
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL._tkinter_finder',
        # Virtual camera
        'pyvirtualcam',
        'pyvirtualcam.camera',
        # App modules
        'first_run',
        'camera_manager',
        'compositor',
        'main_window',
        'settings',
        'template_generator',
        # Stdlib that may be needed
        'json',
        'configparser',
        'email',
        'email.mime',
        'email.mime.text',
        'http',
        'http.client',
        'urllib',
        'urllib.request',
        'webbrowser',
        'subprocess',
        'threading',
        'logging',
        'logging.handlers',
        'traceback',
        'pkg_resources',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Conservative exclusions - only exclude what we're sure is not needed
    excludes=[
        # PyQt5 / Qt (no longer used)
        'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'sip', 'sipbuild',
        # Heavy scientific libs
        'scipy', 'pandas', 'matplotlib', 'seaborn', 'plotly',
        'sklearn', 'tensorflow', 'torch', 'torchvision',
        # Testing
        'pytest', 'doctest',
        # Dev tools
        'IPython', 'jupyter', 'notebook', 'ipykernel',
        # Unused stdlib
        'pydoc', 'pdb', 'profile', 'cProfile',
        'lib2to3', 'ensurepip', 'venv',
        'asyncio', 'aiohttp',
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
    strip=False,
    upx=False,
    console=True,   # ENABLED for debugging - shows console with error messages
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
    strip=False,
    upx=False,
    upx_exclude=[
        'python*.dll',
        'python3*.dll',
        'vcruntime*.dll',
        'ucrtbase.dll',
        'msvcp*.dll',
        'api-ms-win-*.dll',
        'libcrypto*.dll',
        'libssl*.dll',
        'libffi*.dll',
        'select.pyd',
        '_socket.pyd',
    ],
    name='VirtualCamStudio',
)
