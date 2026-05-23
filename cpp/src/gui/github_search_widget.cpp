#include "gui/github_search_widget.h"
#include "core/config_manager.h"

#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QPushButton>
#include <QSplitter>
#include <QJsonDocument>
#include <QJsonArray>
#include <QJsonObject>
#include <QUrl>
#include <QUrlQuery>

GitHubSearchWidget::GitHubSearchWidget(ConfigManager* config, QWidget* parent)
    : QWidget(parent)
    , m_config(config)
    , m_networkManager(new QNetworkAccessManager(this))
{
    initUI();
    
    connect(m_networkManager, &QNetworkAccessManager::finished,
            this, &GitHubSearchWidget::onSearchFinished);
}

void GitHubSearchWidget::initUI()
{
    QVBoxLayout* layout = new QVBoxLayout(this);
    
    // Search bar
    QHBoxLayout* searchLayout = new QHBoxLayout();
    
    m_searchInput = new QLineEdit(this);
    m_searchInput->setPlaceholderText("Search GitHub for Flipper Zero projects...");
    connect(m_searchInput, &QLineEdit::returnPressed, this, &GitHubSearchWidget::search);
    searchLayout->addWidget(m_searchInput);
    
    QPushButton* searchBtn = new QPushButton("Search", this);
    connect(searchBtn, &QPushButton::clicked, this, &GitHubSearchWidget::search);
    searchLayout->addWidget(searchBtn);
    
    layout->addLayout(searchLayout);
    
    // Results splitter
    QSplitter* splitter = new QSplitter(Qt::Horizontal, this);
    
    // Results list
    m_resultsList = new QListWidget(this);
    connect(m_resultsList, &QListWidget::itemClicked, 
            this, &GitHubSearchWidget::onResultSelected);
    splitter->addWidget(m_resultsList);
    
    // Details view
    m_detailsView = new QTextEdit(this);
    m_detailsView->setReadOnly(true);
    m_detailsView->setPlaceholderText("Select a repository to view details...");
    splitter->addWidget(m_detailsView);
    
    splitter->setSizes({300, 500});
    layout->addWidget(splitter);
    
    // Action buttons
    QHBoxLayout* buttonLayout = new QHBoxLayout();
    
    QPushButton* cloneBtn = new QPushButton("Clone Repository", this);
    buttonLayout->addWidget(cloneBtn);
    
    QPushButton* downloadBtn = new QPushButton("Download ZIP", this);
    buttonLayout->addWidget(downloadBtn);
    
    QPushButton* openBtn = new QPushButton("Open in Browser", this);
    buttonLayout->addWidget(openBtn);
    
    buttonLayout->addStretch();
    layout->addLayout(buttonLayout);
}

void GitHubSearchWidget::search()
{
    QString query = m_searchInput->text().trimmed();
    if (query.isEmpty()) return;
    
    m_resultsList->clear();
    m_detailsView->clear();
    m_detailsView->setPlaceholderText("Searching...");
    
    // Build GitHub API URL
    QUrl url("https://api.github.com/search/repositories");
    QUrlQuery urlQuery;
    urlQuery.addQueryItem("q", query + " flipper");
    urlQuery.addQueryItem("sort", "stars");
    urlQuery.addQueryItem("order", "desc");
    urlQuery.addQueryItem("per_page", "25");
    url.setQuery(urlQuery);
    
    QNetworkRequest request(url);
    request.setHeader(QNetworkRequest::ContentTypeHeader, "application/json");
    request.setRawHeader("Accept", "application/vnd.github.v3+json");
    request.setRawHeader("User-Agent", "NiA-FBT26");
    
    m_networkManager->get(request);
    
    emit logMessage("Searching GitHub: " + query);
}

void GitHubSearchWidget::onSearchFinished(QNetworkReply* reply)
{
    if (reply->error() != QNetworkReply::NoError) {
        m_detailsView->setPlainText("Error: " + reply->errorString());
        reply->deleteLater();
        return;
    }
    
    QByteArray data = reply->readAll();
    reply->deleteLater();
    
    QJsonDocument doc = QJsonDocument::fromJson(data);
    QJsonObject root = doc.object();
    QJsonArray items = root["items"].toArray();
    
    m_resultsList->clear();
    
    for (const QJsonValue& value : items) {
        QJsonObject repo = value.toObject();
        
        QString name = repo["full_name"].toString();
        QString description = repo["description"].toString();
        int stars = repo["stargazers_count"].toInt();
        
        QListWidgetItem* item = new QListWidgetItem(m_resultsList);
        item->setText(QString("%1 (%2 stars)").arg(name).arg(stars));
        item->setData(Qt::UserRole, QVariant::fromValue(repo));
        item->setToolTip(description);
    }
    
    m_detailsView->setPlaceholderText("Select a repository to view details...");
    emit logMessage(QString("Found %1 repositories").arg(items.size()));
}

void GitHubSearchWidget::onResultSelected(QListWidgetItem* item)
{
    QJsonObject repo = item->data(Qt::UserRole).toJsonObject();
    
    QString details;
    details += QString("<h2>%1</h2>").arg(repo["full_name"].toString());
    details += QString("<p>%1</p>").arg(repo["description"].toString());
    details += QString("<p><b>Stars:</b> %1 | <b>Forks:</b> %2</p>")
                   .arg(repo["stargazers_count"].toInt())
                   .arg(repo["forks_count"].toInt());
    details += QString("<p><b>Language:</b> %1</p>").arg(repo["language"].toString());
    details += QString("<p><b>URL:</b> <a href='%1'>%1</a></p>")
                   .arg(repo["html_url"].toString());
    
    if (!repo["topics"].toArray().isEmpty()) {
        QStringList topics;
        for (const QJsonValue& topic : repo["topics"].toArray()) {
            topics << topic.toString();
        }
        details += QString("<p><b>Topics:</b> %1</p>").arg(topics.join(", "));
    }
    
    m_detailsView->setHtml(details);
    
    emit repositorySelected(repo["html_url"].toString());
}
