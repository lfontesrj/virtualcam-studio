"""
First Run Setup Module
Handles first-time setup, driver detection, and automatic configuration.
Provides a wizard-like experience for first-time users.
"""

import os
import sys
import logging
import subprocess
import json

logger = logging.getLogger(__name__)


def get_app_dir():
    """Get the application directory."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_data_dir():
    """Get the application data directory."""
    appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
    data_dir = os.path.join(appdata, 'VirtualCamStudio')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def is_first_run():
    """Check if this is the first time the application is running."""
    marker = os.path.join(get_data_dir(), '.initialized')
    return not os.path.exists(marker)


def mark_initialized():
    """Mark that the first-run setup has been completed."""
    marker = os.path.join(get_data_dir(), '.initialized')
    with open(marker, 'w') as f:
        f.write('1')


def check_virtual_camera_driver():
    """
    Check if a virtual camera driver is available.
    Returns dict with status information.
    """
    status = {
        'available': False,
        'driver_name': None,
        'needs_install': False,
        'obs_installed': False,
        'bundled_driver_available': False,
        'message': '',
    }

    # 1. Check if OBS is installed
    obs_paths = [
        r"C:\Program Files\obs-studio",
        r"C:\Program Files (x86)\obs-studio",
    ]
    for path in obs_paths:
        if os.path.exists(path):
            status['obs_installed'] = True
            # Check if virtual camera module exists
            vcam_dll = os.path.join(
                path, 'data', 'obs-plugins', 'win-dshow',
                'obs-virtualcam-module64.dll'
            )
            if os.path.exists(vcam_dll):
                status['available'] = True
                status['driver_name'] = 'OBS Virtual Camera'
                status['message'] = 'OBS Virtual Camera detectada.'
                return status
            break

    # 2. Check if bundled driver exists
    app_dir = get_app_dir()
    bundled_paths = [
        os.path.join(app_dir, 'drivers', 'virtualcam'),
        os.path.join(app_dir, 'drivers'),
    ]
    for path in bundled_paths:
        if os.path.exists(path):
            status['bundled_driver_available'] = True
            break

    # 3. Check pyvirtualcam
    try:
        import pyvirtualcam
        # Try to detect any backend
        status['available'] = True
        status['driver_name'] = 'pyvirtualcam'
        status['message'] = 'Driver de câmera virtual detectado.'
        return status
    except ImportError:
        pass
    except Exception:
        pass

    # No driver found
    if not status['obs_installed']:
        status['needs_install'] = True
        status['message'] = (
            'Nenhum driver de câmera virtual encontrado.\n'
            'O OBS Studio precisa ser instalado para o driver funcionar.'
        )
    else:
        status['needs_install'] = True
        status['message'] = (
            'OBS está instalado, mas o driver de câmera virtual '
            'não foi registrado. Tente iniciar a câmera virtual no OBS '
            'pelo menos uma vez.'
        )

    return status


def install_obs_virtualcam():
    """
    Try to register the OBS virtual camera.
    Looks for the virtualcam-install.bat in OBS directory.
    """
    obs_dirs = [
        r"C:\Program Files\obs-studio",
        r"C:\Program Files (x86)\obs-studio",
    ]

    for obs_dir in obs_dirs:
        bat_path = os.path.join(
            obs_dir, 'data', 'obs-plugins', 'win-dshow',
            'virtualcam-install.bat'
        )
        if os.path.exists(bat_path):
            try:
                # Run as admin
                result = subprocess.run(
                    ['cmd', '/c', bat_path],
                    capture_output=True, text=True, timeout=30,
                    cwd=os.path.dirname(bat_path)
                )
                if result.returncode == 0:
                    return True, "Câmera virtual do OBS registrada!"
                else:
                    return False, f"Falha: {result.stderr}"
            except Exception as e:
                return False, f"Erro: {str(e)}"

    return False, "Arquivo de instalação do OBS não encontrado."


def download_obs_installer():
    """
    Return the URL for downloading OBS Studio.
    """
    return "https://obsproject.com/download"


def get_setup_instructions():
    """
    Return setup instructions based on the current system state.
    """
    status = check_virtual_camera_driver()

    if status['available']:
        return {
            'ready': True,
            'title': 'Tudo pronto!',
            'message': (
                f"Driver detectado: {status['driver_name']}\n\n"
                "O VirtualCam Studio está pronto para uso. "
                "Selecione 'OBS Virtual Camera' como câmera no "
                "Teams, Zoom ou outro aplicativo."
            ),
            'steps': []
        }

    steps = []

    if not status['obs_installed']:
        steps.append({
            'number': 1,
            'title': 'Instalar OBS Studio',
            'description': (
                'Baixe e instale o OBS Studio. Ele inclui o driver '
                'de câmera virtual necessário.'
            ),
            'action': 'download_obs',
            'url': 'https://obsproject.com/download'
        })
        steps.append({
            'number': 2,
            'title': 'Ativar Câmera Virtual',
            'description': (
                'Abra o OBS Studio e clique em "Iniciar Câmera Virtual" '
                'na parte inferior direita. Isso registra o driver no sistema. '
                'Depois pode fechar o OBS.'
            ),
            'action': 'manual',
        })
    else:
        steps.append({
            'number': 1,
            'title': 'Registrar Câmera Virtual',
            'description': (
                'O OBS está instalado, mas o driver precisa ser registrado. '
                'Clique no botão abaixo para registrar automaticamente, '
                'ou abra o OBS e clique em "Iniciar Câmera Virtual".'
            ),
            'action': 'register_obs_vcam',
        })

    steps.append({
        'number': len(steps) + 1,
        'title': 'Reiniciar VirtualCam Studio',
        'description': (
            'Após instalar o driver, reinicie o VirtualCam Studio '
            'para detectar a câmera virtual.'
        ),
        'action': 'restart',
    })

    return {
        'ready': False,
        'title': 'Configuração Necessária',
        'message': status['message'],
        'steps': steps
    }


def create_first_run_config():
    """Create initial configuration files and directories."""
    data_dir = get_data_dir()

    # Create subdirectories
    dirs = ['logs', 'templates', 'data']
    for d in dirs:
        os.makedirs(os.path.join(data_dir, d), exist_ok=True)

    # Copy sample files if they exist
    app_dir = get_app_dir()
    samples = [
        ('assets/sample_ticker.txt', 'data/sample_ticker.txt'),
        ('assets/sample_indicators.txt', 'data/sample_indicators.txt'),
        ('assets/sample_indicators.json', 'data/sample_indicators.json'),
    ]

    for src_rel, dst_rel in samples:
        src = os.path.join(app_dir, src_rel)
        dst = os.path.join(data_dir, dst_rel)
        if os.path.exists(src) and not os.path.exists(dst):
            try:
                import shutil
                shutil.copy2(src, dst)
            except Exception as e:
                logger.warning(f"Falha ao copiar {src}: {e}")

    logger.info(f"Configuração inicial criada em: {data_dir}")
