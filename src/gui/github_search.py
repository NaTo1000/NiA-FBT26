from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QListWidget

class GitHubSearchWidget(QWidget):
    def __init__(self, config):
        super().__init__()
        layout = QVBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search GitHub...")
        layout.addWidget(self.search_input)
        self.results = QListWidget()
        layout.addWidget(self.results)
        self.setLayout(layout)
