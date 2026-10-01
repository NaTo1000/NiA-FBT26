#include "gui/werewolf_widget.h"
#include "werewolf/werewolf.h"

#include <QFileDialog>
#include <QFrame>
#include <QFormLayout>
#include <QGroupBox>
#include <QHeaderView>
#include <QHBoxLayout>
#include <QJsonDocument>
#include <QLabel>
#include <QMessageBox>
#include <QPlainTextEdit>
#include <QPushButton>
#include <QTableWidget>
#include <QTableWidgetItem>
#include <QVBoxLayout>

WerewolfWidget::WerewolfWidget(QWidget* parent)
    : QWidget(parent)
{
    setObjectName("werewolfWidget");
    auto* layout = new QVBoxLayout(this);
    auto* heading = new QLabel("<h2>Defensive Simulation</h2>", this);
    auto* explanation = new QLabel(
        "Local dry-run only. Proximity never activates defence; only a scenario verifier-issued "
        "alert can. No hardware, network, serial, firmware, retaliation, or OS policy actions.",
        this);
    explanation->setWordWrap(true);
    layout->addWidget(heading);
    layout->addWidget(explanation);

    auto* controls = new QHBoxLayout;
    auto* load = new QPushButton("Load scenario", this);
    m_runButton = new QPushButton("Run simulation", this);
    auto* clear = new QPushButton("Clear", this);
    m_runButton->setEnabled(false);
    m_fileLabel = new QLabel("No scenario loaded", this);
    controls->addWidget(load);
    controls->addWidget(m_runButton);
    controls->addWidget(clear);
    controls->addWidget(m_fileLabel, 1);
    layout->addLayout(controls);

    auto* stateBox = new QGroupBox("Simulation state", this);
    auto* stateLayout = new QHBoxLayout(stateBox);
    m_modeBadge = new QLabel("Mode: dormant", stateBox);
    m_skinBadge = new QLabel("Skin: werewolf", stateBox);
    m_energyBadge = new QLabel("Energy: 20 / 100", stateBox);
    m_shieldBadge = new QLabel("Shield: 0 / 60", stateBox);
    for (QLabel* badge : {m_modeBadge, m_skinBadge, m_energyBadge, m_shieldBadge}) {
        badge->setFrameStyle(QFrame::StyledPanel | QFrame::Sunken);
        badge->setMargin(6);
        stateLayout->addWidget(badge);
    }
    layout->addWidget(stateBox);

    m_metrics = new QTableWidget(0, 2, this);
    m_metrics->setHorizontalHeaderLabels({"Metric", "Value"});
    m_metrics->horizontalHeader()->setStretchLastSection(true);
    m_metrics->verticalHeader()->setVisible(false);
    m_metrics->setEditTriggers(QAbstractItemView::NoEditTriggers);
    m_events = new QPlainTextEdit(this);
    m_events->setReadOnly(true);
    m_events->setPlaceholderText("Structured simulation events");
    layout->addWidget(new QLabel("Metrics", this));
    layout->addWidget(m_metrics, 1);
    layout->addWidget(new QLabel("Events and limitations", this));
    layout->addWidget(m_events, 1);
    m_events->setPlainText(
        "Limitations: simulation verifier only; no production authentication; no hardware "
        "integration; no OS containment; local isolation requests are recorded but not executed.");

    connect(load, &QPushButton::clicked, this, &WerewolfWidget::loadScenario);
    connect(m_runButton, &QPushButton::clicked, this, &WerewolfWidget::runLoadedScenario);
    connect(clear, &QPushButton::clicked, this, &WerewolfWidget::clearResult);
}

void WerewolfWidget::loadScenario()
{
    const QString path = QFileDialog::getOpenFileName(
        this, "Load defensive simulation scenario", {}, "JSON scenarios (*.json)");
    if (path.isEmpty()) return;
    try {
        werewolf::ScenarioAdapter().loadFile(path);
        m_scenarioPath = path;
        m_fileLabel->setText(path);
        m_runButton->setEnabled(true);
    } catch (const std::exception& error) {
        showError(QString::fromUtf8(error.what()));
    }
}

void WerewolfWidget::runLoadedScenario()
{
    try {
        const auto scenario = werewolf::ScenarioAdapter().loadFile(m_scenarioPath);
        renderState(werewolf::runScenario(scenario).state.toJson());
    } catch (const std::exception& error) {
        showError(QString::fromUtf8(error.what()));
    }
}

void WerewolfWidget::clearResult()
{
    m_scenarioPath.clear();
    m_fileLabel->setText("No scenario loaded");
    m_runButton->setEnabled(false);
    m_modeBadge->setText("Mode: dormant");
    m_skinBadge->setText("Skin: werewolf");
    m_energyBadge->setText("Energy: 20 / 100");
    m_shieldBadge->setText("Shield: 0 / 60");
    m_metrics->setRowCount(0);
    m_events->setPlainText(
        "Limitations: simulation verifier only; no production authentication; no hardware "
        "integration; no OS containment; local isolation requests are recorded but not executed.");
}

void WerewolfWidget::showError(const QString& message)
{
    QMessageBox::critical(this, "Defensive simulation rejected", message);
}

void WerewolfWidget::renderState(const QJsonObject& state)
{
    m_modeBadge->setText("Mode: " + state.value("mode").toString());
    m_skinBadge->setText("Skin: " + state.value("skin").toString());
    m_energyBadge->setText(QStringLiteral("Energy: %1 / 100").arg(state.value("energy").toInt()));
    m_shieldBadge->setText(QStringLiteral("Shield: %1 / 60").arg(state.value("shield").toInt()));
    const QJsonObject metrics = state.value("metrics").toObject();
    m_metrics->setRowCount(metrics.size());
    int row = 0;
    for (auto it = metrics.begin(); it != metrics.end(); ++it, ++row) {
        m_metrics->setItem(row, 0, new QTableWidgetItem(it.key()));
        m_metrics->setItem(row, 1, new QTableWidgetItem(
            it.value().isObject()
                ? QString::fromUtf8(QJsonDocument(it.value().toObject()).toJson(QJsonDocument::Compact))
                : it.value().toVariant().toString()));
    }
    m_events->setPlainText(
        QString::fromUtf8(QJsonDocument(state.value("event_log").toArray())
                              .toJson(QJsonDocument::Indented))
        + "\nLimitations: dry-run local requested isolation only; simulation verifier is "
          "unavailable for production; no hardware/authentication/OS/network/serial/firmware action.");
}
