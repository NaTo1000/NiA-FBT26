import json

import pytest

from src.core.config_manager import ConfigManager


def test_missing_configuration_uses_defaults(tmp_path):
    manager = ConfigManager()
    manager.config_path = tmp_path / "settings.json"

    assert manager.load_config() == manager.default_config()


def test_configuration_round_trip(tmp_path):
    manager = ConfigManager()
    manager.config_path = tmp_path / "settings.json"
    manager.config = {"firmware_path": "~/firmware"}

    manager.save_config()

    assert json.loads(manager.config_path.read_text()) == manager.config
    assert manager.load_config() == manager.config


def test_invalid_configuration_reports_file_path(tmp_path):
    manager = ConfigManager()
    manager.config_path = tmp_path / "settings.json"
    manager.config_path.write_text("{invalid")

    with pytest.raises(ValueError, match=str(manager.config_path)):
        manager.load_config()
