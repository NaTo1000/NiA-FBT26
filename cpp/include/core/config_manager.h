#ifndef CONFIG_MANAGER_H
#define CONFIG_MANAGER_H

#include <QString>
#include <QJsonObject>
#include <QJsonDocument>
#include <QFile>
#include <QDir>

/**
 * @brief Configuration Manager for NiA FBT26
 * 
 * Handles loading, saving, and managing application configuration settings.
 */
class ConfigManager
{
public:
    ConfigManager();
    ~ConfigManager() = default;
    
    // Configuration accessors
    QString firmwarePath() const;
    void setFirmwarePath(const QString& path);
    
    QString sdkPath() const;
    void setSdkPath(const QString& path);
    
    QString arduinoPath() const;
    void setArduinoPath(const QString& path);
    
    QString editorTheme() const;
    void setEditorTheme(const QString& theme);
    
    int editorFontSize() const;
    void setEditorFontSize(int size);
    
    // Persistence
    bool loadConfig();
    bool saveConfig();
    
private:
    QJsonObject defaultConfig() const;
    QString configFilePath() const;
    
    QJsonObject m_config;
    QString m_configPath;
};

#endif // CONFIG_MANAGER_H
