"""
NiA FBT26 — Integration Tests
End-to-end tests for configuration loading and version resolution.
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent


class TestConfigIntegration(unittest.TestCase):
    """Integration tests: configs work together correctly."""

    def test_versions_in_settings_match_version_dirs(self):
        """Every version listed in settings.json must have a versions/ directory."""
        with open(REPO_ROOT / "config" / "settings.json") as f:
            settings = json.load(f)
        supported = settings.get("versions", {}).get("supported", [])
        self.assertGreater(len(supported), 0, "No supported versions listed")
        for ver in supported:
            ver_dir = REPO_ROOT / "versions" / f"v{ver}"
            self.assertTrue(ver_dir.exists(), f"Missing version directory: versions/v{ver}")
            version_file = ver_dir / "version.json"
            self.assertTrue(version_file.exists(), f"Missing version.json for v{ver}")

    def test_runtime_models_backends_known(self):
        """All model backends must be from a known set."""
        with open(REPO_ROOT / "config" / "runtime.json") as f:
            runtime = json.load(f)
        known_backends = {"ollama", "onnxruntime", "huggingface", "openai", "anthropic"}
        for name, cfg in runtime["models"].items():
            self.assertIn(
                cfg["backend"], known_backends,
                f"Unknown backend '{cfg['backend']}' for model '{name}'"
            )

    def test_all_version_json_parseable(self):
        """All version.json files in versions/ must be valid JSON."""
        versions_dir = REPO_ROOT / "versions"
        version_files = list(versions_dir.glob("*/version.json"))
        self.assertGreater(len(version_files), 0, "No version.json files found")
        for vf in version_files:
            with open(vf) as f:
                data = json.load(f)
            self.assertIn("version", data)
            self.assertIn("features", data)

    def test_json_config_validation_via_subprocess(self):
        """Validate JSON configs using the Python interpreter subprocess."""
        configs = [
            REPO_ROOT / "config" / "runtime.json",
            REPO_ROOT / "config" / "settings.json",
            REPO_ROOT / "versions" / "v1.0.0" / "version.json",
            REPO_ROOT / "versions" / "v2.0.0" / "version.json",
        ]
        for cfg in configs:
            result = subprocess.run(
                [sys.executable, "-c", f"import json; json.load(open('{cfg}'))"],
                capture_output=True, text=True
            )
            self.assertEqual(
                result.returncode, 0,
                f"Failed to parse {cfg}: {result.stderr}"
            )

    def test_developers_md_has_links(self):
        """DEVELOPERS.md must contain actual links."""
        path = REPO_ROOT / "DEVELOPERS.md"
        self.assertTrue(path.exists())
        content = path.read_text()
        self.assertIn("http", content, "DEVELOPERS.md should contain links")
        self.assertIn("github.com", content.lower())

    def test_ci_yml_references_python(self):
        """CI workflow must reference Python setup."""
        path = REPO_ROOT / ".github" / "workflows" / "ci.yml"
        content = path.read_text()
        self.assertIn("python", content.lower())
        self.assertIn("pytest", content.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
