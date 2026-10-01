cmake_minimum_required(VERSION 3.16)
project(NiA-FBT26 VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

# Find Qt6
find_package(Qt6 REQUIRED COMPONENTS Widgets Core Gui Network SerialPort)

include(CTest)

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
    src/gui/werewolf_widget.cpp
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
    include/gui/werewolf_widget.h
)

add_library(werewolf-domain STATIC
    src/werewolf/werewolf.cpp
    include/werewolf/werewolf.h
)
target_include_directories(werewolf-domain PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_link_libraries(werewolf-domain PUBLIC Qt6::Core)

add_executable(nia-werewolf src/werewolf/cli_main.cpp)
target_link_libraries(nia-werewolf PRIVATE werewolf-domain Qt6::Core)

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
    Qt6::SerialPort
    werewolf-domain
)

if(BUILD_TESTING)
    find_package(Qt6 REQUIRED COMPONENTS Test)
    add_executable(werewolf-tests tests/werewolf_tests.cpp)
    target_link_libraries(werewolf-tests PRIVATE werewolf-domain Qt6::Test)
    target_compile_definitions(werewolf-tests PRIVATE
        WEREWOLF_FIXTURE_DIR="${CMAKE_CURRENT_SOURCE_DIR}/tests/fixtures"
        WEREWOLF_CLI_PATH="$<TARGET_FILE:nia-werewolf>"
    )
    add_dependencies(werewolf-tests nia-werewolf)
    add_test(NAME werewolf-tests COMMAND werewolf-tests)

    add_executable(werewolf-gui-smoke tests/werewolf_gui_smoke.cpp)
    target_link_libraries(werewolf-gui-smoke PRIVATE
        werewolf-domain Qt6::Widgets Qt6::Test
    )
    target_sources(werewolf-gui-smoke PRIVATE
        src/gui/werewolf_widget.cpp include/gui/werewolf_widget.h
    )
    add_test(NAME werewolf-gui-smoke COMMAND werewolf-gui-smoke)
    set_tests_properties(werewolf-gui-smoke PROPERTIES ENVIRONMENT "QT_QPA_PLATFORM=offscreen")
endif()

# Installation
install(TARGETS ${PROJECT_NAME} nia-werewolf RUNTIME DESTINATION bin)
