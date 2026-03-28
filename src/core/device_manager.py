"""Device manager — v2.0 (USB/serial detection, Qt signals)."""

from __future__ import annotations

from typing import Optional

try:
    from PyQt6.QtCore import QObject, pyqtSignal
    _QT = True
except ImportError:
    _QT = False

_FLIPPER_VID = 0x0483  # STMicroelectronics — Flipper Zero uses an STM32 MCU
_FLIPPER_PID = 0x5740  # Flipper Zero CDC ACM (virtual serial over USB)


if _QT:
    class DeviceManager(QObject):
        """Detect and communicate with a connected Flipper Zero device."""

        device_connected = pyqtSignal(dict)
        device_disconnected = pyqtSignal()

        def __init__(self, parent=None):
            super().__init__(parent)
            self.device: Optional[object] = None
            self.port: Optional[str] = None
            self.connected: bool = False
            self._info: dict = {}

        # --------------------------------------------------------------

        def list_ports(self) -> list[str]:
            """Return all available serial ports."""
            try:
                import serial.tools.list_ports as lp
                return [p.device for p in lp.comports()]
            except Exception:
                return []

        def find_flipper_port(self) -> Optional[str]:
            """Return the serial port of the first connected Flipper Zero."""
            try:
                import serial.tools.list_ports as lp
                for p in lp.comports():
                    if p.vid == _FLIPPER_VID and p.pid == _FLIPPER_PID:
                        return p.device
            except Exception:
                pass
            return None

        def connect(self, port: Optional[str] = None) -> bool:
            """Connect to a Flipper Zero (auto-detect if port is None)."""
            target = port or self.find_flipper_port()
            if not target:
                return False
            try:
                import serial
                self.device = serial.Serial(target, baudrate=115200, timeout=1)
                self.port = target
                self.connected = True
                self._info = {"port": target}
                self.device_connected.emit(self._info)
                return True
            except Exception:
                self.connected = False
                return False

        def disconnect(self):
            """Disconnect from the device."""
            if self.device:
                try:
                    self.device.close()
                except Exception:
                    pass
            self.device = None
            self.port = None
            self.connected = False
            self._info = {}
            self.device_disconnected.emit()

        def flash_firmware(self, firmware_path: str):
            """Flash firmware to the connected device (placeholder)."""
            pass

        def get_info(self) -> dict:
            """Return cached device info."""
            return dict(self._info)

else:
    class DeviceManager:  # type: ignore[no-redef]
        """Fallback (no Qt) device manager."""

        def __init__(self):
            self.device = None
            self.port = None
            self.connected = False

        def connect(self, port=None) -> bool:
            self.connected = True
            return True

        def disconnect(self):
            self.connected = False

        def flash_firmware(self, firmware_path: str):
            pass

        def get_info(self) -> dict:
            return {}

