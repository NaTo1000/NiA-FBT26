from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel

class FirmwareBuilderWidget(QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Firmware Builder - Coming Soon"))
        self.setLayout(layout)
