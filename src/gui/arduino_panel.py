from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel

class ArduinoPanelWidget(QWidget):
    def __init__(self, config):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Arduino/ESP32 - Coming Soon"))
        self.setLayout(layout)
