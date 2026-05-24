"""Tests for the ResearchLab conferencing and guardrail logic."""
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so imports work without installing.
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ai.research_lab import ResearchLab


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def guardrails_file(tmp_path):
    """Write a temporary guardrails YAML file and return its path."""
    data = {
        "guardrails": [
            {"name": "Ethical Research", "prompt": "Be ethical."},
            {"name": "Technical Focus", "prompt": "Focus on firmware."},
        ]
    }
    p = tmp_path / "research_lab.yaml"
    p.write_text(yaml.dump(data))
    return p


@pytest.fixture()
def lab(guardrails_file):
    return ResearchLab(hf_api_key="test-key", guardrails_path=guardrails_file)


# ---------------------------------------------------------------------------
# load_guardrails
# ---------------------------------------------------------------------------

class TestLoadGuardrails:
    def test_loads_from_yaml(self, lab):
        guardrails = lab.load_guardrails()
        assert len(guardrails) == 2
        assert guardrails[0]["name"] == "Ethical Research"

    def test_returns_empty_list_when_file_missing(self, tmp_path):
        lab = ResearchLab(guardrails_path=tmp_path / "nonexistent.yaml")
        assert lab.load_guardrails() == []


# ---------------------------------------------------------------------------
# apply_guardrails
# ---------------------------------------------------------------------------

class TestApplyGuardrails:
    def test_injects_guidance_before_prompt(self):
        lab = ResearchLab()
        guardrails = [
            {"name": "A", "prompt": "Be safe."},
            {"name": "B", "prompt": "Be accurate."},
        ]
        result = lab.apply_guardrails("My topic", guardrails)
        assert "Be safe." in result
        assert "Be accurate." in result
        assert "My topic" in result
        # Guidance should come first
        assert result.index("Be safe.") < result.index("My topic")

    def test_returns_prompt_unchanged_when_no_guardrails(self):
        lab = ResearchLab()
        assert lab.apply_guardrails("My topic", []) == "My topic"

    def test_skips_entries_without_prompt_key(self):
        lab = ResearchLab()
        guardrails = [{"name": "No prompt here"}]
        result = lab.apply_guardrails("Topic", guardrails)
        assert result == "Topic"


# ---------------------------------------------------------------------------
# aggregate_answers
# ---------------------------------------------------------------------------

class TestAggregateAnswers:
    def test_includes_all_models(self):
        lab = ResearchLab()
        responses = [
            {"model": "model-a", "response": "Answer A", "error": None},
            {"model": "model-b", "response": "Answer B", "error": None},
        ]
        result = lab.aggregate_answers(responses)
        assert "model-a" in result
        assert "Answer A" in result
        assert "model-b" in result
        assert "Answer B" in result

    def test_shows_error_when_present(self):
        lab = ResearchLab()
        responses = [
            {"model": "model-x", "response": "", "error": "timeout"},
        ]
        result = lab.aggregate_answers(responses)
        assert "Error: timeout" in result

    def test_empty_responses_returns_string(self):
        lab = ResearchLab()
        result = lab.aggregate_answers([])
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# start_conference (mocked HTTP)
# ---------------------------------------------------------------------------

class TestStartConference:
    def _make_mock_response(self, text: str):
        mock_resp = MagicMock()
        mock_resp.json.return_value = [{"generated_text": text}]
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    @patch("src.ai.research_lab.ResearchLab._query_model")
    def test_returns_result_for_each_model(self, mock_query, lab):
        mock_query.side_effect = lambda model, prompt: {
            "model": model, "response": f"Answer from {model}", "error": None
        }
        models = ["model-a", "model-b", "model-c"]
        results = lab.start_conference("Flipper Zero firmware topic", models)
        assert len(results) == 3
        returned_models = {r["model"] for r in results}
        assert returned_models == set(models)

    @patch("src.ai.research_lab.ResearchLab._query_model")
    def test_applies_guardrails_to_prompt(self, mock_query, lab):
        """Guardrail guidance must be prepended to the prompt."""
        captured = []

        def capture(model, prompt):
            captured.append(prompt)
            return {"model": model, "response": "ok", "error": None}

        mock_query.side_effect = capture
        guardrails = lab.load_guardrails()
        lab.start_conference("Test topic", ["model-a"], guardrails=guardrails)
        assert len(captured) == 1
        # The guided prompt must be longer than the bare topic
        assert len(captured[0]) > len("Test topic")
        assert "Test topic" in captured[0]

    @patch("src.ai.research_lab.ResearchLab._query_model")
    def test_processes_all_models_regardless_of_parallel_limit(self, mock_query, lab):
        mock_query.side_effect = lambda m, p: {"model": m, "response": "", "error": None}
        models = [f"model-{i}" for i in range(7)]
        results = lab.start_conference("topic", models)
        assert len(results) == 7  # all models get results, capped at 5 workers
