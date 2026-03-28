
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QListWidget, QListWidgetItem,
    QGroupBox, QTextEdit,
)
from PyQt6.QtCore import Qt


class GitHubSearchWidget(QWidget):
    """GitHub search widget — v2.0."""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self._results_cache: list[dict] = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # ── Search bar ─────────────────────────────────────────────────
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Flipper apps, firmware, plugins…")
        self.search_input.returnPressed.connect(self.do_search)
        search_row.addWidget(self.search_input)
        self.search_btn = QPushButton("🔍 Search")
        self.search_btn.clicked.connect(self.do_search)
        search_row.addWidget(self.search_btn)
        layout.addLayout(search_row)

        # ── Results list ───────────────────────────────────────────────
        results_group = QGroupBox("📋 Results")
        results_layout = QVBoxLayout()
        self.results_list = QListWidget()
        self.results_list.currentRowChanged.connect(self._on_result_selected)
        results_layout.addWidget(self.results_list)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        # ── Detail panel ───────────────────────────────────────────────
        detail_group = QGroupBox("ℹ️ Details")
        detail_layout = QVBoxLayout()
        self.detail_view = QTextEdit()
        self.detail_view.setReadOnly(True)
        self.detail_view.setMaximumHeight(120)
        detail_layout.addWidget(self.detail_view)
        detail_group.setLayout(detail_layout)
        layout.addWidget(detail_group)

        # ── Action buttons ─────────────────────────────────────────────
        btn_row = QHBoxLayout()
        self.download_btn = QPushButton("⬇️ Download / Clone")
        self.download_btn.clicked.connect(self.download_selected)
        self.download_btn.setEnabled(False)
        btn_row.addWidget(self.download_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.setLayout(layout)

    def do_search(self):
        query = self.search_input.text().strip()
        if not query:
            return
        self.results_list.clear()
        self.detail_view.clear()
        self.download_btn.setEnabled(False)
        self.detail_view.setText(f"Searching for '{query}'… (GitHub token required for live results)")
        # Placeholder — real search requires PyGithub + token
        placeholder_results = [
            {"name": f"flipper-zero-{query.replace(' ', '-')}", "stars": 0, "description": "Placeholder result"},
        ]
        self._results_cache = placeholder_results
        for item in placeholder_results:
            self.results_list.addItem(QListWidgetItem(f"⭐ {item['stars']}  {item['name']}"))

    def _on_result_selected(self, row: int):
        if 0 <= row < len(self._results_cache):
            item = self._results_cache[row]
            self.detail_view.setText(
                f"Name: {item['name']}\nStars: {item['stars']}\nDescription: {item['description']}"
            )
            self.download_btn.setEnabled(True)

    def download_selected(self):
        row = self.results_list.currentRow()
        if 0 <= row < len(self._results_cache):
            self.detail_view.append("\nDownload queued…")

