"""TireForge factory health check: a sequential multi-agent orchestration built with Microsoft Agent Framework.

anomaly-detection-agent  ->  fault-diagnosis-agent  ->  create_work_order (needs human approval)

Used by run_local.py (console) and main.py (hosted agent).
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import urlparse

from agent_framework import Agent, AgentExecutor, Message, Workflow, tool
from agent_framework.foundry import FoundryChatClient
from agent_framework.orchestrations import SequentialBuilder
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from pydantic import Field

HERE = Path(__file__).resolve().parent
SENSOR_DATA_PATH = HERE / "sensor_data.json"

# Locally, settings come from factory/.env. When hosted, Foundry sets FOUNDRY_PROJECT_ENDPOINT
# and azure.yaml sets AZURE_AI_MODEL_DEPLOYMENT_NAME.
for folder in HERE.parents:
    if (folder / ".env").exists():
        load_dotenv(folder / ".env")
        break


@tool(approval_mode="never_require")
def check_thresholds(
    machine_id: Annotated[str, Field(description="Machine ID, for example 'CP-003', or name, for example 'curing_press'.")],
) -> str:
    """Check a machine's latest sensor readings against its normal operating thresholds."""
    machines = json.loads(SENSOR_DATA_PATH.read_text())["machines"]
    machine = next((m for m in machines if machine_id in (m["machine_id"], m["name"])), None)
    if machine is None:
        return json.dumps({"error": f"Machine '{machine_id}' not found"})

    anomalies = []
    for sensor, reading in machine["readings"].items():
        value, limits = reading["value"], machine["thresholds"][sensor]
        if value > limits["max"]:
            anomalies.append(f"{sensor} {value} {reading['unit']} is {(value - limits['max']) / limits['max']:.1%} above max {limits['max']}")
        elif value < limits["min"]:
            anomalies.append(f"{sensor} {value} {reading['unit']} is {(limits['min'] - value) / limits['min']:.1%} below min {limits['min']}")

    return json.dumps(
        {
            "machine_id": machine["machine_id"],
            "name": machine["name"],
            "status": machine["status"],
            "last_maintenance": machine["last_maintenance"],
            "anomalies": anomalies,
        }
    )


@tool(approval_mode="always_require")
def create_work_order(
    machine_id: Annotated[str, Field(description="Machine ID, for example 'CP-003'.")],
    urgency: Annotated[Literal["IMMEDIATE", "WITHIN 24H"], Field(description="How soon the work must start.")],
    summary: Annotated[str, Field(description="One-line description of the fault and the maintenance action.")],
) -> str:
    """Open a maintenance work order. A maintenance supervisor must approve it before it is created."""
    # Simulated. In production this would call your CMMS, for example SAP PM, Maximo or ServiceNow.
    work_order_id = f"WO-{machine_id}-{datetime.now(timezone.utc):%Y%m%d%H%M}"
    return json.dumps({"work_order_id": work_order_id, "machine_id": machine_id, "urgency": urgency, "summary": summary, "status": "created"})


ANOMALY_INSTRUCTIONS = """
You are an industrial sensor anomaly detection expert for TireForge Industries.
The plant has five machines: MX-001, EX-002, CP-003, CU-004 and IS-005.
Use the check_thresholds tool for every machine, unless the user names specific machines.
For each machine, report its name, ID, status (normal, warning or critical) and every out-of-spec reading
with its value, the threshold it breaks and the deviation. Be concise and structured.
Report facts only. Never mention work orders or maintenance actions; the fault diagnosis agent handles them.
"""

DIAGNOSIS_INSTRUCTIONS = """
You are a mechanical fault diagnosis expert for TireForge Industries.
Read the anomaly report in the conversation. For each machine with anomalies:
1. Identify the most likely root cause:
   - High temperature + high pressure: likely blockage or restricted flow
   - High vibration alone: likely bearing wear, misalignment or imbalance
   - High temperature + high vibration: likely bearing failure or lubrication issue
   - Several sensors critical: compound failure, escalate immediately
2. Recommend specific maintenance actions.
3. Set urgency: IMMEDIATE (stop now), WITHIN 24H or MONITOR.
Before you write your answer, call create_work_order once for every machine with urgency IMMEDIATE.
A human must approve each call, so never skip it and never invent a work order.
Report a work order as created only if the tool returned a work_order_id, and quote that ID.
If the call was rejected, say the work order was rejected.
Format each machine as: MACHINE, LIKELY CAUSE, MAINTENANCE ACTIONS, URGENCY.
Finish with a short factory health summary that lists the work orders created or rejected.
"""


def text_only(conversation: list[Message]) -> list[Message]:
    """Hand the next agent the user request and the anomaly report as plain text, without the first agent's tool calls."""
    return [Message(m.role, [m.text], author_name=m.author_name) for m in conversation if m.role in ("user", "assistant") and m.text]


def make_client():
    """Sign in with Entra ID by default. If FOUNDRY_API_KEY is set (local runs only), call the model with the key instead."""
    endpoint = os.getenv("FOUNDRY_PROJECT_ENDPOINT") or os.environ["PROJECT_CONNECTION_STRING"]
    model = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME") or os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-5.4")
    api_key = os.getenv("FOUNDRY_API_KEY")
    if api_key:
        from agent_framework.openai import OpenAIChatClient

        resource = urlparse(endpoint).hostname.split(".")[0]
        return OpenAIChatClient(model=model, api_key=api_key, base_url=f"https://{resource}.openai.azure.com/openai/v1/")
    return FoundryChatClient(project_endpoint=endpoint, model=model, credential=DefaultAzureCredential())


def build_workflow() -> Workflow:
    """Build the two agents and chain them in a sequential orchestration."""
    client = make_client()
    anomaly_agent = Agent(
        client=client,
        name="anomaly-detection-agent",
        instructions=ANOMALY_INSTRUCTIONS,
        tools=[check_thresholds],
    )
    diagnosis_agent = Agent(
        client=client,
        name="fault-diagnosis-agent",
        instructions=DIAGNOSIS_INSTRUCTIONS,
        tools=[create_work_order],
    )
    return SequentialBuilder(
        name="factory-health-check",
        participants=[
            anomaly_agent,
            AgentExecutor(diagnosis_agent, id="fault-diagnosis-agent", context_mode="custom", context_filter=text_only),
        ],
        output_from="all",
    ).build()
