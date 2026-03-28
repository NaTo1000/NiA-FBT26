"""
Analysis Sub-Orchestrator — Port 7200
Manages: signal_classifier (8005), firmware_analysis (8006),
         github_ranker (8007), log_analyzer (8008), protocol_parser (8010)
"""

from .sub_orchestrator import SubOrchestrator


class AnalysisSubOrchestrator(SubOrchestrator):
    domain = "analysis"
    port = 7200
    task_types = ["signal_classifier", "firmware_analysis", "github_ranker", "log_analyzer", "protocol_parser"]
    runner_ports = [8005, 8006, 8007, 8008, 8010]


_instance = AnalysisSubOrchestrator()
app = _instance.app


def main():
    _instance.run()


if __name__ == "__main__":
    main()
