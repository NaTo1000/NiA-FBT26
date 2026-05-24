"""Home Dashboard widget — v2.0."""

import platform

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QGroupBox, QListWidget, QListWidgetItem,
    QProgressBar,
)
from PyQt6.QtCore import Qt, QTimer


class DashboardWidget(QWidget):
    """Home dashboard: device status, quick actions, recent projects, health."""

    def __init__(self, config, device_manager):
        super().__init__()
        self.config = config
        self.device_manager = device_manager
        self.init_ui()
        self._start_health_timer()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)

        # Top row: device card + quick actions
        top_row = QHBoxLayout()
        top_row.addWidget(self._build_device_card(), stretch=1)
        top_row.addWidget(self._build_quick_actions(), stretch=1)
        layout.addLayout(top_row)

        # Bottom row: recent projects + system health
        bottom_row = QHBoxLayout()
        bottom_row.addWidget(self._build_recent_projects(), stretch=1)
        bottom_row.addWidget(self._build_system_health(), stretch=1)
        layout.addLayout(bottom_row)

        self.setLayout(layout)

    # ------------------------------------------------------------------
    # Device status card
    # ------------------------------------------------------------------

    def _build_device_card(self) -> QGroupBox:
        box = QGroupBox("📟 Device Status")
        layout = QVBoxLayout()

        self._lbl_connection = QLabel("● Disconnected")
        self._lbl_connection.setStyleSheet("color: #f38ba8; font-size: 14px;")
        self._lbl_model = QLabel("Model: —")
        self._lbl_serial = QLabel("Serial: —")
        self._lbl_fw_version = QLabel("Firmware: —")

        for lbl in (self._lbl_connection, self._lbl_model, self._lbl_serial, self._lbl_fw_version):
            layout.addWidget(lbl)

        btn_connect = QPushButton("Connect Device")
        btn_connect.clicked.connect(self._on_connect)
        layout.addWidget(btn_connect)

        box.setLayout(layout)
        return box

    # ------------------------------------------------------------------
    # Quick actions
    # ------------------------------------------------------------------

    def _build_quick_actions(self) -> QGroupBox:
        box = QGroupBox("⚡ Quick Actions")
        grid = QGridLayout()

        actions = [
            ("🔨 Build FAP", self._action_build_fap),
            ("⚡ Flash Firmware", self._action_flash_firmware),
            ("💻 Open Terminal", self._action_open_terminal),
            ("🔍 GitHub Search", self._action_github_search),
        ]

        for idx, (label, slot) in enumerate(actions):
            btn = QPushButton(label)
            btn.setMinimumHeight(48)
            btn.clicked.connect(slot)
            grid.addWidget(btn, idx // 2, idx % 2)

        box.setLayout(grid)
        return box

    # ------------------------------------------------------------------
    # Recent projects
    # ------------------------------------------------------------------

    def _build_recent_projects(self) -> QGroupBox:
        box = QGroupBox("📂 Recent Projects")
        layout = QVBoxLayout()

        self._recent_list = QListWidget()
        # Placeholder entries
        for name in ("my_fap_app", "custom_firmware_v2", "esp32_bridge"):
            self._recent_list.addItem(QListWidgetItem(name))

        layout.addWidget(self._recent_list)
        box.setLayout(layout)
        return box

    # ------------------------------------------------------------------
    # System health
    # ------------------------------------------------------------------

    def _build_system_health(self) -> QGroupBox:
        box = QGroupBox("🖥️ System Health")
        layout = QVBoxLayout()

        self._cpu_bar = self._make_bar("CPU")
        self._mem_bar = self._make_bar("Memory")
        self._disk_bar = self._make_bar("Disk")

        for label, bar in (
            ("CPU", self._cpu_bar),
            ("Memory", self._mem_bar),
            ("Disk", self._disk_bar),
        ):
            row = QHBoxLayout()
            lbl = QLabel(f"{label}:")
            lbl.setFixedWidth(60)
            row.addWidget(lbl)
            row.addWidget(bar)
            layout.addLayout(row)

        layout.addWidget(QLabel(f"OS: {platform.system()} {platform.release()}"))
        layout.addWidget(QLabel(f"Python: {platform.python_version()}"))

        box.setLayout(layout)
        return box

    @staticmethod
    def _make_bar(name: str) -> QProgressBar:
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(0)
        bar.setTextVisible(True)
        return bar

    # ------------------------------------------------------------------
    # Health timer
    # ------------------------------------------------------------------

    def _start_health_timer(self):
        self._health_timer = QTimer(self)
        self._health_timer.timeout.connect(self._update_health)
        self._health_timer.start(5000)
        self._update_health()

    def _update_health(self):
        try:
            import psutil  # optional — gracefully skip if not installed
            self._cpu_bar.setValue(int(psutil.cpu_percent()))
            mem = psutil.virtual_memory()
            self._mem_bar.setValue(int(mem.percent))
            disk = psutil.disk_usage("/")
            self._disk_bar.setValue(int(disk.percent))
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_connect(self):
        connected = self.device_manager.connect()
        if connected:
            self._lbl_connection.setText("● Connected")
            self._lbl_connection.setStyleSheet("color: #a6e3a1; font-size: 14px;")

    def _action_build_fap(self):
        pass

    def _action_flash_firmware(self):
        pass

    def _action_open_terminal(self):
        pass

    def _action_github_search(self):
        pass
