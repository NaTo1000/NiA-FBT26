
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QTextEdit, QGroupBox, QFormLayout, QLineEdit,
    QSplitter,
)
from PyQt6.QtCore import Qt


class ArduinoPanelWidget(QWidget):
    """Arduino / ESP32 panel — v2.0."""

    BOARDS = [
        "ESP32 Dev Module",
        "ESP32-S2",
        "ESP32-S3",
        "ESP32-C3",
        "ESP8266",
        "Arduino Uno",
        "Arduino Nano",
        "Arduino Mega 2560",
    ]

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # ── Board selector ─────────────────────────────────────────────
        board_group = QGroupBox("🔌 Board Configuration")
        board_form = QFormLayout()

        self.board_combo = QComboBox()
        self.board_combo.addItems(self.BOARDS)
        board_form.addRow("Board:", self.board_combo)

        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("/dev/ttyUSB0 or COM3")
        board_form.addRow("Port:", self.port_input)

        board_group.setLayout(board_form)
        layout.addWidget(board_group)

        # ── Sketch editor ──────────────────────────────────────────────
        editor_group = QGroupBox("📝 Sketch Editor")
        editor_layout = QVBoxLayout()
        self.sketch_editor = QTextEdit()
        self.sketch_editor.setFontFamily("Monospace")
        self.sketch_editor.setPlaceholderText(
            "void setup() {\n  Serial.begin(115200);\n}\n\nvoid loop() {\n  // code here\n}"
        )
        editor_layout.addWidget(self.sketch_editor)
        editor_group.setLayout(editor_layout)
        layout.addWidget(editor_group)

        # ── Serial monitor ─────────────────────────────────────────────
        monitor_group = QGroupBox("📡 Serial Monitor")
        monitor_layout = QVBoxLayout()
        self.serial_output = QTextEdit()
        self.serial_output.setReadOnly(True)
        self.serial_output.setFontFamily("Monospace")
        self.serial_output.setMaximumHeight(120)
        monitor_layout.addWidget(self.serial_output)
        monitor_group.setLayout(monitor_layout)
        layout.addWidget(monitor_group)

        # ── Buttons ────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        self.compile_btn = QPushButton("🔨 Compile")
        self.compile_btn.clicked.connect(self.compile_sketch)
        self.upload_btn = QPushButton("🚀 Upload")
        self.upload_btn.clicked.connect(self.upload_sketch)
        self.monitor_btn = QPushButton("📡 Open Monitor")
        self.monitor_btn.clicked.connect(self.open_monitor)
        btn_row.addWidget(self.compile_btn)
        btn_row.addWidget(self.upload_btn)
        btn_row.addWidget(self.monitor_btn)
        layout.addLayout(btn_row)

        self.setLayout(layout)

    def compile_sketch(self):
        self.serial_output.append(f"Compiling for {self.board_combo.currentText()}…")

    def upload_sketch(self):
        self.serial_output.append(f"Uploading to {self.port_input.text() or 'auto'}…")

    def open_monitor(self):
        self.serial_output.append("Serial monitor opened.")

