"""
AI Orchestration Tab
Displays health status for all 13 services, allows task submission,
and integrates the HuggingFace manager widget.
"""

import json
from typing import Any, Dict

import requests
from PyQt6.QtCore import QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .huggingface_manager import HuggingFaceManagerWidget

SUPER_ORCH_URL = "http://localhost:7000"

TASK_TYPES = [
    "code_generation",
    "code_review",
    "build_diagnostics",
    "signal_classifier",
    "firmware_analysis",
    "github_ranker",
    "log_analyzer",
    "protocol_parser",
    "nl_to_cli",
    "docs_generator",
]


class HealthPollThread(QThread):
    """Polls /health/all from the super orchestrator."""

    data_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def run(self):
        try:
            resp = requests.get(f"{SUPER_ORCH_URL}/health/all", timeout=5)
            resp.raise_for_status()
            self.data_ready.emit(resp.json())
        except Exception as exc:
            self.error_occurred.emit(str(exc))


class TaskSubmitThread(QThread):
    """Submits a task to the super orchestrator."""

    result_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, task_type: str, prompt: str):
        super().__init__()
        self.task_type = task_type
        self.prompt = prompt

    def run(self):
        try:
            body = {"task_type": self.task_type, "payload": {"prompt": self.prompt}}
            resp = requests.post(f"{SUPER_ORCH_URL}/task", json=body, timeout=120)
            resp.raise_for_status()
            self.result_ready.emit(resp.json())
        except Exception as exc:
            self.error_occurred.emit(str(exc))


class ServiceHealthWidget(QWidget):
    """Compact row showing a single service's health."""

    def __init__(self, name: str, port: int):
        super().__init__()
        self.name = name
        self.port = port
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        self._dot = QLabel("●")
        self._dot.setStyleSheet("color: grey; font-size: 14px;")
        self._label = QLabel(f"{name}  :{port}")
        self._latency = QLabel("")
        layout.addWidget(self._dot)
        layout.addWidget(self._label)
        layout.addStretch()
        layout.addWidget(self._latency)

    def update_health(self, healthy: bool, latency_ms: Optional[float] = None):
        color = "green" if healthy else "red"
        self._dot.setStyleSheet(f"color: {color}; font-size: 14px;")
        if latency_ms is not None:
            self._latency.setText(f"{latency_ms:.0f} ms")
        else:
            self._latency.setText("")


class OrchestrationTab(QWidget):
    """Main AI Orchestration tab widget."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        self._service_widgets: Dict[str, ServiceHealthWidget] = {}
        self._poll_thread: Optional[HealthPollThread] = None
        self._submit_thread: Optional[TaskSubmitThread] = None
        self._init_ui()
        self._start_health_timer()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _init_ui(self):
        root = QVBoxLayout(self)
        splitter = QSplitter()
        splitter.setChildrenCollapsible(False)

        # Left: health panel
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("<b>Service Health</b>"))
        self._health_scroll_content = QWidget()
        self._health_layout = QVBoxLayout(self._health_scroll_content)
        self._health_layout.setSpacing(2)
        self._populate_health_rows()
        scroll = QScrollArea()
        scroll.setWidget(self._health_scroll_content)
        scroll.setWidgetResizable(True)
        left_layout.addWidget(scroll, stretch=1)
        refresh_btn = QPushButton("Refresh Now")
        refresh_btn.clicked.connect(self._poll_health)
        left_layout.addWidget(refresh_btn)

        # Right: task submission + HF settings
        right = QWidget()
        right_layout = QVBoxLayout(right)

        task_group = QGroupBox("Submit Task")
        task_form = QFormLayout(task_group)
        self._task_type_combo = QComboBox()
        self._task_type_combo.addItems(TASK_TYPES)
        self._prompt_input = QTextEdit()
        self._prompt_input.setPlaceholderText("Enter prompt / code / query…")
        self._prompt_input.setMaximumHeight(120)
        submit_btn = QPushButton("Submit Task")
        submit_btn.clicked.connect(self._submit_task)
        self._result_display = QTextEdit()
        self._result_display.setReadOnly(True)
        self._result_display.setFont(QFont("Monospace", 9))
        self._result_display.setPlaceholderText("Result will appear here…")
        task_form.addRow("Task Type:", self._task_type_combo)
        task_form.addRow("Prompt:", self._prompt_input)
        task_form.addRow("", submit_btn)
        task_form.addRow("Result:", self._result_display)
        right_layout.addWidget(task_group)

        hf_group = QGroupBox("HuggingFace Settings")
        hf_layout = QVBoxLayout(hf_group)
        hf_layout.addWidget(HuggingFaceManagerWidget(self.config))
        right_layout.addWidget(hf_group, stretch=1)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        root.addWidget(splitter)

    def _populate_health_rows(self):
        services = [
            ("super_orchestrator", 7000),
            ("sub_orch_code", 7100),
            ("sub_orch_analysis", 7200),
            ("sub_orch_interface", 7300),
            ("code_generation", 8001),
            ("code_review", 8002),
            ("nl_to_cli", 8003),
            ("docs_generator", 8004),
            ("signal_classifier", 8005),
            ("firmware_analysis", 8006),
            ("github_ranker", 8007),
            ("log_analyzer", 8008),
            ("build_diagnostics", 8009),
            ("protocol_parser", 8010),
        ]
        for name, port in services:
            w = ServiceHealthWidget(name, port)
            self._service_widgets[name] = w
            self._health_layout.addWidget(w)
        self._health_layout.addStretch()

    # ------------------------------------------------------------------
    # Health polling
    # ------------------------------------------------------------------

    def _start_health_timer(self):
        self._timer = QTimer(self)
        interval_ms = self.config.get("orchestration", {}).get("health_interval", 30) * 1000
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self._poll_health)
        self._timer.start()
        # Immediate first poll
        self._poll_health()

    def _poll_health(self):
        if self._poll_thread and self._poll_thread.isRunning():
            return
        self._poll_thread = HealthPollThread()
        self._poll_thread.data_ready.connect(self._on_health_data)
        self._poll_thread.error_occurred.connect(self._on_health_error)
        self._poll_thread.start()

    def _on_health_data(self, data: list):
        for item in data:
            name = item.get("service", "")
            if name in self._service_widgets:
                self._service_widgets[name].update_health(
                    item.get("healthy", False),
                    item.get("latency_ms"),
                )

    def _on_health_error(self, error: str):
        # Mark super orchestrator as unhealthy
        if "super_orchestrator" in self._service_widgets:
            self._service_widgets["super_orchestrator"].update_health(False)

    # ------------------------------------------------------------------
    # Task submission
    # ------------------------------------------------------------------

    def _submit_task(self):
        task_type = self._task_type_combo.currentText()
        prompt = self._prompt_input.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Input Required", "Please enter a prompt.")
            return
        self._result_display.setPlainText("Submitting task…")
        self._submit_thread = TaskSubmitThread(task_type, prompt)
        self._submit_thread.result_ready.connect(self._on_task_result)
        self._submit_thread.error_occurred.connect(self._on_task_error)
        self._submit_thread.start()

    def _on_task_result(self, data: dict):
        self._result_display.setPlainText(json.dumps(data, indent=2))

    def _on_task_error(self, error: str):
        self._result_display.setPlainText(f"Error: {error}")
