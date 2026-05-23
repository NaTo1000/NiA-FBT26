#include "gui/arduino_panel_widget.h"
#include "core/config_manager.h"

#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QGroupBox>
#include <QPushButton>
#include <QSplitter>
#include <QSerialPortInfo>

ArduinoPanelWidget::ArduinoPanelWidget(ConfigManager* config, QWidget* parent)
    : QWidget(parent)
    , m_config(config)
{
    initUI();
    populateBoards();
    populatePorts();
}

void ArduinoPanelWidget::initUI()
{
    QVBoxLayout* layout = new QVBoxLayout(this);
    
    // Board and port selection
    QGroupBox* configGroup = new QGroupBox("Configuration", this);
    QHBoxLayout* configLayout = new QHBoxLayout(configGroup);
    
    configLayout->addWidget(new QLabel("Board:", this));
    m_boardCombo = new QComboBox(this);
    configLayout->addWidget(m_boardCombo);
    
    configLayout->addWidget(new QLabel("Port:", this));
    m_portCombo = new QComboBox(this);
    configLayout->addWidget(m_portCombo);
    
    QPushButton* refreshBtn = new QPushButton("Refresh", this);
    connect(refreshBtn, &QPushButton::clicked, this, &ArduinoPanelWidget::populatePorts);
    configLayout->addWidget(refreshBtn);
    
    layout->addWidget(configGroup);
    
    // Splitter for code editor and output
    QSplitter* splitter = new QSplitter(Qt::Vertical, this);
    
    // Code editor
    QGroupBox* editorGroup = new QGroupBox("Sketch", this);
    QVBoxLayout* editorLayout = new QVBoxLayout(editorGroup);
    
    m_codeEditor = new QTextEdit(this);
    m_codeEditor->setFontFamily("Consolas, Monaco, monospace");
    m_codeEditor->setPlainText(
        "void setup() {\n"
        "    Serial.begin(115200);\n"
        "    Serial.println(\"Hello from ESP32!\");\n"
        "}\n"
        "\n"
        "void loop() {\n"
        "    // Your code here\n"
        "    delay(1000);\n"
        "}\n"
    );
    editorLayout->addWidget(m_codeEditor);
    splitter->addWidget(editorGroup);
    
    // Output log
    QGroupBox* outputGroup = new QGroupBox("Output", this);
    QVBoxLayout* outputLayout = new QVBoxLayout(outputGroup);
    
    m_outputLog = new QTextEdit(this);
    m_outputLog->setReadOnly(true);
    m_outputLog->setFontFamily("Consolas, Monaco, monospace");
    outputLayout->addWidget(m_outputLog);
    splitter->addWidget(outputGroup);
    
    layout->addWidget(splitter);
    
    // Action buttons
    QHBoxLayout* buttonLayout = new QHBoxLayout();
    
    QPushButton* compileBtn = new QPushButton("Compile", this);
    connect(compileBtn, &QPushButton::clicked, this, &ArduinoPanelWidget::compileSketch);
    buttonLayout->addWidget(compileBtn);
    
    QPushButton* uploadBtn = new QPushButton("Upload", this);
    connect(uploadBtn, &QPushButton::clicked, this, &ArduinoPanelWidget::uploadSketch);
    buttonLayout->addWidget(uploadBtn);
    
    QPushButton* serialBtn = new QPushButton("Serial Monitor", this);
    connect(serialBtn, &QPushButton::clicked, this, &ArduinoPanelWidget::openSerialMonitor);
    buttonLayout->addWidget(serialBtn);
    
    layout->addLayout(buttonLayout);
}

void ArduinoPanelWidget::populateBoards()
{
    m_boardCombo->clear();
    m_boardCombo->addItems({
        "ESP32 Dev Module",
        "ESP32-S2 Dev Module",
        "ESP32-S3 Dev Module",
        "ESP32-C3 Dev Module",
        "Arduino Uno",
        "Arduino Nano",
        "Arduino Mega 2560"
    });
}

void ArduinoPanelWidget::populatePorts()
{
    m_portCombo->clear();
    
    const auto ports = QSerialPortInfo::availablePorts();
    for (const QSerialPortInfo& info : ports) {
        m_portCombo->addItem(info.portName() + " - " + info.description());
    }
    
    if (m_portCombo->count() == 0) {
        m_portCombo->addItem("No ports available");
    }
}

void ArduinoPanelWidget::selectBoard()
{
    // Board selection logic
}

void ArduinoPanelWidget::compileSketch()
{
    m_outputLog->clear();
    m_outputLog->append("Compiling sketch...");
    m_outputLog->append("Board: " + m_boardCombo->currentText());
    m_outputLog->append("");
    
    // Simulated compilation
    m_outputLog->append("Sketch uses 234567 bytes (17%) of program storage space.");
    m_outputLog->append("Global variables use 12345 bytes (3%) of dynamic memory.");
    m_outputLog->append("");
    m_outputLog->append("Compilation complete.");
    
    emit logMessage("Sketch compiled successfully");
}

void ArduinoPanelWidget::uploadSketch()
{
    m_outputLog->append("");
    m_outputLog->append("Uploading to " + m_boardCombo->currentText() + "...");
    m_outputLog->append("Port: " + m_portCombo->currentText());
    m_outputLog->append("");
    m_outputLog->append("Upload complete.");
    
    emit logMessage("Sketch uploaded successfully");
}

void ArduinoPanelWidget::openSerialMonitor()
{
    m_outputLog->append("");
    m_outputLog->append("--- Serial Monitor Started (115200 baud) ---");
    
    emit logMessage("Serial monitor opened");
}
