"""
HuggingFace Manager Widget
Provides:
  - API key input with validation
  - Model browser (search HuggingFace API)
  - Per-service model selection dropdowns
  - Local / remote toggle per service
  - Save to config
"""

import json
from pathlib import Path
from typing import Any, Dict

import requests
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

HF_MODELS_API = "https://huggingface.co/api/models"

DEFAULT_MODELS: Dict[str, str] = {
    "code_generation": "deepseek-ai/deepseek-coder-6.7b-instruct",
    "code_review": "codellama/CodeLlama-70b-hf",
    "nl_to_cli": "meta-llama/Meta-Llama-3.1-70B-Instruct",
    "docs_generator": "mistralai/Mistral-Large-Instruct-2407",
    "signal_classifier": "local-onnx-model",
    "firmware_analysis": "bigcode/starcoder2-15b",
    "github_ranker": "BAAI/bge-large-en-v1.5",
    "log_analyzer": "microsoft/Phi-3-medium-128k-instruct",
    "build_diagnostics": "deepseek-ai/deepseek-coder-6.7b-instruct",
    "protocol_parser": "meta-llama/Meta-Llama-3.1-8B-Instruct",
}

ROLE_LABELS: Dict[str, str] = {
    "code_generation": "Code Generation",
    "code_review": "Code Review",
    "nl_to_cli": "NL → CLI",
    "docs_generator": "Docs Generator",
    "signal_classifier": "Signal Classifier",
    "firmware_analysis": "Firmware Analysis",
    "github_ranker": "GitHub Ranker",
    "log_analyzer": "Log Analyzer",
    "build_diagnostics": "Build Diagnostics",
    "protocol_parser": "Protocol Parser",
}


class ModelSearchThread(QThread):
    """Background thread to search HuggingFace models."""

    results_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, query: str, api_key: str = ""):
        super().__init__()
        self.query = query
        self.api_key = api_key

    def run(self):
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        try:
            resp = requests.get(
                HF_MODELS_API,
                params={"search": self.query, "limit": 20},
                headers=headers,
                timeout=10,
            )
            resp.raise_for_status()
            models = [m.get("modelId", "") for m in resp.json() if m.get("modelId")]
            self.results_ready.emit(models)
        except Exception as exc:
            self.error_occurred.emit(str(exc))


class KeyValidationThread(QThread):
    """Background thread to validate a HuggingFace API key."""

    valid = pyqtSignal(str)    # emits username on success
    invalid = pyqtSignal(int)  # emits HTTP status code on failure
    error_occurred = pyqtSignal(str)

    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key

    def run(self):
        try:
            resp = requests.get(
                "https://huggingface.co/api/whoami",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10,
            )
            if resp.status_code == 200:
                self.valid.emit(resp.json().get("name", "OK"))
            else:
                self.invalid.emit(resp.status_code)
        except Exception as exc:
            self.error_occurred.emit(str(exc))


class HuggingFaceManagerWidget(QWidget):
    """Full HuggingFace management panel."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        self._search_thread: Optional[ModelSearchThread] = None
        self._model_combos: Dict[str, QComboBox] = {}
        self._local_checks: Dict[str, QCheckBox] = {}
        self._init_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _init_ui(self):
        root = QVBoxLayout(self)

        # --- API Key section ---
        key_group = QGroupBox("HuggingFace API Key")
        key_layout = QHBoxLayout(key_group)
        self._key_input = QLineEdit()
        self._key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._key_input.setPlaceholderText("hf_…  (leave empty for public / local models)")
        saved_key = self.config.get("huggingface", {}).get("api_key", "")
        self._key_input.setText(saved_key)
        validate_btn = QPushButton("Validate Key")
        validate_btn.clicked.connect(self._validate_key)
        self._key_status = QLabel("●")
        self._key_status.setStyleSheet("color: grey; font-size: 16px;")
        key_layout.addWidget(QLabel("API Key:"))
        key_layout.addWidget(self._key_input, stretch=1)
        key_layout.addWidget(validate_btn)
        key_layout.addWidget(self._key_status)
        root.addWidget(key_group)

        # --- Model search ---
        search_group = QGroupBox("Model Browser")
        search_layout = QHBoxLayout(search_group)
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search HuggingFace (e.g. 'code llama')")
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self._search_models)
        self._search_results = QComboBox()
        self._search_results.setMinimumWidth(350)
        apply_btn = QPushButton("Apply to Selected Service")
        apply_btn.clicked.connect(self._apply_search_result)
        search_layout.addWidget(self._search_input, stretch=1)
        search_layout.addWidget(search_btn)
        search_layout.addWidget(self._search_results, stretch=1)
        search_layout.addWidget(apply_btn)
        root.addWidget(search_group)

        # --- Per-service model selection ---
        services_group = QGroupBox("Per-Service Model Configuration")
        services_layout = QFormLayout(services_group)
        for role, label in ROLE_LABELS.items():
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)

            combo = QComboBox()
            combo.setEditable(True)
            combo.setMinimumWidth(350)
            current_model = (
                self.config.get("huggingface", {})
                .get("default_models", {})
                .get(role, DEFAULT_MODELS.get(role, ""))
            )
            combo.addItem(current_model)
            combo.setCurrentText(current_model)
            self._model_combos[role] = combo

            local_check = QCheckBox("Local")
            orch_cfg = self.config.get("orchestration", {})
            runners = orch_cfg.get("model_runners", {}) if isinstance(orch_cfg, dict) else {}
            local_check.setChecked(runners.get(role, {}).get("local", False))
            self._local_checks[role] = local_check

            row_layout.addWidget(combo, stretch=1)
            row_layout.addWidget(local_check)
            services_layout.addRow(f"{label}:", row_widget)

        scroll = QScrollArea()
        scroll.setWidget(services_group)
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(320)
        root.addWidget(scroll)

        # --- Save ---
        save_btn = QPushButton("Save Configuration")
        save_btn.clicked.connect(self._save_config)
        root.addWidget(save_btn)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _validate_key(self):
        key = self._key_input.text().strip()
        if not key:
            self._key_status.setStyleSheet("color: grey; font-size: 16px;")
            self._key_status.setToolTip("No key provided — public/local access only")
            return

        self._key_status.setStyleSheet("color: grey; font-size: 16px;")
        self._key_status.setToolTip("Validating…")
        self._key_validation_thread = KeyValidationThread(key)
        self._key_validation_thread.valid.connect(self._on_key_valid)
        self._key_validation_thread.invalid.connect(self._on_key_invalid)
        self._key_validation_thread.error_occurred.connect(self._on_key_error)
        self._key_validation_thread.start()

    def _on_key_valid(self, username: str):
        self._key_status.setStyleSheet("color: green; font-size: 16px;")
        self._key_status.setToolTip(f"Valid key — logged in as: {username}")

    def _on_key_invalid(self, status_code: int):
        self._key_status.setStyleSheet("color: red; font-size: 16px;")
        self._key_status.setToolTip(f"Invalid key (HTTP {status_code})")

    def _on_key_error(self, error: str):
        self._key_status.setStyleSheet("color: orange; font-size: 16px;")
        self._key_status.setToolTip(f"Network error: {error}")

    def _search_models(self):
        query = self._search_input.text().strip()
        if not query:
            return
        key = self._key_input.text().strip()
        self._search_thread = ModelSearchThread(query, key)
        self._search_thread.results_ready.connect(self._on_search_results)
        self._search_thread.error_occurred.connect(
            lambda e: QMessageBox.warning(self, "Search Error", e)
        )
        self._search_results.clear()
        self._search_results.addItem("Searching…")
        self._search_thread.start()

    def _on_search_results(self, models: list):
        self._search_results.clear()
        for m in models:
            self._search_results.addItem(m)
        if not models:
            self._search_results.addItem("(no results)")

    def _apply_search_result(self):
        model = self._search_results.currentText()
        if not model or model in ("Searching…", "(no results)"):
            return
        # Apply to whichever combo currently has focus, else show picker
        focused = self.focusWidget()
        for role, combo in self._model_combos.items():
            if combo is focused or combo.lineEdit() is focused:
                if combo.findText(model) == -1:
                    combo.insertItem(0, model)
                combo.setCurrentText(model)
                return
        QMessageBox.information(
            self,
            "Apply Model",
            f"Click inside a service model field first, then press 'Apply to Selected Service'.\n\nSelected model: {model}",
        )

    def _save_config(self):
        hf_models = {role: combo.currentText() for role, combo in self._model_combos.items()}
        local_flags = {role: cb.isChecked() for role, cb in self._local_checks.items()}

        if "huggingface" not in self.config:
            self.config["huggingface"] = {}
        self.config["huggingface"]["api_key"] = self._key_input.text().strip()
        self.config["huggingface"]["default_models"] = hf_models

        if "orchestration" not in self.config:
            self.config["orchestration"] = {"model_runners": {}}
        if "model_runners" not in self.config["orchestration"]:
            self.config["orchestration"]["model_runners"] = {}
        for role, is_local in local_flags.items():
            if role not in self.config["orchestration"]["model_runners"]:
                self.config["orchestration"]["model_runners"][role] = {}
            self.config["orchestration"]["model_runners"][role]["local"] = is_local
            self.config["orchestration"]["model_runners"][role]["model"] = hf_models[role]

        config_path = Path("config/settings.json")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(self.config, f, indent=2)

        QMessageBox.information(self, "Saved", "HuggingFace configuration saved successfully.")
