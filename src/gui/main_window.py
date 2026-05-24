
from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QStatusBar,
                             QMenuBar, QMenu, QToolBar, QDockWidget, QSplitter)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon

from ai.healing_manager import HealingManager
from core.hotkey_handler import HotkeyHandler


class MainWindow(QMainWindow):
    """Main application window with all development tools"""
    
    def __init__(self, config, device_manager):
        super().__init__()
        self.config = config
        self.device_manager = device_manager
        
        self.setWindowTitle("NiA FBT26 - Flipper Zero Development Suite")
        self.setGeometry(100, 100, 1400, 900)

        # Set up healing manager and hotkey before building UI so that
        # the healing widget can connect to the manager's signals.
        self._healing_manager = HealingManager(
            config=self.config.config if hasattr(self.config, "config") else {},
            parent=self,
        )
        self._hotkey_handler = HotkeyHandler(
            parent_window=self,
            config=self.config.config if hasattr(self.config, "config") else {},
            parent=self,
        )
        self._hotkey_handler.heal_triggered.connect(self._healing_manager.heal)
        
        self.init_ui()

        # Auto-heal on startup if configured
        cfg = self.config.config if hasattr(self.config, "config") else {}
        if cfg.get("healing", {}).get("auto_heal_on_startup", False):
            self._healing_manager.heal()
        
    def init_ui(self):
        # Create menu bar
        self.create_menus()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create central widget with tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Add tabs for each feature
        from .fap_builder import FAPBuilderWidget
        from .firmware_builder import FirmwareBuilderWidget
        from .arduino_panel import ArduinoPanelWidget
        from .terminal_widget import TerminalWidget
        from .github_search import GitHubSearchWidget
        from .healing_widget import HealingWidget
        
        self.tabs.addTab(FAPBuilderWidget(self.config), "FAP Builder")
        self.tabs.addTab(FirmwareBuilderWidget(self.config), "Firmware Builder")
        self.tabs.addTab(ArduinoPanelWidget(self.config), "Arduino/ESP32")
        self.tabs.addTab(TerminalWidget(self.config), "Terminal")
        self.tabs.addTab(GitHubSearchWidget(self.config), "GitHub Search")
        self.tabs.addTab(HealingWidget(self._healing_manager), "AI Orchestration")

        # Connect healing log to status bar
        self._healing_manager.log_message.connect(
            lambda msg: self.statusBar().showMessage(msg, 5000)
        )
        
        # Create status bar
        self.statusBar().showMessage("Ready")
        
    def create_menus(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        file_menu.addAction("New Project", self.new_project)
        file_menu.addAction("Open Project", self.open_project)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)
        
        # Device menu
        device_menu = menubar.addMenu("Device")
        device_menu.addAction("Connect", self.connect_device)
        device_menu.addAction("Disconnect", self.disconnect_device)
        device_menu.addSeparator()
        device_menu.addAction("Flash Firmware", self.flash_firmware)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        tools_menu.addAction("Settings", self.show_settings)
        tools_menu.addSeparator()
        tools_menu.addAction("Heal All AI Services  (Ctrl+Shift+A)",
                             self._healing_manager.heal)
        
    def create_toolbar(self):
        toolbar = self.addToolBar("Main")
        toolbar.addAction("Connect", self.connect_device)
        toolbar.addAction("Build", self.build_project)
        toolbar.addAction("Flash", self.flash_firmware)
        toolbar.addSeparator()
        toolbar.addAction("⚕ Heal", self._healing_manager.heal)
        
    def new_project(self):
        pass
    
    def open_project(self):
        pass
    
    def connect_device(self):
        self.statusBar().showMessage("Connecting to device...")
    
    def disconnect_device(self):
        pass
    
    def flash_firmware(self):
        pass
    
    def build_project(self):
        pass
    
    def show_settings(self):
        pass
