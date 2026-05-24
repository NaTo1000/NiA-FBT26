"""
Unit tests for HealingManager.

These tests exercise the healing logic without needing a real Docker
installation or a running HuggingFace environment.  All external I/O
(subprocess, socket, file I/O) is patched via unittest.mock.
"""

import json
import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

# ---------------------------------------------------------------------------
# Ensure src/ is on the path so we can import the modules under test
# ---------------------------------------------------------------------------
SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


# ---------------------------------------------------------------------------
# Minimal PyQt6 stub so tests run without a display server
# ---------------------------------------------------------------------------
try:
    from PyQt6.QtWidgets import QApplication
    _app = QApplication.instance() or QApplication(sys.argv[:1])
    from ai.healing_manager import HealingManager, ServiceStatus, SERVICES
except ImportError:
    pytest.skip("PyQt6 not available", allow_module_level=True)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def manager():
    """Return a fresh HealingManager with no external side-effects.

    ``auto_heal_on_startup`` is disabled so that creating the fixture never
    triggers background I/O.  The production default (True) is exercised by
    the ``TestWriteDefaultConfig`` tests via ``_write_default_config``.
    """
    return HealingManager(config={
        "healing": {
            "hotkey": "Ctrl+Shift+A",
            "auto_heal_on_startup": False,
            "healing_timeout": 300,
            "rebuild_models": True,
        }
    })


# ---------------------------------------------------------------------------
# Tests — check_service_health
# ---------------------------------------------------------------------------

class TestCheckServiceHealth:
    def test_all_healthy_when_sockets_open(self, manager):
        with patch("ai.healing_manager.HealingManager._ping_service",
                   return_value=ServiceStatus.HEALTHY):
            results = manager.check_service_health()

        assert set(results.keys()) == set(SERVICES.keys())
        assert all(v == ServiceStatus.HEALTHY for v in results.values())

    def test_all_failed_when_sockets_closed(self, manager):
        with patch("ai.healing_manager.HealingManager._ping_service",
                   return_value=ServiceStatus.FAILED):
            results = manager.check_service_health()

        assert all(v == ServiceStatus.FAILED for v in results.values())

    def test_status_updated_signal_emitted(self, manager):
        received = []
        manager.status_updated.connect(lambda n, s: received.append((n, s)))

        with patch("ai.healing_manager.HealingManager._ping_service",
                   return_value=ServiceStatus.HEALTHY):
            manager.check_service_health()

        assert len(received) == len(SERVICES)

    def test_ping_healthy_on_open_port(self, manager):
        """_ping_service returns HEALTHY when the TCP connect succeeds."""
        mock_socket = MagicMock()
        mock_socket.__enter__ = MagicMock(return_value=mock_socket)
        mock_socket.__exit__ = MagicMock(return_value=False)

        with patch("socket.create_connection", return_value=mock_socket):
            result = manager._ping_service("code-generation", 8001)

        assert result == ServiceStatus.HEALTHY

    def test_ping_failed_on_refused_port(self, manager):
        """_ping_service returns FAILED when the TCP connect is refused."""
        with patch("socket.create_connection", side_effect=OSError("refused")):
            result = manager._ping_service("code-generation", 8001)

        assert result == ServiceStatus.FAILED


# ---------------------------------------------------------------------------
# Tests — restart_failed_services
# ---------------------------------------------------------------------------

class TestRestartFailedServices:
    def test_restarts_only_failed(self, manager):
        # Mark two services as failed
        manager.statuses["code-generation"].state = ServiceStatus.FAILED
        manager.statuses["code-review"].state = ServiceStatus.FAILED

        with patch.object(manager, "_docker_restart") as mock_restart:
            count = manager.restart_failed_services()

        assert count == 2
        assert mock_restart.call_count == 2

    def test_no_restarts_when_all_healthy(self, manager):
        for s in manager.statuses.values():
            s.state = ServiceStatus.HEALTHY

        with patch.object(manager, "_docker_restart") as mock_restart:
            count = manager.restart_failed_services()

        assert count == 0
        mock_restart.assert_not_called()

    def test_state_set_to_rebuilding_after_restart(self, manager):
        manager.statuses["code-generation"].state = ServiceStatus.FAILED

        with patch.object(manager, "_docker_restart"):
            manager.restart_failed_services()

        assert manager.statuses["code-generation"].state == ServiceStatus.REBUILDING


# ---------------------------------------------------------------------------
# Tests — rebuild_missing_models
# ---------------------------------------------------------------------------

class TestRebuildMissingModels:
    def test_downloads_only_for_failed_services_with_hf_model(self, manager):
        for s in manager.statuses.values():
            s.state = ServiceStatus.HEALTHY
        # Make one service with an hf_model appear failed
        manager.statuses["code-generation"].state = ServiceStatus.FAILED

        with patch.object(manager, "_hf_download") as mock_dl:
            count = manager.rebuild_missing_models()

        assert count == 1
        mock_dl.assert_called_once()

    def test_skips_services_without_hf_model(self, manager):
        # signal-classifier has no hf_model in the registry
        for s in manager.statuses.values():
            s.state = ServiceStatus.HEALTHY
        manager.statuses["signal-classifier"].state = ServiceStatus.FAILED

        with patch.object(manager, "_hf_download") as mock_dl:
            count = manager.rebuild_missing_models()

        assert count == 0
        mock_dl.assert_not_called()


# ---------------------------------------------------------------------------
# Tests — regenerate_configs
# ---------------------------------------------------------------------------

class TestRegenerateConfigs:
    def test_regenerates_when_file_missing(self, manager, tmp_path):
        missing = tmp_path / "settings.json"
        with patch("ai.healing_manager.DEFAULT_CONFIG_TEMPLATE",
                   str(missing)), \
             patch.object(manager, "_write_default_config") as mock_write:
            result = manager.regenerate_configs()

        assert result is True
        mock_write.assert_called_once()

    def test_regenerates_when_file_corrupt(self, manager, tmp_path):
        corrupt = tmp_path / "settings.json"
        corrupt.write_text("not valid json{{{{")

        with patch("ai.healing_manager.DEFAULT_CONFIG_TEMPLATE",
                   str(corrupt)), \
             patch.object(manager, "_write_default_config") as mock_write:
            result = manager.regenerate_configs()

        assert result is True
        mock_write.assert_called_once()

    def test_no_regen_when_config_valid(self, manager, tmp_path):
        valid = tmp_path / "settings.json"
        valid.write_text(json.dumps({"healing": {}}))

        with patch("ai.healing_manager.DEFAULT_CONFIG_TEMPLATE", str(valid)), \
             patch.object(manager, "_write_default_config") as mock_write:
            result = manager.regenerate_configs()

        assert result is False
        mock_write.assert_not_called()


# ---------------------------------------------------------------------------
# Tests — spawn_containers
# ---------------------------------------------------------------------------

class TestSpawnContainers:
    def test_returns_true_on_success(self, manager):
        with patch.object(manager, "_docker_compose_up", return_value=True):
            assert manager.spawn_containers() is True

    def test_returns_false_on_failure(self, manager):
        with patch.object(manager, "_docker_compose_up", return_value=False):
            assert manager.spawn_containers() is False

    def test_uses_configured_compose_file(self, manager):
        manager._healing_config["compose_file"] = "custom/compose.yml"
        with patch.object(manager, "_docker_compose_up",
                          return_value=True) as mock_up:
            manager.spawn_containers()

        mock_up.assert_called_once_with("custom/compose.yml")


# ---------------------------------------------------------------------------
# Tests — heal() orchestration
# ---------------------------------------------------------------------------

class TestHealOrchestration:
    def test_heal_runs_all_steps(self, manager):
        events = []

        with patch.object(manager, "check_service_health",
                          side_effect=lambda: events.append("check") or {}), \
             patch.object(manager, "restart_failed_services",
                          side_effect=lambda: events.append("restart") or 0), \
             patch.object(manager, "rebuild_missing_models",
                          side_effect=lambda: events.append("rebuild") or 0), \
             patch.object(manager, "regenerate_configs",
                          side_effect=lambda: events.append("regen") or False), \
             patch.object(manager, "spawn_containers",
                          side_effect=lambda: events.append("spawn") or True):

            finished = threading.Event()
            from PyQt6.QtCore import Qt
            manager.healing_finished.connect(lambda _: finished.set(),
                                             Qt.ConnectionType.DirectConnection)
            manager.heal()
            finished.wait(timeout=10)

        assert "check" in events
        assert "restart" in events
        assert "rebuild" in events
        assert "regen" in events
        assert "spawn" in events

    def test_heal_emits_started_and_finished(self, manager):
        started = threading.Event()
        finished_any = threading.Event()

        from PyQt6.QtCore import Qt
        manager.healing_started.connect(started.set,
                                        Qt.ConnectionType.DirectConnection)
        manager.healing_finished.connect(lambda _ok: finished_any.set(),
                                         Qt.ConnectionType.DirectConnection)

        with patch.object(manager, "check_service_health", return_value={}), \
             patch.object(manager, "restart_failed_services", return_value=0), \
             patch.object(manager, "rebuild_missing_models", return_value=0), \
             patch.object(manager, "regenerate_configs", return_value=False), \
             patch.object(manager, "spawn_containers", return_value=True):
            manager.heal()
            finished_any.wait(timeout=10)

        assert started.is_set()
        assert finished_any.is_set()

    def test_second_heal_ignored_while_running(self, manager):
        """A second call to heal() while one is in progress is a no-op."""
        # Verify _running flag is set synchronously before the thread starts
        manager.heal()
        is_running_immediately = manager._running
        # Give the thread time to clear the flag
        manager.statuses  # force access so the thread has time to start
        assert is_running_immediately is True

    def test_second_heal_no_op_while_flag_set(self, manager):
        """heal() returns immediately without spawning a thread when _running is True."""
        spawned = []
        original_thread_start = threading.Thread.start

        def patched_start(self_thread):
            spawned.append(1)
            original_thread_start(self_thread)

        gate = threading.Event()
        finished = threading.Event()

        from PyQt6.QtCore import Qt
        manager.healing_finished.connect(lambda _: finished.set(),
                                         Qt.ConnectionType.DirectConnection)

        def slow_spawn():
            gate.wait(timeout=10)
            return True

        with patch.object(manager, "check_service_health", return_value={}), \
             patch.object(manager, "restart_failed_services", return_value=0), \
             patch.object(manager, "rebuild_missing_models", return_value=0), \
             patch.object(manager, "regenerate_configs", return_value=False), \
             patch.object(manager, "spawn_containers", side_effect=slow_spawn), \
             patch.object(threading.Thread, "start", patched_start):
            manager.heal()   # first — sets _running, spawns thread
            # _running is True now, second call must be ignored
            manager.heal()
            gate.set()
            finished.wait(timeout=10)

        # Only one thread should have been started
        assert len(spawned) == 1


# ---------------------------------------------------------------------------
# Tests — write_default_config
# ---------------------------------------------------------------------------

class TestWriteDefaultConfig:
    def test_creates_valid_json(self, manager, tmp_path):
        cfg_path = tmp_path / "config" / "settings.json"
        manager._write_default_config(cfg_path)

        assert cfg_path.exists()
        data = json.loads(cfg_path.read_text())
        assert "healing" in data
        assert data["healing"]["hotkey"] == "Ctrl+Shift+A"
