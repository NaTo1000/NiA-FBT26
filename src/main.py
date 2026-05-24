#!/usr/bin/env python3
"""
NiA FBT26 - Advanced Flipper Zero Development Suite
Main Application Entry Point
"""

import sys
import os
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from gui.main_window import MainWindow
from core.config_manager import ConfigManager
from core.device_manager import DeviceManager

__version__ = "2.0.0"
__author__ = "NaTo1000"

def main():
    """Main entry point for NiA FBT26"""

    # Qt6 handles high-DPI scaling automatically; PassThrough avoids
    # fractional-scale rounding artefacts on mixed-DPI displays.
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("NiA FBT26")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("NaTo1000")
    
    # Initialize configuration
    config = ConfigManager()
    
    # Initialize device manager
    device_manager = DeviceManager()
    
    # Create and show main window
    window = MainWindow(config, device_manager)
    window.show()
    
    # Run application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
