/**
 * NiA FBT26 - Advanced Flipper Zero Development Suite
 * Main Application Entry Point
 * 
 * C++ Port from Python/PyQt6
 */

#include <QApplication>
#include <QStyleFactory>

#include "core/config_manager.h"
#include "core/device_manager.h"
#include "gui/main_window.h"

constexpr const char* APP_VERSION = "1.0.0";
constexpr const char* APP_AUTHOR = "NaTo1000";

int main(int argc, char *argv[])
{
    // Enable high DPI scaling
    QApplication::setHighDpiScaleFactorRoundingPolicy(
        Qt::HighDpiScaleFactorRoundingPolicy::PassThrough);
    
    // Create application
    QApplication app(argc, argv);
    app.setApplicationName("NiA FBT26");
    app.setApplicationVersion(APP_VERSION);
    app.setOrganizationName(APP_AUTHOR);
    
    // Apply Fusion style for consistent look
    app.setStyle(QStyleFactory::create("Fusion"));
    
    // Initialize configuration manager
    ConfigManager config;
    
    // Initialize device manager
    DeviceManager deviceManager;
    
    // Create and show main window
    MainWindow window(&config, &deviceManager);
    window.show();
    
    return app.exec();
}
