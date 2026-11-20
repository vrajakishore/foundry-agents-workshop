"""
Challenge 2: Monitor with Application Insights (SDK track)
Turn on GenAI tracing and check that traces reach Application Insights.

Usage:
    python monitor.py

IMPORTANT: the tracing settings must be loaded BEFORE you import azure.ai.projects.
"""

import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv


def load_settings() -> None:
    """Load .env from this folder upwards. If there is none, use factory/.env from the setup."""
    for folder in Path(__file__).resolve().parents:
        for candidate in (folder / ".env", folder / "factory" / ".env"):
            if candidate.exists():
                load_dotenv(candidate)
                return


# Load the settings FIRST. The tracing settings must exist before the SDK is imported.
load_settings()

if os.getenv("AZURE_EXPERIMENTAL_ENABLE_GENAI_TRACING") != "true":
    print("❌ AZURE_EXPERIMENTAL_ENABLE_GENAI_TRACING is not set to 'true' in .env")
    print("   Add: AZURE_EXPERIMENTAL_ENABLE_GENAI_TRACING=true")
    sys.exit(1)

PROJECT_CONNECTION_STRING = os.getenv("PROJECT_CONNECTION_STRING")
MODEL_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-5.4")
APPINSIGHTS_CONN_STRING = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")


def setup_tracing():
    """Configure OpenTelemetry instrumentation and the Azure Monitor exporter."""
    print("=== Setting up tracing ===")
    print("✅ AZURE_EXPERIMENTAL_ENABLE_GENAI_TRACING is enabled")

    from azure.ai.projects.telemetry import AIProjectInstrumentor
    AIProjectInstrumentor().instrument()
    print("✅ AIProjectInstrumentor configured")

    from azure.monitor.opentelemetry import configure_azure_monitor
    configure_azure_monitor(connection_string=APPINSIGHTS_CONN_STRING, enable_live_metrics=True)
    print("✅ Azure Monitor exporter connected")


def run_traced_agent_call():
    """Make an agent call that is captured as a trace."""
    print("\n=== Running a traced agent call ===")

    from azure.ai.projects import AIProjectClient
    from azure.ai.projects.models import PromptAgentDefinition
    from azure.identity import DefaultAzureCredential

    client = AIProjectClient(endpoint=PROJECT_CONNECTION_STRING, credential=DefaultAzureCredential())
    openai_client = client.get_openai_client()

    agent = client.agents.create_version(
        agent_name="tracing-test-agent",
        definition=PromptAgentDefinition(
            model=MODEL_DEPLOYMENT_NAME,
            instructions=(
                "You are a portfolio monitoring assistant for Woodgrove Finance, a retail lender. "
                "Use the early-warning batch in the message and return a short risk summary by status."
            ),
        ),
    )

    conversation = openai_client.conversations.create()
    response = openai_client.responses.create(
        input=(
            "Summarise this early-warning batch by status.\n"
            "lender: Woodgrove Finance\n"
            "scan: monthly early-warning scan, 20 November 2026\n"
            "accounts: HL-1001 normal, LAP-1002 watch, UBL-1003 critical, UCL-1004 normal, PL-1005 watch\n"
            "tool_reference: check_account_signals"
        ),
        conversation=conversation.id,
        extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
    )
    print(f"✅ Agent responded: {response.output_text[:100]}...")

    openai_client.conversations.delete(conversation_id=conversation.id)
    client.agents.delete_version(agent_name=agent.name, agent_version=agent.version)
    client.close()


def verify_traces():
    """Wait for the traces to arrive in Application Insights."""
    print("\n=== Verifying traces in Application Insights ===")

    if not APPINSIGHTS_CONN_STRING:
        print("⚠️  APPLICATIONINSIGHTS_CONNECTION_STRING is not set. Skipping the check.")
        print("   You can still check the traces in the Azure portal.")
        return

    print("⏳ Waiting 30 seconds for the traces to arrive...")
    time.sleep(30)
    print("✅ The traces should now show in Application Insights")
    print("   Go to: Azure portal → Application Insights → Investigate → Search")
    print("   Filter: last 30 minutes")


def main():
    if not PROJECT_CONNECTION_STRING:
        print("❌ PROJECT_CONNECTION_STRING is not set. Complete Challenge 0 first.")
        sys.exit(1)

    setup_tracing()
    run_traced_agent_call()
    verify_traces()
    print("\n🎉 Monitoring is active. Open Application Insights for the full trace view.")


if __name__ == "__main__":
    main()
