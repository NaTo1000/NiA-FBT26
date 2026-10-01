#include "werewolf/werewolf.h"

#include <QFile>
#include <QJsonDocument>
#include <QProcess>
#include <QRandomGenerator>
#include <QTemporaryDir>
#include <QTest>

#include <stdexcept>
#include <utility>

using namespace werewolf;

namespace {

RawAlert rawAlert(QString target = "target", QString id = "alert-1", bool trusted = true)
{
    return {std::move(id), "simulation-detector", std::move(target),
            "simulated protected-route access", 4, trusted};
}

VerifiedAttackAlert verified(QString target = "target", QString id = "alert-1")
{
    const auto result = SimulationAlertVerifier().verify(rawAlert(target, id));
    Q_ASSERT(result);
    return *result;
}

NearbyDevice device(QString id = "target", DeviceClass type = DeviceClass::Flipper,
                    QString beacon = "beacon-1", qint64 issued = 990, qint64 expires = 1010)
{
    return {std::move(id), type, -40, true, true, 30, false,
            std::move(beacon), issued, expires};
}

QByteArray minimalScenario(const QByteArray& devices = "[]")
{
    return "{\"schema_version\":1,\"current_time\":1000,\"devices\":" + devices + "}";
}

}

class WerewolfTests : public QObject
{
    Q_OBJECT

private slots:
    void proximityNeverActivates();
    void verifierBoundaryFailsClosed();
    void targetBoundSingleUseDefence();
    void energyRequiresIncident();
    void replayExpiryAndCaps();
    void parserStrictness();
    void parserSizeAndDuplicates();
    void atomicReportError();
    void cliParity();
    void adversarialInvariants();
    void goldenFixture();
};

void WerewolfTests::proximityNeverActivates()
{
    Engine engine([] { return 1000; });
    QCOMPARE(engine.scan({device()}).accepted, 1);
    QCOMPARE(engine.state().mode, Mode::Dormant);
    QCOMPARE(engine.state().metrics.attacksDetected, 0);
}

void WerewolfTests::verifierBoundaryFailsClosed()
{
    QString error;
    QVERIFY(!SimulationAlertVerifier().verify(rawAlert("target", "raw", false), &error));
    QVERIFY(!error.isEmpty());
    Engine engine([] { return 1000; });
    engine.rejectRawAlert("raw");
    QCOMPARE(engine.state().mode, Mode::Dormant);
    QCOMPARE(engine.state().metrics.invalidAlerts, 1);
}

void WerewolfTests::targetBoundSingleUseDefence()
{
    DryRunContainmentAdapter adapter;
    Engine engine([] { return 1000; }, &adapter);
    QVERIFY(engine.reportAttack(verified()));
    QVERIFY_EXCEPTION_THROWN(engine.defend(device("other")), std::runtime_error);
    QCOMPARE(engine.defend(device()), QString("blocked"));
    QCOMPARE(adapter.requests().size(), size_t(1));
    QCOMPARE(adapter.requests().front().action, QString("block_and_isolate"));
    QVERIFY_EXCEPTION_THROWN(engine.defend(device()), std::runtime_error);
}

void WerewolfTests::energyRequiresIncident()
{
    Engine dormant([] { return 1000; });
    dormant.scan({device("source", DeviceClass::Pineapple)});
    QCOMPARE(dormant.state().energy, 20);
    QVERIFY_EXCEPTION_THROWN(dormant.chargeShield(1), std::runtime_error);

    Engine active([] { return 1000; });
    active.reportAttack(verified());
    active.scan({device("source", DeviceClass::Pineapple)});
    QCOMPARE(active.state().energy, 50);
    QCOMPARE(active.chargeShield(25), 25);
}

void WerewolfTests::replayExpiryAndCaps()
{
    qint64 now = 1000;
    Engine engine([&] { return now; });
    QCOMPARE(engine.scan({device()}).accepted, 1);
    QCOMPARE(engine.scan({device()}).rejectionReasons.value("target").toString(),
             QString("replayed"));
    now = 1012;
    QCOMPARE(engine.scan({device("target", DeviceClass::Flipper, "beacon-1", 1012, 1020)}).accepted, 1);

    std::vector<NearbyDevice> full;
    full.reserve(LiveBeaconReplayCap);
    for (int index = 0; index < LiveBeaconReplayCap; ++index)
        full.push_back(device(QString("d-%1").arg(index), DeviceClass::Nano,
                              QString("b-%1").arg(index), 1012, 1020));
    Engine capped([&] { return now; });
    QCOMPARE(capped.scan(full).accepted, LiveBeaconReplayCap);
    QCOMPARE(capped.scan({device("overflow", DeviceClass::Nano, "overflow", 1012, 1020)})
                 .rejectionReasons.value("overflow").toString(),
             QString("replay_store_full"));
    QCOMPARE(capped.liveBeaconReplaySize(), LiveBeaconReplayCap);
}

void WerewolfTests::parserStrictness()
{
    ScenarioAdapter parser;
    QVERIFY_EXCEPTION_THROWN(parser.parse("{}"), std::runtime_error);
    QVERIFY_EXCEPTION_THROWN(parser.parse(
        "{\"schema_version\":2,\"current_time\":1000,\"devices\":[]}"), std::runtime_error);
    QVERIFY_EXCEPTION_THROWN(parser.parse(
        "{\"schema_version\":1,\"current_time\":1000,\"devices\":[],\"security\":{}}"),
        std::runtime_error);
    QVERIFY_EXCEPTION_THROWN(parser.parse(
        "{\"schema_version\":1,\"current_time\":1000,\"devices\":[],"
        "\"attack_alert\":{\"alert_id\":\"a\",\"detector\":\"d\",\"target_device_id\":\"t\","
        "\"reason\":\"r\",\"severity\":1,\"simulation_trusted\":\"true\"}}"),
        std::runtime_error);
    QVERIFY_EXCEPTION_THROWN(parser.parse(
        "{\"schema_version\":1,\"current_time\":1000.5,\"devices\":[]}"), std::runtime_error);
}

void WerewolfTests::parserSizeAndDuplicates()
{
    ScenarioAdapter parser;
    QVERIFY_EXCEPTION_THROWN(parser.parse(QByteArray(ScenarioByteCap + 1, ' ')), std::runtime_error);
    const QByteArray one =
        "{\"device_id\":\"d\",\"device_class\":\"nano\",\"signal_dbm\":-40,"
        "\"opted_in\":true,\"game_beacon_valid\":true,\"battle_power\":0,"
        "\"connected_first\":false,\"beacon_id\":\"b\",\"issued_at\":990,\"expires_at\":1010}";
    QVERIFY_EXCEPTION_THROWN(parser.parse(minimalScenario("[" + one + "," + one + "]")),
                             std::runtime_error);
    QByteArray expired = one;
    expired.replace("\"expires_at\":1010", "\"expires_at\":999");
    QVERIFY_EXCEPTION_THROWN(parser.parse(minimalScenario("[" + expired + "]")),
                             std::runtime_error);
}

void WerewolfTests::atomicReportError()
{
    QTemporaryDir directory;
    QVERIFY(directory.isValid());
    QString error;
    QVERIFY(!writeAtomicReport(directory.path(), {{"status", "test"}}, &error));
    QVERIFY(!error.isEmpty());
}

void WerewolfTests::cliParity()
{
    QProcess process;
    process.start(WEREWOLF_CLI_PATH, {"check"});
    QVERIFY(process.waitForFinished());
    QCOMPARE(process.exitCode(), 0);
    const QJsonObject check = QJsonDocument::fromJson(process.readAllStandardOutput()).object();
    QCOMPARE(check.value("dry_run").toBool(), true);
    QCOMPARE(check.value("remote_actions").toBool(), false);

    process.start(WEREWOLF_CLI_PATH,
                  {"run", QString(WEREWOLF_FIXTURE_DIR) + "/golden-scenario-v1.json"});
    QVERIFY(process.waitForFinished());
    QCOMPARE(process.exitCode(), 0);
    const QJsonObject output = QJsonDocument::fromJson(process.readAllStandardOutput()).object();
    QCOMPARE(output.value("mode").toString(), QString("guard"));
    QCOMPARE(output.value("dry_run").toBool(), true);
}

void WerewolfTests::adversarialInvariants()
{
    QRandomGenerator random(2025);
    Engine engine([] { return 1000; });
    for (int index = 0; index < 2000; ++index) {
        switch (random.bounded(4)) {
        case 0: {
            const RawAlert raw = rawAlert(QString("t-%1").arg(random.bounded(8)),
                                          QString("a-%1").arg(index), random.bounded(2));
            auto alert = SimulationAlertVerifier().verify(raw);
            if (alert) engine.reportAttack(*alert);
            else engine.rejectRawAlert(raw.alertId);
            break;
        }
        case 1:
            engine.clearIncident();
            break;
        case 2:
            try { engine.chargeShield(random.bounded(101)); } catch (const std::runtime_error&) {}
            break;
        default:
            engine.scan({device(QString("d-%1").arg(index), DeviceClass::Nano,
                                QString("b-%1").arg(index), 990, 1010)});
        }
        QVERIFY(engine.state().energy >= 0 && engine.state().energy <= EnergyCap);
        QVERIFY(engine.state().shield >= 0 && engine.state().shield <= ShieldCap);
        QVERIFY(engine.state().events.size() <= EventCap);
        QVERIFY(engine.liveBeaconReplaySize() <= LiveBeaconReplayCap);
        QVERIFY(engine.alertReplaySize() <= AlertReplayCap);
        QVERIFY(engine.resolvedReplaySize() <= ResolvedReplayCap);
    }
}

void WerewolfTests::goldenFixture()
{
    const Scenario scenario = ScenarioAdapter().loadFile(
        QString(WEREWOLF_FIXTURE_DIR) + "/golden-scenario-v1.json");
    const RunResult result = runScenario(scenario);
    QCOMPARE(result.acceptedDevices, 2);
    QCOMPARE(result.containmentRequests, 1);
    QCOMPARE(result.state.skin, Skin::Secured);
    QCOMPARE(result.state.metrics.attacksBlocked, 1);
}

QTEST_APPLESS_MAIN(WerewolfTests)
#include "werewolf_tests.moc"
