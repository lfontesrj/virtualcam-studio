"""
Main Window - CustomTkinter GUI (Optimized - replaces PyQt5)
Control panel for VirtualCam Studio.
~5 MB instead of ~80 MB for PyQt5.
"""

import sys
import os
import time
import logging
import threading
import numpy as np
import cv2
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox, colorchooser

logger = logging.getLogger(__name__)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class CompositorThread(threading.Thread):
    """Thread that runs the compositor loop."""

    def __init__(self, camera_manager, compositor, virtual_camera,
                 on_frame=None, on_fps=None, on_error=None):
        super().__init__(daemon=True)
        self.camera_manager = camera_manager
        self.compositor = compositor
        self.virtual_camera = virtual_camera
        self.on_frame = on_frame
        self.on_fps = on_fps
        self.on_error = on_error
        self._running = False
        self._target_fps = 30

    def run(self):
        self._running = True
        frame_count = 0
        fps_timer = time.time()

        while self._running:
            try:
                start = time.time()
                webcam_frame = self.camera_manager.get_frame()
                composed = self.compositor.compose_frame(webcam_frame)

                if self.virtual_camera and self.virtual_camera.is_running():
                    self.virtual_camera.send_frame(composed)

                if self.on_frame:
                    self.on_frame(composed)

                frame_count += 1
                elapsed = time.time() - fps_timer
                if elapsed >= 1.0:
                    if self.on_fps:
                        self.on_fps(frame_count / elapsed)
                    frame_count = 0
                    fps_timer = time.time()

                frame_time = time.time() - start
                sleep_time = max(0, (1.0 / self._target_fps) - frame_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)

            except Exception as e:
                if self.on_error:
                    self.on_error(str(e))
                time.sleep(0.1)

    def stop(self):
        self._running = False


class PreviewCanvas(ctk.CTkLabel):
    """Widget that displays the video preview using CTkLabel."""

    def __init__(self, master, **kwargs):
        super().__init__(master, text="Preview", width=640, height=360,
                         fg_color="#1a1a1a", corner_radius=8, **kwargs)
        self._photo = None

    def update_frame(self, frame):
        """Update preview with a new BGR frame."""
        try:
            h, w = frame.shape[:2]
            # Resize to fit widget
            target_w, target_h = 640, 360
            scale = min(target_w / w, target_h / h)
            new_w, new_h = int(w * scale), int(h * scale)
            resized = cv2.resize(frame, (new_w, new_h))
            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

            from PIL import Image as PILImage, ImageTk
            pil_img = PILImage.fromarray(rgb)
            self._photo = ImageTk.PhotoImage(pil_img)
            self.configure(image=self._photo, text="")
        except ImportError:
            # If PIL not available, use a simpler approach
            self.configure(text=f"Transmitindo ({frame.shape[1]}x{frame.shape[0]})")
        except Exception as e:
            logger.error(f"Preview error: {e}")


class MainWindow(ctk.CTk):
    """Main application window using CustomTkinter."""

    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.camera_manager = None
        self.compositor = None
        self.virtual_camera = None
        self.compositor_thread = None
        self._is_streaming = False
        self._latest_frame = None

        self.title("VirtualCam Studio")
        self.geometry("1200x750")
        self.minsize(1000, 650)

        self._build_ui()
        self._load_settings_to_ui()

    def _build_ui(self):
        """Build the user interface."""
        # Main container
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        # Left: Preview area
        left_frame = ctk.CTkFrame(self, corner_radius=10)
        left_frame.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        self.preview = PreviewCanvas(left_frame)
        self.preview.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="nsew")

        # Preview controls
        ctrl_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        ctrl_frame.grid(row=1, column=0, padx=10, pady=(5, 10), sticky="ew")

        self.btn_start = ctk.CTkButton(
            ctrl_frame, text="\u25b6  Iniciar Transmissao",
            fg_color="#2ecc71", hover_color="#27ae60",
            height=40, font=ctk.CTkFont(size=14, weight="bold"),
            command=self._toggle_streaming
        )
        self.btn_start.pack(side="left", padx=(0, 5))

        self.btn_stop = ctk.CTkButton(
            ctrl_frame, text="\u23f9  Parar",
            fg_color="#e74c3c", hover_color="#c0392b",
            height=40, font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled", command=self._stop_streaming
        )
        self.btn_stop.pack(side="left", padx=5)

        self.lbl_fps = ctk.CTkLabel(ctrl_frame, text="FPS: --",
                                     text_color="#aaaaaa")
        self.lbl_fps.pack(side="right", padx=10)

        self.lbl_status = ctk.CTkLabel(ctrl_frame, text="\u25cf Parado",
                                        text_color="#e74c3c")
        self.lbl_status.pack(side="right", padx=10)

        # Right: Tab controls
        right_frame = ctk.CTkFrame(self, width=400, corner_radius=10)
        right_frame.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="ns")
        right_frame.grid_propagate(False)

        self.tabview = ctk.CTkTabview(right_frame, width=380)
        self.tabview.pack(padx=5, pady=5, fill="both", expand=True)

        self._build_camera_tab()
        self._build_template_tab()
        self._build_ticker_tab()
        self._build_countdown_tab()
        self._build_indicators_tab()
        self._build_settings_tab()

        # Status bar
        self.status_bar = ctk.CTkLabel(
            self, text="VirtualCam Studio pronto", anchor="w",
            text_color="#888888", height=25
        )
        self.status_bar.grid(row=1, column=0, columnspan=2,
                              padx=10, pady=(0, 5), sticky="ew")

        # Timer for preview updates
        self._schedule_preview_update()

    def _build_camera_tab(self):
        tab = self.tabview.add("Camera")

        # Input camera
        ctk.CTkLabel(tab, text="Camera de Entrada",
                     font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))

        cam_frame = ctk.CTkFrame(tab, fg_color="transparent")
        cam_frame.pack(fill="x", padx=10)

        ctk.CTkLabel(cam_frame, text="Dispositivo:").grid(
            row=0, column=0, sticky="w", pady=2)
        self.combo_camera = ctk.CTkComboBox(
            cam_frame, values=["Camera 0 (Padrao)", "Camera 1",
                                "Camera 2", "Camera 3"],
            width=200
        )
        self.combo_camera.grid(row=0, column=1, padx=5, pady=2)
        self.combo_camera.set("Camera 0 (Padrao)")

        self.chk_flip = ctk.CTkCheckBox(tab, text="Espelhar horizontalmente")
        self.chk_flip.pack(pady=5, padx=10, anchor="w")

        # Output
        ctk.CTkLabel(tab, text="Saida Virtual",
                     font=ctk.CTkFont(weight="bold")).pack(pady=(15, 5))

        out_frame = ctk.CTkFrame(tab, fg_color="transparent")
        out_frame.pack(fill="x", padx=10)

        ctk.CTkLabel(out_frame, text="Resolucao:").grid(
            row=0, column=0, sticky="w", pady=2)
        self.combo_resolution = ctk.CTkComboBox(
            out_frame, values=["1920x1080 (Full HD)", "1280x720 (HD)",
                                "960x540", "640x480"],
            width=200
        )
        self.combo_resolution.grid(row=0, column=1, padx=5, pady=2)
        self.combo_resolution.set("1280x720 (HD)")

        ctk.CTkLabel(out_frame, text="FPS:").grid(
            row=1, column=0, sticky="w", pady=2)
        self.spin_fps = ctk.CTkEntry(out_frame, width=80, placeholder_text="30")
        self.spin_fps.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        self.spin_fps.insert(0, "30")

        ctk.CTkLabel(out_frame, text="Backend:").grid(
            row=2, column=0, sticky="w", pady=2)
        self.combo_backend = ctk.CTkComboBox(
            out_frame, values=["OBS Virtual Camera", "Unity Capture",
                                "Automatico"],
            width=200
        )
        self.combo_backend.grid(row=2, column=1, padx=5, pady=2)
        self.combo_backend.set("Automatico")

    def _build_template_tab(self):
        tab = self.tabview.add("Template")

        ctk.CTkLabel(tab, text="Template de Overlay",
                     font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))

        # Built-in templates
        ctk.CTkLabel(tab, text="Templates prontos:").pack(
            padx=10, anchor="w")
        self.combo_builtin = ctk.CTkComboBox(
            tab, values=["Telejornal Classico", "Corporativo Moderno",
                          "Minimalista", "Esportivo"],
            width=280, command=self._apply_builtin_template
        )
        self.combo_builtin.pack(padx=10, pady=5)

        # Custom template
        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(btn_frame, text="Carregar Imagem...",
                      command=self._load_template).pack(side="left", padx=(0, 5))
        ctk.CTkButton(btn_frame, text="Remover",
                      fg_color="#555555",
                      command=self._clear_template).pack(side="left")

        self.lbl_template = ctk.CTkLabel(tab, text="Nenhum template carregado",
                                          text_color="#888888")
        self.lbl_template.pack(padx=10, pady=5)

        # Opacity
        ctk.CTkLabel(tab, text="Opacidade:").pack(padx=10, anchor="w")
        self.slider_template_opacity = ctk.CTkSlider(
            tab, from_=0, to=100, number_of_steps=100,
            command=self._update_template_opacity
        )
        self.slider_template_opacity.set(100)
        self.slider_template_opacity.pack(padx=10, fill="x")

    def _build_ticker_tab(self):
        tab = self.tabview.add("Ticker")

        self.chk_ticker = ctk.CTkCheckBox(
            tab, text="Ativar ticker de texto",
            command=self._toggle_ticker
        )
        self.chk_ticker.pack(pady=(10, 5), padx=10, anchor="w")
        self.chk_ticker.select()

        # File source
        file_frame = ctk.CTkFrame(tab, fg_color="transparent")
        file_frame.pack(fill="x", padx=10, pady=5)

        self.txt_ticker_file = ctk.CTkEntry(
            file_frame, placeholder_text="Arquivo .txt com texto do ticker",
            width=240
        )
        self.txt_ticker_file.pack(side="left", padx=(0, 5))

        ctk.CTkButton(file_frame, text="...", width=40,
                      command=self._select_ticker_file).pack(side="left")

        # Manual text
        ctk.CTkLabel(tab, text="Ou digite o texto:").pack(
            padx=10, anchor="w", pady=(10, 0))
        self.txt_ticker_manual = ctk.CTkTextbox(tab, height=80)
        self.txt_ticker_manual.pack(padx=10, fill="x")

        ctk.CTkButton(tab, text="Aplicar Texto Manual",
                      command=self._apply_manual_ticker).pack(padx=10, pady=5)

        # Speed
        ctk.CTkLabel(tab, text="Velocidade:").pack(padx=10, anchor="w")
        self.slider_ticker_speed = ctk.CTkSlider(
            tab, from_=1, to=10, number_of_steps=9,
            command=self._update_ticker_speed
        )
        self.slider_ticker_speed.set(2)
        self.slider_ticker_speed.pack(padx=10, fill="x")

        # Font size
        font_frame = ctk.CTkFrame(tab, fg_color="transparent")
        font_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(font_frame, text="Tamanho fonte:").pack(
            side="left")
        self.entry_ticker_font = ctk.CTkEntry(font_frame, width=60)
        self.entry_ticker_font.pack(side="left", padx=5)
        self.entry_ticker_font.insert(0, "28")

        ctk.CTkLabel(font_frame, text="Altura barra:").pack(
            side="left", padx=(10, 0))
        self.entry_ticker_height = ctk.CTkEntry(font_frame, width=60)
        self.entry_ticker_height.pack(side="left", padx=5)
        self.entry_ticker_height.insert(0, "50")

    def _build_countdown_tab(self):
        tab = self.tabview.add("Contador")

        self.chk_countdown = ctk.CTkCheckBox(
            tab, text="Ativar contador regressivo",
            command=self._toggle_countdown
        )
        self.chk_countdown.pack(pady=(10, 5), padx=10, anchor="w")

        # Duration
        dur_frame = ctk.CTkFrame(tab, fg_color="transparent")
        dur_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(dur_frame, text="Duracao (min):").pack(side="left")
        self.entry_countdown_min = ctk.CTkEntry(dur_frame, width=60)
        self.entry_countdown_min.pack(side="left", padx=5)
        self.entry_countdown_min.insert(0, "5")

        # Label
        label_frame = ctk.CTkFrame(tab, fg_color="transparent")
        label_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(label_frame, text="Rotulo:").pack(side="left")
        self.entry_countdown_label = ctk.CTkEntry(label_frame, width=150)
        self.entry_countdown_label.pack(side="left", padx=5)
        self.entry_countdown_label.insert(0, "TEMPO")

        # Position
        ctk.CTkLabel(tab, text="Posicao:").pack(padx=10, anchor="w")
        self.combo_countdown_pos = ctk.CTkComboBox(
            tab, values=["Superior Direito", "Superior Esquerdo",
                          "Centro Superior", "Inferior Direito",
                          "Inferior Esquerdo", "Centro"],
            width=200, command=self._update_countdown_position
        )
        self.combo_countdown_pos.pack(padx=10, pady=5)
        self.combo_countdown_pos.set("Superior Direito")

        # Control buttons
        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(btn_frame, text="\u25b6 Iniciar",
                      fg_color="#2ecc71", hover_color="#27ae60",
                      command=self._start_countdown).pack(
            side="left", padx=(0, 5))
        self.btn_countdown_pause = ctk.CTkButton(
            btn_frame, text="\u23f8 Pausar",
            command=self._pause_countdown
        )
        self.btn_countdown_pause.pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Resetar",
                      fg_color="#555555",
                      command=self._reset_countdown).pack(side="left", padx=5)

        self.lbl_countdown_display = ctk.CTkLabel(
            tab, text="05:00",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color="#e74c3c"
        )
        self.lbl_countdown_display.pack(pady=10)

    def _build_indicators_tab(self):
        tab = self.tabview.add("Indicadores")

        self.chk_indicators = ctk.CTkCheckBox(
            tab, text="Ativar indicadores",
            command=self._toggle_indicators
        )
        self.chk_indicators.pack(pady=(10, 5), padx=10, anchor="w")

        # File
        file_frame = ctk.CTkFrame(tab, fg_color="transparent")
        file_frame.pack(fill="x", padx=10, pady=5)

        self.txt_indicators_file = ctk.CTkEntry(
            file_frame, placeholder_text="Arquivo .txt ou .json",
            width=240
        )
        self.txt_indicators_file.pack(side="left", padx=(0, 5))

        ctk.CTkButton(file_frame, text="...", width=40,
                      command=self._select_indicators_file).pack(side="left")

        # Position
        ctk.CTkLabel(tab, text="Posicao:").pack(padx=10, anchor="w", pady=(10, 0))
        self.combo_indicators_pos = ctk.CTkComboBox(
            tab, values=["Superior Esquerdo", "Superior Direito",
                          "Inferior Esquerdo", "Inferior Direito"],
            width=200, command=self._update_indicators_position
        )
        self.combo_indicators_pos.pack(padx=10, pady=5)
        self.combo_indicators_pos.set("Superior Esquerdo")

        # Auto reload
        self.chk_auto_reload = ctk.CTkCheckBox(
            tab, text="Recarregar automaticamente"
        )
        self.chk_auto_reload.pack(padx=10, pady=5, anchor="w")
        self.chk_auto_reload.select()

        reload_frame = ctk.CTkFrame(tab, fg_color="transparent")
        reload_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(reload_frame, text="Intervalo (seg):").pack(side="left")
        self.entry_reload_interval = ctk.CTkEntry(reload_frame, width=60)
        self.entry_reload_interval.pack(side="left", padx=5)
        self.entry_reload_interval.insert(0, "5")

        ctk.CTkButton(tab, text="Recarregar Agora",
                      command=self._reload_indicators).pack(padx=10, pady=10)

        # Help text
        ctk.CTkLabel(
            tab, text="Formato: LABEL: VALOR (um por linha)\nOu JSON: [{\"label\":..., \"value\":...}]",
            text_color="#888888", font=ctk.CTkFont(size=11),
            justify="left"
        ).pack(padx=10, anchor="w")

    def _build_settings_tab(self):
        tab = self.tabview.add("Config")

        ctk.CTkLabel(tab, text="Configuracoes Gerais",
                     font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))

        self.chk_auto_start = ctk.CTkCheckBox(
            tab, text="Iniciar camera automaticamente"
        )
        self.chk_auto_start.pack(padx=10, pady=5, anchor="w")

        self.chk_start_minimized = ctk.CTkCheckBox(
            tab, text="Iniciar minimizado"
        )
        self.chk_start_minimized.pack(padx=10, pady=5, anchor="w")

        ctk.CTkButton(tab, text="Salvar Configuracoes",
                      command=self._save_all_settings).pack(padx=10, pady=10)

        ctk.CTkButton(tab, text="Restaurar Padroes",
                      fg_color="#555555",
                      command=self._reset_settings).pack(padx=10, pady=5)

        # Driver tools
        ctk.CTkLabel(tab, text="Driver de Camera Virtual",
                     font=ctk.CTkFont(weight="bold")).pack(pady=(20, 5))

        ctk.CTkButton(tab, text="Verificar Status do Driver",
                      command=self._check_driver_status).pack(padx=10, pady=5)

        ctk.CTkButton(tab, text="Instalar/Registrar Driver",
                      command=self._install_driver).pack(padx=10, pady=5)

        # Info
        ctk.CTkLabel(
            tab,
            text="VirtualCam Studio v1.0.0\nCamera virtual com overlays\nestilo telejornal",
            text_color="#888888", font=ctk.CTkFont(size=11),
            justify="center"
        ).pack(pady=20)

    # ---- Preview Update ----

    def _schedule_preview_update(self):
        """Schedule periodic preview updates from the compositor thread."""
        if self._latest_frame is not None:
            self.preview.update_frame(self._latest_frame)
        # Update countdown display
        if self.compositor and self.compositor.countdown_layer.visible:
            remaining = self.compositor.countdown_layer.get_remaining()
            self.lbl_countdown_display.configure(
                text=self.compositor.countdown_layer._format_time(remaining)
            )
        self.after(33, self._schedule_preview_update)  # ~30fps

    def _on_frame(self, frame):
        """Called from compositor thread with new frame."""
        self._latest_frame = frame

    def _on_fps(self, fps):
        """Called from compositor thread with FPS update."""
        self.lbl_fps.configure(text=f"FPS: {fps:.1f}")

    def _on_error(self, error_msg):
        logger.error(f"Compositor error: {error_msg}")

    # ---- Component setters ----

    def set_compositor(self, compositor):
        self.compositor = compositor

    def set_camera_manager(self, camera_manager):
        self.camera_manager = camera_manager

    def set_virtual_camera(self, virtual_camera):
        self.virtual_camera = virtual_camera

    # ---- Streaming ----

    def _toggle_streaming(self):
        if not self._is_streaming:
            self._start_streaming()
        else:
            self._stop_streaming()

    def _start_streaming(self):
        if self.compositor is None or self.camera_manager is None:
            messagebox.showwarning("Erro", "Compositor nao inicializado.")
            return

        try:
            # Parse camera index
            cam_text = self.combo_camera.get()
            device_idx = 0
            for i in range(10):
                if f"Camera {i}" in cam_text:
                    device_idx = i
                    break
            self.camera_manager.device_index = device_idx
            self.camera_manager.start()

            # Start virtual camera
            if self.virtual_camera:
                backend_text = self.combo_backend.get()
                backend_map = {
                    "OBS Virtual Camera": "obs",
                    "Unity Capture": "unitycapture",
                    "Automatico": None
                }
                backend = backend_map.get(backend_text, None)
                if backend:
                    self.virtual_camera.start(preferred_backend=backend)
                else:
                    self.virtual_camera.start()

            # Start compositor thread
            self.compositor_thread = CompositorThread(
                self.camera_manager, self.compositor, self.virtual_camera,
                on_frame=self._on_frame,
                on_fps=self._on_fps,
                on_error=self._on_error
            )
            self.compositor_thread.start()

            self._is_streaming = True
            self.btn_start.configure(state="disabled")
            self.btn_stop.configure(state="normal")
            self.lbl_status.configure(text="\u25cf Transmitindo",
                                       text_color="#2ecc71")
            self.status_bar.configure(text="Camera virtual ativa")

        except Exception as e:
            messagebox.showerror("Erro ao iniciar", f"Erro: {str(e)}")
            self._stop_streaming()

    def _stop_streaming(self):
        if self.compositor_thread:
            self.compositor_thread.stop()
            self.compositor_thread = None

        if self.camera_manager:
            self.camera_manager.stop()

        if self.virtual_camera:
            self.virtual_camera.stop()

        self._is_streaming = False
        self._latest_frame = None
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.lbl_status.configure(text="\u25cf Parado", text_color="#e74c3c")
        self.lbl_fps.configure(text="FPS: --")
        self.status_bar.configure(text="Camera virtual parada")

    # ---- Template ----

    def _load_template(self):
        filepath = filedialog.askopenfilename(
            title="Selecionar Template",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp")]
        )
        if filepath and self.compositor:
            if self.compositor.template_layer.load_image(filepath):
                self.compositor.template_layer.visible = True
                self.lbl_template.configure(
                    text=os.path.basename(filepath))

    def _clear_template(self):
        if self.compositor:
            self.compositor.template_layer._image_bgra = None
            self.compositor.template_layer.visible = False
            self.lbl_template.configure(text="Nenhum template carregado")

    def _apply_builtin_template(self, choice):
        template_map = {
            "Telejornal Classico": "newscast_classic",
            "Corporativo Moderno": "corporate_modern",
            "Minimalista": "minimalist",
            "Esportivo": "sports",
        }
        template_id = template_map.get(choice)
        if template_id and self.compositor:
            base_dir = os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            path = os.path.join(base_dir, 'assets', 'templates',
                                f'{template_id}.png')
            if os.path.exists(path):
                self.compositor.template_layer.load_image(path)
                self.compositor.template_layer.visible = True
                self.lbl_template.configure(text=choice)

    def _update_template_opacity(self, value):
        if self.compositor:
            self.compositor.template_layer.opacity = value / 100.0

    # ---- Ticker ----

    def _toggle_ticker(self):
        if self.compositor:
            self.compositor.ticker_layer.visible = self.chk_ticker.get()

    def _select_ticker_file(self):
        filepath = filedialog.askopenfilename(
            title="Selecionar Arquivo de Texto",
            filetypes=[("Texto", "*.txt"), ("Todos", "*.*")]
        )
        if filepath:
            self.txt_ticker_file.delete(0, "end")
            self.txt_ticker_file.insert(0, filepath)
            if self.compositor:
                self.compositor.ticker_layer.load_text_from_file(filepath)

    def _apply_manual_ticker(self):
        text = self.txt_ticker_manual.get("1.0", "end").strip()
        if text and self.compositor:
            sep = "     \u25cf     "
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            self.compositor.ticker_layer.text = sep.join(lines)

    def _update_ticker_speed(self, value):
        if self.compositor:
            self.compositor.ticker_layer.scroll_speed = int(value)

    # ---- Countdown ----

    def _toggle_countdown(self):
        if self.compositor:
            self.compositor.countdown_layer.visible = self.chk_countdown.get()

    def _start_countdown(self):
        if self.compositor:
            try:
                minutes = int(self.entry_countdown_min.get())
            except ValueError:
                minutes = 5
            self.compositor.countdown_layer.duration_seconds = minutes * 60
            self.compositor.countdown_layer.start()

    def _pause_countdown(self):
        if self.compositor:
            layer = self.compositor.countdown_layer
            if layer._paused:
                layer.resume()
                self.btn_countdown_pause.configure(text="\u23f8 Pausar")
            else:
                layer.pause()
                self.btn_countdown_pause.configure(text="\u25b6 Retomar")

    def _reset_countdown(self):
        if self.compositor:
            try:
                minutes = int(self.entry_countdown_min.get())
            except ValueError:
                minutes = 5
            self.compositor.countdown_layer.reset(minutes * 60)

    def _update_countdown_position(self, choice):
        pos_map = {
            "Superior Direito": "top-right",
            "Superior Esquerdo": "top-left",
            "Centro Superior": "top-center",
            "Inferior Direito": "bottom-right",
            "Inferior Esquerdo": "bottom-left",
            "Centro": "center",
        }
        if self.compositor:
            self.compositor.countdown_layer.position = pos_map.get(
                choice, "top-right"
            )

    # ---- Indicators ----

    def _toggle_indicators(self):
        if self.compositor:
            self.compositor.indicator_layer.visible = self.chk_indicators.get()

    def _select_indicators_file(self):
        filepath = filedialog.askopenfilename(
            title="Selecionar Arquivo de Indicadores",
            filetypes=[("Texto", "*.txt"), ("JSON", "*.json"),
                        ("Todos", "*.*")]
        )
        if filepath:
            self.txt_indicators_file.delete(0, "end")
            self.txt_indicators_file.insert(0, filepath)
            if self.compositor:
                self.compositor.indicator_layer.load_indicators(filepath)

    def _update_indicators_position(self, choice):
        pos_map = {
            "Superior Esquerdo": "top-left",
            "Superior Direito": "top-right",
            "Inferior Esquerdo": "bottom-left",
            "Inferior Direito": "bottom-right",
        }
        if self.compositor:
            self.compositor.indicator_layer.position = pos_map.get(
                choice, "top-left"
            )

    def _reload_indicators(self):
        if self.compositor:
            self.compositor.indicator_layer.reload()
            self.status_bar.configure(text="Indicadores recarregados")

    # ---- Settings ----

    def _save_all_settings(self):
        s = self.settings
        s.set('camera', 'flip_horizontal', bool(self.chk_flip.get()))
        try:
            s.set('camera', 'fps', int(self.spin_fps.get()))
        except ValueError:
            pass

        res_text = self.combo_resolution.get()
        if "1920" in res_text:
            s.set('camera', 'output_width', 1920)
            s.set('camera', 'output_height', 1080)
        elif "1280" in res_text:
            s.set('camera', 'output_width', 1280)
            s.set('camera', 'output_height', 720)
        elif "960" in res_text:
            s.set('camera', 'output_width', 960)
            s.set('camera', 'output_height', 540)
        else:
            s.set('camera', 'output_width', 640)
            s.set('camera', 'output_height', 480)

        s.set('ticker', 'enabled', bool(self.chk_ticker.get()))
        s.set('ticker', 'text_file', self.txt_ticker_file.get())
        s.set('ticker', 'scroll_speed', int(self.slider_ticker_speed.get()))

        s.set('countdown', 'enabled', bool(self.chk_countdown.get()))
        s.set('indicators', 'enabled', bool(self.chk_indicators.get()))
        s.set('indicators', 'data_file', self.txt_indicators_file.get())

        s.set('general', 'auto_start_camera',
              bool(self.chk_auto_start.get()))
        s.set('general', 'start_minimized',
              bool(self.chk_start_minimized.get()))

        s.save()
        self.status_bar.configure(text="Configuracoes salvas!")

    def _load_settings_to_ui(self):
        s = self.settings
        if s.get('camera', 'flip_horizontal', False):
            self.chk_flip.select()
        if s.get('ticker', 'enabled', True):
            self.chk_ticker.select()
        ticker_file = s.get('ticker', 'text_file', '')
        if ticker_file:
            self.txt_ticker_file.insert(0, ticker_file)
        if s.get('countdown', 'enabled', False):
            self.chk_countdown.select()
        if s.get('indicators', 'enabled', False):
            self.chk_indicators.select()
        ind_file = s.get('indicators', 'data_file', '')
        if ind_file:
            self.txt_indicators_file.insert(0, ind_file)
        if s.get('general', 'auto_start_camera', False):
            self.chk_auto_start.select()
        if s.get('general', 'start_minimized', False):
            self.chk_start_minimized.select()

    def _reset_settings(self):
        if messagebox.askyesno("Confirmar",
                                "Restaurar todas as configuracoes?"):
            self.settings.reset()
            self.status_bar.configure(text="Configuracoes restauradas")

    # ---- Driver Tools ----

    def _check_driver_status(self):
        try:
            from first_run import check_virtual_camera_driver
            status = check_virtual_camera_driver()
            if status['available']:
                messagebox.showinfo(
                    "Status do Driver",
                    f"Driver Disponivel!\n\n"
                    f"Driver: {status['driver_name']}\n"
                    f"{status['message']}"
                )
            else:
                messagebox.showwarning(
                    "Status do Driver",
                    f"Driver Nao Encontrado\n\n{status['message']}"
                )
        except Exception as e:
            messagebox.showwarning("Erro", f"Erro ao verificar: {e}")

    def _install_driver(self):
        import webbrowser
        choice = messagebox.askyesnocancel(
            "Instalar Driver",
            "O VirtualCam Studio precisa do driver de camera virtual "
            "do OBS Studio.\n\n"
            "Sim - Abrir pagina de download do OBS\n"
            "Nao - Tentar registrar driver existente\n"
            "Cancelar - Voltar"
        )
        if choice is True:
            webbrowser.open("https://obsproject.com/download")
        elif choice is False:
            try:
                from first_run import install_obs_virtualcam
                success, message = install_obs_virtualcam()
                if success:
                    messagebox.showinfo("Sucesso", message)
                else:
                    messagebox.showwarning("Aviso", message)
            except Exception as e:
                messagebox.showwarning("Erro", f"Erro: {e}")

    # ---- Cleanup ----

    def on_closing(self):
        if self._is_streaming:
            if not messagebox.askyesno("Confirmar",
                                        "A camera esta ativa. Deseja sair?"):
                return
            self._stop_streaming()
        self._save_all_settings()
        self.destroy()
