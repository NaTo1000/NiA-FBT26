"""
Code Sub-Orchestrator — Port 7100
Manages: code_generation (8001), code_review (8002), build_diagnostics (8009)
"""

from .sub_orchestrator import SubOrchestrator


class CodeSubOrchestrator(SubOrchestrator):
    domain = "code"
    port = 7100
    task_types = ["code_generation", "code_review", "build_diagnostics"]
    runner_ports = [8001, 8002, 8009]


_instance = CodeSubOrchestrator()
app = _instance.app


def main():
    _instance.run()


if __name__ == "__main__":
    main()
