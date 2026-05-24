"""
HealingManager — Self-Healing AI Runner Manager for NiA FBT26.

Checks health of all 13 AI services (3 orchestrators + 10 models),
restarts failed services, rebuilds missing models and regenerates
broken configs, all in a background thread so the GUI stays
responsive.
"""

import json
import logging
import subprocess
import threading
import time
from pathlib import Path
from typing import Callable, Dict, Optional

from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Service registry — 3 orchestrators + 10 model runners
# ---------------------------------------------------------------------------
SERVICES: Dict[str, Dict] = {
    # Orchestrators
    "super-orchestrator":   {"port": 9000, "compose_service": "super-orchestrator"},
    "code-orchestrator":    {"port": 9001, "compose_service": "code-orchestrator"},
    "analysis-orchestrator": {"port": 9002, "compose_service": "analysis-orchestrator"},
    # Model runners
    "code-generation":      {"port": 8001, "compose_service": "code-generation",
                             "hf_model": "deepseek-ai/deepseek-coder-6.7b-instruct"},
    "code-review":          {"port": 8002, "compose_service": "code-review",
                             "hf_model": "codellama/CodeLlama-7b-hf"},
    "nl-to-cli":            {"port": 8003, "compose_service": "nl-to-cli",
                             "hf_model": "meta-llama/Llama-3.2-1B"},
    "docs-generator":       {"port": 8004, "compose_service": "docs-generator",
                             "hf_model": "mistralai/Mistral-7B-v0.3"},
    "signal-classifier":    {"port": 8005, "compose_service": "signal-classifier"},
    "firmware-analysis":    {"port": 8006, "compose_service": "firmware-analysis",
                             "hf_model": "bigcode/starcoder2-3b"},
    "github-ranker":        {"port": 8007, "compose_service": "github-ranker",
                             "hf_model": "BAAI/bge-small-en-v1.5"},
    "log-analyzer":         {"port": 8008, "compose_service": "log-analyzer",
                             "hf_model": "microsoft/phi-2"},
    "build-diagnostics":    {"port": 8009, "compose_service": "build-diagnostics",
                             "hf_model": "deepseek-ai/deepseek-coder-1.3b-instruct"},
    "protocol-parser":      {"port": 8010, "compose_service": "protocol-parser",
                             "hf_model": "meta-llama/Llama-3.2-1B"},
}

DEFAULT_COMPOSE_FILE = "docker/docker-compose.full.yml"
DEFAULT_CONFIG_TEMPLATE = "config/settings.json"


class ServiceStatus:
    """Holds the current status of a single service."""

    HEALTHY = "healthy"
    FAILED = "failed"
    REBUILDING = "rebuilding"
    UNKNOWN = "unknown"

    def __init__(self, name: str):
        self.name = name
        self.state = self.UNKNOWN
        self.message = ""

    def __repr__(self):
        return f"ServiceStatus({self.name}, {self.state})"


class HealingManager(QObject):
    """
    Manages self-healing of all AI model runner services.

    Signals
    -------
    healing_started  — emitted when a heal cycle begins
    healing_finished — emitted when the cycle completes (success: bool)
    status_updated   — emitted with (service_name, status_string) as each
                       service is checked / repaired
    progress_updated — emitted with (current: int, total: int) for the
                       progress bar
    log_message      — emitted with a plain-text log line for the GUI
    """

    healing_started = pyqtSignal()
    healing_finished = pyqtSignal(bool)        # success
    status_updated = pyqtSignal(str, str)      # name, state
    progress_updated = pyqtSignal(int, int)    # current, total
    log_message = pyqtSignal(str)

    def __init__(self, config: Optional[Dict] = None, parent=None):
        super().__init__(parent)
        self._config = config or {}
        self._healing_config = self._config.get("healing", {})
        self._compose_file = DEFAULT_COMPOSE_FILE
        self._lock = threading.Lock()
        self._running = False

        self.statuses: Dict[str, ServiceStatus] = {
            name: ServiceStatus(name) for name in SERVICES
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def heal(self):
        """Start a full heal cycle in a background thread (non-blocking)."""
        with self._lock:
            if self._running:
                self._emit_log("Healing already in progress — skipping.")
                return
            self._running = True
        thread = threading.Thread(target=self._heal_cycle, daemon=True)
        thread.start()

    # ------------------------------------------------------------------
    # Core healing steps (also callable individually for testing)
    # ------------------------------------------------------------------

    def check_service_health(self) -> Dict[str, str]:
        """
        Ping all 13 services and return a dict of {name: state}.

        Uses ``requests`` if available, falls back to a simple socket
        connect so that the method works even in lightweight test
        environments.
        """
        results: Dict[str, str] = {}
        for name, info in SERVICES.items():
            state = self._ping_service(name, info["port"])
            self.statuses[name].state = state
            results[name] = state
            self.status_updated.emit(name, state)
        return results

    def restart_failed_services(self) -> int:
        """
        Issue ``docker restart`` for every service whose state is FAILED.

        Returns the number of services restarted.
        """
        restarted = 0
        for name, status in self.statuses.items():
            if status.state == ServiceStatus.FAILED:
                self._emit_log(f"Restarting failed service: {name}")
                self._docker_restart(SERVICES[name]["compose_service"])
                self.statuses[name].state = ServiceStatus.REBUILDING
                self.status_updated.emit(name, ServiceStatus.REBUILDING)
                restarted += 1
        return restarted

    def rebuild_missing_models(self) -> int:
        """
        Trigger HuggingFace downloads for models that are missing.

        For services with a ``hf_model`` entry in the registry, this runs
        ``huggingface-cli download <model>`` in a subprocess.  Returns the
        number of downloads attempted.
        """
        attempted = 0
        for name, info in SERVICES.items():
            if self.statuses[name].state in (ServiceStatus.FAILED,
                                             ServiceStatus.UNKNOWN):
                hf_model = info.get("hf_model")
                if hf_model:
                    self._emit_log(f"Downloading model for {name}: {hf_model}")
                    self._hf_download(hf_model)
                    self.statuses[name].state = ServiceStatus.REBUILDING
                    self.status_updated.emit(name, ServiceStatus.REBUILDING)
                    attempted += 1
        return attempted

    def regenerate_configs(self) -> bool:
        """
        Restore ``config/settings.json`` from the bundled defaults if it is
        missing or corrupt.  Returns True if regeneration was performed.
        """
        config_path = Path(DEFAULT_CONFIG_TEMPLATE)
        needs_regen = False

        if not config_path.exists():
            needs_regen = True
            self._emit_log("Config file missing — regenerating from defaults.")
        else:
            try:
                with open(config_path) as fh:
                    json.load(fh)
            except (json.JSONDecodeError, OSError):
                needs_regen = True
                self._emit_log("Config file corrupt — regenerating from defaults.")

        if needs_regen:
            self._write_default_config(config_path)
        return needs_regen

    def spawn_containers(self) -> bool:
        """
        Run ``docker compose up -d`` for the full stack using the compose
        file configured in settings.  Returns True if the command succeeded.
        """
        compose_file = self._healing_config.get("compose_file", self._compose_file)
        self._emit_log(f"Spawning containers via {compose_file} …")
        return self._docker_compose_up(compose_file)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _heal_cycle(self):
        """Full heal cycle — runs in a background thread."""
        self.healing_started.emit()
        self._emit_log("=== Heal cycle started ===")
        success = True

        try:
            # Step 1 — check health
            self._emit_log("Step 1/4 — Checking service health …")
            self.check_service_health()
            self.progress_updated.emit(1, 4)

            # Step 2 — restart failed services
            self._emit_log("Step 2/4 — Restarting failed services …")
            restarted = self.restart_failed_services()
            self._emit_log(f"  {restarted} service(s) restarted.")
            self.progress_updated.emit(2, 4)

            # Step 3 — rebuild missing models
            if self._healing_config.get("rebuild_models", True):
                self._emit_log("Step 3/4 — Rebuilding missing models …")
                attempted = self.rebuild_missing_models()
                self._emit_log(f"  {attempted} model download(s) initiated.")
            self.progress_updated.emit(3, 4)

            # Step 4 — regenerate configs & spawn any missing containers
            self._emit_log("Step 4/4 — Regenerating configs & spawning containers …")
            self.regenerate_configs()
            self.spawn_containers()
            self.progress_updated.emit(4, 4)

            # Brief pause then re-check
            time.sleep(2)
            self.check_service_health()

        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Heal cycle error: %s", exc)
            self._emit_log(f"ERROR during heal cycle: {exc}")
            success = False
        finally:
            with self._lock:
                self._running = False

        self._emit_log("=== Heal cycle complete ===")
        self.healing_finished.emit(success)

    def _ping_service(self, name: str, port: int) -> str:
        """Return HEALTHY or FAILED based on a TCP connect attempt."""
        try:
            import socket
            with socket.create_connection(("127.0.0.1", port), timeout=2):
                return ServiceStatus.HEALTHY
        except OSError:
            return ServiceStatus.FAILED

    def _docker_restart(self, compose_service: str):
        """Run docker restart for a single compose service."""
        try:
            subprocess.run(
                ["docker", "restart", compose_service],
                capture_output=True, timeout=30, check=False
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            logger.warning("docker restart failed for %s: %s", compose_service, exc)

    def _docker_compose_up(self, compose_file: str) -> bool:
        """Run docker compose up -d."""
        try:
            result = subprocess.run(
                ["docker", "compose", "-f", compose_file, "up", "-d",
                 "--remove-orphans"],
                capture_output=True, timeout=120, check=False
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            logger.warning("docker compose up failed: %s", exc)
            return False

    def _hf_download(self, model_id: str):
        """Attempt to download a HuggingFace model via the CLI."""
        try:
            subprocess.run(
                ["huggingface-cli", "download", model_id],
                capture_output=True, timeout=300, check=False
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            logger.warning("HuggingFace download failed for %s: %s", model_id, exc)

    def _write_default_config(self, path: Path):
        """Write a minimal default config to *path*."""
        path.parent.mkdir(parents=True, exist_ok=True)
        default = {
            "firmware_path": "~/flipper-firmware",
            "sdk_path": "~/flipper-sdk",
            "arduino_path": "~/Arduino",
            "editor": {"theme": "monokai", "font_size": 12},
            "healing": {
                "hotkey": "Ctrl+Shift+A",
                "auto_heal_on_startup": True,
                "healing_timeout": 300,
                "rebuild_models": True,
            },
        }
        with open(path, "w") as fh:
            json.dump(default, fh, indent=2)

    def _emit_log(self, message: str):
        logger.info(message)
        self.log_message.emit(message)
