"""Device Manager widget — v2.0."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QTreeWidget, QTreeWidgetItem, QTextEdit, QFormLayout,
)
from PyQt6.QtCore import Qt


class DeviceManagerWidget(QWidget):
    """Auto-detect and manage connected Flipper Zero devices — v2.0."""

    def __init__(self, config, device_manager):
        super().__init__()
        self.config = config
        self.device_manager = device_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # ── Device info card ───────────────────────────────────────────
        info_group = QGroupBox("📟 Connected Device")
        info_form = QFormLayout()

        self._lbl_status = QLabel("Disconnected")
        self._lbl_status.setStyleSheet("color: #f38ba8;")
        info_form.addRow("Status:", self._lbl_status)

        self._lbl_model = QLabel("—")
        info_form.addRow("Model:", self._lbl_model)

        self._lbl_serial = QLabel("—")
        info_form.addRow("Serial:", self._lbl_serial)

        self._lbl_fw = QLabel("—")
        info_form.addRow("Firmware:", self._lbl_fw)

        self._lbl_storage = QLabel("—")
        info_form.addRow("Storage:", self._lbl_storage)

        info_group.setLayout(info_form)
        layout.addWidget(info_group)

        # ── File browser ───────────────────────────────────────────────
        browser_group = QGroupBox("📁 SD Card File Browser")
        browser_layout = QVBoxLayout()
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(["Name", "Size", "Type"])
        self.file_tree.setMinimumHeight(200)
        browser_layout.addWidget(self.file_tree)
        browser_group.setLayout(browser_layout)
        layout.addWidget(browser_group)

        # ── Transfer log ───────────────────────────────────────────────
        log_group = QGroupBox("📋 Transfer Log")
        log_layout = QVBoxLayout()
        self.transfer_log = QTextEdit()
        self.transfer_log.setReadOnly(True)
        self.transfer_log.setFontFamily("Monospace")
        self.transfer_log.setMaximumHeight(100)
        log_layout.addWidget(self.transfer_log)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        # ── Buttons ────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        self.connect_btn = QPushButton("🔌 Connect")
        self.connect_btn.clicked.connect(self._on_connect)
        self.refresh_btn = QPushButton("🔄 Refresh Files")
        self.refresh_btn.clicked.connect(self._on_refresh)
        self.fw_check_btn = QPushButton("⬆️ Check Firmware Update")
        self.fw_check_btn.clicked.connect(self._on_fw_check)
        btn_row.addWidget(self.connect_btn)
        btn_row.addWidget(self.refresh_btn)
        btn_row.addWidget(self.fw_check_btn)
        layout.addLayout(btn_row)

        self.setLayout(layout)

    # ------------------------------------------------------------------

    def _on_connect(self):
        connected = self.device_manager.connect()
        if connected:
            self._lbl_status.setText("Connected")
            self._lbl_status.setStyleSheet("color: #a6e3a1;")
            self.transfer_log.append("Device connected.")
        else:
            self.transfer_log.append("Connection failed — check USB cable.")

    def _on_refresh(self):
        self.file_tree.clear()
        self.transfer_log.append("Refreshing file list… (device must be connected)")

    def _on_fw_check(self):
        self.transfer_log.append("Checking for firmware updates…")
