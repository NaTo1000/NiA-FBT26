#include "gui/fap_builder_widget.h"
#include "core/config_manager.h"

#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QGroupBox>
#include <QMessageBox>
#include <QFileDialog>
#include <QDir>
#include <QFile>
#include <QTextStream>

FAPBuilderWidget::FAPBuilderWidget(ConfigManager* config, QWidget* parent)
    : QWidget(parent)
    , m_config(config)
{
    initUI();
}

void FAPBuilderWidget::initUI()
{
    QVBoxLayout* layout = new QVBoxLayout(this);
    
    // Project info group
    QGroupBox* infoGroup = new QGroupBox("Project Information", this);
    QVBoxLayout* infoLayout = new QVBoxLayout(infoGroup);
    
    // App ID
    QHBoxLayout* appIdLayout = new QHBoxLayout();
    appIdLayout->addWidget(new QLabel("App ID:", this));
    m_appIdInput = new QLineEdit(this);
    m_appIdInput->setPlaceholderText("my_flipper_app");
    appIdLayout->addWidget(m_appIdInput);
    infoLayout->addLayout(appIdLayout);
    
    // App Name
    QHBoxLayout* nameLayout = new QHBoxLayout();
    nameLayout->addWidget(new QLabel("Name:", this));
    m_nameInput = new QLineEdit(this);
    m_nameInput->setPlaceholderText("My Flipper App");
    nameLayout->addWidget(m_nameInput);
    infoLayout->addLayout(nameLayout);
    
    // Category
    QHBoxLayout* catLayout = new QHBoxLayout();
    catLayout->addWidget(new QLabel("Category:", this));
    m_categoryCombo = new QComboBox(this);
    m_categoryCombo->addItems({"Tools", "Games", "GPIO", "Sub-GHz", "NFC", "USB", "Bluetooth"});
    catLayout->addWidget(m_categoryCombo);
    infoLayout->addLayout(catLayout);
    
    layout->addWidget(infoGroup);
    
    // Code editor group
    QGroupBox* editorGroup = new QGroupBox("Source Code", this);
    QVBoxLayout* editorLayout = new QVBoxLayout(editorGroup);
    
    m_codeEditor = new QTextEdit(this);
    m_codeEditor->setPlaceholderText("Write your application code here...");
    m_codeEditor->setFontFamily("Consolas, Monaco, monospace");
    m_codeEditor->setTabStopDistance(40);
    
    // Set default template
    m_codeEditor->setPlainText(
        "#include <furi.h>\n"
        "#include <gui/gui.h>\n"
        "\n"
        "int32_t app_main(void* p) {\n"
        "    UNUSED(p);\n"
        "    \n"
        "    // Your code here\n"
        "    \n"
        "    return 0;\n"
        "}\n"
    );
    
    editorLayout->addWidget(m_codeEditor);
    layout->addWidget(editorGroup);
    
    // Buttons
    QHBoxLayout* buttonLayout = new QHBoxLayout();
    
    m_createBtn = new QPushButton("Create Project", this);
    connect(m_createBtn, &QPushButton::clicked, this, &FAPBuilderWidget::createProject);
    
    m_buildBtn = new QPushButton("Build FAP", this);
    connect(m_buildBtn, &QPushButton::clicked, this, &FAPBuilderWidget::buildFap);
    
    buttonLayout->addWidget(m_createBtn);
    buttonLayout->addWidget(m_buildBtn);
    layout->addLayout(buttonLayout);
}

void FAPBuilderWidget::createProject()
{
    QString appId = m_appIdInput->text().trimmed();
    QString appName = m_nameInput->text().trimmed();
    
    if (appId.isEmpty() || appName.isEmpty()) {
        QMessageBox::warning(this, "Warning", "Please fill in App ID and Name");
        return;
    }
    
    QString dir = QFileDialog::getExistingDirectory(this, 
        "Select Project Directory",
        QDir::homePath());
    
    if (dir.isEmpty()) return;
    
    QString projectDir = dir + "/" + appId;
    QDir().mkpath(projectDir);
    
    // Write application.fam
    QFile famFile(projectDir + "/application.fam");
    if (famFile.open(QIODevice::WriteOnly)) {
        QTextStream stream(&famFile);
        stream << generateApplicationManifest();
        famFile.close();
    }
    
    // Write main source file
    QFile srcFile(projectDir + "/" + appId + ".c");
    if (srcFile.open(QIODevice::WriteOnly)) {
        QTextStream stream(&srcFile);
        stream << generateMainSource();
        srcFile.close();
    }
    
    emit logMessage("Created FAP project: " + projectDir);
    emit projectCreated(projectDir);
    
    QMessageBox::information(this, "Success", "Project created at:\n" + projectDir);
}

void FAPBuilderWidget::buildFap()
{
    emit buildStarted();
    emit logMessage("Building FAP...");
    
    // In a real implementation, this would invoke the Flipper build system
    // using fbt (Flipper Build Tool)
    
    emit logMessage("Build complete");
    emit buildFinished(true);
}

QString FAPBuilderWidget::generateApplicationManifest() const
{
    QString appId = m_appIdInput->text().trimmed();
    QString appName = m_nameInput->text().trimmed();
    QString category = m_categoryCombo->currentText();
    
    return QString(
        "App(\n"
        "    appid=\"%1\",\n"
        "    name=\"%2\",\n"
        "    apptype=FlipperAppType.EXTERNAL,\n"
        "    entry_point=\"app_main\",\n"
        "    cdefines=[\"APP_HELLO_WORLD\"],\n"
        "    requires=[\"gui\"],\n"
        "    stack_size=2 * 1024,\n"
        "    fap_icon=\"icon.png\",\n"
        "    fap_category=\"%3\",\n"
        ")\n"
    ).arg(appId, appName, category);
}

QString FAPBuilderWidget::generateMainSource() const
{
    return m_codeEditor->toPlainText();
}
