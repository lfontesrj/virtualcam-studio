"""
VirtualCam Studio - Entry Point (Optimized)
Uses CustomTkinter instead of PyQt5 for a lightweight footprint.
"""

import sys
import os
import logging

# Add src directory to path
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
parent_dir = os.path.dirname(src_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Determine base directory
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Setup logging
log_dir = os.path.join(
    os.environ.get('APPDATA', os.path.expanduser('~')),
    'VirtualCamStudio', 'logs'
)
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(log_dir, 'virtualcam_studio.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('VirtualCamStudio')


def check_dependencies():
    """Check if required dependencies are available."""
    missing = []
    try:
        import cv2
    except ImportError:
        missing.append("opencv-python-headless")
    try:
        import numpy
    except ImportError:
        missing.append("numpy")
    try:
        import customtkinter
    except ImportError:
        missing.append("customtkinter")

    # pyvirtualcam is optional at startup
    try:
        import pyvirtualcam
    except ImportError:
        logger.warning(
            "pyvirtualcam not installed. Virtual camera output will be "
            "unavailable. Install with: pip install pyvirtualcam"
        )

    if missing:
        print(f"Dependencias faltando: {', '.join(missing)}")
        print("Instale com: pip install " + " ".join(missing))
        sys.exit(1)


def main():
    """Main application entry point."""
    logger.info("=" * 60)
    logger.info("VirtualCam Studio starting...")
    logger.info(f"Base directory: {BASE_DIR}")
    logger.info("=" * 60)

    check_dependencies()

    # Import modules
    from settings import Settings
    from compositor import Compositor
    from camera_manager import WebcamCapture, VirtualCameraOutput
    from first_run import (is_first_run, mark_initialized,
                           check_virtual_camera_driver,
                           create_first_run_config, get_setup_instructions)

    # Load settings
    settings = Settings()
    logger.info("Configuracoes carregadas")

    # First run check
    if is_first_run():
        logger.info("Primeira execucao detectada")
        create_first_run_config()
        mark_initialized()

    # Check driver
    driver_status = check_virtual_camera_driver()
    logger.info(f"Status do driver: {driver_status}")

    # Initialize compositor
    width = settings.get('camera', 'output_width', 1280)
    height = settings.get('camera', 'output_height', 720)
    fps = settings.get('camera', 'fps', 30)

    compositor = Compositor(width=width, height=height)
    webcam = WebcamCapture(
        device_index=settings.get('camera', 'input_device', 0),
        width=width, height=height, fps=fps
    )
    virtual_cam = VirtualCameraOutput(width=width, height=height, fps=fps)

    # Apply saved settings to compositor
    compositor.ticker_layer.visible = settings.get('ticker', 'enabled', True)
    ticker_file = settings.get('ticker', 'text_file', '')
    if ticker_file and os.path.exists(ticker_file):
        compositor.ticker_layer.load_text_from_file(ticker_file)
    compositor.ticker_layer.scroll_speed = settings.get(
        'ticker', 'scroll_speed', 2
    )
    compositor.ticker_layer.font_size = settings.get(
        'ticker', 'font_size', 28
    )
    compositor.ticker_layer.bar_height = settings.get(
        'ticker', 'bar_height', 50
    )
    compositor.ticker_layer.font_color = tuple(
        settings.get('ticker', 'font_color', [255, 255, 255])
    )
    compositor.ticker_layer.bg_color = tuple(
        settings.get('ticker', 'bg_color', [30, 30, 30])
    )

    compositor.countdown_layer.visible = settings.get(
        'countdown', 'enabled', False
    )
    compositor.countdown_layer.duration_seconds = settings.get(
        'countdown', 'duration_minutes', 5
    ) * 60
    compositor.countdown_layer.label_text = settings.get(
        'countdown', 'label_text', 'TEMPO'
    )

    compositor.indicator_layer.visible = settings.get(
        'indicators', 'enabled', False
    )
    ind_file = settings.get('indicators', 'data_file', '')
    if ind_file and os.path.exists(ind_file):
        compositor.indicator_layer.load_indicators(ind_file)
    compositor.indicator_layer.auto_reload = settings.get(
        'indicators', 'auto_reload', True
    )
    compositor.indicator_layer.reload_interval = settings.get(
        'indicators', 'reload_interval', 5
    )

    # Webcam flip
    compositor.webcam_layer.flip_horizontal = settings.get(
        'camera', 'flip_horizontal', False
    )

    # Create and show main window
    from main_window import MainWindow

    window = MainWindow(settings)
    window.set_compositor(compositor)
    window.set_camera_manager(webcam)
    window.set_virtual_camera(virtual_cam)
    window.protocol("WM_DELETE_WINDOW", window.on_closing)

    # Show first-run dialog if driver not found
    if not driver_status['available']:
        import tkinter.messagebox as mb
        instructions = get_setup_instructions()
        steps_text = "\n".join(
            f"{s['number']}. {s['title']}: {s['description']}"
            for s in instructions['steps']
        )
        mb.showwarning(
            instructions['title'],
            f"{instructions['message']}\n\n{steps_text}"
        )

    # Auto-start if configured
    if (settings.get('general', 'auto_start_camera', False)
            and driver_status['available']):
        window.after(1000, window._start_streaming)

    logger.info("Interface grafica iniciada")
    window.mainloop()

    # Cleanup
    logger.info("Encerrando...")
    webcam.stop()
    virtual_cam.stop()
    logger.info("=== VirtualCam Studio encerrado ===")


if __name__ == '__main__':
    main()
