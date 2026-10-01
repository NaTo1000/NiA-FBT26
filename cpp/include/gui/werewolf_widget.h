#ifndef WEREWOLF_WIDGET_H
#define WEREWOLF_WIDGET_H

#include <QWidget>

class QLabel;
class QPushButton;
class QPlainTextEdit;
class QTableWidget;
class QJsonObject;

class WerewolfWidget : public QWidget
{
    Q_OBJECT

public:
    explicit WerewolfWidget(QWidget* parent = nullptr);

private slots:
    void loadScenario();
    void runLoadedScenario();
    void clearResult();

private:
    void showError(const QString& message);
    void renderState(const QJsonObject& state);

    QString m_scenarioPath;
    QLabel* m_fileLabel;
    QLabel* m_modeBadge;
    QLabel* m_skinBadge;
    QLabel* m_energyBadge;
    QLabel* m_shieldBadge;
    QTableWidget* m_metrics;
    QPlainTextEdit* m_events;
    QPushButton* m_runButton;
};

#endif
