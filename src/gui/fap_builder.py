
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QComboBox, QTextEdit, QGroupBox, QFormLayout,
)
from PyQt6.QtCore import Qt


class FAPBuilderWidget(QWidget):
    """Widget for building Flipper Application Packages — v2.0."""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # ── Project wizard ─────────────────────────────────────────────
        wizard = QGroupBox("📋 Project Configuration")
        form = QFormLayout()

        self.app_id_input = QLineEdit()
        self.app_id_input.setPlaceholderText("e.g. my_tool")
        form.addRow("App ID:", self.app_id_input)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. My Tool")
        form.addRow("Name:", self.name_input)

        self.category_combo = QComboBox()
        self.category_combo.addItems(
            ["Tools", "Games", "GPIO", "Sub-GHz", "NFC", "USB", "Bluetooth", "Misc"]
        )
        form.addRow("Category:", self.category_combo)

        self.entry_point_input = QLineEdit()
        self.entry_point_input.setPlaceholderText("e.g. my_tool_app")
        form.addRow("Entry Point:", self.entry_point_input)

        wizard.setLayout(form)
        layout.addWidget(wizard)

        # ── Code editor ────────────────────────────────────────────────
        editor_group = QGroupBox("📝 Source Code (C)")
        editor_layout = QVBoxLayout()
        self.code_editor = QTextEdit()
        self.code_editor.setFontFamily("Monospace")
        self.code_editor.setPlaceholderText(
            "#include <furi.h>\n\nint32_t my_app_main(void* p) {\n    UNUSED(p);\n    return 0;\n}"
        )
        editor_layout.addWidget(self.code_editor)
        editor_group.setLayout(editor_layout)
        layout.addWidget(editor_group)

        # ── Build log ──────────────────────────────────────────────────
        log_group = QGroupBox("🔨 Build Output")
        log_layout = QVBoxLayout()
        self.build_log = QTextEdit()
        self.build_log.setReadOnly(True)
        self.build_log.setFontFamily("Monospace")
        self.build_log.setMaximumHeight(120)
        log_layout.addWidget(self.build_log)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        # ── Action buttons ─────────────────────────────────────────────
        btn_row = QHBoxLayout()
        self.create_btn = QPushButton("📁 Create Project")
        self.create_btn.clicked.connect(self.create_project)
        self.build_btn = QPushButton("🔨 Build FAP")
        self.build_btn.clicked.connect(self.build_fap)
        self.deploy_btn = QPushButton("🚀 Deploy to Device")
        self.deploy_btn.clicked.connect(self.deploy_fap)
        btn_row.addWidget(self.create_btn)
        btn_row.addWidget(self.build_btn)
        btn_row.addWidget(self.deploy_btn)
        layout.addLayout(btn_row)

        self.setLayout(layout)

    # ------------------------------------------------------------------

    def create_project(self):
        self.build_log.append("Creating FAP project scaffold…")

    def build_fap(self):
        self.build_log.append("Building FAP…")

    def deploy_fap(self):
        self.build_log.append("Deploying to connected Flipper Zero…")

