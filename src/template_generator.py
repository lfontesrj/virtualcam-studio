"""
Template Generator Module (Optimized - No Pillow dependency)
Creates broadcast-style overlay templates using only OpenCV + NumPy.
"""

import os
import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)


def draw_rect_alpha(img, pt1, pt2, color_bgra):
    """Draw a semi-transparent filled rectangle on a BGRA image."""
    x1, y1 = int(pt1[0]), int(pt1[1])
    x2, y2 = int(pt2[0]), int(pt2[1])
    x1, x2 = max(0, x1), min(img.shape[1], x2)
    y1, y2 = max(0, y1), min(img.shape[0], y2)
    b, g, r, a = color_bgra
    alpha = a / 255.0
    roi = img[y1:y2, x1:x2]
    roi[:, :, 0] = (roi[:, :, 0] * (1 - alpha) + b * alpha).astype(np.uint8)
    roi[:, :, 1] = (roi[:, :, 1] * (1 - alpha) + g * alpha).astype(np.uint8)
    roi[:, :, 2] = (roi[:, :, 2] * (1 - alpha) + r * alpha).astype(np.uint8)
    roi[:, :, 3] = np.clip(
        roi[:, :, 3].astype(np.float32) + a * alpha, 0, 255
    ).astype(np.uint8)


def put_text_alpha(img, text, org, font_scale, color_bgra, thickness=1,
                   font=cv2.FONT_HERSHEY_SIMPLEX):
    """Draw text with alpha on a BGRA image."""
    b, g, r, a = color_bgra
    # Draw on a temporary layer
    temp = np.zeros_like(img)
    cv2.putText(temp, text, org, font, font_scale, (b, g, r, 255),
                thickness, cv2.LINE_AA)
    mask = temp[:, :, 3] > 0
    alpha = a / 255.0
    for c in range(3):
        img[:, :, c][mask] = (
            img[:, :, c][mask] * (1 - alpha) + temp[:, :, c][mask] * alpha
        ).astype(np.uint8)
    img[:, :, 3][mask] = np.clip(
        img[:, :, 3][mask].astype(np.float32) + a * alpha, 0, 255
    ).astype(np.uint8)


def create_newscast_classic(width=1280, height=720, output_path=None):
    """Classic newscast-style overlay template."""
    img = np.zeros((height, width, 4), dtype=np.uint8)

    # Top bar
    top_h = 50
    for y in range(top_h):
        a = int(200 * (1 - y / top_h * 0.3))
        draw_rect_alpha(img, (0, y), (width, y + 1), (60, 30, 20, a))

    # Top accent line
    draw_rect_alpha(img, (0, top_h - 3), (width, top_h), (185, 128, 41, 230))

    # LIVE badge
    draw_rect_alpha(img, (15, 10), (75, 40), (60, 76, 231, 230))
    put_text_alpha(img, "LIVE", (22, 32), 0.6, (255, 255, 255, 255), 2,
                   cv2.FONT_HERSHEY_DUPLEX)

    # Brand text
    put_text_alpha(img, "VirtualCam Studio", (width - 220, 30), 0.5,
                   (200, 200, 200, 200), 1)

    # Lower third name plate
    lt_y = height - 160
    lt_h = 60
    lt_w = 400
    draw_rect_alpha(img, (30, lt_y), (30 + lt_w, lt_y + lt_h),
                    (185, 128, 41, 220))
    draw_rect_alpha(img, (30, lt_y), (38, lt_y + lt_h), (219, 152, 52, 250))

    put_text_alpha(img, "Seu Nome Aqui", (48, lt_y + 28), 0.7,
                   (255, 255, 255, 255), 2, cv2.FONT_HERSHEY_DUPLEX)
    put_text_alpha(img, "Cargo / Departamento", (48, lt_y + 52), 0.45,
                   (240, 220, 200, 220), 1)

    # Bottom ticker bar
    tk_y = height - 55
    for y in range(55):
        a = int(220 * (0.7 + 0.3 * (y / 55)))
        draw_rect_alpha(img, (0, tk_y + y), (width, tk_y + y + 1),
                        (40, 20, 15, a))
    draw_rect_alpha(img, (0, tk_y), (width, tk_y + 2), (185, 128, 41, 200))

    if output_path:
        cv2.imwrite(output_path, img)
        logger.info(f"Template saved: {output_path}")
    return img


def create_corporate_modern(width=1280, height=720, output_path=None):
    """Modern corporate-style overlay template."""
    img = np.zeros((height, width, 4), dtype=np.uint8)

    # Top gradient
    for y in range(40):
        a = int(180 * (1 - y / 40))
        draw_rect_alpha(img, (0, y), (width, y + 1), (30, 30, 30, a))

    # Accent line (green to blue gradient)
    for x in range(width):
        p = x / width
        r = int(46 + (52 - 46) * p)
        g = int(204 + (152 - 204) * p)
        b = int(113 + (219 - 113) * p)
        draw_rect_alpha(img, (x, 40), (x + 1, 43), (b, g, r, 200))

    # Logo area
    put_text_alpha(img, "EMPRESA", (40, 28), 0.6, (255, 255, 255, 200), 2,
                   cv2.FONT_HERSHEY_DUPLEX)

    # Lower third
    lt_y = height - 140
    lt_w = 350
    lt_h = 50
    draw_rect_alpha(img, (25, lt_y), (25 + lt_w, lt_y + lt_h),
                    (255, 255, 255, 40))
    draw_rect_alpha(img, (25, lt_y), (32, lt_y + lt_h), (113, 204, 46, 230))

    put_text_alpha(img, "Nome do Apresentador", (42, lt_y + 24), 0.6,
                   (255, 255, 255, 240), 2, cv2.FONT_HERSHEY_DUPLEX)
    put_text_alpha(img, "Titulo / Departamento", (42, lt_y + 44), 0.4,
                   (200, 200, 200, 200), 1)

    # Bottom bar
    bar_y = height - 50
    draw_rect_alpha(img, (0, bar_y), (width, height), (20, 20, 20, 200))
    draw_rect_alpha(img, (0, bar_y), (width, bar_y + 2), (113, 204, 46, 180))

    if output_path:
        cv2.imwrite(output_path, img)
        logger.info(f"Template saved: {output_path}")
    return img


def create_minimalist(width=1280, height=720, output_path=None):
    """Minimalist overlay template."""
    img = np.zeros((height, width, 4), dtype=np.uint8)

    # Thin top line
    draw_rect_alpha(img, (0, 0), (width, 2), (255, 255, 255, 100))

    # Brand
    put_text_alpha(img, "VirtualCam Studio", (width - 220, 20), 0.45,
                   (255, 255, 255, 120), 1)

    # Lower third
    lt_y = height - 120
    draw_rect_alpha(img, (30, lt_y), (200, lt_y + 2), (255, 255, 255, 150))
    put_text_alpha(img, "Seu Nome", (30, lt_y + 24), 0.6,
                   (255, 255, 255, 200), 2, cv2.FONT_HERSHEY_DUPLEX)
    put_text_alpha(img, "Cargo", (30, lt_y + 44), 0.4,
                   (180, 180, 180, 160), 1)

    # Bottom gradient
    bar_y = height - 45
    for y in range(45):
        a = int(150 * (y / 45))
        draw_rect_alpha(img, (0, bar_y + y), (width, bar_y + y + 1),
                        (0, 0, 0, a))

    if output_path:
        cv2.imwrite(output_path, img)
        logger.info(f"Template saved: {output_path}")
    return img


def create_sports(width=1280, height=720, output_path=None):
    """Sports-style overlay template."""
    img = np.zeros((height, width, 4), dtype=np.uint8)

    # Top bar
    draw_rect_alpha(img, (0, 0), (width, 55), (20, 20, 180, 220))

    # Title
    put_text_alpha(img, "AO VIVO", (160, 38), 0.8, (255, 255, 255, 255), 2,
                   cv2.FONT_HERSHEY_DUPLEX)

    # Score box
    bx = width - 250
    draw_rect_alpha(img, (bx, 5), (width - 10, 50), (0, 0, 0, 180))
    put_text_alpha(img, "PLACAR / INFO", (bx + 15, 35), 0.5,
                   (255, 255, 255, 200), 1)

    # Lower third
    lt_y = height - 150
    draw_rect_alpha(img, (20, lt_y), (420, lt_y + 55), (20, 20, 180, 220))
    draw_rect_alpha(img, (0, lt_y + 55), (400, lt_y + 80), (30, 30, 30, 220))

    put_text_alpha(img, "APRESENTADOR", (35, lt_y + 38), 0.7,
                   (255, 255, 255, 255), 2, cv2.FONT_HERSHEY_DUPLEX)
    put_text_alpha(img, "Informacao adicional", (15, lt_y + 74), 0.4,
                   (200, 200, 200, 200), 1)

    # Bottom ticker
    bar_y = height - 55
    draw_rect_alpha(img, (0, bar_y), (width, height), (20, 20, 20, 230))
    draw_rect_alpha(img, (0, bar_y), (width, bar_y + 3), (0, 200, 255, 230))

    if output_path:
        cv2.imwrite(output_path, img)
        logger.info(f"Template saved: {output_path}")
    return img


def generate_all_templates(output_dir, width=1280, height=720):
    """Generate all built-in templates."""
    os.makedirs(output_dir, exist_ok=True)

    templates = {
        'newscast_classic': create_newscast_classic,
        'corporate_modern': create_corporate_modern,
        'minimalist': create_minimalist,
        'sports': create_sports,
    }

    for name, func in templates.items():
        path = os.path.join(output_dir, f'{name}.png')
        func(width=width, height=height, output_path=path)
        logger.info(f"Generated template: {name}")

    return list(templates.keys())


if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    templates_dir = os.path.join(base_dir, 'assets', 'templates')
    generate_all_templates(templates_dir)
    print(f"Templates generated in: {templates_dir}")
