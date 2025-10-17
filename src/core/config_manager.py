import json
from pathlib import Path

class ConfigManager:
    def __init__(self):
        self.config_path = Path("config/settings.json")
        self.config = self.load_config()
    
    def load_config(self):
        if self.config_path.exists():
            with open(self.config_path) as f:
                return json.load(f)
        return self.default_config()
    
    def default_config(self):
        return {
            "firmware_path": "~/flipper-firmware",
            "sdk_path": "~/flipper-sdk",
            "arduino_path": "~/Arduino",
            "editor": {
                "theme": "monokai",
                "font_size": 12
            }
        }
    
    def save_config(self):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
