#ifndef TERMINAL_WIDGET_H
#define TERMINAL_WIDGET_H

#include <QWidget>
#include <QTextEdit>
#include <QLineEdit>
#include <QProcess>

class ConfigManager;

/**
 * @brief Embedded terminal widget for command execution
 */
class TerminalWidget : public QWidget
{
    Q_OBJECT

public:
    explicit TerminalWidget(ConfigManager* config, QWidget* parent = nullptr);
    ~TerminalWidget() override;

public slots:
    void appendLog(const QString& message);
    void executeCommand();
    void clearTerminal();

signals:
    void commandExecuted(const QString& command);

private slots:
    void onProcessReadyRead();
    void onProcessFinished(int exitCode, QProcess::ExitStatus exitStatus);

private:
    void initUI();

    ConfigManager* m_config;
    QTextEdit* m_terminal;
    QLineEdit* m_commandInput;
    QProcess* m_process;
    QString m_currentDir;
};

#endif // TERMINAL_WIDGET_H
