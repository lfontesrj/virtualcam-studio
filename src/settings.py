"""
Settings Module
Manages application configuration and persistence.
"""

import json
import os
import logging

logger = logging.getLogger(__name__)

DEFAULT_SETTINGS = {
    "general": {
        "language": "pt-BR",
        "theme": "dark",
        "start_minimized": False,
        "auto_start_camera": False,
    },
    "camera": {
        "input_device": 0,
        "output_width": 1280,
        "output_height": 720,
        "fps": 30,
        "virtual_cam_backend": "obs",
        "flip_horizontal": False,
    },
    "template": {
        "current_template": "",
        "custom_templates_dir": "",
    },
    "ticker": {
        "enabled": True,
        "text_file": "",
        "scroll_speed": 2,
        "font_size": 28,
        "font_color": [255, 255, 255],
        "bg_color": [30, 30, 30],
        "bar_height": 50,
        "bar_opacity": 0.85,
        "separator": "     ●     ",
    },
    "countdown": {
        "enabled": False,
        "duration_minutes": 5,
        "font_size": 48,
        "font_color": [255, 255, 255],
        "bg_color": [200, 30, 30],
        "position": "top-right",
        "show_label": True,
        "label_text": "TEMPO",
    },
    "indicators": {
        "enabled": False,
        "data_file": "",
        "font_size": 22,
        "font_color": [255, 255, 255],
        "bg_color": [40, 40, 40],
        "position": "top-left",
        "auto_reload": True,
        "reload_interval": 5,
    },
}


class Settings:
    """Application settings manager with JSON persistence."""

    def __init__(self, config_dir=None):
        if config_dir is None:
            appdata = os.environ.get('APPDATA',
                                      os.path.expanduser('~'))
            config_dir = os.path.join(appdata, 'VirtualCamStudio')

        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, 'settings.json')
        self._settings = {}
        self._load()

    def _load(self):
        """Load settings from file, or create defaults."""
        os.makedirs(self.config_dir, exist_ok=True)

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                # Merge with defaults (to handle new settings)
                self._settings = self._deep_merge(DEFAULT_SETTINGS, saved)
                logger.info(f"Settings loaded from {self.config_file}")
            except Exception as e:
                logger.error(f"Failed to load settings: {e}")
                self._settings = DEFAULT_SETTINGS.copy()
        else:
            self._settings = DEFAULT_SETTINGS.copy()
            self.save()

    def _deep_merge(self, defaults, overrides):
        """Deep merge two dicts, preferring overrides."""
        result = defaults.copy()
        for key, value in overrides.items():
            if (key in result and isinstance(result[key], dict)
                    and isinstance(value, dict)):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def save(self):
        """Save current settings to file."""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
            logger.info("Settings saved")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

    def get(self, section, key=None, default=None):
        """Get a setting value."""
        if section in self._settings:
            if key is None:
                return self._settings[section]
            return self._settings[section].get(key, default)
        return default

    def set(self, section, key, value):
        """Set a setting value."""
        if section not in self._settings:
            self._settings[section] = {}
        self._settings[section][key] = value

    def get_all(self):
        """Get all settings."""
        return self._settings.copy()

    def reset(self):
        """Reset to default settings."""
        self._settings = DEFAULT_SETTINGS.copy()
        self.save()
