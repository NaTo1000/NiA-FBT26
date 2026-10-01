#include "gui/werewolf_widget.h"

#include <QLabel>
#include <QTabWidget>
#include <QTest>

#include <algorithm>

class WerewolfGuiSmoke : public QObject
{
    Q_OBJECT
private slots:
    void exposesAccessibleSimulationState()
    {
        WerewolfWidget widget;
        QCOMPARE(widget.objectName(), QString("werewolfWidget"));
        const auto labels = widget.findChildren<QLabel*>();
        QVERIFY(std::any_of(labels.begin(), labels.end(), [](QLabel* label) {
            return label->text().contains("Defensive Simulation");
        }));
        QVERIFY(std::any_of(labels.begin(), labels.end(), [](QLabel* label) {
            return label->text().contains("Proximity never activates");
        }));
    }
};

QTEST_MAIN(WerewolfGuiSmoke)
#include "werewolf_gui_smoke.moc"
