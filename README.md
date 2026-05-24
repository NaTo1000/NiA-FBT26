# NiA FBT26 v2.0 — Flipper Zero Development Suite

![CI](https://github.com/NaTo1000/NiA-FBT26/actions/workflows/ci.yml/badge.svg)
![Docker](https://ghcr.io/nato1000/nia-fbt26)
**Version**: 2.0.0 | **Platform**: macOS, Linux, Windows | **Author**: NaTo1000

---

## 🚀 Overview

NiA FBT26 is a modern, all-in-one development environment for the Flipper Zero. v2.0 brings a complete GUI rewrite, upgraded dependencies, Docker support, and a full CI/CD pipeline.

---

## ✨ Features

| Panel | Description |
|---|---|
| 🏠 **Dashboard** | Device status card, quick actions, recent projects, system health |
| 📱 **FAP Builder** | Project wizard, C code editor, one-click build & deploy |
| ⚡ **Firmware Builder** | Official / Unleashed / RogueMaster sources, build config, flash |
| 🔧 **Arduino/ESP32** | Board selector, sketch editor, compile/upload, serial monitor |
| 💻 **Terminal** | Multi-tab terminal with command history and Flipper CLI |
| 🔍 **GitHub Search** | Search Flipper apps/firmware, one-click download |
| 📟 **Device Manager** | Auto-detect Flipper, SD card file browser |
| ⚙️ **Settings** | Theme, editor prefs, paths, GitHub token, AI integration hooks |

---

## 📋 Requirements

- Python **3.11+**
- Git, curl
- (Optional) ARM GCC toolchain for firmware building

---

## 🚀 Installation

### From Source (recommended)

```bash
git clone https://github.com/NaTo1000/NiA-FBT26.git
cd NiA-FBT26
./setup.sh
./nia-fbt26
```

### pip

```bash
pip install -r requirements.txt
python3 src/main.py
```

### Docker

```bash
docker pull ghcr.io/nato1000/nia-fbt26:latest
# GUI apps require a display — use X11 forwarding or VNC
docker run -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix \
    ghcr.io/nato1000/nia-fbt26:latest
```

---

## 🔧 Configuration

Edit `config/settings.json` (auto-created on first run):

```json
{
  "version": "2.0.0",
  "firmware_path": "~/flipper-firmware",
  "sdk_path": "~/flipper-sdk",
  "editor": { "theme": "monokai", "font_size": 12, "tab_size": 4 },
  "build": { "parallel_jobs": 4, "optimization": "size", "debug": true },
  "github": { "token": "", "cache_duration": 3600 },
  "ai_integration": {
    "huggingface_api_key": "",
    "model_endpoint": "",
    "local_model_path": ""
  },
  "device": { "auto_connect": true, "default_baud_rate": 115200 }
}
```

Environment variable overrides (via `.env` or shell):

| Variable | Config field |
|---|---|
| `NIA_GITHUB_TOKEN` | `github.token` |
| `NIA_HF_API_KEY` | `ai_integration.huggingface_api_key` |
| `NIA_MODEL_ENDPOINT` | `ai_integration.model_endpoint` |
| `NIA_LOCAL_MODEL_PATH` | `ai_integration.local_model_path` |

---

## 🏗️ Project Structure

```
NiA-FBT26/
├── src/
│   ├── main.py                  # Entry point (v2.0.0)
│   ├── gui/
│   │   ├── main_window.py       # Modern tabbed QMainWindow
│   │   ├── dashboard.py         # Home dashboard
│   │   ├── fap_builder.py       # FAP project wizard & editor
│   │   ├── firmware_builder.py  # Firmware source & build
│   │   ├── arduino_panel.py     # Arduino/ESP32 editor
│   │   ├── terminal_widget.py   # Multi-tab terminal emulator
│   │   ├── github_search.py     # GitHub search & download
│   │   ├── device_manager.py    # USB device manager
│   │   └── settings_widget.py   # Settings UI
│   ├── core/
│   │   ├── config_manager.py    # JSON config + env overrides
│   │   └── device_manager.py    # USB/serial detection, Qt signals
│   └── builders/
│       ├── fap_builder.py       # FAP scaffolding + FBT integration
│       └── firmware_builder.py  # Firmware clone/build/flash
├── config/
│   └── settings.json            # Default settings
├── .github/
│   └── workflows/
│       └── ci.yml               # lint + test + docker-build
├── Dockerfile
├── .dockerignore
├── requirements.txt
├── package.json
├── setup.sh
└── README.md
```

---

## 🔄 v2.0 Changelog

- **Full GUI rewrite** — modern dark-themed dashboard with 8 tabs
- **Dependencies** — all packages upgraded to latest 2026 versions
- **New deps** — grpcio, confluent-kafka, redis, pydantic, aiohttp, python-dotenv
- **Bug fix** — removed deprecated `AA_EnableHighDpiScaling` / `AA_UseHighDpiPixmaps` (Qt5 compat flags removed in Qt6 6.5+)
- **Config manager** — Pydantic validation, env-var overrides, config versioning
- **Device manager** — pyserial/pyusb detection, Qt signals for connect/disconnect
- **FAP builder** — project scaffolding, FBT integration, deploy button
- **Firmware builder** — Official/Unleashed/RogueMaster source selector, progress log
- **New widgets** — Device Manager tab, Settings tab with AI integration hooks
- **Docker** — `Dockerfile` + `.dockerignore` for containerised deployments
- **CI/CD** — GitHub Actions: lint → test → docker-build & push to ghcr.io

---

## 🐳 Docker Usage

```bash
# Build locally
docker build -t nia-fbt26 .

# Run (Linux with X11)
docker run --rm -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    nia-fbt26
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m 'feat: add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

Please run `black src/` and `flake8 src/` before submitting.

---

## 📝 License

MIT License — see LICENSE for details.

---

**Built with ❤️ by NaTo1000 for the Flipper Zero Community**


---

## 🚀 Overview

NiA FBT26 is a comprehensive development environment for Flipper Zero that combines the functionality of qFlipper with powerful firmware and FAP development tools. It provides an all-in-one solution for creating, compiling, and deploying Flipper Zero applications.

## ✨ Features

### 📱 Device Management
- **qFlipper-style interface** - Familiar UI for device interaction
- **Firmware flashing** - DFU, .tgz, and .zip support
- **File browser** - Browse and manage SD card files
- **Backup/Restore** - Complete device backup capabilities
- **Serial terminal** - Built-in terminal for debugging

### 🛠️ Development Tools
- **FAP Builder** - Create and compile Flipper applications
- **Firmware Builder** - Assemble custom firmware from components
- **Project Scaffolding** - Quick-start templates for apps
- **Build System Integration** - FBT (Flipper Build Tool) wrapper
- **Code Editor** - Integrated editor with syntax highlighting

### 🔧 Arduino & ESP32 Support
- **Arduino IDE Integration** - Compile Arduino sketches
- **ESP32 Support** - Flash ESP32 modules for WiFi capabilities
- **Library Management** - Install and manage Arduino libraries
- **Board Configuration** - Support for multiple ESP32 boards
- **Serial Monitor** - Monitor ESP32 serial output

### 🐍 Python Development
- **Dedicated Python 3 Environment** - Isolated Python interpreter
- **Script Runner** - Execute Python scripts with FBT
- **Package Manager** - pip integration for dependencies
- **REPL** - Interactive Python shell
- **Flipper API Bindings** - Python wrappers for Flipper tools

### 💻 Terminal Integration
- **Embedded Terminal** - Full-featured terminal in the app
- **FBT Commands** - Direct access to FBT build system
- **Shell Integration** - Run any shell command
- **Command History** - Remember previous commands
- **Output Capture** - Capture and display build output

### 🔍 GitHub Integration
- **Repository Search** - Find Flipper-related repos
- **Code Search** - Search for FAP, DFU, tar.gz files
- **Direct Download** - Clone or download from search results
- **Release Browser** - Browse and download releases
- **Trending Repos** - Discover popular projects

### 📦 File Handlers
- **FAP Parser** - Analyze and extract FAP files
- **DFU Handler** - Work with DFU firmware images
- **Archive Support** - tar.gz, tgz, zip extraction
- **Manifest Editor** - Edit application.fam files
- **Resource Manager** - Manage icons, animations, assets

## 📋 Requirements

### System Requirements
- macOS 10.15+, Linux (Ubuntu 20.04+), or Windows 10+
- 4GB RAM minimum (8GB recommended)
- 10GB free disk space
- USB port for Flipper Zero connection

### Dependencies
- Python 3.8+
- Git
- ARM GCC toolchain
- Arduino IDE (optional, for Arduino support)
- Node.js 16+ (for GUI)

## 🚀 Installation

### Quick Start
```bash
# Clone repository
git clone https://github.com/NaTo1000/NiA-FBT26.git
cd NiA-FBT26

# Run setup script
./setup.sh

# Launch application
./nia-fbt26
```

### Manual Installation
```bash
# Install Python dependencies
pip3 install -r requirements.txt

# Install Node.js dependencies
npm install

# Install Arduino CLI (optional)
./scripts/install_arduino_cli.sh

# Build application
npm run build

# Run
npm start
```

## 📖 Usage Guide

### Creating a New FAP

1. **Launch NiA FBT26**
2. **Click "New Project"** → "FAP Application"
3. **Fill in details**:
   - App ID: `my_app`
   - Name: "My Application"
   - Category: Tools, Games, etc.
4. **Project scaffolding** automatically created
5. **Edit code** in integrated editor
6. **Build** → Compile FAP
7. **Deploy** → Copy to Flipper Zero

### Building Custom Firmware

1. **Firmware Builder** → "New Firmware"
2. **Select base**: Unleashed, Xtreme, Momentum, or Official
3. **Add applications**:
   - Drag and drop FAPs
   - Select from catalog
   - Add custom apps
4. **Configure options**:
   - Auto-start app
   - Debug settings
   - Optimization level
5. **Build firmware** → Generates DFU/tgz
6. **Flash** → Deploy to device

### Arduino & ESP32 Development

1. **Arduino Builder** tab
2. **Select board type**:
   - ESP32 Dev Module
   - ESP32-S2
   - ESP32-C3
3. **Write or import sketch**
4. **Configure pins** for Flipper connection
5. **Compile and upload** to ESP32
6. **Test** with built-in serial monitor

### GitHub Repository Search

1. **GitHub Search** tab
2. **Enter search terms**:
   - "flipper fap"
   - "flipper zero dfu"
   - "flipper firmware"
3. **Filter results**:
   - Stars, forks, recent updates
   - Has releases
   - File types (FAP, DFU, tar.gz)
4. **Download** → Clone or get release assets

## 🏗️ Project Structure

```
NiA-FBT26/
├── src/
│   ├── gui/                # GUI components
│   │   ├── main_window.py  # Main application window
│   │   ├── fap_builder.py  # FAP creation interface
│   │   ├── firmware_builder.py
│   │   ├── arduino_panel.py
│   │   ├── terminal_widget.py
│   │   └── github_search.py
│   ├── core/               # Core functionality
│   │   ├── device_manager.py
│   │   ├── fbt_wrapper.py
│   │   ├── project_manager.py
│   │   └── config_manager.py
│   ├── builders/           # Build systems
│   │   ├── fap_compiler.py
│   │   ├── firmware_assembler.py
│   │   └── fbt_integration.py
│   ├── tools/              # Development tools
│   │   ├── code_editor.py
│   │   ├── manifest_editor.py
│   │   └── resource_manager.py
│   ├── arduino/            # Arduino support
│   │   ├── arduino_cli.py
│   │   ├── esp32_flasher.py
│   │   └── serial_monitor.py
│   ├── esp32/              # ESP32 specific
│   │   ├── board_manager.py
│   │   ├── wifi_tools.py
│   │   └── pin_mapper.py
│   ├── terminal/           # Terminal integration
│   │   ├── embedded_terminal.py
│   │   ├── command_runner.py
│   │   └── output_parser.py
│   ├── github_search/      # GitHub integration
│   │   ├── repo_search.py
│   │   ├── code_search.py
│   │   ├── release_manager.py
│   │   └── download_handler.py
│   └── file_handlers/      # File format handlers
│       ├── fap_parser.py
│       ├── dfu_handler.py
│       ├── archive_handler.py
│       └── manifest_parser.py
├── config/                 # Configuration
│   ├── settings.json
│   ├── boards.json        # Arduino/ESP32 boards
│   └── templates.json
├── templates/              # Project templates
│   ├── fap_basic/
│   ├── fap_advanced/
│   ├── game_template/
│   ├── tool_template/
│   └── esp32_template/
├── examples/               # Example projects
│   ├── hello_world/
│   ├── gpio_reader/
│   └── esp32_wifi/
├── docs/                   # Documentation
│   ├── user_guide.md
│   ├── api_reference.md
│   ├── fap_development.md
│   └── arduino_integration.md
├── assets/                 # UI assets
│   └── icons/
├── scripts/                # Utility scripts
│   ├── setup.sh
│   ├── install_arduino_cli.sh
│   └── download_toolchain.sh
├── requirements.txt        # Python dependencies
├── package.json           # Node.js dependencies
└── nia-fbt26              # Launch script
```

## 🔧 Configuration

### Settings File (`config/settings.json`)
```json
{
  "firmware_path": "~/flipper-firmware",
  "sdk_path": "~/flipper-sdk",
  "arduino_path": "~/Arduino",
  "esp32_tools": "~/.platformio",
  "python_env": ".venv",
  "editor": {
    "theme": "monokai",
    "font_size": 12,
    "tab_size": 4
  },
  "build": {
    "parallel_jobs": 4,
    "optimization": "size",
    "debug": true
  },
  "github": {
    "token": "",
    "cache_duration": 3600
  }
}
```

## 🐍 Python API

```python
from nia_fbt26 import FBT, FAP, Firmware

# Create FAP project
fap = FAP.create(
    app_id="my_app",
    name="My Application",
    entry_point="my_app_main",
    category="Tools"
)

# Add source files
fap.add_source("main.c")
fap.add_source("utils.c")

# Build
fap.compile()

# Deploy to device
fap.deploy()

# Build custom firmware
firmware = Firmware(base="unleashed")
firmware.add_app(fap)
firmware.set_autostart("my_app")
firmware.build()
firmware.flash()
```

## 💻 Terminal Commands

```bash
# Build FAP
nia-fbt build-fap --app my_app

# Build firmware
nia-fbt build-firmware --base unleashed --apps my_app,another_app

# Flash firmware
nia-fbt flash --firmware custom.dfu

# Search GitHub
nia-fbt github-search "flipper fap games"

# Download release
nia-fbt download-release RogueMaster/flipperzero-firmware-wPlugins

# Arduino compile
nia-fbt arduino-compile --board esp32 --sketch wifi_marauder.ino

# ESP32 flash
nia-fbt esp32-flash --port /dev/ttyUSB0 --firmware esp32.bin
```

## 🔌 Plugin System

Create custom plugins:

```python
# plugins/my_plugin.py
from nia_fbt26.plugin import Plugin

class MyPlugin(Plugin):
    name = "My Custom Tool"
    version = "1.0.0"
    
    def on_load(self):
        self.add_menu_item("Tools", "My Tool", self.run)
    
    def run(self):
        # Plugin logic
        pass
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- **Flipper Devices** - Original hardware and firmware
- **qFlipper** - Inspiration for device management
- **FBT Team** - Build system tools
- **Community** - All the amazing contributors

## 📞 Support

- **GitHub Issues**: https://github.com/NaTo1000/NiA-FBT26/issues
- **Documentation**: https://nia-fbt26.readthedocs.io
- **Discord**: https://discord.gg/nia-fbt26

## 🗺️ Roadmap

### Version 1.1
- [ ] Visual application designer
- [ ] Animation editor
- [ ] Remote debugging support
- [ ] Cloud project sync

### Version 1.2
- [ ] Collaborative editing
- [ ] Marketplace integration
- [ ] CI/CD pipeline
- [ ] Mobile companion app

### Version 2.0
- [ ] Web-based IDE
- [ ] Plugin marketplace
- [ ] AI-assisted coding
- [ ] Multi-device support

---

**Built with ❤️ by NaTo1000**  
**For the Flipper Zero Community**