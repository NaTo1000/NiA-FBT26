"""
Interface Sub-Orchestrator — Port 7300
Manages: nl_to_cli (8003), docs_generator (8004)
"""

from .sub_orchestrator import SubOrchestrator


class InterfaceSubOrchestrator(SubOrchestrator):
    domain = "interface"
    port = 7300
    task_types = ["nl_to_cli", "docs_generator"]
    runner_ports = [8003, 8004]


_instance = InterfaceSubOrchestrator()
app = _instance.app


def main():
    _instance.run()


if __name__ == "__main__":
    main()
