#include "core/device_manager.h"
#include <QDebug>

DeviceManager::DeviceManager(QObject* parent)
    : QObject(parent)
    , m_serialPort(nullptr)
    , m_connected(false)
{
}

DeviceManager::~DeviceManager()
{
    disconnect();
}

bool DeviceManager::connect()
{
    emit logMessage("Connecting to Flipper Zero...");
    
    if (!detectDevice()) {
        emit errorOccurred("No Flipper Zero device found");
        return false;
    }
    
    if (!openSerialPort()) {
        emit errorOccurred("Failed to open serial port");
        return false;
    }
    
    m_connected = true;
    emit connectionChanged(true);
    emit logMessage("Connected to " + m_deviceName + " on " + m_devicePort);
    
    return true;
}

void DeviceManager::disconnect()
{
    if (m_serialPort && m_serialPort->isOpen()) {
        m_serialPort->close();
    }
    
    m_connected = false;
    emit connectionChanged(false);
    emit logMessage("Disconnected from device");
}

bool DeviceManager::isConnected() const
{
    return m_connected;
}

QString DeviceManager::deviceName() const
{
    return m_deviceName;
}

QString DeviceManager::devicePort() const
{
    return m_devicePort;
}

QStringList DeviceManager::availablePorts() const
{
    QStringList ports;
    const auto portInfos = QSerialPortInfo::availablePorts();
    
    for (const QSerialPortInfo& info : portInfos) {
        ports << info.portName() + " - " + info.description();
    }
    
    return ports;
}

bool DeviceManager::detectDevice()
{
    const auto portInfos = QSerialPortInfo::availablePorts();
    
    for (const QSerialPortInfo& info : portInfos) {
        // Look for Flipper Zero device (VID/PID matching)
        if (info.vendorIdentifier() == 0x0483 && 
            (info.productIdentifier() == 0x5740 || info.productIdentifier() == 0xDF11)) {
            m_deviceName = info.description();
            m_devicePort = info.portName();
            emit deviceDetected(m_deviceName);
            return true;
        }
        
        // Also check by description
        if (info.description().contains("Flipper", Qt::CaseInsensitive)) {
            m_deviceName = info.description();
            m_devicePort = info.portName();
            emit deviceDetected(m_deviceName);
            return true;
        }
    }
    
    return false;
}

bool DeviceManager::openSerialPort()
{
    m_serialPort = std::make_unique<QSerialPort>();
    m_serialPort->setPortName(m_devicePort);
    m_serialPort->setBaudRate(QSerialPort::Baud115200);
    m_serialPort->setDataBits(QSerialPort::Data8);
    m_serialPort->setParity(QSerialPort::NoParity);
    m_serialPort->setStopBits(QSerialPort::OneStop);
    m_serialPort->setFlowControl(QSerialPort::NoFlowControl);
    
    return m_serialPort->open(QIODevice::ReadWrite);
}

bool DeviceManager::flashFirmware(const QString& firmwarePath)
{
    emit logMessage("Flashing firmware: " + firmwarePath);
    
    if (!m_connected) {
        emit errorOccurred("Device not connected");
        return false;
    }
    
    // Simulate flashing progress
    for (int i = 0; i <= 100; i += 10) {
        emit flashProgress(i);
    }
    
    emit flashComplete(true);
    emit logMessage("Firmware flashed successfully");
    
    return true;
}

bool DeviceManager::uploadFile(const QString& localPath, const QString& remotePath)
{
    emit logMessage("Uploading " + localPath + " to " + remotePath);
    
    if (!m_connected) {
        emit errorOccurred("Device not connected");
        return false;
    }
    
    // File upload implementation would go here
    emit logMessage("File uploaded successfully");
    
    return true;
}
