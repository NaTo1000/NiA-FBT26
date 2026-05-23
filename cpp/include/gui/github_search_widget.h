#ifndef GITHUB_SEARCH_WIDGET_H
#define GITHUB_SEARCH_WIDGET_H

#include <QWidget>
#include <QLineEdit>
#include <QListWidget>
#include <QTextEdit>
#include <QNetworkAccessManager>
#include <QNetworkReply>

class ConfigManager;

/**
 * @brief Widget for searching GitHub repositories
 */
class GitHubSearchWidget : public QWidget
{
    Q_OBJECT

public:
    explicit GitHubSearchWidget(ConfigManager* config, QWidget* parent = nullptr);
    ~GitHubSearchWidget() override = default;

public slots:
    void search();
    void onResultSelected(QListWidgetItem* item);

signals:
    void repositorySelected(const QString& repoUrl);
    void logMessage(const QString& message);

private slots:
    void onSearchFinished(QNetworkReply* reply);

private:
    void initUI();

    ConfigManager* m_config;
    QNetworkAccessManager* m_networkManager;
    
    QLineEdit* m_searchInput;
    QListWidget* m_resultsList;
    QTextEdit* m_detailsView;
};

#endif // GITHUB_SEARCH_WIDGET_H
