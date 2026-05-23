cmake_minimum_required(VERSION 3.16)
project(NiA-FBT26 VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

# Find Qt6
find_package(Qt6 REQUIRED COMPONENTS Widgets Core Gui Network)

# Include directories
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)

# Source files
set(CORE_SOURCES
    src/core/config_manager.cpp
    src/core/device_manager.cpp
)

set(GUI_SOURCES
    src/gui/main_window.cpp
    src/gui/fap_builder_widget.cpp
    src/gui/firmware_builder_widget.cpp
    src/gui/arduino_panel_widget.cpp
    src/gui/terminal_widget.cpp
    src/gui/github_search_widget.cpp
)

set(HEADER_FILES
    include/core/config_manager.h
    include/core/device_manager.h
    include/gui/main_window.h
    include/gui/fap_builder_widget.h
    include/gui/firmware_builder_widget.h
    include/gui/arduino_panel_widget.h
    include/gui/terminal_widget.h
    include/gui/github_search_widget.h
)

# Main executable
add_executable(${PROJECT_NAME}
    src/main.cpp
    ${CORE_SOURCES}
    ${GUI_SOURCES}
    ${HEADER_FILES}
)

target_link_libraries(${PROJECT_NAME} PRIVATE
    Qt6::Widgets
    Qt6::Core
    Qt6::Gui
    Qt6::Network
)

# Installation
install(TARGETS ${PROJECT_NAME} DESTINATION bin)
