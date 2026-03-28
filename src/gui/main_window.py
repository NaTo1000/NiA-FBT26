
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStatusBar, QMenuBar, QMenu, QToolBar,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon


class MainWindow(QMainWindow):
    """Main application window — v2.0 modern tabbed dashboard."""

    # Tab indices — must match the order in init_ui
    _TAB_DASHBOARD = 0
    _TAB_FAP = 1
    _TAB_FIRMWARE = 2
    _TAB_ARDUINO = 3
    _TAB_TERMINAL = 4
    _TAB_GITHUB = 5
    _TAB_DEVICE = 6
    _TAB_SETTINGS = 7

    def __init__(self, config, device_manager):
        super().__init__()
        self.config = config
        self.device_manager = device_manager

        self.setWindowTitle("NiA FBT26 v2.0 — Flipper Zero Development Suite")
        self.setGeometry(100, 100, 1400, 900)

        self._apply_dark_theme()
        self.init_ui()

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def _apply_dark_theme(self):
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
            QTabWidget::pane { border: 1px solid #313244; }
            QTabBar::tab {
                background: #313244;
                color: #cdd6f4;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected { background: #45475a; }
            QMenuBar { background-color: #181825; color: #cdd6f4; }
            QMenuBar::item:selected { background-color: #313244; }
            QMenu { background-color: #1e1e2e; color: #cdd6f4; }
            QMenu::item:selected { background-color: #313244; }
            QToolBar { background-color: #181825; border: none; }
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                border: none;
                padding: 6px 14px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #74c7ec; }
            QStatusBar { background-color: #181825; color: #a6e3a1; }
            """
        )

    # ------------------------------------------------------------------
    # UI initialisation
    # ------------------------------------------------------------------

    def init_ui(self):
        self.create_menus()
        self.create_toolbar()

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Import tab widgets
        from .dashboard import DashboardWidget
        from .fap_builder import FAPBuilderWidget
        from .firmware_builder import FirmwareBuilderWidget
        from .arduino_panel import ArduinoPanelWidget
        from .terminal_widget import TerminalWidget
        from .github_search import GitHubSearchWidget
        from .device_manager import DeviceManagerWidget
        from .settings_widget import SettingsWidget

        self.tabs.addTab(DashboardWidget(self.config, self.device_manager), "🏠 Dashboard")
        self.tabs.addTab(FAPBuilderWidget(self.config), "📱 FAP Builder")
        self.tabs.addTab(FirmwareBuilderWidget(self.config), "⚡ Firmware Builder")
        self.tabs.addTab(ArduinoPanelWidget(self.config), "🔧 Arduino/ESP32")
        self.tabs.addTab(TerminalWidget(self.config), "💻 Terminal")
        self.tabs.addTab(GitHubSearchWidget(self.config), "🔍 GitHub Search")
        self.tabs.addTab(DeviceManagerWidget(self.config, self.device_manager), "📟 Device Manager")
        self.tabs.addTab(SettingsWidget(self.config), "⚙️ Settings")

        # Status bar
        self._status_device = QLabel("Device: Disconnected")
        self._status_build = QLabel("Build: Idle")
        self._status_version = QLabel("v2.0.0")
        self.statusBar().addWidget(self._status_device)
        self.statusBar().addPermanentWidget(self._status_build)
        self.statusBar().addPermanentWidget(self._status_version)

    # ------------------------------------------------------------------
    # Menus
    # ------------------------------------------------------------------

    def create_menus(self):
        menubar = self.menuBar()

        # File
        file_menu = menubar.addMenu("File")
        file_menu.addAction("New Project", self.new_project)
        file_menu.addAction("Open Project", self.open_project)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)

        # Device
        device_menu = menubar.addMenu("Device")
        device_menu.addAction("Connect", self.connect_device)
        device_menu.addAction("Disconnect", self.disconnect_device)
        device_menu.addSeparator()
        device_menu.addAction("Flash Firmware", self.flash_firmware)

        # Build
        build_menu = menubar.addMenu("Build")
        build_menu.addAction("Build FAP", self.build_fap)
        build_menu.addAction("Build Firmware", self.build_firmware)
        build_menu.addAction("Build Arduino", self.build_arduino)

        # Tools
        tools_menu = menubar.addMenu("Tools")
        tools_menu.addAction("Settings", self.show_settings)
        tools_menu.addAction("Plugins", self.show_plugins)

        # Help
        help_menu = menubar.addMenu("Help")
        help_menu.addAction("About", self.show_about)
        help_menu.addAction("Documentation", self.show_docs)

    # ------------------------------------------------------------------
    # Toolbar
    # ------------------------------------------------------------------

    def create_toolbar(self):
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)
        toolbar.addAction("🔌 Connect", self.connect_device)
        toolbar.addSeparator()
        toolbar.addAction("🔨 Build FAP", self.build_fap)
        toolbar.addAction("⚡ Build FW", self.build_firmware)
        toolbar.addSeparator()
        toolbar.addAction("🚀 Flash", self.flash_firmware)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def new_project(self):
        pass

    def open_project(self):
        pass

    def connect_device(self):
        self._status_device.setText("Device: Connecting…")
        self.statusBar().showMessage("Connecting to device…", 3000)

    def disconnect_device(self):
        self._status_device.setText("Device: Disconnected")

    def flash_firmware(self):
        self.statusBar().showMessage("Flashing firmware…", 3000)

    def build_fap(self):
        self._status_build.setText("Build: Running")
        self.statusBar().showMessage("Building FAP…", 3000)

    def build_firmware(self):
        self._status_build.setText("Build: Running")
        self.statusBar().showMessage("Building firmware…", 3000)

    def build_arduino(self):
        self._status_build.setText("Build: Running")
        self.statusBar().showMessage("Building Arduino sketch…", 3000)

    def show_settings(self):
        self.tabs.setCurrentIndex(self._TAB_SETTINGS)

    def show_plugins(self):
        pass

    def show_about(self):
        pass

    def show_docs(self):
        pass

