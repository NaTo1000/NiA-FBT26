
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QTextEdit, QGroupBox, QCheckBox, QProgressBar,
    QLineEdit, QFormLayout,
)
from PyQt6.QtCore import Qt


class FirmwareBuilderWidget(QWidget):
    """Firmware builder — v2.0."""

    SOURCES = ["Official", "Unleashed", "RogueMaster", "Custom URL"]
    OPT_LEVELS = ["size", "speed", "debug"]

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # ── Source selector ────────────────────────────────────────────
        src_group = QGroupBox("📦 Firmware Source")
        src_form = QFormLayout()

        self.source_combo = QComboBox()
        self.source_combo.addItems(self.SOURCES)
        self.source_combo.currentTextChanged.connect(self._on_source_changed)
        src_form.addRow("Source:", self.source_combo)

        self.custom_url = QLineEdit()
        self.custom_url.setPlaceholderText("https://github.com/…")
        self.custom_url.setVisible(False)
        src_form.addRow("Custom URL:", self.custom_url)

        src_group.setLayout(src_form)
        layout.addWidget(src_group)

        # ── Build configuration ────────────────────────────────────────
        cfg_group = QGroupBox("🔧 Build Configuration")
        cfg_layout = QVBoxLayout()

        cfg_row = QHBoxLayout()
        cfg_row.addWidget(QLabel("Optimisation:"))
        self.opt_combo = QComboBox()
        self.opt_combo.addItems(self.OPT_LEVELS)
        cfg_row.addWidget(self.opt_combo)
        cfg_layout.addLayout(cfg_row)

        self.debug_check = QCheckBox("Enable debug symbols")
        self.debug_check.setChecked(True)
        cfg_layout.addWidget(self.debug_check)

        cfg_group.setLayout(cfg_layout)
        layout.addWidget(cfg_group)

        # ── Build log ──────────────────────────────────────────────────
        log_group = QGroupBox("📋 Build Log")
        log_layout = QVBoxLayout()
        self.build_log = QTextEdit()
        self.build_log.setReadOnly(True)
        self.build_log.setFontFamily("Monospace")
        log_layout.addWidget(self.build_log)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        # ── Progress + buttons ─────────────────────────────────────────
        self.progress = QProgressBar()
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        btn_row = QHBoxLayout()
        self.build_btn = QPushButton("🔨 Build Firmware")
        self.build_btn.clicked.connect(self.build_firmware)
        self.flash_btn = QPushButton("🚀 Flash to Device")
        self.flash_btn.clicked.connect(self.flash_firmware)
        btn_row.addWidget(self.build_btn)
        btn_row.addWidget(self.flash_btn)
        layout.addLayout(btn_row)

        self.setLayout(layout)

    def _on_source_changed(self, text: str):
        self.custom_url.setVisible(text == "Custom URL")

    def build_firmware(self):
        self.build_log.append(f"Starting firmware build from source: {self.source_combo.currentText()}…")

    def flash_firmware(self):
        self.build_log.append("Flashing firmware to connected Flipper Zero…")

