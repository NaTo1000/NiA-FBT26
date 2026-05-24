"""
Integration tests for the triple orchestration layer.

Tests are designed to run without live services by mocking HTTP calls.
They validate:
  - Config loading and structure
  - Routing rules
  - Sub-orchestrator task_type assignment
  - Health status models
  - Super orchestrator app endpoints (using FastAPI TestClient)
  - Sub-orchestrator app endpoints (using FastAPI TestClient)
"""

import asyncio
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CONFIG_PATH = "config/orchestration/settings.yaml"


def load_test_config() -> Dict[str, Any]:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Config tests
# ---------------------------------------------------------------------------


class TestOrchestrationConfig:
    def test_config_loads(self):
        cfg = load_test_config()
        assert "orchestration" in cfg

    def test_super_orchestrator_port(self):
        cfg = load_test_config()
        assert cfg["orchestration"]["super_orchestrator"]["port"] == 7000

    def test_sub_orchestrators_defined(self):
        cfg = load_test_config()
        subs = cfg["orchestration"]["sub_orchestrators"]
        assert "code" in subs
        assert "analysis" in subs
        assert "interface" in subs

    def test_sub_orchestrator_ports(self):
        cfg = load_test_config()
        subs = cfg["orchestration"]["sub_orchestrators"]
        assert subs["code"]["port"] == 7100
        assert subs["analysis"]["port"] == 7200
        assert subs["interface"]["port"] == 7300

    def test_model_runners_count(self):
        cfg = load_test_config()
        runners = cfg["orchestration"]["model_runners"]
        assert len(runners) == 10

    def test_model_runner_ports_range(self):
        cfg = load_test_config()
        ports = [r["port"] for r in cfg["orchestration"]["model_runners"].values()]
        assert all(8001 <= p <= 8010 for p in ports)

    def test_routing_rules_complete(self):
        cfg = load_test_config()
        rules = cfg["routing_rules"]
        expected_types = {
            "code_generation", "code_review", "build_diagnostics",
            "signal_classifier", "firmware_analysis", "github_ranker",
            "log_analyzer", "protocol_parser", "nl_to_cli", "docs_generator",
        }
        assert expected_types == set(rules.keys())

    def test_routing_rules_domains(self):
        cfg = load_test_config()
        rules = cfg["routing_rules"]
        assert rules["code_generation"] == "code"
        assert rules["code_review"] == "code"
        assert rules["build_diagnostics"] == "code"
        assert rules["signal_classifier"] == "analysis"
        assert rules["firmware_analysis"] == "analysis"
        assert rules["github_ranker"] == "analysis"
        assert rules["log_analyzer"] == "analysis"
        assert rules["protocol_parser"] == "analysis"
        assert rules["nl_to_cli"] == "interface"
        assert rules["docs_generator"] == "interface"

    def test_redis_config_present(self):
        cfg = load_test_config()
        redis = cfg["orchestration"]["redis"]
        assert "url" in redis
        assert redis["url"].startswith("redis://")


# ---------------------------------------------------------------------------
# Sub-orchestrator class tests
# ---------------------------------------------------------------------------


class TestSubOrchestratorClasses:
    def test_code_sub_orch_config(self):
        from src.orchestration.code_sub_orch import CodeSubOrchestrator
        assert CodeSubOrchestrator.port == 7100
        assert "code_generation" in CodeSubOrchestrator.task_types
        assert "code_review" in CodeSubOrchestrator.task_types
        assert "build_diagnostics" in CodeSubOrchestrator.task_types
        assert set(CodeSubOrchestrator.runner_ports) == {8001, 8002, 8009}

    def test_analysis_sub_orch_config(self):
        from src.orchestration.analysis_sub_orch import AnalysisSubOrchestrator
        assert AnalysisSubOrchestrator.port == 7200
        assert set(AnalysisSubOrchestrator.task_types) == {
            "signal_classifier", "firmware_analysis", "github_ranker",
            "log_analyzer", "protocol_parser",
        }
        assert set(AnalysisSubOrchestrator.runner_ports) == {8005, 8006, 8007, 8008, 8010}

    def test_interface_sub_orch_config(self):
        from src.orchestration.interface_sub_orch import InterfaceSubOrchestrator
        assert InterfaceSubOrchestrator.port == 7300
        assert set(InterfaceSubOrchestrator.task_types) == {"nl_to_cli", "docs_generator"}
        assert set(InterfaceSubOrchestrator.runner_ports) == {8003, 8004}


# ---------------------------------------------------------------------------
# Super orchestrator FastAPI endpoint tests
# ---------------------------------------------------------------------------


class TestSuperOrchestratorEndpoints:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        import src.orchestration.super_orchestrator as so
        so._config = load_test_config()
        return TestClient(so.app)

    def test_health_endpoint(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["port"] == 7000

    def test_services_endpoint(self, client):
        resp = client.get("/services")
        assert resp.status_code == 200
        data = resp.json()
        assert "sub_orchestrators" in data
        assert "model_runners" in data
        assert len(data["model_runners"]) == 10

    def test_config_endpoint(self, client):
        resp = client.get("/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "orchestration" in data

    def test_task_unknown_type(self, client):
        resp = client.post("/task", json={"task_type": "nonexistent", "payload": {}})
        assert resp.status_code == 400

    def test_task_routing_calls_sub_orch(self, client):
        """Verify that a valid task is forwarded to the correct sub-orchestrator."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "completed", "result": {"output": "ok"}}
        mock_response.raise_for_status = MagicMock()

        with patch("src.orchestration.super_orchestrator.httpx.AsyncClient") as mock_client_cls:
            mock_aclient = AsyncMock()
            mock_aclient.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_aclient)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            resp = client.post(
                "/task",
                json={"task_type": "code_generation", "payload": {"prompt": "hello"}},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["routed_to"] == "code"


# ---------------------------------------------------------------------------
# Sub-orchestrator FastAPI endpoint tests
# ---------------------------------------------------------------------------


class TestSubOrchestratorEndpoints:
    @pytest.fixture
    def code_client(self):
        from fastapi.testclient import TestClient
        from src.orchestration.code_sub_orch import app
        return TestClient(app)

    @pytest.fixture
    def analysis_client(self):
        from fastapi.testclient import TestClient
        from src.orchestration.analysis_sub_orch import app
        return TestClient(app)

    @pytest.fixture
    def interface_client(self):
        from fastapi.testclient import TestClient
        from src.orchestration.interface_sub_orch import app
        return TestClient(app)

    def test_code_health(self, code_client):
        resp = code_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["domain"] == "code"

    def test_analysis_health(self, analysis_client):
        resp = analysis_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["domain"] == "analysis"

    def test_interface_health(self, interface_client):
        resp = interface_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["domain"] == "interface"

    def test_code_wrong_task_type(self, code_client):
        resp = code_client.post(
            "/task",
            json={"task_type": "docs_generator", "payload": {"prompt": "x"}},
        )
        assert resp.status_code == 400

    def test_analysis_wrong_task_type(self, analysis_client):
        resp = analysis_client.post(
            "/task",
            json={"task_type": "code_generation", "payload": {"prompt": "x"}},
        )
        assert resp.status_code == 400

    def test_code_task_delegates(self, code_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"output": "generated code"}
        mock_response.raise_for_status = MagicMock()

        with patch("src.orchestration.sub_orchestrator.httpx.AsyncClient") as mock_cls:
            mock_ac = AsyncMock()
            mock_ac.post = AsyncMock(return_value=mock_response)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_ac)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            resp = code_client.post(
                "/task",
                json={"task_type": "code_generation", "payload": {"prompt": "write hello world"}},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["result"] == {"output": "generated code"}

    def test_metrics_endpoint(self, code_client):
        resp = code_client.get("/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "tasks_processed" in data

    def test_runners_health_endpoint(self, code_client):
        resp = code_client.get("/runners/health")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        ports = {item["port"] for item in data}
        assert ports == {8001, 8002, 8009}
