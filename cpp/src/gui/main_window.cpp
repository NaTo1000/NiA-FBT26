#include "gui/main_window.h"
#include "gui/fap_builder_widget.h"
#include "gui/firmware_builder_widget.h"
#include "gui/arduino_panel_widget.h"
#include "gui/terminal_widget.h"
#include "gui/github_search_widget.h"
#include "core/config_manager.h"
#include "core/device_manager.h"

#include <QAction>
#include <QMessageBox>
#include <QFileDialog>

MainWindow::MainWindow(ConfigManager* config, DeviceManager* deviceManager, QWidget* parent)
    : QMainWindow(parent)
    , m_config(config)
    , m_deviceManager(deviceManager)
    , m_tabs(nullptr)
    , m_fapBuilder(nullptr)
    , m_firmwareBuilder(nullptr)
    , m_arduinoPanel(nullptr)
    , m_terminal(nullptr)
    , m_githubSearch(nullptr)
{
    setWindowTitle("NiA FBT26 - Flipper Zero Development Suite");
    setGeometry(100, 100, 1400, 900);
    
    initUI();
    setupConnections();
}

void MainWindow::initUI()
{
    createMenus();
    createToolbar();
    
    // Create central widget with tabs
    m_tabs = new QTabWidget(this);
    setCentralWidget(m_tabs);
    
    // Create tab widgets
    m_fapBuilder = new FAPBuilderWidget(m_config, this);
    m_firmwareBuilder = new FirmwareBuilderWidget(m_config, this);
    m_arduinoPanel = new ArduinoPanelWidget(m_config, this);
    m_terminal = new TerminalWidget(m_config, this);
    m_githubSearch = new GitHubSearchWidget(m_config, this);
    
    // Add tabs
    m_tabs->addTab(m_fapBuilder, "FAP Builder");
    m_tabs->addTab(m_firmwareBuilder, "Firmware Builder");
    m_tabs->addTab(m_arduinoPanel, "Arduino/ESP32");
    m_tabs->addTab(m_terminal, "Terminal");
    m_tabs->addTab(m_githubSearch, "GitHub Search");
    
    // Create status bar
    statusBar()->showMessage("Ready");
}

void MainWindow::createMenus()
{
    QMenuBar* menubar = this->menuBar();
    
    // File menu
    QMenu* fileMenu = menubar->addMenu("&File");
    fileMenu->addAction("&New Project", this, &MainWindow::newProject, QKeySequence::New);
    fileMenu->addAction("&Open Project", this, &MainWindow::openProject, QKeySequence::Open);
    fileMenu->addSeparator();
    fileMenu->addAction("E&xit", this, &MainWindow::close, QKeySequence::Quit);
    
    // Device menu
    QMenu* deviceMenu = menubar->addMenu("&Device");
    deviceMenu->addAction("&Connect", this, &MainWindow::connectDevice);
    deviceMenu->addAction("&Disconnect", this, &MainWindow::disconnectDevice);
    deviceMenu->addSeparator();
    deviceMenu->addAction("&Flash Firmware", this, &MainWindow::flashFirmware);
    
    // Tools menu
    QMenu* toolsMenu = menubar->addMenu("&Tools");
    toolsMenu->addAction("&Settings", this, &MainWindow::showSettings);
}

void MainWindow::createToolbar()
{
    QToolBar* toolbar = addToolBar("Main");
    toolbar->setMovable(false);
    
    toolbar->addAction("Connect", this, &MainWindow::connectDevice);
    toolbar->addAction("Build", this, &MainWindow::buildProject);
    toolbar->addAction("Flash", this, &MainWindow::flashFirmware);
}

void MainWindow::setupConnections()
{
    connect(m_deviceManager, &DeviceManager::connectionChanged, 
            this, &MainWindow::onConnectionChanged);
    
    connect(m_deviceManager, &DeviceManager::logMessage, 
            m_terminal, &TerminalWidget::appendLog);
    
    connect(m_deviceManager, &DeviceManager::errorOccurred, 
            [this](const QString& error) {
                statusBar()->showMessage("Error: " + error, 5000);
            });
}

void MainWindow::newProject()
{
    statusBar()->showMessage("Creating new project...");
    // Implementation for new project wizard
}

void MainWindow::openProject()
{
    QString dir = QFileDialog::getExistingDirectory(this, 
        "Open Project Directory",
        QDir::homePath(),
        QFileDialog::ShowDirsOnly);
    
    if (!dir.isEmpty()) {
        statusBar()->showMessage("Opened project: " + dir);
    }
}

void MainWindow::connectDevice()
{
    statusBar()->showMessage("Connecting to device...");
    
    if (m_deviceManager->connect()) {
        statusBar()->showMessage("Connected to " + m_deviceManager->deviceName());
    }
}

void MainWindow::disconnectDevice()
{
    m_deviceManager->disconnect();
    statusBar()->showMessage("Disconnected");
}

void MainWindow::flashFirmware()
{
    if (!m_deviceManager->isConnected()) {
        QMessageBox::warning(this, "Warning", "Please connect a device first");
        return;
    }
    
    QString firmware = QFileDialog::getOpenFileName(this,
        "Select Firmware",
        m_config->firmwarePath(),
        "Firmware Files (*.bin *.dfu);;All Files (*)");
    
    if (!firmware.isEmpty()) {
        m_deviceManager->flashFirmware(firmware);
    }
}

void MainWindow::buildProject()
{
    statusBar()->showMessage("Building project...");
    m_fapBuilder->buildFap();
}

void MainWindow::showSettings()
{
    QMessageBox::information(this, "Settings", "Settings dialog coming soon");
}

void MainWindow::onConnectionChanged(bool connected)
{
    if (connected) {
        statusBar()->showMessage("Device connected: " + m_deviceManager->deviceName());
    } else {
        statusBar()->showMessage("Device disconnected");
    }
}
