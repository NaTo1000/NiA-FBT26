#include "werewolf/werewolf.h"

#include <QFile>
#include <QDateTime>
#include <QJsonDocument>
#include <QJsonParseError>
#include <QSaveFile>

#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <utility>

namespace werewolf {
namespace {

std::runtime_error inputError(const QString& message)
{
    return std::runtime_error(message.toStdString());
}

void requireFields(const QJsonObject& object, const QStringList& allowed,
                   const QStringList& required, const QString& context)
{
    for (auto it = object.begin(); it != object.end(); ++it) {
        if (!allowed.contains(it.key())) {
            throw inputError(QStringLiteral("%1 contains unknown field '%2'").arg(context, it.key()));
        }
    }
    for (const QString& field : required) {
        if (!object.contains(field)) {
            throw inputError(QStringLiteral("%1 is missing '%2'").arg(context, field));
        }
    }
}

QString strictString(const QJsonObject& object, const QString& key, const QString& context)
{
    const QJsonValue value = object.value(key);
    if (!value.isString() || value.toString().trimmed().isEmpty() || value.toString().size() > 256) {
        throw inputError(QStringLiteral("%1.%2 must be a non-empty string of at most 256 characters")
                             .arg(context, key));
    }
    return value.toString();
}

bool strictBool(const QJsonObject& object, const QString& key, const QString& context)
{
    if (!object.value(key).isBool()) {
        throw inputError(QStringLiteral("%1.%2 must be a boolean").arg(context, key));
    }
    return object.value(key).toBool();
}

qint64 strictInteger(const QJsonObject& object, const QString& key, qint64 minimum,
                     qint64 maximum, const QString& context)
{
    const QJsonValue value = object.value(key);
    if (!value.isDouble()) {
        throw inputError(QStringLiteral("%1.%2 must be an integer").arg(context, key));
    }
    const double number = value.toDouble();
    if (number != std::floor(number) || number < minimum || number > maximum) {
        throw inputError(QStringLiteral("%1.%2 is outside the allowed integer range")
                             .arg(context, key));
    }
    return static_cast<qint64>(number);
}

DeviceClass parseDeviceClass(const QString& value)
{
    static const std::vector<std::pair<QString, DeviceClass>> values = {
        {"flipper", DeviceClass::Flipper}, {"pwnagotchi", DeviceClass::Pwnagotchi},
        {"bjorn", DeviceClass::Bjorn}, {"tamafi", DeviceClass::Tamafi},
        {"pineapple", DeviceClass::Pineapple}, {"phones64", DeviceClass::Phones64},
        {"wifi7", DeviceClass::Wifi7}, {"nano", DeviceClass::Nano},
        {"sharkbite", DeviceClass::Sharkbite}, {"other", DeviceClass::Other},
    };
    const auto found = std::find_if(values.begin(), values.end(),
                                    [&](const auto& item) { return item.first == value; });
    if (found == values.end()) {
        throw inputError(QStringLiteral("Unknown device_class '%1'").arg(value));
    }
    return found->second;
}

bool isTarget(DeviceClass value)
{
    return value == DeviceClass::Flipper || value == DeviceClass::Pwnagotchi
        || value == DeviceClass::Bjorn || value == DeviceClass::Tamafi;
}

int energyValue(DeviceClass value)
{
    switch (value) {
    case DeviceClass::Pineapple: return 30;
    case DeviceClass::Phones64: return 24;
    case DeviceClass::Wifi7: return 20;
    case DeviceClass::Nano: return 16;
    case DeviceClass::Sharkbite: return 26;
    default: return 0;
    }
}

QJsonObject metricsJson(const Metrics& metrics)
{
    return {
        {"scans", metrics.scans}, {"devices_seen", metrics.devicesSeen},
        {"opted_in_devices", metrics.optedInDevices}, {"ignored_devices", metrics.ignoredDevices},
        {"invalid_beacons", metrics.invalidBeacons}, {"expired_beacons", metrics.expiredBeacons},
        {"replayed_beacons", metrics.replayedBeacons}, {"invalid_alerts", metrics.invalidAlerts},
        {"attacks_detected", metrics.attacksDetected},
        {"guard_mode_entries", metrics.guardModeEntries},
        {"energy_collected", metrics.energyCollected},
        {"defence_actions", metrics.defenceActions}, {"attacks_blocked", metrics.attacksBlocked},
        {"defence_failures", metrics.defenceFailures}, {"shields_used", metrics.shieldsUsed},
        {"protected_sessions", metrics.protectedSessions},
        {"detections_by_class", metrics.detectionsByClass},
    };
}

} // namespace

VerifiedAttackAlert::VerifiedAttackAlert(QString alertId, QString detector,
                                         QString targetDeviceId, QString reason, int severity)
    : alertId_(std::move(alertId)), detector_(std::move(detector)),
      targetDeviceId_(std::move(targetDeviceId)), reason_(std::move(reason)),
      severity_(severity)
{
}

std::optional<VerifiedAttackAlert> SimulationAlertVerifier::verify(
    const RawAlert& raw, QString* error) const
{
    const bool valid = raw.simulationTrusted && !raw.alertId.trimmed().isEmpty()
        && !raw.detector.trimmed().isEmpty() && !raw.targetDeviceId.trimmed().isEmpty()
        && !raw.reason.trimmed().isEmpty() && raw.severity >= 1 && raw.severity <= 5;
    if (!valid) {
        if (error) *error = QStringLiteral("simulation alert failed closed verification");
        return std::nullopt;
    }
    return VerifiedAttackAlert(raw.alertId, raw.detector, raw.targetDeviceId,
                               raw.reason, raw.severity);
}

QString modeName(Mode mode)
{
    switch (mode) {
    case Mode::Dormant: return QStringLiteral("dormant");
    case Mode::Guard: return QStringLiteral("guard");
    case Mode::Defence: return QStringLiteral("defence");
    }
    return {};
}

QString skinName(Skin skin)
{
    switch (skin) {
    case Skin::Werewolf: return QStringLiteral("werewolf");
    case Skin::FullMoon: return QStringLiteral("full_moon");
    case Skin::Shielded: return QStringLiteral("shielded");
    case Skin::Secured: return QStringLiteral("secured");
    case Skin::Wounded: return QStringLiteral("wounded");
    }
    return {};
}

QString deviceClassName(DeviceClass deviceClass)
{
    switch (deviceClass) {
    case DeviceClass::Flipper: return "flipper";
    case DeviceClass::Pwnagotchi: return "pwnagotchi";
    case DeviceClass::Bjorn: return "bjorn";
    case DeviceClass::Tamafi: return "tamafi";
    case DeviceClass::Pineapple: return "pineapple";
    case DeviceClass::Phones64: return "phones64";
    case DeviceClass::Wifi7: return "wifi7";
    case DeviceClass::Nano: return "nano";
    case DeviceClass::Sharkbite: return "sharkbite";
    case DeviceClass::Other: return "other";
    }
    return {};
}

QJsonObject State::toJson() const
{
    return {
        {"mode", modeName(mode)}, {"skin", skinName(skin)}, {"energy", energy},
        {"shield", shield}, {"score", score}, {"streak", streak},
        {"last_target", lastTarget.isEmpty() ? QJsonValue(QJsonValue::Null)
                                              : QJsonValue(lastTarget)},
        {"assistant_messages", assistantMessages}, {"metrics", metricsJson(metrics)},
        {"event_log", events}, {"dry_run", true}, {"remote_actions", false},
    };
}

void DryRunContainmentAdapter::requestLocalIsolation(const VerifiedAttackAlert& alert)
{
    requests_.push_back({alert.alertId(), alert.targetDeviceId(), "block_and_isolate"});
}

Engine::Engine(Clock clock, DryRunContainmentAdapter* containment)
    : clock_(std::move(clock)), containment_(containment)
{
    state_.assistantMessages = {
        {"guardian", "Dormant. Defence activates only on a verifier-issued alert."},
        {"privacy_sentinel", "No privacy warning."},
        {"update_guide", "No firmware update is active."},
    };
}

bool Engine::reportAttack(const VerifiedAttackAlert& alert)
{
    if (seenAlerts_.count(alert.alertId())) {
        rejectRawAlert(alert.alertId());
        return false;
    }
    activeAlert_ = alert;
    remember(alertOrder_, seenAlerts_, alert.alertId(), AlertReplayCap);
    ++state_.metrics.attacksDetected;
    if (state_.mode == Mode::Dormant) ++state_.metrics.guardModeEntries;
    state_.mode = Mode::Guard;
    state_.skin = Skin::FullMoon;
    state_.lastTarget = alert.targetDeviceId();
    event("guard_mode", {{"alert_id", alert.alertId()}, {"detector", alert.detector()},
                         {"reason", alert.reason()}, {"severity", alert.severity()},
                         {"target_device_id", alert.targetDeviceId()}});
    state_.assistantMessages["guardian"] =
        "Verified simulation alert active. Isolate only the affected local session.";
    assertInvariants();
    return true;
}

void Engine::rejectRawAlert(const QString& alertId)
{
    ++state_.metrics.invalidAlerts;
    event("alert_rejected", {{"alert_id", alertId}});
}

void Engine::pruneBeacons(qint64 now)
{
    for (auto it = seenBeacons_.begin(); it != seenBeacons_.end();) {
        if (it->second < now) it = seenBeacons_.erase(it);
        else ++it;
    }
}

ScanResult Engine::scan(const std::vector<NearbyDevice>& devices)
{
    ScanResult result;
    ++state_.metrics.scans;
    state_.metrics.devicesSeen += static_cast<int>(devices.size());
    const qint64 now = clock_();
    pruneBeacons(now);

    for (const NearbyDevice& device : devices) {
        QString reason;
        if (!device.optedIn || !device.gameBeaconValid || device.beaconId.isEmpty()
            || device.expiresAt < device.issuedAt
            || device.expiresAt - device.issuedAt > BeaconLifetimeSeconds
            || device.issuedAt > now) {
            reason = "invalid";
            ++state_.metrics.invalidBeacons;
        } else if (device.expiresAt < now) {
            reason = "expired";
            ++state_.metrics.expiredBeacons;
        } else if (seenBeacons_.count(device.beaconId)) {
            reason = "replayed";
            ++state_.metrics.replayedBeacons;
        } else if (static_cast<int>(seenBeacons_.size()) >= LiveBeaconReplayCap) {
            reason = "replay_store_full";
            ++state_.metrics.invalidBeacons;
        }

        if (!reason.isEmpty()) {
            ++result.ignored;
            result.rejectionReasons[device.deviceId] = reason;
            continue;
        }

        seenBeacons_[device.beaconId] = device.expiresAt;
        ++result.accepted;
        ++state_.metrics.optedInDevices;
        const QString className = deviceClassName(device.deviceClass);
        state_.metrics.detectionsByClass[className] =
            state_.metrics.detectionsByClass.value(className).toInt() + 1;
        const int sourceEnergy = activeAlert_ ? energyValue(device.deviceClass) : 0;
        const int gained = std::min(sourceEnergy, EnergyCap - state_.energy);
        if (gained > 0) {
            state_.energy += gained;
            state_.metrics.energyCollected += gained;
            event("energy_collected", {{"device_id", device.deviceId},
                                       {"device_class", className}, {"amount", gained}});
        }
    }
    state_.metrics.ignoredDevices += result.ignored;
    state_.assistantMessages["privacy_sentinel"] = result.ignored
        ? QStringLiteral("Ignored %1 invalid, replayed, expired, or non-consenting beacon(s).")
              .arg(result.ignored)
        : QStringLiteral("Observed simulation beacons passed strict validation.");
    assertInvariants();
    return result;
}

int Engine::chargeShield(int amount)
{
    if (!activeAlert_) throw inputError("Shield charging requires an active verified alert");
    if (amount < 0) throw inputError("shield charge must not be negative");
    const int transferred = std::min({amount, state_.energy, ShieldCap - state_.shield});
    state_.energy -= transferred;
    state_.shield += transferred;
    if (transferred) {
        state_.skin = Skin::Shielded;
        event("shield_charged", {{"amount", transferred}});
    }
    assertInvariants();
    return transferred;
}

QString Engine::defend(const NearbyDevice& opponent)
{
    if (!activeAlert_ || activeAlert_->targetDeviceId() != opponent.deviceId)
        throw inputError("Defence requires a verifier-issued alert bound to this target");
    if (resolvedAlerts_.count(activeAlert_->alertId()))
        throw inputError("This attack alert has already been resolved");
    if (!isTarget(opponent.deviceClass))
        throw inputError("Target is not a recognized defensive profile");

    state_.mode = Mode::Defence;
    ++state_.metrics.defenceActions;
    const int initiative = opponent.connectedFirst ? 10 : 20;
    const int threat = opponent.battlePower + (opponent.connectedFirst ? 20 : 0);
    const int protection = state_.energy + state_.shield + initiative;
    const int shieldSpent = std::min(state_.shield, std::max(0, threat - state_.energy));
    state_.shield -= shieldSpent;
    if (shieldSpent) ++state_.metrics.shieldsUsed;

    const bool blocked = protection >= threat;
    if (blocked) {
        ++state_.metrics.attacksBlocked;
        ++state_.metrics.protectedSessions;
        state_.score += 100 + state_.streak * 25;
        ++state_.streak;
        state_.skin = Skin::Secured;
    } else {
        ++state_.metrics.defenceFailures;
        state_.streak = 0;
        state_.skin = Skin::Wounded;
    }
    state_.energy = std::max(0, state_.energy - 15);
    state_.mode = Mode::Guard;
    remember(resolvedOrder_, resolvedAlerts_, activeAlert_->alertId(), ResolvedReplayCap);
    if (containment_) containment_->requestLocalIsolation(*activeAlert_);
    event("defence", {{"opponent_id", opponent.deviceId},
                      {"opponent_class", deviceClassName(opponent.deviceClass)},
                      {"opponent_connected_first", opponent.connectedFirst},
                      {"outcome", blocked ? "blocked" : "defence_failed"},
                      {"response", "block_and_isolate"}});
    assertInvariants();
    return blocked ? QStringLiteral("blocked") : QStringLiteral("defence_failed");
}

void Engine::clearIncident()
{
    activeAlert_.reset();
    state_.mode = Mode::Dormant;
    state_.skin = Skin::Werewolf;
    state_.lastTarget.clear();
    event("incident_cleared");
    state_.assistantMessages["guardian"] =
        "Dormant. Defence activates only on a verifier-issued alert.";
    assertInvariants();
}

void Engine::event(const QString& type, const QJsonObject& details)
{
    QJsonObject value = details;
    value["type"] = type;
    value["timestamp_utc"] =
        QDateTime::fromSecsSinceEpoch(clock_()).toUTC().toString(Qt::ISODate);
    state_.events.append(value);
    while (state_.events.size() > EventCap) state_.events.removeAt(0);
}

void Engine::remember(std::deque<QString>& order, std::unordered_set<QString>& ids,
                      const QString& id, int cap)
{
    ids.insert(id);
    order.push_back(id);
    const QString protectedId = activeAlert_ ? activeAlert_->alertId() : QString();
    while (static_cast<int>(order.size()) > cap) {
        const QString oldest = order.front();
        order.pop_front();
        if (oldest == protectedId) order.push_back(oldest);
        else ids.erase(oldest);
    }
}

void Engine::assertInvariants() const
{
    if (state_.energy < 0 || state_.energy > EnergyCap
        || state_.shield < 0 || state_.shield > ShieldCap
        || state_.events.size() > EventCap
        || seenBeacons_.size() > LiveBeaconReplayCap
        || seenAlerts_.size() > AlertReplayCap
        || resolvedAlerts_.size() > ResolvedReplayCap
        || (state_.mode != Mode::Dormant && !activeAlert_)
        || (state_.mode == Mode::Dormant && state_.skin != Skin::Werewolf)
        || state_.metrics.attacksBlocked > state_.metrics.defenceActions) {
        throw std::logic_error("Werewolf state invariant violated");
    }
}

Scenario ScenarioAdapter::loadFile(const QString& path) const
{
    QFile file(path);
    if (!file.open(QIODevice::ReadOnly))
        throw inputError(QStringLiteral("Cannot read scenario: %1").arg(file.errorString()));
    if (file.size() > ScenarioByteCap) throw inputError("Scenario exceeds the 1 MiB limit");
    return parse(file.readAll());
}

Scenario ScenarioAdapter::parse(const QByteArray& bytes) const
{
    if (bytes.size() > ScenarioByteCap) throw inputError("Scenario exceeds the 1 MiB limit");
    QJsonParseError parseError;
    const QJsonDocument document = QJsonDocument::fromJson(bytes, &parseError);
    if (parseError.error != QJsonParseError::NoError || !document.isObject())
        throw inputError(QStringLiteral("Invalid scenario JSON: %1").arg(parseError.errorString()));
    const QJsonObject root = document.object();
    requireFields(root,
                  {"schema_version", "current_time", "devices", "attack_alert",
                   "shield_charge", "attacker_device_id"},
                  {"schema_version", "current_time", "devices"}, "scenario");
    if (strictInteger(root, "schema_version", 1, 1, "scenario") != 1)
        throw inputError("Unknown scenario schema");
    Scenario scenario;
    scenario.currentTime = strictInteger(root, "current_time", 0, 4102444800LL, "scenario");
    if (!root.value("devices").isArray()) throw inputError("scenario.devices must be an array");
    if (root.value("devices").toArray().size() > LiveBeaconReplayCap)
        throw inputError("scenario.devices exceeds the live beacon cap");

    std::unordered_set<QString> deviceIds;
    std::unordered_set<QString> beaconIds;
    int index = 0;
    for (const QJsonValue& item : root.value("devices").toArray()) {
        const QString context = QStringLiteral("devices[%1]").arg(index++);
        if (!item.isObject()) throw inputError(context + " must be an object");
        const QJsonObject value = item.toObject();
        requireFields(value,
                      {"device_id", "device_class", "signal_dbm", "opted_in",
                       "game_beacon_valid", "battle_power", "connected_first",
                       "beacon_id", "issued_at", "expires_at"},
                      {"device_id", "device_class", "signal_dbm", "opted_in",
                       "game_beacon_valid", "battle_power", "connected_first",
                       "beacon_id", "issued_at", "expires_at"}, context);
        NearbyDevice device;
        device.deviceId = strictString(value, "device_id", context);
        device.deviceClass = parseDeviceClass(strictString(value, "device_class", context));
        device.signalDbm = static_cast<int>(strictInteger(value, "signal_dbm", -200, 0, context));
        device.optedIn = strictBool(value, "opted_in", context);
        device.gameBeaconValid = strictBool(value, "game_beacon_valid", context);
        device.battlePower = static_cast<int>(strictInteger(value, "battle_power", 0, 100, context));
        device.connectedFirst = strictBool(value, "connected_first", context);
        device.beaconId = strictString(value, "beacon_id", context);
        device.issuedAt = strictInteger(value, "issued_at", 0, 4102444800LL, context);
        device.expiresAt = strictInteger(value, "expires_at", 0, 4102444800LL, context);
        if (!deviceIds.insert(device.deviceId).second)
            throw inputError("Duplicate device_id");
        if (!beaconIds.insert(device.beaconId).second)
            throw inputError("Duplicate beacon_id");
        if (device.issuedAt > scenario.currentTime || device.expiresAt < scenario.currentTime
            || device.expiresAt < device.issuedAt
            || device.expiresAt - device.issuedAt > BeaconLifetimeSeconds)
            throw inputError("Scenario contains a future, expired, or overlong beacon");
        scenario.devices.push_back(device);
    }

    if (root.contains("attack_alert")) {
        if (!root.value("attack_alert").isObject())
            throw inputError("scenario.attack_alert must be an object");
        const QJsonObject value = root.value("attack_alert").toObject();
        requireFields(value,
                      {"alert_id", "detector", "target_device_id", "reason",
                       "severity", "simulation_trusted"},
                      {"alert_id", "detector", "target_device_id", "reason",
                       "severity", "simulation_trusted"}, "attack_alert");
        scenario.rawAlert = RawAlert{
            strictString(value, "alert_id", "attack_alert"),
            strictString(value, "detector", "attack_alert"),
            strictString(value, "target_device_id", "attack_alert"),
            strictString(value, "reason", "attack_alert"),
            static_cast<int>(strictInteger(value, "severity", 1, 5, "attack_alert")),
            strictBool(value, "simulation_trusted", "attack_alert"),
        };
    }
    if (root.contains("shield_charge"))
        scenario.shieldCharge = static_cast<int>(
            strictInteger(root, "shield_charge", 0, EnergyCap, "scenario"));
    if (root.contains("attacker_device_id"))
        scenario.attackerDeviceId = strictString(root, "attacker_device_id", "scenario");
    return scenario;
}

RunResult runScenario(const Scenario& scenario)
{
    DryRunContainmentAdapter containment;
    Engine engine([now = scenario.currentTime] { return now; }, &containment);
    if (scenario.rawAlert) {
        QString error;
        auto verified = SimulationAlertVerifier().verify(*scenario.rawAlert, &error);
        if (!verified) {
            engine.rejectRawAlert(scenario.rawAlert->alertId);
            throw inputError(error);
        }
        if (!engine.reportAttack(*verified)) throw inputError("Scenario alert was replayed");
    }
    const ScanResult scan = engine.scan(scenario.devices);
    if (scenario.shieldCharge) engine.chargeShield(scenario.shieldCharge);
    if (!scenario.attackerDeviceId.isEmpty()) {
        const auto found = std::find_if(scenario.devices.begin(), scenario.devices.end(),
                                        [&](const NearbyDevice& device) {
                                            return device.deviceId == scenario.attackerDeviceId;
                                        });
        if (found == scenario.devices.end())
            throw inputError("attacker_device_id must reference a scenario device");
        engine.defend(*found);
    }
    return {engine.state(), scan.accepted, scan.ignored,
            static_cast<int>(containment.requests().size())};
}

bool writeAtomicReport(const QString& path, const QJsonObject& report, QString* error)
{
    QSaveFile file(path);
    if (!file.open(QIODevice::WriteOnly)) {
        if (error) *error = file.errorString();
        return false;
    }
    if (file.write(QJsonDocument(report).toJson(QJsonDocument::Indented)) < 0 || !file.commit()) {
        if (error) *error = file.errorString();
        return false;
    }
    return true;
}

QJsonObject checkReport()
{
    return {
        {"application", "nia-werewolf"}, {"schema_version", 1}, {"status", "ready"},
        {"dry_run", true}, {"remote_actions", false},
        {"verifier", "simulation_only_unavailable_for_production"},
        {"capabilities", QJsonArray{"strict_scenario_validation",
                                    "defensive_state_simulation",
                                    "local_requested_isolation_recording",
                                    "atomic_json_reports"}},
        {"limitations", QJsonArray{"no_hardware_integration", "no_production_authentication",
                                   "no_operating_system_containment", "no_network_actions",
                                   "no_serial_actions", "no_firmware_flashing"}},
    };
}

} // namespace werewolf
