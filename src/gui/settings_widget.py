"""Settings widget — v2.0."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QFormLayout, QLineEdit, QComboBox, QSpinBox,
    QCheckBox, QTabWidget,
)
from PyQt6.QtCore import Qt


class SettingsWidget(QWidget):
    """Application settings — v2.0."""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        tabs = QTabWidget()
        tabs.addTab(self._build_editor_tab(), "✏️ Editor")
        tabs.addTab(self._build_paths_tab(), "📂 Paths")
        tabs.addTab(self._build_github_tab(), "🐙 GitHub")
        tabs.addTab(self._build_ai_tab(), "🤖 AI Integration")
        tabs.addTab(self._build_device_tab(), "📟 Device")
        layout.addWidget(tabs)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("💾 Save Settings")
        save_btn.clicked.connect(self._save)
        reset_btn = QPushButton("↺ Reset to Defaults")
        reset_btn.clicked.connect(self._reset)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(reset_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.setLayout(layout)

    # ------------------------------------------------------------------
    # Editor tab
    # ------------------------------------------------------------------

    def _build_editor_tab(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout()

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["monokai", "solarized-dark", "dracula", "light"])
        form.addRow("Theme:", self.theme_combo)

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 32)
        self.font_size_spin.setValue(12)
        form.addRow("Font Size:", self.font_size_spin)

        self.tab_size_spin = QSpinBox()
        self.tab_size_spin.setRange(1, 8)
        self.tab_size_spin.setValue(4)
        form.addRow("Tab Width:", self.tab_size_spin)

        self.line_numbers_check = QCheckBox("Show line numbers")
        self.line_numbers_check.setChecked(True)
        form.addRow("", self.line_numbers_check)

        widget.setLayout(form)
        return widget

    # ------------------------------------------------------------------
    # Paths tab
    # ------------------------------------------------------------------

    def _build_paths_tab(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout()

        self.firmware_path = QLineEdit("~/flipper-firmware")
        form.addRow("Firmware Path:", self.firmware_path)

        self.sdk_path = QLineEdit("~/flipper-sdk")
        form.addRow("SDK Path:", self.sdk_path)

        self.arduino_path = QLineEdit("~/Arduino")
        form.addRow("Arduino Path:", self.arduino_path)

        self.esp32_tools = QLineEdit("~/.platformio")
        form.addRow("ESP32 Tools:", self.esp32_tools)

        widget.setLayout(form)
        return widget

    # ------------------------------------------------------------------
    # GitHub tab
    # ------------------------------------------------------------------

    def _build_github_tab(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout()

        self.github_token = QLineEdit()
        self.github_token.setPlaceholderText("ghp_…")
        self.github_token.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("GitHub Token:", self.github_token)

        self.cache_duration_spin = QSpinBox()
        self.cache_duration_spin.setRange(60, 86400)
        self.cache_duration_spin.setValue(3600)
        self.cache_duration_spin.setSuffix(" s")
        form.addRow("Cache Duration:", self.cache_duration_spin)

        widget.setLayout(form)
        return widget

    # ------------------------------------------------------------------
    # AI Integration tab
    # ------------------------------------------------------------------

    def _build_ai_tab(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout()

        form.addRow(QLabel("Fill in your own API keys to enable AI-assisted features."))

        self.hf_api_key = QLineEdit()
        self.hf_api_key.setPlaceholderText("hf_…")
        self.hf_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("HuggingFace API Key:", self.hf_api_key)

        self.model_endpoint = QLineEdit()
        self.model_endpoint.setPlaceholderText("https://api-inference.huggingface.co/…")
        form.addRow("Model Endpoint:", self.model_endpoint)

        self.local_model_path = QLineEdit()
        self.local_model_path.setPlaceholderText("/path/to/local/model")
        form.addRow("Local Model Path:", self.local_model_path)

        widget.setLayout(form)
        return widget

    # ------------------------------------------------------------------
    # Device tab
    # ------------------------------------------------------------------

    def _build_device_tab(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout()

        self.auto_connect_check = QCheckBox("Auto-connect on launch")
        self.auto_connect_check.setChecked(True)
        form.addRow("", self.auto_connect_check)

        self.baud_rate_combo = QComboBox()
        self.baud_rate_combo.addItems(["9600", "57600", "115200", "230400"])
        self.baud_rate_combo.setCurrentText("115200")
        form.addRow("Default Baud Rate:", self.baud_rate_combo)

        widget.setLayout(form)
        return widget

    # ------------------------------------------------------------------

    def _save(self):
        cfg = self.config.config
        cfg.setdefault("editor", {})
        cfg["editor"]["theme"] = self.theme_combo.currentText()
        cfg["editor"]["font_size"] = self.font_size_spin.value()
        cfg["editor"]["tab_size"] = self.tab_size_spin.value()
        cfg["editor"]["show_line_numbers"] = self.line_numbers_check.isChecked()

        cfg["firmware_path"] = self.firmware_path.text()
        cfg["sdk_path"] = self.sdk_path.text()
        cfg["arduino_path"] = self.arduino_path.text()
        cfg["esp32_tools"] = self.esp32_tools.text()

        cfg.setdefault("github", {})
        cfg["github"]["token"] = self.github_token.text()
        cfg["github"]["cache_duration"] = self.cache_duration_spin.value()

        cfg.setdefault("ai_integration", {})
        cfg["ai_integration"]["huggingface_api_key"] = self.hf_api_key.text()
        cfg["ai_integration"]["model_endpoint"] = self.model_endpoint.text()
        cfg["ai_integration"]["local_model_path"] = self.local_model_path.text()

        cfg.setdefault("device", {})
        cfg["device"]["auto_connect"] = self.auto_connect_check.isChecked()
        cfg["device"]["default_baud_rate"] = int(self.baud_rate_combo.currentText())

        self.config.save_config()

    def _reset(self):
        self.config.config = self.config.default_config()
        self.config.save_config()
