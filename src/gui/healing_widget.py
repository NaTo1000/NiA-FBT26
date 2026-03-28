"""
HealingWidget — Optional GUI panel shown in the "AI Orchestration" tab.

Provides:
- A "Heal All" button to trigger a manual heal cycle
- Per-service status indicators (healthy / failed / rebuilding / unknown)
- A progress bar for the active heal operation
- A scrollable log view
"""

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

# Colour mapping for each state string
_STATE_COLOURS = {
    "healthy":    "#2ecc71",
    "failed":     "#e74c3c",
    "rebuilding": "#f39c12",
    "unknown":    "#95a5a6",
}


class _ServiceRow(QWidget):
    """A single row showing a service name and a coloured status badge."""

    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)

        self._name_label = QLabel(name)
        self._name_label.setMinimumWidth(200)

        self._status_label = QLabel("unknown")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setMinimumWidth(90)
        self._status_label.setStyleSheet(
            f"background: {_STATE_COLOURS['unknown']}; "
            "color: white; border-radius: 4px; padding: 2px 6px;"
        )

        layout.addWidget(self._name_label)
        layout.addStretch()
        layout.addWidget(self._status_label)

    def set_state(self, state: str):
        colour = _STATE_COLOURS.get(state, _STATE_COLOURS["unknown"])
        self._status_label.setText(state)
        self._status_label.setStyleSheet(
            f"background: {colour}; "
            "color: white; border-radius: 4px; padding: 2px 6px;"
        )


class HealingWidget(QWidget):
    """
    Full healing panel widget.

    Parameters
    ----------
    healing_manager : HealingManager
        An already-constructed HealingManager instance.
    parent : QWidget, optional
    """

    def __init__(self, healing_manager, parent=None):
        super().__init__(parent)
        self._manager = healing_manager
        self._rows: dict[str, _ServiceRow] = {}

        self._build_ui()
        self._connect_signals()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)

        # ── Controls row ────────────────────────────────────────────────
        controls = QHBoxLayout()
        self._heal_btn = QPushButton("⚕  Heal All  (Ctrl+Shift+A)")
        self._heal_btn.setToolTip("Trigger a full self-healing cycle for all AI services")
        self._heal_btn.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        self._heal_btn.clicked.connect(self._on_heal_clicked)

        self._status_banner = QLabel("Idle")
        self._status_banner.setStyleSheet("color: #555; font-style: italic;")

        controls.addWidget(self._heal_btn)
        controls.addWidget(self._status_banner)
        controls.addStretch()
        root.addLayout(controls)

        # ── Progress bar ─────────────────────────────────────────────────
        self._progress = QProgressBar()
        self._progress.setRange(0, 4)
        self._progress.setValue(0)
        self._progress.setVisible(False)
        root.addWidget(self._progress)

        # ── Service status grid ──────────────────────────────────────────
        group = QGroupBox("Service Status")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(2)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(2)
        scroll_layout.setContentsMargins(0, 0, 0, 0)

        from ai.healing_manager import SERVICES
        for name in SERVICES:
            row = _ServiceRow(name)
            self._rows[name] = row
            scroll_layout.addWidget(row)
        scroll_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidget(scroll_content)
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(300)
        group_layout.addWidget(scroll)
        root.addWidget(group)

        # ── Log view ─────────────────────────────────────────────────────
        log_group = QGroupBox("Healing Log")
        log_layout = QVBoxLayout(log_group)
        self._log_view = QPlainTextEdit()
        self._log_view.setReadOnly(True)
        self._log_view.setMaximumHeight(180)
        log_layout.addWidget(self._log_view)
        root.addWidget(log_group)

    # ------------------------------------------------------------------
    # Signal wiring
    # ------------------------------------------------------------------

    def _connect_signals(self):
        self._manager.healing_started.connect(self._on_healing_started)
        self._manager.healing_finished.connect(self._on_healing_finished)
        self._manager.status_updated.connect(self._on_status_updated)
        self._manager.progress_updated.connect(self._on_progress_updated)
        self._manager.log_message.connect(self._on_log_message)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    @pyqtSlot()
    def _on_heal_clicked(self):
        self._manager.heal()

    @pyqtSlot()
    def _on_healing_started(self):
        self._heal_btn.setEnabled(False)
        self._status_banner.setText("Healing in progress …")
        self._progress.setValue(0)
        self._progress.setVisible(True)

    @pyqtSlot(bool)
    def _on_healing_finished(self, success: bool):
        self._heal_btn.setEnabled(True)
        self._progress.setVisible(False)
        if success:
            self._status_banner.setText("Heal cycle completed successfully ✓")
            self._status_banner.setStyleSheet("color: #27ae60;")
        else:
            self._status_banner.setText("Heal cycle finished with errors ✗")
            self._status_banner.setStyleSheet("color: #c0392b;")

    @pyqtSlot(str, str)
    def _on_status_updated(self, name: str, state: str):
        if name in self._rows:
            self._rows[name].set_state(state)

    @pyqtSlot(int, int)
    def _on_progress_updated(self, current: int, total: int):
        self._progress.setMaximum(total)
        self._progress.setValue(current)

    @pyqtSlot(str)
    def _on_log_message(self, message: str):
        self._log_view.appendPlainText(message)
        # Auto-scroll to bottom
        sb = self._log_view.verticalScrollBar()
        sb.setValue(sb.maximum())
