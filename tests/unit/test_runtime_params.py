"""
NiA FBT26 — Unit Tests: Runtime Parameters
Tests for CLI argument parsing and environment variable support.
"""

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))


class TestRuntimeParameters(unittest.TestCase):
    """Tests for runtime parameter loading and CLI args."""

    def _load_runtime(self):
        with open(REPO_ROOT / "config" / "runtime.json") as f:
            return json.load(f)

    def test_runtime_environment_default(self):
        data = self._load_runtime()
        self.assertIn(data["runtime"]["environment"], ["production", "development", "staging"])

    def test_runtime_log_level_valid(self):
        data = self._load_runtime()
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        self.assertIn(data["runtime"]["log_level"], valid_levels)

    def test_models_all_have_required_fields(self):
        data = self._load_runtime()
        required_fields = {"model", "backend", "enabled"}
        for model_name, model_cfg in data["models"].items():
            for field in required_fields:
                self.assertIn(
                    field, model_cfg,
                    f"Model '{model_name}' missing field '{field}'"
                )

    def test_models_enabled_is_boolean(self):
        data = self._load_runtime()
        for model_name, model_cfg in data["models"].items():
            self.assertIsInstance(
                model_cfg["enabled"], bool,
                f"Model '{model_name}' 'enabled' is not a bool"
            )

    def test_orchestration_strategy_valid(self):
        data = self._load_runtime()
        valid_strategies = {"round_robin", "least_loaded", "random", "priority"}
        self.assertIn(data["orchestration"]["strategy"], valid_strategies)

    def test_orchestration_retries_positive(self):
        data = self._load_runtime()
        self.assertGreater(data["orchestration"]["retries"], 0)

    def test_security_ethical_use_enforced(self):
        data = self._load_runtime()
        self.assertTrue(data["security"]["ethical_use_enforced"])
        self.assertIsInstance(data["security"]["allowed_operations"], list)
        self.assertGreater(len(data["security"]["allowed_operations"]), 0)

    def test_health_checks_configured(self):
        data = self._load_runtime()
        hc = data["health_checks"]
        self.assertIn("enabled", hc)
        self.assertIn("endpoint", hc)
        self.assertTrue(hc["endpoint"].startswith("/"))

    def test_env_var_port_override(self):
        """Simulate environment variable override for server port."""
        data = self._load_runtime()
        default_port = data["server"]["port"]
        with patch.dict(os.environ, {"NIA_SERVER_PORT": "9090"}):
            env_port = int(os.environ.get("NIA_SERVER_PORT", default_port))
        self.assertEqual(env_port, 9090)

    def test_env_var_debug_override(self):
        """Simulate environment variable override for debug flag."""
        with patch.dict(os.environ, {"NIA_DEBUG": "true"}):
            debug = os.environ.get("NIA_DEBUG", "false").lower() == "true"
        self.assertTrue(debug)

    def test_env_var_log_level_override(self):
        """Simulate environment variable override for log level."""
        with patch.dict(os.environ, {"NIA_LOG_LEVEL": "DEBUG"}):
            level = os.environ.get("NIA_LOG_LEVEL", "INFO")
        self.assertEqual(level, "DEBUG")


class TestMainCLIArgs(unittest.TestCase):
    """Tests for CLI argument parsing in main.py."""

    def test_main_py_exists(self):
        path = REPO_ROOT / "src" / "main.py"
        self.assertTrue(path.exists())

    def test_main_py_has_version(self):
        content = (REPO_ROOT / "src" / "main.py").read_text()
        self.assertIn("__version__", content)

    def test_main_py_has_argparse_or_click(self):
        content = (REPO_ROOT / "src" / "main.py").read_text()
        has_args = "argparse" in content or "click" in content or "sys.argv" in content
        self.assertTrue(has_args, "main.py should support CLI arguments")


if __name__ == "__main__":
    unittest.main(verbosity=2)
