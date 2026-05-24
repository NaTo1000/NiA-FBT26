"""
NiA FBT26 — Unit Tests
Tests for config manager, runtime parameters, and version handling.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Make src importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

REPO_ROOT = Path(__file__).parent.parent.parent


class TestConfigFiles(unittest.TestCase):
    """Validate that all JSON config files are well-formed."""

    def test_runtime_json_is_valid(self):
        path = REPO_ROOT / "config" / "runtime.json"
        self.assertTrue(path.exists(), f"Missing: {path}")
        with open(path) as f:
            data = json.load(f)
        self.assertIn("runtime", data)
        self.assertIn("security", data)
        self.assertTrue(data["security"]["ethical_use_enforced"])

    def test_settings_json_is_valid(self):
        path = REPO_ROOT / "config" / "settings.json"
        self.assertTrue(path.exists(), f"Missing: {path}")
        with open(path) as f:
            data = json.load(f)
        self.assertIn("build", data)
        self.assertIn("runtime_flags", data)
        self.assertIn("ports", data)

    def test_runtime_has_all_required_sections(self):
        path = REPO_ROOT / "config" / "runtime.json"
        with open(path) as f:
            data = json.load(f)
        required = ["runtime", "server", "models", "orchestration", "build",
                    "device", "github", "ui", "security", "health_checks"]
        for section in required:
            self.assertIn(section, data, f"Missing section: {section}")

    def test_runtime_port_is_integer(self):
        path = REPO_ROOT / "config" / "runtime.json"
        with open(path) as f:
            data = json.load(f)
        self.assertIsInstance(data["server"]["port"], int)
        self.assertGreater(data["server"]["port"], 0)
        self.assertLess(data["server"]["port"], 65536)

    def test_settings_versions_section(self):
        path = REPO_ROOT / "config" / "settings.json"
        with open(path) as f:
            data = json.load(f)
        self.assertIn("versions", data)
        self.assertEqual(data["versions"]["current"], "1.0.0")
        self.assertIn("1.0.0", data["versions"]["supported"])
        self.assertIn("2.0.0", data["versions"]["supported"])


class TestVersionFiles(unittest.TestCase):
    """Validate version directory structure and content."""

    def _load_version(self, ver):
        path = REPO_ROOT / "versions" / ver / "version.json"
        self.assertTrue(path.exists(), f"Missing: {path}")
        with open(path) as f:
            return json.load(f)

    def test_v1_version_json_valid(self):
        data = self._load_version("v1.0.0")
        self.assertEqual(data["version"], "1.0.0")
        self.assertIn("features", data)
        self.assertIsInstance(data["features"], list)
        self.assertGreater(len(data["features"]), 0)

    def test_v2_version_json_valid(self):
        data = self._load_version("v2.0.0")
        self.assertEqual(data["version"], "2.0.0")
        self.assertIn("features", data)
        self.assertGreater(len(data["features"]), 0)

    def test_v1_changelog_exists(self):
        path = REPO_ROOT / "versions" / "v1.0.0" / "CHANGELOG.md"
        self.assertTrue(path.exists())
        content = path.read_text()
        self.assertIn("v1.0.0", content)

    def test_v2_changelog_exists(self):
        path = REPO_ROOT / "versions" / "v2.0.0" / "CHANGELOG.md"
        self.assertTrue(path.exists())
        content = path.read_text()
        self.assertIn("v2.0.0", content)

    def test_v2_has_breaking_changes(self):
        data = self._load_version("v2.0.0")
        self.assertIn("breaking_changes", data)
        self.assertIsInstance(data["breaking_changes"], list)

    def test_v2_has_docker_images(self):
        data = self._load_version("v2.0.0")
        self.assertIn("docker_images", data)
        self.assertIn("app", data["docker_images"])


class TestConfigManager(unittest.TestCase):
    """Tests for the ConfigManager class."""

    def test_config_manager_loads_defaults(self):
        from core.config_manager import ConfigManager
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_dir = os.getcwd()
            try:
                os.chdir(tmpdir)
                cm = ConfigManager()
                self.assertIsInstance(cm.config, dict)
                self.assertIn("firmware_path", cm.config)
            finally:
                os.chdir(orig_dir)

    def test_config_manager_saves_and_reloads(self):
        from core.config_manager import ConfigManager
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_dir = os.getcwd()
            try:
                os.chdir(tmpdir)
                cm = ConfigManager()
                cm.config["test_key"] = "test_value"
                cm.save_config()
                cm2 = ConfigManager()
                self.assertEqual(cm2.config.get("test_key"), "test_value")
            finally:
                os.chdir(orig_dir)


class TestScriptFiles(unittest.TestCase):
    """Validate that script files exist and are executable."""

    def test_build_images_sh_exists(self):
        path = REPO_ROOT / "scripts" / "build_images.sh"
        self.assertTrue(path.exists())

    def test_test_all_sh_exists(self):
        path = REPO_ROOT / "scripts" / "test_all.sh"
        self.assertTrue(path.exists())

    def test_build_images_is_executable(self):
        path = REPO_ROOT / "scripts" / "build_images.sh"
        self.assertTrue(os.access(path, os.X_OK))

    def test_test_all_is_executable(self):
        path = REPO_ROOT / "scripts" / "test_all.sh"
        self.assertTrue(os.access(path, os.X_OK))

    def test_ci_yml_exists(self):
        path = REPO_ROOT / ".github" / "workflows" / "ci.yml"
        self.assertTrue(path.exists())

    def test_developers_md_exists(self):
        path = REPO_ROOT / "DEVELOPERS.md"
        self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
