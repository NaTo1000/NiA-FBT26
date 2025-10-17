from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit

class TerminalWidget(QWidget):
    def __init__(self, config):
        super().__init__()
        layout = QVBoxLayout()
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        layout.addWidget(self.terminal)
        self.setLayout(layout)
