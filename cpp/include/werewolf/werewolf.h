#ifndef WEREWOLF_WEREWOLF_H
#define WEREWOLF_WEREWOLF_H

#include <QByteArray>
#include <QJsonArray>
#include <QJsonObject>
#include <QString>

#include <deque>
#include <functional>
#include <optional>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace werewolf {

inline constexpr int EnergyCap = 100;
inline constexpr int ShieldCap = 60;
inline constexpr int EventCap = 500;
inline constexpr int BeaconLifetimeSeconds = 300;
inline constexpr int AlertReplayCap = 1024;
inline constexpr int ResolvedReplayCap = 1024;
inline constexpr int LiveBeaconReplayCap = 4096;
inline constexpr qint64 ScenarioByteCap = 1024 * 1024;

enum class DeviceClass {
    Flipper, Pwnagotchi, Bjorn, Tamafi, Pineapple, Phones64, Wifi7, Nano, Sharkbite, Other
};
enum class Mode { Dormant, Guard, Defence };
enum class Skin { Werewolf, FullMoon, Shielded, Secured, Wounded };

struct RawAlert {
    QString alertId;
    QString detector;
    QString targetDeviceId;
    QString reason;
    int severity = 0;
    bool simulationTrusted = false;
};

class VerifiedAttackAlert {
public:
    const QString& alertId() const { return alertId_; }
    const QString& detector() const { return detector_; }
    const QString& targetDeviceId() const { return targetDeviceId_; }
    const QString& reason() const { return reason_; }
    int severity() const { return severity_; }

private:
    VerifiedAttackAlert(QString alertId, QString detector, QString targetDeviceId,
                        QString reason, int severity);
    QString alertId_;
    QString detector_;
    QString targetDeviceId_;
    QString reason_;
    int severity_;
    friend class SimulationAlertVerifier;
};

class SimulationAlertVerifier {
public:
    std::optional<VerifiedAttackAlert> verify(const RawAlert& raw, QString* error = nullptr) const;
};

struct NearbyDevice {
    QString deviceId;
    DeviceClass deviceClass = DeviceClass::Other;
    int signalDbm = -100;
    bool optedIn = false;
    bool gameBeaconValid = false;
    int battlePower = 0;
    bool connectedFirst = false;
    QString beaconId;
    qint64 issuedAt = 0;
    qint64 expiresAt = 0;
};

struct Metrics {
    int scans = 0;
    int devicesSeen = 0;
    int optedInDevices = 0;
    int ignoredDevices = 0;
    int invalidBeacons = 0;
    int expiredBeacons = 0;
    int replayedBeacons = 0;
    int invalidAlerts = 0;
    int attacksDetected = 0;
    int guardModeEntries = 0;
    int energyCollected = 0;
    int defenceActions = 0;
    int attacksBlocked = 0;
    int defenceFailures = 0;
    int shieldsUsed = 0;
    int protectedSessions = 0;
    QJsonObject detectionsByClass;
};

struct State {
    Mode mode = Mode::Dormant;
    Skin skin = Skin::Werewolf;
    int energy = 20;
    int shield = 0;
    int score = 0;
    int streak = 0;
    QString lastTarget;
    Metrics metrics;
    QJsonArray events;
    QJsonObject assistantMessages;
    QJsonObject toJson() const;
};

struct ScanResult {
    int accepted = 0;
    int ignored = 0;
    QJsonObject rejectionReasons;
};

struct IsolationRequest {
    QString alertId;
    QString targetDeviceId;
    QString action = QStringLiteral("block_and_isolate");
};

class DryRunContainmentAdapter {
public:
    void requestLocalIsolation(const VerifiedAttackAlert& alert);
    const std::vector<IsolationRequest>& requests() const { return requests_; }
private:
    std::vector<IsolationRequest> requests_;
};

class Engine {
public:
    using Clock = std::function<qint64()>;
    explicit Engine(Clock clock, DryRunContainmentAdapter* containment = nullptr);

    bool reportAttack(const VerifiedAttackAlert& alert);
    void rejectRawAlert(const QString& alertId);
    ScanResult scan(const std::vector<NearbyDevice>& devices);
    int chargeShield(int amount);
    QString defend(const NearbyDevice& opponent);
    void clearIncident();
    const State& state() const { return state_; }
    int liveBeaconReplaySize() const { return static_cast<int>(seenBeacons_.size()); }
    int alertReplaySize() const { return static_cast<int>(seenAlerts_.size()); }
    int resolvedReplaySize() const { return static_cast<int>(resolvedAlerts_.size()); }

private:
    void event(const QString& type, const QJsonObject& details = {});
    void pruneBeacons(qint64 now);
    void remember(std::deque<QString>& order, std::unordered_set<QString>& ids,
                  const QString& id, int cap);
    void assertInvariants() const;

    Clock clock_;
    DryRunContainmentAdapter* containment_;
    State state_;
    std::optional<VerifiedAttackAlert> activeAlert_;
    std::unordered_map<QString, qint64> seenBeacons_;
    std::deque<QString> alertOrder_;
    std::unordered_set<QString> seenAlerts_;
    std::deque<QString> resolvedOrder_;
    std::unordered_set<QString> resolvedAlerts_;
};

struct Scenario {
    qint64 currentTime = 0;
    std::vector<NearbyDevice> devices;
    std::optional<RawAlert> rawAlert;
    int shieldCharge = 0;
    QString attackerDeviceId;
};

struct RunResult {
    State state;
    int acceptedDevices = 0;
    int ignoredDevices = 0;
    int containmentRequests = 0;
};

class ScenarioAdapter {
public:
    Scenario loadFile(const QString& path) const;
    Scenario parse(const QByteArray& bytes) const;
};

RunResult runScenario(const Scenario& scenario);
bool writeAtomicReport(const QString& path, const QJsonObject& report, QString* error = nullptr);
QJsonObject checkReport();
QString modeName(Mode mode);
QString skinName(Skin skin);
QString deviceClassName(DeviceClass deviceClass);

} // namespace werewolf

#endif
