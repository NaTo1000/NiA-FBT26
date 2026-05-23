#include "gui/terminal_widget.h"
#include "core/config_manager.h"

#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QPushButton>
#include <QDir>
#include <QDateTime>

TerminalWidget::TerminalWidget(ConfigManager* config, QWidget* parent)
    : QWidget(parent)
    , m_config(config)
    , m_process(new QProcess(this))
    , m_currentDir(QDir::homePath())
{
    initUI();
    
    connect(m_process, &QProcess::readyReadStandardOutput, 
            this, &TerminalWidget::onProcessReadyRead);
    connect(m_process, &QProcess::readyReadStandardError,
            this, &TerminalWidget::onProcessReadyRead);
    connect(m_process, QOverload<int, QProcess::ExitStatus>::of(&QProcess::finished),
            this, &TerminalWidget::onProcessFinished);
}

TerminalWidget::~TerminalWidget()
{
    if (m_process->state() != QProcess::NotRunning) {
        m_process->terminate();
        m_process->waitForFinished(1000);
    }
}

void TerminalWidget::initUI()
{
    QVBoxLayout* layout = new QVBoxLayout(this);
    layout->setContentsMargins(0, 0, 0, 0);
    
    // Terminal output
    m_terminal = new QTextEdit(this);
    m_terminal->setReadOnly(true);
    m_terminal->setFontFamily("Consolas, Monaco, Menlo, monospace");
    m_terminal->setStyleSheet(
        "QTextEdit {"
        "  background-color: #1e1e1e;"
        "  color: #d4d4d4;"
        "  border: none;"
        "  padding: 8px;"
        "}"
    );
    layout->addWidget(m_terminal);
    
    // Command input row
    QHBoxLayout* inputLayout = new QHBoxLayout();
    
    m_commandInput = new QLineEdit(this);
    m_commandInput->setPlaceholderText("Enter command...");
    m_commandInput->setStyleSheet(
        "QLineEdit {"
        "  background-color: #2d2d2d;"
        "  color: #d4d4d4;"
        "  border: 1px solid #3c3c3c;"
        "  padding: 6px;"
        "  font-family: Consolas, Monaco, monospace;"
        "}"
    );
    connect(m_commandInput, &QLineEdit::returnPressed, 
            this, &TerminalWidget::executeCommand);
    inputLayout->addWidget(m_commandInput);
    
    QPushButton* runBtn = new QPushButton("Run", this);
    connect(runBtn, &QPushButton::clicked, this, &TerminalWidget::executeCommand);
    inputLayout->addWidget(runBtn);
    
    QPushButton* clearBtn = new QPushButton("Clear", this);
    connect(clearBtn, &QPushButton::clicked, this, &TerminalWidget::clearTerminal);
    inputLayout->addWidget(clearBtn);
    
    layout->addLayout(inputLayout);
    
    // Initial message
    appendLog("NiA FBT26 Terminal");
    appendLog("Type commands below to execute.");
    appendLog("");
}

void TerminalWidget::appendLog(const QString& message)
{
    QString timestamp = QDateTime::currentDateTime().toString("hh:mm:ss");
    m_terminal->append(QString("[%1] %2").arg(timestamp, message));
}

void TerminalWidget::executeCommand()
{
    QString command = m_commandInput->text().trimmed();
    if (command.isEmpty()) return;
    
    m_commandInput->clear();
    appendLog("$ " + command);
    
    emit commandExecuted(command);
    
    // Handle cd command specially
    if (command.startsWith("cd ")) {
        QString newDir = command.mid(3).trimmed();
        if (newDir == "~") {
            newDir = QDir::homePath();
        } else if (!QDir::isAbsolutePath(newDir)) {
            newDir = m_currentDir + "/" + newDir;
        }
        
        QDir dir(newDir);
        if (dir.exists()) {
            m_currentDir = dir.canonicalPath();
            appendLog("Changed directory to: " + m_currentDir);
        } else {
            appendLog("Directory not found: " + newDir);
        }
        return;
    }
    
    // Execute other commands
    m_process->setWorkingDirectory(m_currentDir);
    
#ifdef Q_OS_WIN
    m_process->start("cmd.exe", QStringList() << "/C" << command);
#else
    m_process->start("/bin/sh", QStringList() << "-c" << command);
#endif
}

void TerminalWidget::clearTerminal()
{
    m_terminal->clear();
}

void TerminalWidget::onProcessReadyRead()
{
    QString output = QString::fromUtf8(m_process->readAllStandardOutput());
    QString error = QString::fromUtf8(m_process->readAllStandardError());
    
    if (!output.isEmpty()) {
        m_terminal->append(output.trimmed());
    }
    if (!error.isEmpty()) {
        m_terminal->append("<span style='color: #f44747;'>" + error.trimmed() + "</span>");
    }
}

void TerminalWidget::onProcessFinished(int exitCode, QProcess::ExitStatus exitStatus)
{
    Q_UNUSED(exitStatus);
    
    if (exitCode != 0) {
        appendLog(QString("Process exited with code %1").arg(exitCode));
    }
}
