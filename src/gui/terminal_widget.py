
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLineEdit, QLabel, QTabWidget, QComboBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent, QFont


class TerminalWidget(QWidget):
    """Full terminal emulator widget — v2.0."""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Multi-tab support
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self._close_tab)

        # Add default terminal tab
        self._add_terminal_tab("Terminal 1")

        btn_row = QHBoxLayout()
        new_tab_btn = QPushButton("＋ New Tab")
        new_tab_btn.clicked.connect(self._new_tab)

        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200", "230400"])
        self.baud_combo.setCurrentText("115200")

        btn_row.addWidget(new_tab_btn)
        btn_row.addWidget(QLabel("Baud:"))
        btn_row.addWidget(self.baud_combo)
        btn_row.addStretch()

        layout.addLayout(btn_row)
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

    # ------------------------------------------------------------------

    def _add_terminal_tab(self, label: str):
        tab = _TerminalTab()
        self.tab_widget.addTab(tab, label)
        self.tab_widget.setCurrentWidget(tab)

    def _new_tab(self):
        count = self.tab_widget.count() + 1
        self._add_terminal_tab(f"Terminal {count}")

    def _close_tab(self, index: int):
        if self.tab_widget.count() > 1:
            self.tab_widget.removeTab(index)


class _TerminalTab(QWidget):
    """Single terminal session pane."""

    def __init__(self):
        super().__init__()
        self._history: list[str] = []
        self._history_idx: int = -1
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        mono = QFont("Monospace")
        mono.setStyleHint(QFont.StyleHint.Monospace)
        self.output.setFont(mono)
        self.output.setStyleSheet("background-color: #11111b; color: #cdd6f4;")
        self.output.append("NiA FBT26 v2.0 — Flipper CLI")
        self.output.append("Type 'help' for available commands.\n")
        layout.addWidget(self.output, stretch=1)

        input_row = QHBoxLayout()
        self.prompt_label = QLabel("flipper> ")
        self.prompt_label.setStyleSheet("color: #a6e3a1; font-family: Monospace;")
        self.cmd_input = _HistoryLineEdit(self._history)
        self.cmd_input.returnPressed.connect(self._run_command)
        self.run_btn = QPushButton("▶")
        self.run_btn.setFixedWidth(36)
        self.run_btn.clicked.connect(self._run_command)

        input_row.addWidget(self.prompt_label)
        input_row.addWidget(self.cmd_input)
        input_row.addWidget(self.run_btn)
        layout.addLayout(input_row)

        self.setLayout(layout)

    def _run_command(self):
        cmd = self.cmd_input.text().strip()
        if not cmd:
            return
        self._history.append(cmd)
        self._history_idx = len(self._history)
        self.output.append(f"<span style='color:#89b4fa'>flipper&gt;</span> {cmd}")
        self.cmd_input.clear()
        # Placeholder response
        self.output.append(f"[{cmd}]: command queued (device not connected)")


class _HistoryLineEdit(QLineEdit):
    """QLineEdit with command history navigation (up/down arrows)."""

    def __init__(self, history: list[str]):
        super().__init__()
        self._history = history
        self._idx = -1

    def keyPressEvent(self, event: QKeyEvent):  # type: ignore[override]
        if event.key() == Qt.Key.Key_Up:
            if self._history:
                self._idx = max(0, len(self._history) - 1 if self._idx < 0 else self._idx - 1)
                self.setText(self._history[self._idx])
        elif event.key() == Qt.Key.Key_Down:
            if self._history and self._idx >= 0:
                self._idx += 1
                if self._idx >= len(self._history):
                    self._idx = -1
                    self.clear()
                else:
                    self.setText(self._history[self._idx])
        else:
            self._idx = -1
            super().keyPressEvent(event)

