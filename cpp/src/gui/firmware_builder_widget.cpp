#include "gui/firmware_builder_widget.h"
#include "core/config_manager.h"

#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QGroupBox>
#include <QPushButton>
#include <QFileDialog>

FirmwareBuilderWidget::FirmwareBuilderWidget(ConfigManager* config, QWidget* parent)
    : QWidget(parent)
    , m_config(config)
{
    initUI();
}

void FirmwareBuilderWidget::initUI()
{
    QVBoxLayout* layout = new QVBoxLayout(this);
    
    // Firmware source group
    QGroupBox* sourceGroup = new QGroupBox("Firmware Source", this);
    QVBoxLayout* sourceLayout = new QVBoxLayout(sourceGroup);
    
    // Firmware type selection
    QHBoxLayout* typeLayout = new QHBoxLayout();
    typeLayout->addWidget(new QLabel("Firmware Type:", this));
    m_firmwareTypeCombo = new QComboBox(this);
    m_firmwareTypeCombo->addItems({
        "Official Flipper",
        "Unleashed",
        "RogueMaster",
        "Xtreme",
        "Custom"
    });
    typeLayout->addWidget(m_firmwareTypeCombo);
    sourceLayout->addLayout(typeLayout);
    
    // Firmware path
    QHBoxLayout* pathLayout = new QHBoxLayout();
    pathLayout->addWidget(new QLabel("Source Path:", this));
    m_firmwarePathInput = new QLineEdit(this);
    m_firmwarePathInput->setText(m_config->firmwarePath());
    pathLayout->addWidget(m_firmwarePathInput);
    
    QPushButton* browseBtn = new QPushButton("Browse", this);
    connect(browseBtn, &QPushButton::clicked, this, &FirmwareBuilderWidget::selectFirmwareSource);
    pathLayout->addWidget(browseBtn);
    sourceLayout->addLayout(pathLayout);
    
    layout->addWidget(sourceGroup);
    
    // Build options group
    QGroupBox* buildGroup = new QGroupBox("Build", this);
    QVBoxLayout* buildLayout = new QVBoxLayout(buildGroup);
    
    // Progress bar
    m_progressBar = new QProgressBar(this);
    m_progressBar->setRange(0, 100);
    m_progressBar->setValue(0);
    buildLayout->addWidget(m_progressBar);
    
    // Build buttons
    QHBoxLayout* buttonLayout = new QHBoxLayout();
    
    QPushButton* buildBtn = new QPushButton("Build Firmware", this);
    connect(buildBtn, &QPushButton::clicked, this, &FirmwareBuilderWidget::buildFirmware);
    buttonLayout->addWidget(buildBtn);
    
    QPushButton* cleanBtn = new QPushButton("Clean Build", this);
    connect(cleanBtn, &QPushButton::clicked, this, &FirmwareBuilderWidget::cleanBuild);
    buttonLayout->addWidget(cleanBtn);
    
    buildLayout->addLayout(buttonLayout);
    layout->addWidget(buildGroup);
    
    // Build log
    QGroupBox* logGroup = new QGroupBox("Build Log", this);
    QVBoxLayout* logLayout = new QVBoxLayout(logGroup);
    
    m_buildLog = new QTextEdit(this);
    m_buildLog->setReadOnly(true);
    m_buildLog->setFontFamily("Consolas, Monaco, monospace");
    logLayout->addWidget(m_buildLog);
    
    layout->addWidget(logGroup);
}

void FirmwareBuilderWidget::selectFirmwareSource()
{
    QString dir = QFileDialog::getExistingDirectory(this,
        "Select Firmware Source Directory",
        m_config->firmwarePath());
    
    if (!dir.isEmpty()) {
        m_firmwarePathInput->setText(dir);
        m_config->setFirmwarePath(dir);
    }
}

void FirmwareBuilderWidget::buildFirmware()
{
    emit buildStarted();
    m_buildLog->clear();
    m_buildLog->append("Starting firmware build...");
    m_buildLog->append("Firmware type: " + m_firmwareTypeCombo->currentText());
    m_buildLog->append("Source path: " + m_firmwarePathInput->text());
    m_buildLog->append("");
    
    // Simulate build progress
    for (int i = 0; i <= 100; i += 10) {
        m_progressBar->setValue(i);
        emit buildProgress(i);
    }
    
    m_buildLog->append("Build complete!");
    emit buildFinished(true);
}

void FirmwareBuilderWidget::cleanBuild()
{
    m_buildLog->append("Cleaning build artifacts...");
    m_progressBar->setValue(0);
    m_buildLog->append("Clean complete.");
}
