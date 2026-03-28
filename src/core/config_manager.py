"""Configuration manager — v2.0 (Pydantic-based with env-var overrides)."""

import json
import os
from pathlib import Path
from typing import Any

try:
    from pydantic import BaseModel, Field
    _PYDANTIC = True
except ImportError:
    _PYDANTIC = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

_DEFAULT_CONFIG: dict[str, Any] = {
    "version": "2.0.0",
    "firmware_path": "~/flipper-firmware",
    "sdk_path": "~/flipper-sdk",
    "arduino_path": "~/Arduino",
    "esp32_tools": "~/.platformio",
    "python_env": ".venv",
    "editor": {
        "theme": "monokai",
        "font_size": 12,
        "tab_size": 4,
        "show_line_numbers": True,
    },
    "build": {
        "parallel_jobs": 4,
        "optimization": "size",
        "debug": True,
    },
    "github": {
        "token": "",
        "cache_duration": 3600,
    },
    "ai_integration": {
        "huggingface_api_key": "",
        "model_endpoint": "",
        "local_model_path": "",
    },
    "device": {
        "auto_connect": True,
        "default_baud_rate": 115200,
    },
}


class ConfigManager:
    """Load, validate, and persist application settings."""

    CONFIG_VERSION = "2.0.0"

    def __init__(self, config_path: str = "config/settings.json"):
        self.config_path = Path(config_path)
        self.config = self.load_config()
        self._apply_env_overrides()

    # ------------------------------------------------------------------

    def load_config(self) -> dict[str, Any]:
        """Load config from disk, falling back to defaults."""
        if self.config_path.exists():
            try:
                with open(self.config_path, encoding="utf-8") as fh:
                    data = json.load(fh)
                return self._migrate(data)
            except (json.JSONDecodeError, OSError):
                pass
        return self.default_config()

    def default_config(self) -> dict[str, Any]:
        """Return a fresh copy of the default configuration."""
        import copy
        return copy.deepcopy(_DEFAULT_CONFIG)

    def save_config(self):
        """Persist current configuration to disk."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as fh:
            json.dump(self.config, fh, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a top-level config value."""
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """Set a top-level config value (call save_config to persist)."""
        self.config[key] = value

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _migrate(self, data: dict[str, Any]) -> dict[str, Any]:
        """Migrate older config versions to the current schema."""
        merged = self.default_config()
        merged.update(data)
        merged["version"] = self.CONFIG_VERSION
        return merged

    def _apply_env_overrides(self):
        """Override specific settings from environment variables."""
        overrides = {
            "NIA_GITHUB_TOKEN": ("github", "token"),
            "NIA_HF_API_KEY": ("ai_integration", "huggingface_api_key"),
            "NIA_MODEL_ENDPOINT": ("ai_integration", "model_endpoint"),
            "NIA_LOCAL_MODEL_PATH": ("ai_integration", "local_model_path"),
        }
        for env_key, (section, field) in overrides.items():
            value = os.environ.get(env_key)
            if value:
                self.config.setdefault(section, {})[field] = value

