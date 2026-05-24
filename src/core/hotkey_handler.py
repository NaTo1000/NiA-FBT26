"""
HotkeyHandler — Qt global hotkey registration for NiA FBT26.

Registers a ``QShortcut`` on the main window using the hotkey defined in
``config/settings.json`` (default: Ctrl+Shift+A) and emits a
``heal_triggered`` signal when the key combination is pressed from anywhere
inside the application.
"""

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QKeySequence
from PyQt6.QtWidgets import QShortcut


DEFAULT_HOTKEY = "Ctrl+Shift+A"


class HotkeyHandler(QObject):
    """
    Registers a global (window-level) shortcut and exposes a signal that
    other components can connect to.

    Parameters
    ----------
    parent_window : QMainWindow
        The main application window to attach the shortcut to.
    hotkey : str, optional
        Key sequence string (e.g. ``"Ctrl+Shift+A"``).  If *None* the value
        is read from *config* under ``healing.hotkey``, falling back to
        ``DEFAULT_HOTKEY``.
    config : dict, optional
        Application configuration dictionary (from ConfigManager).
    """

    heal_triggered = pyqtSignal()

    def __init__(self, parent_window, hotkey: str = None, config: dict = None,
                 parent: QObject = None):
        super().__init__(parent)
        self._window = parent_window

        if hotkey is None:
            cfg = config or {}
            hotkey = cfg.get("healing", {}).get("hotkey", DEFAULT_HOTKEY)

        self._hotkey_str = hotkey
        self._shortcut = self._register(hotkey)

    def _register(self, hotkey: str) -> QShortcut:
        """Create and return a QShortcut bound to the main window."""
        shortcut = QShortcut(QKeySequence(hotkey), self._window)
        shortcut.activated.connect(self.heal_triggered)
        return shortcut

    @property
    def hotkey(self) -> str:
        """The registered key-sequence string."""
        return self._hotkey_str
