#include "core/config_manager.h"
#include <QStandardPaths>
#include <QDebug>

ConfigManager::ConfigManager()
    : m_configPath(configFilePath())
{
    if (!loadConfig()) {
        m_config = defaultConfig();
        saveConfig();
    }
}

QString ConfigManager::configFilePath() const
{
    QString configDir = QStandardPaths::writableLocation(QStandardPaths::AppConfigLocation);
    return configDir + "/settings.json";
}

QJsonObject ConfigManager::defaultConfig() const
{
    QJsonObject editor;
    editor["theme"] = "monokai";
    editor["font_size"] = 12;
    
    QJsonObject config;
    config["firmware_path"] = QDir::homePath() + "/flipper-firmware";
    config["sdk_path"] = QDir::homePath() + "/flipper-sdk";
    config["arduino_path"] = QDir::homePath() + "/Arduino";
    config["editor"] = editor;
    
    return config;
}

bool ConfigManager::loadConfig()
{
    QFile file(m_configPath);
    if (!file.exists()) {
        return false;
    }
    
    if (!file.open(QIODevice::ReadOnly)) {
        qWarning() << "Failed to open config file:" << m_configPath;
        return false;
    }
    
    QByteArray data = file.readAll();
    file.close();
    
    QJsonParseError error;
    QJsonDocument doc = QJsonDocument::fromJson(data, &error);
    
    if (error.error != QJsonParseError::NoError) {
        qWarning() << "Failed to parse config:" << error.errorString();
        return false;
    }
    
    m_config = doc.object();
    return true;
}

bool ConfigManager::saveConfig()
{
    QFileInfo fileInfo(m_configPath);
    QDir dir = fileInfo.dir();
    
    if (!dir.exists()) {
        dir.mkpath(".");
    }
    
    QFile file(m_configPath);
    if (!file.open(QIODevice::WriteOnly)) {
        qWarning() << "Failed to save config file:" << m_configPath;
        return false;
    }
    
    QJsonDocument doc(m_config);
    file.write(doc.toJson(QJsonDocument::Indented));
    file.close();
    
    return true;
}

QString ConfigManager::firmwarePath() const
{
    return m_config["firmware_path"].toString();
}

void ConfigManager::setFirmwarePath(const QString& path)
{
    m_config["firmware_path"] = path;
}

QString ConfigManager::sdkPath() const
{
    return m_config["sdk_path"].toString();
}

void ConfigManager::setSdkPath(const QString& path)
{
    m_config["sdk_path"] = path;
}

QString ConfigManager::arduinoPath() const
{
    return m_config["arduino_path"].toString();
}

void ConfigManager::setArduinoPath(const QString& path)
{
    m_config["arduino_path"] = path;
}

QString ConfigManager::editorTheme() const
{
    return m_config["editor"].toObject()["theme"].toString();
}

void ConfigManager::setEditorTheme(const QString& theme)
{
    QJsonObject editor = m_config["editor"].toObject();
    editor["theme"] = theme;
    m_config["editor"] = editor;
}

int ConfigManager::editorFontSize() const
{
    return m_config["editor"].toObject()["font_size"].toInt();
}

void ConfigManager::setEditorFontSize(int size)
{
    QJsonObject editor = m_config["editor"].toObject();
    editor["font_size"] = size;
    m_config["editor"] = editor;
}
