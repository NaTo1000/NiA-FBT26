"""Firmware builder — v2.0 (clone, patch, build, flash)."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable, Optional

FIRMWARE_SOURCES: dict[str, str] = {
    "Official": "https://github.com/flipperdevices/flipperzero-firmware.git",
    "Unleashed": "https://github.com/DarkFlippers/unleashed-firmware.git",
    "RogueMaster": "https://github.com/RogueMaster/flipperzero-firmware-wPlugins.git",
}


class FirmwareBuilder:
    """Clone, build, and flash Flipper Zero firmware."""

    def __init__(self, config):
        self.config = config
        self.firmware_path = Path(config.get("firmware_path", "~/flipper-firmware")).expanduser()

    # ------------------------------------------------------------------

    def clone(
        self,
        source: str,
        custom_url: Optional[str] = None,
        on_output: Optional[Callable[[str], None]] = None,
    ) -> bool:
        """Clone the firmware source repository."""
        url = custom_url if source == "Custom URL" else FIRMWARE_SOURCES.get(source, "")
        if not url:
            _emit(on_output, f"Unknown firmware source: {source}")
            return False
        _emit(on_output, f"Cloning {url} …")
        if self.firmware_path.exists():
            _emit(on_output, f"Destination {self.firmware_path} already exists — skipping clone.")
            return True
        return _run(
            ["git", "clone", "--depth=1", url, str(self.firmware_path)],
            on_output=on_output,
        )

    def build(
        self,
        optimization: str = "size",
        debug: bool = False,
        on_output: Optional[Callable[[str], None]] = None,
    ) -> bool:
        """Build the firmware using FBT."""
        fbt = self.firmware_path / "fbt"
        if not fbt.exists():
            _emit(on_output, "FBT not found — clone the firmware first.")
            return False
        flags = [f"FIRMWARE_OPTIMIZE_FOR_{optimization.upper()}=1"]
        if debug:
            flags.append("DEBUG=1")
        cmd = [str(fbt)] + flags
        return _run(cmd, cwd=self.firmware_path, on_output=on_output)

    def flash(
        self,
        on_output: Optional[Callable[[str], None]] = None,
    ) -> bool:
        """Flash firmware to a connected Flipper Zero via FBT."""
        fbt = self.firmware_path / "fbt"
        if not fbt.exists():
            _emit(on_output, "FBT not found — build the firmware first.")
            return False
        return _run([str(fbt), "flash_usb_full"], cwd=self.firmware_path, on_output=on_output)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _emit(cb: Optional[Callable[[str], None]], msg: str):
    if cb:
        cb(msg)


def _run(
    cmd: list[str],
    cwd: Optional[Path] = None,
    on_output: Optional[Callable[[str], None]] = None,
) -> bool:
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd) if cwd else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        for line in proc.stdout:  # type: ignore[union-attr]
            _emit(on_output, line.rstrip())
        proc.wait()
        return proc.returncode == 0
    except Exception as exc:
        _emit(on_output, f"Build error: {exc}")
        return False
