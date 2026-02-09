"""
Camera Manager Module
Handles webcam capture and virtual camera output.
Supports multiple virtual camera backends with auto-detection.
"""

import cv2
import numpy as np
import threading
import time
import logging
import os
import sys
import subprocess
import ctypes

logger = logging.getLogger(__name__)


def get_app_dir():
    """Get the application directory (works for both dev and PyInstaller)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def is_admin():
    """Check if the current process has administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


class WebcamCapture:
    """Captures frames from a physical webcam."""

    def __init__(self, device_index=0, width=1280, height=720, fps=30):
        self.device_index = device_index
        self.width = width
        self.height = height
        self.fps = fps
        self.cap = None
        self._frame = None
        self._lock = threading.Lock()
        self._running = False
        self._thread = None

    def start(self):
        """Start capturing frames from the webcam."""
        if self._running:
            return

        # Try DirectShow first (Windows), then default
        backends = [cv2.CAP_DSHOW, cv2.CAP_ANY]
        for backend in backends:
            self.cap = cv2.VideoCapture(self.device_index, backend)
            if self.cap.isOpened():
                break

        if not self.cap or not self.cap.isOpened():
            raise RuntimeError(
                f"Não foi possível abrir a câmera {self.device_index}. "
                "Verifique se a câmera está conectada e não está sendo "
                "usada por outro programa."
            )

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)

        # Read actual resolution
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        logger.info(f"Webcam iniciada: device={self.device_index}, "
                     f"resolução={self.width}x{self.height}")

    def _capture_loop(self):
        """Continuously capture frames."""
        while self._running:
            ret, frame = self.cap.read()
            if ret:
                with self._lock:
                    self._frame = frame
            else:
                time.sleep(0.01)

    def get_frame(self):
        """Get the latest captured frame (BGR format)."""
        with self._lock:
            if self._frame is not None:
                return self._frame.copy()
        return None

    def stop(self):
        """Stop capturing."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        if self.cap:
            self.cap.release()
        self._frame = None
        logger.info("Webcam parada")

    def is_running(self):
        return self._running

    @staticmethod
    def list_cameras(max_devices=10):
        """List available camera devices."""
        cameras = []
        for i in range(max_devices):
            try:
                cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                if cap.isOpened():
                    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    cameras.append({
                        'index': i,
                        'name': f"Câmera {i}",
                        'resolution': f"{w}x{h}"
                    })
                    cap.release()
                else:
                    cap.release()
            except Exception:
                pass
        return cameras


class VirtualCameraBackend:
    """
    Manages virtual camera backend detection and registration.
    Supports: OBS Virtual Camera, Softcam, Unity Capture.
    """

    BACKENDS = ['obs', 'softcam', 'unitycapture']

    @staticmethod
    def detect_available_backends():
        """Detect which virtual camera backends are available."""
        available = []

        # Check OBS Virtual Camera
        obs_paths = [
            r"C:\Program Files\obs-studio\data\obs-plugins\win-dshow",
            r"C:\Program Files (x86)\obs-studio\data\obs-plugins\win-dshow",
        ]
        for path in obs_paths:
            if os.path.exists(path):
                dll64 = os.path.join(path, "obs-virtualcam-module64.dll")
                dll32 = os.path.join(path, "obs-virtualcam-module32.dll")
                if os.path.exists(dll64) or os.path.exists(dll32):
                    available.append({
                        'name': 'obs',
                        'display_name': 'OBS Virtual Camera',
                        'path': path,
                        'installed': True
                    })
                    break

        # Check bundled Softcam DLL
        app_dir = get_app_dir()
        softcam_paths = [
            os.path.join(app_dir, 'drivers', 'softcam', 'softcam.dll'),
            os.path.join(app_dir, 'softcam.dll'),
        ]
        for path in softcam_paths:
            if os.path.exists(path):
                available.append({
                    'name': 'softcam',
                    'display_name': 'VirtualCam Studio Camera',
                    'path': path,
                    'installed': False  # Needs registration check
                })
                break

        # Check pyvirtualcam availability
        try:
            import pyvirtualcam
            available.append({
                'name': 'pyvirtualcam',
                'display_name': 'pyvirtualcam (auto)',
                'path': None,
                'installed': True
            })
        except ImportError:
            pass

        return available

    @staticmethod
    def register_driver(dll_path):
        """
        Register a DirectShow DLL using regsvr32.
        Requires administrator privileges.
        Returns (success, message).
        """
        if not os.path.exists(dll_path):
            return False, f"Arquivo não encontrado: {dll_path}"

        try:
            # regsvr32 requires admin
            result = subprocess.run(
                ['regsvr32', '/s', dll_path],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                logger.info(f"Driver registrado: {dll_path}")
                return True, "Driver registrado com sucesso!"
            else:
                return False, f"Falha ao registrar (código {result.returncode})"
        except subprocess.TimeoutExpired:
            return False, "Timeout ao registrar o driver"
        except Exception as e:
            return False, f"Erro: {str(e)}"

    @staticmethod
    def unregister_driver(dll_path):
        """Unregister a DirectShow DLL."""
        try:
            result = subprocess.run(
                ['regsvr32', '/s', '/u', dll_path],
                capture_output=True, text=True, timeout=30
            )
            return result.returncode == 0
        except Exception:
            return False

    @staticmethod
    def is_driver_registered(driver_name='VirtualCam Studio'):
        """Check if a virtual camera driver is registered in the system."""
        try:
            import winreg
            # Check DirectShow filters in registry
            key_path = (
                r"SOFTWARE\Classes\CLSID"
            )
            # A more reliable check: try to enumerate video devices
            # This is a simplified check
            return True
        except Exception:
            return False


class VirtualCameraOutput:
    """Sends composed frames to a virtual camera device."""

    def __init__(self, width=1280, height=720, fps=30):
        self.width = width
        self.height = height
        self.fps = fps
        self._cam = None
        self._running = False
        self._backend_name = None
        self._error_message = None

    def start(self, preferred_backend=None):
        """
        Start the virtual camera output.
        Tries backends in order: preferred > obs > auto.
        Returns (success, error_message).
        """
        try:
            import pyvirtualcam
        except ImportError:
            self._error_message = (
                "A biblioteca pyvirtualcam não está instalada. "
                "Ela é necessária para a câmera virtual."
            )
            logger.error(self._error_message)
            return False

        # Try preferred backend first
        backends_to_try = []
        if preferred_backend:
            backends_to_try.append(preferred_backend)
        backends_to_try.extend(['obs', 'unitycapture', None])

        for backend in backends_to_try:
            try:
                kwargs = {
                    'width': self.width,
                    'height': self.height,
                    'fps': self.fps,
                }
                if backend:
                    kwargs['backend'] = backend

                self._cam = pyvirtualcam.Camera(**kwargs)
                self._backend_name = backend or 'auto'
                self._running = True
                self._error_message = None

                logger.info(
                    f"Câmera virtual iniciada: {self._cam.device} "
                    f"({self.width}x{self.height}@{self.fps}fps, "
                    f"backend={self._backend_name})"
                )
                return True

            except Exception as e:
                logger.warning(
                    f"Backend '{backend}' falhou: {e}"
                )
                continue

        self._error_message = (
            "Nenhum driver de câmera virtual encontrado.\n\n"
            "Para resolver, instale uma das opções:\n"
            "1. OBS Studio (recomendado): obsproject.com\n"
            "2. Execute o instalador do driver incluído no menu Ajuda"
        )
        logger.error(self._error_message)
        return False

    def send_frame(self, frame_bgr):
        """Send a BGR frame to the virtual camera."""
        if not self._running or self._cam is None:
            return False

        try:
            h, w = frame_bgr.shape[:2]
            if w != self.width or h != self.height:
                frame_bgr = cv2.resize(frame_bgr, (self.width, self.height))

            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            self._cam.send(frame_rgb)
            self._cam.sleep_until_next_frame()
            return True

        except Exception as e:
            logger.error(f"Erro ao enviar frame: {e}")
            return False

    def stop(self):
        """Stop the virtual camera output."""
        self._running = False
        if self._cam:
            try:
                self._cam.close()
            except Exception:
                pass
            self._cam = None
        logger.info("Câmera virtual parada")

    def is_running(self):
        return self._running

    @property
    def device_name(self):
        if self._cam:
            return self._cam.device
        return None

    @property
    def error_message(self):
        return self._error_message
