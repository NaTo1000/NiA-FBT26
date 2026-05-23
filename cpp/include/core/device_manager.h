#ifndef DEVICE_MANAGER_H
#define DEVICE_MANAGER_H

#include <QObject>
#include <QString>
#include <QSerialPort>
#include <QSerialPortInfo>
#include <memory>

/**
 * @brief Device Manager for Flipper Zero connections
 * 
 * Handles device detection, connection, and firmware flashing operations.
 */
class DeviceManager : public QObject
{
    Q_OBJECT

public:
    explicit DeviceManager(QObject* parent = nullptr);
    ~DeviceManager() override;
    
    // Connection management
    bool connect();
    void disconnect();
    bool isConnected() const;
    
    // Device information
    QString deviceName() const;
    QString devicePort() const;
    QStringList availablePorts() const;
    
    // Firmware operations
    bool flashFirmware(const QString& firmwarePath);
    bool uploadFile(const QString& localPath, const QString& remotePath);
    
signals:
    void connectionChanged(bool connected);
    void deviceDetected(const QString& deviceName);
    void flashProgress(int percentage);
    void flashComplete(bool success);
    void errorOccurred(const QString& error);
    void logMessage(const QString& message);

private:
    bool detectDevice();
    bool openSerialPort();
    
    std::unique_ptr<QSerialPort> m_serialPort;
    QString m_deviceName;
    QString m_devicePort;
    bool m_connected;
};

#endif // DEVICE_MANAGER_H
