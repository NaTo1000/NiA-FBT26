#!/usr/bin/env python3
"""
NiA FBT26 - Advanced Flipper Zero Development Suite
Main Application Entry Point
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

__version__ = "1.0.0"
__author__ = "NaTo1000"


def parse_args(argv=None):
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="nia-fbt26",
        description="NiA FBT26 — Advanced Flipper Zero Development Suite",
    )
    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--config",
        metavar="FILE",
        default="config/runtime.json",
        help="Path to runtime config JSON (default: config/runtime.json)",
    )
    parser.add_argument(
        "--settings",
        metavar="FILE",
        default="config/settings.json",
        help="Path to settings JSON (default: config/settings.json)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Override server port (env: NIA_SERVER_PORT)",
    )
    parser.add_argument(
        "--host",
        default=None,
        help="Override server host (env: NIA_SERVER_HOST)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=None,
        help="Set log level (env: NIA_LOG_LEVEL)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=None,
        help="Enable debug mode (env: NIA_DEBUG)",
    )
    parser.add_argument(
        "--env",
        choices=["production", "development", "staging"],
        default=None,
        help="Runtime environment (env: NIA_ENV)",
    )
    parser.add_argument(
        "--no-gui",
        action="store_true",
        default=False,
        help="Run in headless/server mode without GUI",
    )
    return parser.parse_args(argv)


def apply_env_overrides(runtime_cfg):
    """Apply environment variable overrides to runtime config."""
    env_map = {
        "NIA_LOG_LEVEL":    ("runtime", "log_level"),
        "NIA_DEBUG":        ("runtime", "debug"),
        "NIA_ENV":          ("runtime", "environment"),
        "NIA_SERVER_PORT":  ("server",  "port"),
        "NIA_SERVER_HOST":  ("server",  "host"),
        "NIA_BUILD_JOBS":   ("build",   "parallel_jobs"),
    }
    for env_var, (section, key) in env_map.items():
        value = os.environ.get(env_var)
        if value is None:
            continue
        if key in ("debug",) or value.lower() in ("true", "false"):
            value = value.lower() == "true"
        elif key in ("port", "parallel_jobs"):
            try:
                value = int(value)
            except ValueError:
                pass
        if section in runtime_cfg:
            runtime_cfg[section][key] = value
    return runtime_cfg


def setup_logging(log_level="INFO"):
    """Configure logging based on runtime parameters."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def load_runtime_config(config_path):
    """Load runtime.json, returning an empty dict on failure."""
    try:
        with open(config_path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        logging.warning("Could not load runtime config %s: %s", config_path, exc)
        return {}


def main(argv=None):
    """Main entry point for NiA FBT26."""
    args = parse_args(argv)

    # Load and override runtime config
    runtime_cfg = load_runtime_config(args.config)
    runtime_cfg = apply_env_overrides(runtime_cfg)

    # CLI args take highest precedence
    if args.log_level:
        runtime_cfg.setdefault("runtime", {})["log_level"] = args.log_level
    if args.debug:
        runtime_cfg.setdefault("runtime", {})["debug"] = True
    if args.env:
        runtime_cfg.setdefault("runtime", {})["environment"] = args.env
    if args.port:
        runtime_cfg.setdefault("server", {})["port"] = args.port
    if args.host:
        runtime_cfg.setdefault("server", {})["host"] = args.host

    log_level = runtime_cfg.get("runtime", {}).get("log_level", "INFO")
    setup_logging(log_level)

    logger = logging.getLogger("nia_fbt26")
    logger.info("NiA FBT26 v%s starting", __version__)
    logger.debug("Runtime config: %s", runtime_cfg)

    if args.no_gui:
        logger.info("Headless mode — GUI disabled")
        return 0

    # Launch GUI
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        from gui.main_window import MainWindow
        from core.config_manager import ConfigManager
        from core.device_manager import DeviceManager

        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

        app = QApplication(sys.argv)
        app.setApplicationName("NiA FBT26")
        app.setApplicationVersion(__version__)
        app.setOrganizationName("NaTo1000")

        config = ConfigManager()
        device_manager = DeviceManager()

        window = MainWindow(config, device_manager)
        window.show()

        return app.exec()
    except ImportError as exc:
        logger.error("GUI dependencies not available: %s", exc)
        logger.error("Install with: pip install PyQt6 PyQt6-WebEngine")
        return 1


if __name__ == "__main__":
    sys.exit(main())
