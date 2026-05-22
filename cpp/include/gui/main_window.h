#ifndef MAIN_WINDOW_H
#define MAIN_WINDOW_H

#include <QMainWindow>
#include <QTabWidget>
#include <QMenuBar>
#include <QToolBar>
#include <QStatusBar>

class ConfigManager;
class DeviceManager;
class FAPBuilderWidget;
class FirmwareBuilderWidget;
class ArduinoPanelWidget;
class TerminalWidget;
class GitHubSearchWidget;

/**
 * @brief Main application window with all development tools
 */
class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    explicit MainWindow(ConfigManager* config, DeviceManager* deviceManager, 
                        QWidget* parent = nullptr);
    ~MainWindow() override = default;

private slots:
    void newProject();
    void openProject();
    void connectDevice();
    void disconnectDevice();
    void flashFirmware();
    void buildProject();
    void showSettings();
    void onConnectionChanged(bool connected);

private:
    void initUI();
    void createMenus();
    void createToolbar();
    void setupConnections();

    ConfigManager* m_config;
    DeviceManager* m_deviceManager;
    
    QTabWidget* m_tabs;
    FAPBuilderWidget* m_fapBuilder;
    FirmwareBuilderWidget* m_firmwareBuilder;
    ArduinoPanelWidget* m_arduinoPanel;
    TerminalWidget* m_terminal;
    GitHubSearchWidget* m_githubSearch;
};

#endif // MAIN_WINDOW_H
