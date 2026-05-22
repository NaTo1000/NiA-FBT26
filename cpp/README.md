# NiA FBT26 - C++ Port

This is the C++ rewrite of NiA FBT26 using Qt6, providing native performance and cross-platform compatibility.

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
cmake ..
make -j$(nproc)
```

### Windows (Visual Studio)

```powershell
cd cpp
mkdir build
cd build
cmake -G "Visual Studio 17 2022" ..
cmake --build . --config Release
```

### Windows (MinGW)

```bash
cd cpp
mkdir build && cd build
cmake -G "MinGW Makefiles" ..
mingw32-make
```

## Project Structure

```
cpp/
├── CMakeLists.txt           # Build configuration
├── include/
│   ├── core/
│   │   ├── config_manager.h
│   │   └── device_manager.h
│   └── gui/
│       ├── main_window.h
│       ├── fap_builder_widget.h
│       ├── firmware_builder_widget.h
│       ├── arduino_panel_widget.h
│       ├── terminal_widget.h
│       └── github_search_widget.h
└── src/
    ├── main.cpp
    ├── core/
    │   ├── config_manager.cpp
    │   └── device_manager.cpp
    └── gui/
        ├── main_window.cpp
        ├── fap_builder_widget.cpp
        ├── firmware_builder_widget.cpp
        ├── arduino_panel_widget.cpp
        ├── terminal_widget.cpp
        └── github_search_widget.cpp
```

## Features

- **FAP Builder**: Create and compile Flipper Application Packages
- **Firmware Builder**: Build and customize Flipper Zero firmware
- **Arduino/ESP32 Panel**: Compile and upload sketches to ESP32 modules
- **Terminal**: Integrated command-line interface
- **GitHub Search**: Search and browse Flipper Zero repositories

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
