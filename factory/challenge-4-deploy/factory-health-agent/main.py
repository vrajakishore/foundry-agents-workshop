"""Hosted agent entry point. Serves the orchestration over the Foundry Responses protocol on port 8088.

Foundry runs each new chat in its own sandbox, so every chat starts a fresh workflow.
If you run this file on your own machine, restart it before each new health check.
"""

from agent_framework_foundry_hosting import ResponsesHostServer

from factory_orchestration import build_workflow


def main() -> None:
    agent = build_workflow().as_agent(
        name="factory-health-agent",
        description="Checks TireForge machine sensors, diagnoses faults and opens work orders after human approval.",
    )
    ResponsesHostServer(agent).run()


if __name__ == "__main__":
    main()
