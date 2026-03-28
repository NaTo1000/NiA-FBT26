"""FAP builder — v2.0 (scaffolding + FBT integration)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Callable, Optional

try:
    from PyQt6.QtCore import QObject, pyqtSignal, QThread
    _QT = True
except ImportError:
    _QT = False

_FAM_TEMPLATE = """\
App(
    appid="{app_id}",
    name="{name}",
    apptype=FlipperAppType.EXTERNAL,
    entry_point="{entry_point}",
    cdefines=[],
    requires=["gui"],
    stack_size=1 * 1024,
    order=10,
    fap_category="{category}",
)
"""

_MAIN_C_TEMPLATE = """\
#include <furi.h>
#include <gui/gui.h>

int32_t {entry_point}(void* p) {{
    UNUSED(p);
    // TODO: implement application
    return 0;
}}
"""


class FAPBuilder:
    """Build Flipper Application Packages."""

    def __init__(self, config):
        self.config = config
        self.firmware_path = Path(config.get("firmware_path", "~/flipper-firmware")).expanduser()

    # ------------------------------------------------------------------

    def scaffold(
        self,
        app_id: str,
        name: str,
        category: str,
        entry_point: str,
        output_dir: Optional[Path] = None,
    ) -> Path:
        """Create a minimal FAP project directory."""
        dest = (output_dir or Path.cwd() / "projects") / app_id
        dest.mkdir(parents=True, exist_ok=True)

        (dest / "application.fam").write_text(
            _FAM_TEMPLATE.format(
                app_id=app_id,
                name=name,
                entry_point=entry_point,
                category=category,
            ),
            encoding="utf-8",
        )
        (dest / "main.c").write_text(
            _MAIN_C_TEMPLATE.format(entry_point=entry_point),
            encoding="utf-8",
        )
        return dest

    def build(
        self,
        project_path: Path,
        on_output: Optional[Callable[[str], None]] = None,
    ) -> bool:
        """Run FBT to compile the FAP."""
        fbt = self.firmware_path / "fbt"
        if not fbt.exists():
            _emit(on_output, "FBT not found — check firmware_path in settings.")
            return False
        cmd = [str(fbt), "fap_dist", f"APPSRC={project_path.name}"]
        return _run(cmd, cwd=self.firmware_path, on_output=on_output)

    def deploy(
        self,
        project_path: Path,
        on_output: Optional[Callable[[str], None]] = None,
    ) -> bool:
        """Deploy the built FAP to a connected Flipper Zero."""
        fbt = self.firmware_path / "fbt"
        if not fbt.exists():
            _emit(on_output, "FBT not found — check firmware_path in settings.")
            return False
        cmd = [str(fbt), "fap_deploy", f"APPSRC={project_path.name}"]
        return _run(cmd, cwd=self.firmware_path, on_output=on_output)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _emit(cb: Optional[Callable[[str], None]], msg: str):
    if cb:
        cb(msg)


def _run(
    cmd: list[str],
    cwd: Path,
    on_output: Optional[Callable[[str], None]] = None,
) -> bool:
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd),
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
