# NiA FBT26 - C++ Port

This is the C++ rewrite of NiA FBT26 using Qt6, providing native performance and cross-platform compatibility. It also builds the clean-room native Werewolf defensive simulation described in [the integration guide](../docs/werewolf-integration.md).

## Requirements

- CMake 3.16+
- Qt6 (Widgets, Core, Gui, Network, SerialPort)
- C++17 compatible compiler
  - GCC 9+
  - Clang 10+
  - MSVC 2019+

## Building

### Linux / macOS

```bash
cd cpp
mkdir build && cd build
cmake -S . -B build -DBUILD_TESTING=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

### Windows (Visual Studio)

```powershell
cmake -S cpp -B cpp/build -G "Visual Studio 17 2022" -DBUILD_TESTING=ON
cmake --build cpp/build --config Release
ctest --test-dir cpp/build -C Release --output-on-failure
cmake --install cpp/build --config Release --prefix cpp/install
```

### Windows (MinGW)

```bash
cmake -S cpp -B cpp/build -G "MinGW Makefiles" -DBUILD_TESTING=ON
cmake --build cpp/build
ctest --test-dir cpp/build --output-on-failure
cmake --install cpp/build --prefix cpp/install
```

## Project Structure

```
cpp/
├── CMakeLists.txt           # Build configuration
├── include/
│   ├── core/
│   │   ├── config_manager.h
│   │   └── device_manager.h
│   ├── werewolf/
│   │   └── werewolf.h
│   └── gui/
│       ├── main_window.h
│       ├── fap_builder_widget.h
│       ├── firmware_builder_widget.h
│       ├── arduino_panel_widget.h
│       ├── terminal_widget.h
│       ├── github_search_widget.h
│       └── werewolf_widget.h
└── src/
    ├── main.cpp
    ├── core/
    │   ├── config_manager.cpp
    │   └── device_manager.cpp
    ├── werewolf/
    │   ├── werewolf.cpp
    │   └── cli_main.cpp
    └── gui/
        ├── main_window.cpp
        ├── fap_builder_widget.cpp
        ├── firmware_builder_widget.cpp
        ├── arduino_panel_widget.cpp
        ├── terminal_widget.cpp
        ├── github_search_widget.cpp
        └── werewolf_widget.cpp
```

## Features

- **FAP Builder**: Create and compile Flipper Application Packages
- **Firmware Builder**: Build and customize Flipper Zero firmware
- **Arduino/ESP32 Panel**: Compile and upload sketches to ESP32 modules
- **Terminal**: Integrated command-line interface
- **GitHub Search**: Search and browse Flipper Zero repositories
- **Defensive Simulation**: Strict local Werewolf + Sasquach dry-run with no hardware, network, serial, firmware, retaliation, or OS policy action

## Werewolf CLI

Both `NiA-FBT26` and `nia-werewolf` are installed to `bin`.

```powershell
.\cpp\build\Release\nia-werewolf.exe check
.\cpp\build\Release\nia-werewolf.exe run .\cpp\tests\fixtures\golden-scenario-v1.json
.\cpp\build\Release\nia-werewolf.exe report .\scenario.json --output .\report.json
```

The CLI emits JSON and returns `0` for success, `2` for input/contract rejection,
and `3` for report write failure. Reports use `QSaveFile` atomic replacement.
The simulation verifier is not production authentication. Local isolation is
recorded only; no containment is executed.

## Dependencies Installation

### Ubuntu/Debian

```bash
sudo apt install qt6-base-dev qt6-serialport-dev cmake build-essential
```

### Fedora

```bash
sudo dnf install qt6-qtbase-devel qt6-qtserialport-devel cmake gcc-c++
```

### macOS (Homebrew)

```bash
brew install qt6 cmake
```

### Windows

Download and install Qt6 from https://www.qt.io/download

## License

MIT License - See LICENSE file for details
