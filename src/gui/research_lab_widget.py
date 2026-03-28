
import yaml
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QTextEdit, QGroupBox, QListWidget, QListWidgetItem,
    QSplitter, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from ..ai.research_lab import ResearchLab


class _ConferenceWorker(QThread):
    """Background thread that runs the model conference."""

    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, lab: ResearchLab, topic: str, models: list, guardrails: list = None):
        super().__init__()
        self.lab = lab
        self.topic = topic
        self.models = models
        self.guardrails = guardrails

    def run(self):
        try:
            responses = self.lab.start_conference(self.topic, self.models, guardrails=self.guardrails)
            self.finished.emit(responses)
        except Exception as exc:
            self.error.emit(str(exc))


class ResearchLabWidget(QWidget):
    """Research Lab: multi-model conferencing with guided guardrails."""

    DEFAULT_MODELS = [
        "meta-llama/Meta-Llama-3.1-8B-Instruct",
        "microsoft/Phi-3-medium-128k-instruct",
        "mistralai/Mistral-7B-Instruct-v0.3",
    ]

    DEFAULT_GUARDRAILS_YAML = (
        "guardrails:\n"
        "  - name: \"Ethical Research\"\n"
        "    prompt: \"Ensure all responses are ethical, legal, and beneficial"
        " to Flipper Zero development.\"\n"
        "  - name: \"Technical Focus\"\n"
        "    prompt: \"Focus on technical aspects of firmware, apps, and hardware.\"\n"
        "  - name: \"Diverse Perspectives\"\n"
        "    prompt: \"Provide varied viewpoints while maintaining accuracy.\"\n"
        "  - name: \"Safety First\"\n"
        "    prompt: \"Prioritize user safety and legal compliance.\"\n"
    )

    def __init__(self, config):
        super().__init__()
        self.config = config
        lab_cfg = config.get("research_lab", {}) if isinstance(config, dict) else {}
        hf_key = lab_cfg.get("hf_api_key", "")
        self.lab = ResearchLab(hf_api_key=hf_key)
        self._worker = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ── Left panel: topic + model selection ──────────────────────
        left = QWidget()
        left_layout = QVBoxLayout(left)

        topic_group = QGroupBox("Research Topic")
        topic_layout = QVBoxLayout()
        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText(
            "Enter a Flipper Zero research topic…"
        )
        topic_layout.addWidget(self.topic_input)
        topic_group.setLayout(topic_layout)
        left_layout.addWidget(topic_group)

        model_group = QGroupBox("Models (select 1–5)")
        model_layout = QVBoxLayout()
        self.model_list = QListWidget()
        self.model_list.setSelectionMode(
            QListWidget.SelectionMode.MultiSelection
        )
        for m in self.DEFAULT_MODELS:
            item = QListWidgetItem(m)
            self.model_list.addItem(item)
            item.setSelected(True)
        model_layout.addWidget(self.model_list)

        add_model_layout = QHBoxLayout()
        self.new_model_input = QLineEdit()
        self.new_model_input.setPlaceholderText("Add HuggingFace model ID…")
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add_model)
        add_model_layout.addWidget(self.new_model_input)
        add_model_layout.addWidget(add_btn)
        model_layout.addLayout(add_model_layout)
        model_group.setLayout(model_layout)
        left_layout.addWidget(model_group)

        guardrail_group = QGroupBox("Guardrails Config (YAML, user-editable)")
        guardrail_layout = QVBoxLayout()
        self.guardrail_editor = QTextEdit()
        self.guardrail_editor.setPlainText(self.DEFAULT_GUARDRAILS_YAML)
        guardrail_layout.addWidget(self.guardrail_editor)
        guardrail_group.setLayout(guardrail_layout)
        left_layout.addWidget(guardrail_group)

        self.start_btn = QPushButton("▶  Start Conference")
        self.start_btn.clicked.connect(self._start_conference)
        left_layout.addWidget(self.start_btn)

        splitter.addWidget(left)

        # ── Right panel: output ───────────────────────────────────────
        right = QWidget()
        right_layout = QVBoxLayout(right)

        output_group = QGroupBox("Model Answers")
        output_layout = QVBoxLayout()
        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        self.output_display.setPlaceholderText(
            "Conference answers will appear here…"
        )
        output_layout.addWidget(self.output_display)
        output_group.setLayout(output_layout)
        right_layout.addWidget(output_group)

        splitter.addWidget(right)
        splitter.setSizes([400, 600])

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _add_model(self):
        model_id = self.new_model_input.text().strip()
        if model_id:
            item = QListWidgetItem(model_id)
            self.model_list.addItem(item)
            item.setSelected(True)
            self.new_model_input.clear()

    def _selected_models(self) -> list:
        return [item.text() for item in self.model_list.selectedItems()]

    def _parse_guardrails(self) -> list:
        try:
            data = yaml.safe_load(self.guardrail_editor.toPlainText())
            return data.get("guardrails", []) if data else []
        except Exception:
            return []

    def _start_conference(self):
        topic = self.topic_input.text().strip()
        if not topic:
            QMessageBox.warning(self, "No Topic", "Please enter a research topic.")
            return

        models = self._selected_models()
        if not models:
            QMessageBox.warning(self, "No Models", "Please select at least one model.")
            return

        guardrails = self._parse_guardrails()

        self.start_btn.setEnabled(False)
        self.output_display.setPlainText("Running conference… please wait.")

        self._worker = _ConferenceWorker(self.lab, topic, models, guardrails)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_finished(self, responses: list):
        aggregated = self.lab.aggregate_answers(responses)
        self.output_display.setPlainText(aggregated)
        self.start_btn.setEnabled(True)

    def _on_error(self, message: str):
        self.output_display.setPlainText(f"Error: {message}")
        self.start_btn.setEnabled(True)
