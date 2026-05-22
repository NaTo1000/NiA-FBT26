#ifndef ARDUINO_PANEL_WIDGET_H
#define ARDUINO_PANEL_WIDGET_H

#include <QWidget>
#include <QComboBox>
#include <QLineEdit>
#include <QTextEdit>

class ConfigManager;

/**
 * @brief Widget for Arduino/ESP32 development integration
 */
class ArduinoPanelWidget : public QWidget
{
    Q_OBJECT

public:
    explicit ArduinoPanelWidget(ConfigManager* config, QWidget* parent = nullptr);
    ~ArduinoPanelWidget() override = default;

public slots:
    void selectBoard();
    void compileSketch();
    void uploadSketch();
    void openSerialMonitor();

signals:
    void logMessage(const QString& message);

private:
    void initUI();
    void populateBoards();
    void populatePorts();

    ConfigManager* m_config;
    
    QComboBox* m_boardCombo;
    QComboBox* m_portCombo;
    QTextEdit* m_codeEditor;
    QTextEdit* m_outputLog;
};

#endif // ARDUINO_PANEL_WIDGET_H
