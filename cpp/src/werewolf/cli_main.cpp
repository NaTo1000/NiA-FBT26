#include "werewolf/werewolf.h"

#include <QCoreApplication>
#include <QFileInfo>
#include <QJsonDocument>
#include <QTextStream>

#include <exception>

namespace {

void printJson(const QJsonObject& value)
{
    QTextStream(stdout) << QJsonDocument(value).toJson(QJsonDocument::Indented);
}

int inputError(const QString& message)
{
    QTextStream(stderr) << "error: " << message << '\n';
    return 2;
}

}

int main(int argc, char* argv[])
{
    QCoreApplication app(argc, argv);
    app.setApplicationName("nia-werewolf");
    const QStringList arguments = app.arguments().mid(1);
    if (arguments.size() == 1 && arguments.first() == "check") {
        printJson(werewolf::checkReport());
        return 0;
    }
    if (arguments.size() < 2 || (arguments.first() != "run" && arguments.first() != "report"))
        return inputError("usage: nia-werewolf check | run SCENARIO | report SCENARIO --output FILE");

    try {
        const werewolf::Scenario scenario = werewolf::ScenarioAdapter().loadFile(arguments.at(1));
        const werewolf::RunResult result = werewolf::runScenario(scenario);
        if (arguments.first() == "run") {
            printJson(result.state.toJson());
            return 0;
        }
        if (arguments.size() != 4 || arguments.at(2) != "--output")
            return inputError("report requires --output FILE");
        QString error;
        if (!werewolf::writeAtomicReport(arguments.at(3), result.state.toJson(), &error)) {
            QTextStream(stderr) << "error: cannot write report: " << error << '\n';
            return 3;
        }
        printJson({{"status", "written"}, {"output", QFileInfo(arguments.at(3)).absoluteFilePath()},
                   {"accepted_devices", result.acceptedDevices},
                   {"ignored_devices", result.ignoredDevices},
                   {"local_isolation_requests", result.containmentRequests}});
        return 0;
    } catch (const std::exception& error) {
        return inputError(QString::fromUtf8(error.what()));
    }
}
