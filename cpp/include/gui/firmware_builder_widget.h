#ifndef FIRMWARE_BUILDER_WIDGET_H
#define FIRMWARE_BUILDER_WIDGET_H

#include <QWidget>
#include <QComboBox>
#include <QLineEdit>
#include <QProgressBar>
#include <QTextEdit>

class ConfigManager;

/**
 * @brief Widget for building and customizing Flipper Zero firmware
 */
class FirmwareBuilderWidget : public QWidget
{
    Q_OBJECT

public:
    explicit FirmwareBuilderWidget(ConfigManager* config, QWidget* parent = nullptr);
    ~FirmwareBuilderWidget() override = default;

public slots:
    void selectFirmwareSource();
    void buildFirmware();
    void cleanBuild();

signals:
    void buildStarted();
    void buildProgress(int percentage);
    void buildFinished(bool success);
    void logMessage(const QString& message);

private:
    void initUI();

    ConfigManager* m_config;
    
    QComboBox* m_firmwareTypeCombo;
    QLineEdit* m_firmwarePathInput;
    QProgressBar* m_progressBar;
    QTextEdit* m_buildLog;
};

#endif // FIRMWARE_BUILDER_WIDGET_H
