"""
Video Compositor Module (Optimized - No Pillow dependency)
Handles frame composition with multiple overlay layers using only OpenCV + NumPy.
"""

import cv2
import numpy as np
import os
import time
import logging
import json

logger = logging.getLogger(__name__)


# ---- Font Helper ----

def find_system_font():
    """Find a usable font file on the system for cv2.freetype (if available)."""
    candidates = [
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for fp in candidates:
        if os.path.exists(fp):
            return fp
    return None


def find_system_font_bold():
    """Find a bold font file."""
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for fp in candidates:
        if os.path.exists(fp):
            return fp
    return find_system_font()


# Try to use cv2.freetype for better text; fall back to cv2.putText
_freetype_instance = None
_freetype_available = False

try:
    _ft = cv2.freetype.createFreeType2()
    _font_path = find_system_font()
    if _font_path:
        _ft.loadFontData(_font_path, 0)
        _freetype_instance = _ft
        _freetype_available = True
except Exception:
    _freetype_available = False


def put_text(img, text, org, font_height, color_bgr, thickness=1, bold=False):
    """
    Draw text on an image. Uses freetype if available, else cv2.putText.
    Returns the (width, height) of the drawn text.
    """
    if _freetype_available and _freetype_instance is not None:
        try:
            ft = _freetype_instance
            (tw, th), baseline = ft.getTextSize(text, font_height, thickness)
            ft.putText(img, text, org, font_height, color_bgr,
                       thickness, cv2.LINE_AA, False)
            return (tw, th)
        except Exception:
            pass

    # Fallback: cv2.putText with FONT_HERSHEY
    font_face = cv2.FONT_HERSHEY_SIMPLEX
    if bold:
        font_face = cv2.FONT_HERSHEY_DUPLEX
    scale = font_height / 30.0
    thick = max(1, int(thickness))
    if bold:
        thick = max(2, thick + 1)
    (tw, th), baseline = cv2.getTextSize(text, font_face, scale, thick)
    # cv2.putText origin is bottom-left of text
    cv2.putText(img, text, (org[0], org[1] + th), font_face, scale,
                color_bgr, thick, cv2.LINE_AA)
    return (tw, th)


def get_text_size(text, font_height, thickness=1):
    """Get the size of text without drawing it."""
    if _freetype_available and _freetype_instance is not None:
        try:
            (tw, th), baseline = _freetype_instance.getTextSize(
                text, font_height, thickness
            )
            return (tw, th)
        except Exception:
            pass

    font_face = cv2.FONT_HERSHEY_SIMPLEX
    scale = font_height / 30.0
    (tw, th), baseline = cv2.getTextSize(text, font_face, scale,
                                          max(1, int(thickness)))
    return (tw, th)


# ---- Layer Classes ----

class Layer:
    """Base class for overlay layers."""

    def __init__(self, name="Layer", visible=True, opacity=1.0, z_order=0):
        self.name = name
        self.visible = visible
        self.opacity = opacity
        self.z_order = z_order

    def render(self, frame, canvas_width, canvas_height, timestamp):
        raise NotImplementedError


class WebcamLayer(Layer):
    """Layer that displays the webcam feed."""

    def __init__(self, **kwargs):
        super().__init__(name="Webcam", **kwargs)
        self.x = 0
        self.y = 0
        self.width = None
        self.height = None
        self.flip_horizontal = False

    def set_region(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def render(self, frame, canvas_width, canvas_height, timestamp,
               webcam_frame=None):
        if not self.visible or webcam_frame is None:
            return frame

        w = self.width or canvas_width
        h = self.height or canvas_height
        resized = cv2.resize(webcam_frame, (w, h))

        if self.flip_horizontal:
            resized = cv2.flip(resized, 1)

        if self.opacity < 1.0:
            roi = frame[self.y:self.y + h, self.x:self.x + w]
            blended = cv2.addWeighted(resized, self.opacity, roi,
                                       1 - self.opacity, 0)
            frame[self.y:self.y + h, self.x:self.x + w] = blended
        else:
            frame[self.y:self.y + h, self.x:self.x + w] = resized

        return frame


class ImageOverlayLayer(Layer):
    """Layer that displays a static image overlay (PNG with transparency)."""

    def __init__(self, image_path=None, **kwargs):
        super().__init__(name="Image Overlay", **kwargs)
        self.image_path = image_path
        self._image_bgra = None
        self._loaded_path = None

    def load_image(self, path):
        if path and os.path.exists(path):
            self._image_bgra = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if self._image_bgra is not None:
                self._loaded_path = path
                self.image_path = path
                logger.info(f"Loaded overlay image: {path}")
                return True
        logger.warning(f"Failed to load image: {path}")
        return False

    def render(self, frame, canvas_width, canvas_height, timestamp, **kwargs):
        if not self.visible or self._image_bgra is None:
            return frame

        overlay = cv2.resize(self._image_bgra, (canvas_width, canvas_height))

        if overlay.shape[2] == 4:
            alpha = overlay[:, :, 3] / 255.0 * self.opacity
            alpha = np.stack([alpha] * 3, axis=-1)
            bgr_overlay = overlay[:, :, :3]
            frame = (bgr_overlay * alpha + frame * (1 - alpha)).astype(np.uint8)
        else:
            if self.opacity < 1.0:
                frame = cv2.addWeighted(overlay[:, :, :3], self.opacity,
                                         frame, 1 - self.opacity, 0)
            else:
                frame = overlay[:, :, :3]

        return frame


class TickerLayer(Layer):
    """Scrolling text ticker (news-style bottom bar) - OpenCV only."""

    def __init__(self, **kwargs):
        super().__init__(name="Ticker", **kwargs)
        self.text = ""
        self.text_file = None
        self.font_size = 28
        self.font_color = (255, 255, 255)  # RGB
        self.bg_color = (30, 30, 30)  # RGB
        self.bar_height = 50
        self.scroll_speed = 2
        self.bar_position = "bottom"
        self.bar_y = None
        self.bar_opacity = 0.85
        self._scroll_offset = 0
        self._separator = "     \u25cf     "

    def load_text_from_file(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            self.text = self._separator.join(
                line.strip() for line in lines if line.strip()
            )
            self.text_file = filepath
            logger.info(f"Loaded ticker text from: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to load ticker text: {e}")
            return False

    def reload_text(self):
        if self.text_file:
            return self.load_text_from_file(self.text_file)
        return False

    def render(self, frame, canvas_width, canvas_height, timestamp, **kwargs):
        if not self.visible or not self.text:
            return frame

        # Determine bar Y position
        if self.bar_position == "bottom":
            bar_y = canvas_height - self.bar_height
        else:
            bar_y = self.bar_y or (canvas_height - self.bar_height)

        # Draw bar background
        bar_overlay = frame.copy()
        bg_bgr = (self.bg_color[2], self.bg_color[1], self.bg_color[0])
        cv2.rectangle(bar_overlay, (0, bar_y),
                       (canvas_width, bar_y + self.bar_height),
                       bg_bgr, -1)
        frame = cv2.addWeighted(bar_overlay, self.bar_opacity,
                                 frame, 1 - self.bar_opacity, 0)

        # Calculate text dimensions
        full_text = self.text + self._separator + self.text
        single_text = self.text + self._separator
        single_tw, single_th = get_text_size(single_text, self.font_size)

        # Text Y centered in bar
        text_y = bar_y + (self.bar_height - self.font_size) // 2

        # Scroll position
        x_pos = canvas_width - int(self._scroll_offset) % (
            single_tw + canvas_width
        )

        # Draw text (color in BGR)
        color_bgr = (self.font_color[2], self.font_color[1], self.font_color[0])
        put_text(frame, full_text, (x_pos, text_y), self.font_size, color_bgr)

        # Update scroll
        self._scroll_offset += self.scroll_speed

        return frame


class CountdownLayer(Layer):
    """Countdown timer overlay - OpenCV only."""

    def __init__(self, **kwargs):
        super().__init__(name="Countdown", **kwargs)
        self.duration_seconds = 300
        self.font_size = 48
        self.font_color = (255, 255, 255)  # RGB
        self.bg_color = (200, 30, 30)  # RGB
        self.position = "top-right"
        self.padding = 15
        self.show_label = True
        self.label_text = "TEMPO"
        self._start_time = None
        self._paused = False
        self._pause_remaining = 0
        self._finished = False

    def start(self):
        self._start_time = time.time()
        self._paused = False
        self._finished = False

    def pause(self):
        if self._start_time and not self._paused:
            elapsed = time.time() - self._start_time
            self._pause_remaining = max(0, self.duration_seconds - elapsed)
            self._paused = True

    def resume(self):
        if self._paused:
            self.duration_seconds = self._pause_remaining
            self._start_time = time.time()
            self._paused = False

    def reset(self, duration=None):
        if duration is not None:
            self.duration_seconds = duration
        self._start_time = None
        self._paused = False
        self._finished = False

    def get_remaining(self):
        if self._start_time is None:
            return self.duration_seconds
        if self._paused:
            return self._pause_remaining
        elapsed = time.time() - self._start_time
        remaining = max(0, self.duration_seconds - elapsed)
        if remaining == 0:
            self._finished = True
        return remaining

    def _format_time(self, seconds):
        seconds = int(seconds)
        if seconds >= 3600:
            h = seconds // 3600
            m = (seconds % 3600) // 60
            s = seconds % 60
            return f"{h:02d}:{m:02d}:{s:02d}"
        else:
            m = seconds // 60
            s = seconds % 60
            return f"{m:02d}:{s:02d}"

    def render(self, frame, canvas_width, canvas_height, timestamp, **kwargs):
        if not self.visible:
            return frame

        remaining = self.get_remaining()
        time_str = self._format_time(remaining)

        # Measure text
        time_tw, time_th = get_text_size(time_str, self.font_size, 2)
        label_th = 0
        label_tw = 0
        label_font_size = int(self.font_size * 0.5)
        if self.show_label:
            label_tw, label_th = get_text_size(
                self.label_text, label_font_size, 1
            )
            label_th += 5

        box_w = max(time_tw, label_tw) + self.padding * 2
        box_h = time_th + label_th + self.padding * 2

        # Position
        positions = {
            "top-left": (10, 10),
            "top-right": (canvas_width - box_w - 10, 10),
            "top-center": ((canvas_width - box_w) // 2, 10),
            "bottom-left": (10, canvas_height - box_h - 60),
            "bottom-right": (canvas_width - box_w - 10,
                              canvas_height - box_h - 60),
            "center": ((canvas_width - box_w) // 2,
                        (canvas_height - box_h) // 2),
        }
        bx, by = positions.get(self.position, (10, 10))

        # Draw background box
        bg_bgr = (self.bg_color[2], self.bg_color[1], self.bg_color[0])
        overlay = frame.copy()
        cv2.rectangle(overlay, (bx, by), (bx + box_w, by + box_h),
                       bg_bgr, -1)
        frame = cv2.addWeighted(overlay, self.opacity, frame,
                                 1 - self.opacity, 0)

        # Draw label
        text_y = by + self.padding
        color_bgr = (self.font_color[2], self.font_color[1],
                      self.font_color[0])

        if self.show_label:
            lx = bx + (box_w - label_tw) // 2
            put_text(frame, self.label_text, (lx, text_y),
                     label_font_size, color_bgr)
            text_y += label_th

        # Flash effect when time is low
        if remaining <= 30 and int(remaining * 2) % 2 == 0:
            color_bgr = (100, 100, 255)  # light red in BGR

        text_x = bx + (box_w - time_tw) // 2
        put_text(frame, time_str, (text_x, text_y), self.font_size,
                 color_bgr, thickness=2, bold=True)

        return frame


class IndicatorLayer(Layer):
    """Displays real-time indicators - OpenCV only."""

    def __init__(self, **kwargs):
        super().__init__(name="Indicators", **kwargs)
        self.indicators_file = None
        self.indicators = []
        self.font_size = 22
        self.font_color = (255, 255, 255)  # RGB
        self.bg_color = (40, 40, 40)  # RGB
        self.position = "top-left"
        self.padding = 10
        self.item_spacing = 5
        self.auto_reload = True
        self.reload_interval = 5
        self._last_reload = 0

    def load_indicators(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            try:
                data = json.loads(content)
                if isinstance(data, list):
                    self.indicators = data
                    self.indicators_file = filepath
                    return True
            except json.JSONDecodeError:
                pass

            indicators = []
            for line in content.split('\n'):
                line = line.strip()
                if ':' in line:
                    parts = line.split(':', 1)
                    indicators.append({
                        'label': parts[0].strip(),
                        'value': parts[1].strip(),
                        'color': None
                    })
                elif line:
                    indicators.append({
                        'label': '',
                        'value': line,
                        'color': None
                    })

            self.indicators = indicators
            self.indicators_file = filepath
            logger.info(f"Loaded {len(indicators)} indicators from {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to load indicators: {e}")
            return False

    def reload(self):
        if self.indicators_file:
            return self.load_indicators(self.indicators_file)
        return False

    def render(self, frame, canvas_width, canvas_height, timestamp, **kwargs):
        if not self.visible or not self.indicators:
            return frame

        if (self.auto_reload and self.indicators_file and
                timestamp - self._last_reload > self.reload_interval):
            self.reload()
            self._last_reload = timestamp

        # Measure all items
        max_w = 0
        total_h = self.padding
        item_heights = []

        for ind in self.indicators:
            text = (f"{ind['label']}: {ind['value']}" if ind['label']
                    else ind['value'])
            tw, th = get_text_size(text, self.font_size)
            max_w = max(max_w, tw)
            item_heights.append(th)
            total_h += th + self.item_spacing

        total_h += self.padding
        box_w = max_w + self.padding * 2
        box_h = total_h

        # Position
        positions = {
            "top-left": (10, 10),
            "top-right": (canvas_width - box_w - 10, 10),
            "bottom-left": (10, canvas_height - box_h - 60),
            "bottom-right": (canvas_width - box_w - 10,
                              canvas_height - box_h - 60),
        }
        bx, by = positions.get(self.position, (10, 10))

        # Draw background
        bg_bgr = (self.bg_color[2], self.bg_color[1], self.bg_color[0])
        overlay = frame.copy()
        cv2.rectangle(overlay, (bx, by), (bx + box_w, by + box_h),
                       bg_bgr, -1)
        frame = cv2.addWeighted(overlay, self.opacity * 0.8, frame,
                                 1 - self.opacity * 0.8, 0)

        # Draw indicators
        y_offset = by + self.padding
        for i, ind in enumerate(self.indicators):
            color = ind.get('color', None) or list(self.font_color)
            color_bgr = (color[2], color[1], color[0])

            text = (f"{ind['label']}: {ind['value']}" if ind['label']
                    else ind['value'])
            put_text(frame, text, (bx + self.padding, y_offset),
                     self.font_size, color_bgr)
            y_offset += item_heights[i] + self.item_spacing

        return frame


class Compositor:
    """Main compositor that manages all layers and produces the final frame."""

    def __init__(self, width=1280, height=720):
        self.width = width
        self.height = height
        self.bg_color = (0, 0, 0)

        self.webcam_layer = WebcamLayer(z_order=0)
        self.template_layer = ImageOverlayLayer(z_order=10)
        self.template_layer.name = "Template"
        self.ticker_layer = TickerLayer(z_order=20)
        self.countdown_layer = CountdownLayer(z_order=30)
        self.countdown_layer.visible = False
        self.indicator_layer = IndicatorLayer(z_order=40)
        self.indicator_layer.visible = False

        self._layers = [
            self.webcam_layer,
            self.template_layer,
            self.ticker_layer,
            self.countdown_layer,
            self.indicator_layer,
        ]

    def compose_frame(self, webcam_frame=None):
        timestamp = time.time()
        canvas = np.full(
            (self.height, self.width, 3),
            self.bg_color, dtype=np.uint8
        )

        sorted_layers = sorted(self._layers, key=lambda l: l.z_order)

        for layer in sorted_layers:
            if not layer.visible:
                continue
            if isinstance(layer, WebcamLayer):
                canvas = layer.render(canvas, self.width, self.height,
                                       timestamp, webcam_frame=webcam_frame)
            else:
                canvas = layer.render(canvas, self.width, self.height,
                                       timestamp)

        return canvas

    def get_layers(self):
        return sorted(self._layers, key=lambda l: l.z_order)

    def add_custom_layer(self, layer):
        self._layers.append(layer)

    def remove_layer(self, layer):
        if layer in self._layers:
            self._layers.remove(layer)
