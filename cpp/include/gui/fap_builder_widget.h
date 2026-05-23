#ifndef FAP_BUILDER_WIDGET_H
#define FAP_BUILDER_WIDGET_H

#include <QWidget>
#include <QLineEdit>
#include <QComboBox>
#include <QTextEdit>
#include <QPushButton>

class ConfigManager;

/**
 * @brief Widget for building Flipper Application Packages (FAP)
 */
class FAPBuilderWidget : public QWidget
{
    Q_OBJECT

public:
    explicit FAPBuilderWidget(ConfigManager* config, QWidget* parent = nullptr);
    ~FAPBuilderWidget() override = default;

public slots:
    void createProject();
    void buildFap();

signals:
    void projectCreated(const QString& path);
    void buildStarted();
    void buildFinished(bool success);
    void logMessage(const QString& message);

private:
    void initUI();
    QString generateApplicationManifest() const;
    QString generateMainSource() const;

    ConfigManager* m_config;
    
    QLineEdit* m_appIdInput;
    QLineEdit* m_nameInput;
    QComboBox* m_categoryCombo;
    QTextEdit* m_codeEditor;
    QPushButton* m_createBtn;
    QPushButton* m_buildBtn;
};

#endif // FAP_BUILDER_WIDGET_H
