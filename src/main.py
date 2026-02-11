"""
VirtualCam Studio - Entry Point (Optimized + Debug)
Uses CustomTkinter instead of PyQt5 for a lightweight footprint.
"""

import sys
import os
import traceback
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
    # For frozen apps, also add _internal to path
    internal_dir = os.path.join(BASE_DIR, '_internal')
    if os.path.isdir(internal_dir) and internal_dir not in sys.path:
        sys.path.insert(0, internal_dir)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Setup logging - write to both file and console
log_dir = os.path.join(
    os.environ.get('APPDATA', os.path.expanduser('~')),
    'VirtualCamStudio', 'logs'
)
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, 'virtualcam_studio.log')

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger('VirtualCamStudio')


def show_error_dialog(title, message):
    """Show error dialog even if CustomTkinter fails."""
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(title, message)
        root.destroy()
    except Exception:
        print(f"ERRO: {title}\n{message}", file=sys.stderr)


def check_dependencies():
    """Check if required dependencies are available."""
    missing = []
    
    logger.debug("Verificando dependencias...")
    
    try:
        import cv2
        logger.debug(f"OpenCV OK: {cv2.__version__}")
    except ImportError as e:
        logger.error(f"OpenCV FALHOU: {e}")
        missing.append("opencv-python-headless")

    try:
        import numpy
        logger.debug(f"NumPy OK: {numpy.__version__}")
    except ImportError as e:
        logger.error(f"NumPy FALHOU: {e}")
        missing.append("numpy")

    try:
        import customtkinter
        logger.debug(f"CustomTkinter OK: {customtkinter.__version__}")
    except ImportError as e:
        logger.error(f"CustomTkinter FALHOU: {e}")
        missing.append("customtkinter")

    try:
        import tkinter
        logger.debug(f"Tkinter OK: {tkinter.TkVersion}")
    except ImportError as e:
        logger.error(f"Tkinter FALHOU: {e}")
        missing.append("tkinter")

    # pyvirtualcam is optional at startup
    try:
        import pyvirtualcam
        logger.debug(f"pyvirtualcam OK: {pyvirtualcam.__version__}")
    except ImportError:
        logger.warning(
            "pyvirtualcam not installed. Virtual camera output will be "
            "unavailable. Install with: pip install pyvirtualcam"
        )

    # PIL is used for preview
    try:
        from PIL import Image, ImageTk
        logger.debug("PIL/Pillow OK")
    except ImportError:
        logger.warning("PIL/Pillow not available - preview will be limited")

    if missing:
        msg = f"Dependencias faltando: {', '.join(missing)}"
        logger.error(msg)
        show_error_dialog("Dependencias Faltando", msg)
        sys.exit(1)

    logger.debug("Todas as dependencias verificadas")


def main():
    """Main application entry point."""
    logger.info("=" * 60)
    logger.info("VirtualCam Studio starting...")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Executable: {sys.executable}")
    logger.info(f"Frozen: {getattr(sys, 'frozen', False)}")
    logger.info(f"Base directory: {BASE_DIR}")
    logger.info(f"Log file: {log_file}")
    logger.info(f"sys.path: {sys.path[:5]}...")
    logger.info("=" * 60)

    check_dependencies()

    logger.debug("Importando modulos internos...")

    try:
        from settings import Settings
        logger.debug("Settings importado OK")
    except Exception as e:
        logger.error(f"Erro ao importar Settings: {e}\n{traceback.format_exc()}")
        show_error_dialog("Erro", f"Falha ao importar Settings:\n{e}")
        sys.exit(1)

    try:
        from compositor import Compositor
        logger.debug("Compositor importado OK")
    except Exception as e:
        logger.error(f"Erro ao importar Compositor: {e}\n{traceback.format_exc()}")
        show_error_dialog("Erro", f"Falha ao importar Compositor:\n{e}")
        sys.exit(1)

    try:
        from camera_manager import WebcamCapture, VirtualCameraOutput
        logger.debug("CameraManager importado OK")
    except Exception as e:
        logger.error(f"Erro ao importar CameraManager: {e}\n{traceback.format_exc()}")
        show_error_dialog("Erro", f"Falha ao importar CameraManager:\n{e}")
        sys.exit(1)

    try:
        from first_run import (is_first_run, mark_initialized,
                               check_virtual_camera_driver,
                               create_first_run_config, get_setup_instructions)
        logger.debug("FirstRun importado OK")
    except Exception as e:
        logger.error(f"Erro ao importar FirstRun: {e}\n{traceback.format_exc()}")
        show_error_dialog("Erro", f"Falha ao importar FirstRun:\n{e}")
        sys.exit(1)

    # Load settings
    try:
        settings = Settings()
        logger.info("Configuracoes carregadas")
    except Exception as e:
        logger.error(f"Erro ao carregar settings: {e}\n{traceback.format_exc()}")
        show_error_dialog("Erro", f"Falha ao carregar configuracoes:\n{e}")
        sys.exit(1)

    # First run check
    try:
        if is_first_run():
            logger.info("Primeira execucao detectada")
            create_first_run_config()
            mark_initialized()
    except Exception as e:
        logger.warning(f"Erro no first_run check: {e}")

    # Check driver
    try:
        driver_status = check_virtual_camera_driver()
        logger.info(f"Status do driver: {driver_status}")
    except Exception as e:
        logger.warning(f"Erro ao verificar driver: {e}")
        driver_status = {'available': False, 'message': str(e)}

    # Initialize compositor
    width = settings.get('camera', 'output_width', 1280)
    height = settings.get('camera', 'output_height', 720)
    fps = settings.get('camera', 'fps', 30)

    try:
        compositor = Compositor(width=width, height=height)
        logger.debug("Compositor inicializado OK")
    except Exception as e:
        logger.error(f"Erro ao criar Compositor: {e}\n{traceback.format_exc()}")
        show_error_dialog("Erro", f"Falha ao criar Compositor:\n{e}")
        sys.exit(1)

    try:
        webcam = WebcamCapture(
            device_index=settings.get('camera', 'input_device', 0),
            width=width, height=height, fps=fps
        )
        logger.debug("WebcamCapture inicializado OK")
    except Exception as e:
        logger.error(f"Erro ao criar WebcamCapture: {e}\n{traceback.format_exc()}")
        show_error_dialog("Erro", f"Falha ao criar WebcamCapture:\n{e}")
        sys.exit(1)

    try:
        virtual_cam = VirtualCameraOutput(width=width, height=height, fps=fps)
        logger.debug("VirtualCameraOutput inicializado OK")
    except Exception as e:
        logger.error(f"Erro ao criar VirtualCameraOutput: {e}\n{traceback.format_exc()}")
        show_error_dialog("Erro", f"Falha ao criar VirtualCameraOutput:\n{e}")
        sys.exit(1)

    # Apply saved settings to compositor (with error handling)
    try:
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
        logger.debug("Settings aplicados ao compositor OK")
    except Exception as e:
        logger.warning(f"Erro ao aplicar settings ao compositor: {e}")

    # Create and show main window
    logger.info("Criando janela principal...")
    try:
        from main_window import MainWindow
        logger.debug("MainWindow importado OK")

        window = MainWindow(settings)
        logger.debug("MainWindow criado OK")

        window.set_compositor(compositor)
        window.set_camera_manager(webcam)
        window.set_virtual_camera(virtual_cam)
        window.protocol("WM_DELETE_WINDOW", window.on_closing)
        logger.debug("Componentes configurados na janela OK")

    except Exception as e:
        logger.error(f"Erro ao criar janela: {e}\n{traceback.format_exc()}")
        show_error_dialog("Erro na Interface",
                          f"Falha ao criar janela principal:\n\n{e}\n\n"
                          f"Verifique o log em:\n{log_file}")
        sys.exit(1)

    # Show first-run dialog if driver not found
    try:
        if not driver_status.get('available', False):
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
    except Exception as e:
        logger.warning(f"Erro ao mostrar dialog first-run: {e}")

    # Auto-start if configured
    if (settings.get('general', 'auto_start_camera', False)
            and driver_status.get('available', False)):
        window.after(1000, window._start_streaming)

    logger.info("Interface grafica iniciada - entrando no mainloop")
    
    try:
        window.mainloop()
    except Exception as e:
        logger.error(f"Erro no mainloop: {e}\n{traceback.format_exc()}")
        show_error_dialog("Erro Fatal", f"Erro durante execucao:\n{e}")

    # Cleanup
    logger.info("Encerrando...")
    try:
        webcam.stop()
        virtual_cam.stop()
    except Exception:
        pass
    logger.info("=== VirtualCam Studio encerrado ===")


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        pass
    except Exception as e:
        # Catch-all for any unhandled exception
        error_msg = f"Erro fatal nao tratado:\n\n{traceback.format_exc()}"
        logger.error(error_msg)
        show_error_dialog("Erro Fatal", error_msg)
        
        # Also write to a crash file on Desktop
        try:
            desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
            crash_file = os.path.join(desktop, 'virtualcam_crash.txt')
            with open(crash_file, 'w', encoding='utf-8') as f:
                f.write(error_msg)
            print(f"Crash log salvo em: {crash_file}", file=sys.stderr)
        except Exception:
            pass
