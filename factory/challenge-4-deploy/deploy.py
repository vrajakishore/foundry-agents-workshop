"""
Challenge 4: Production Workflow -- SDK Track
Multi-agent orchestration workflow for TireForge Industries.
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def _find_repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / ".env").exists():
            return parent
    return Path(__file__).resolve().parents[2]


env_path = _find_repo_root() / ".env"
load_dotenv(env_path)

PROJECT_CONNECTION_STRING = os.getenv("PROJECT_CONNECTION_STRING")
MODEL_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-5.4")
SENSOR_DATA_PATH = Path(__file__).resolve().parent.parent / "challenge-1-build" / "sensor_data.json"

MACHINES = ["MX-001", "EX-002", "CP-003", "CU-004", "IS-005"]
ANOMALY_AGENT_NAME = "anomaly-detection-agent"
DIAGNOSIS_AGENT_NAME = "fault-diagnosis-agent"
# Set WORKFLOW_AGENT_NAME in .env after creating the workflow in the Foundry portal
WORKFLOW_AGENT_NAME = os.getenv("WORKFLOW_AGENT_NAME", "")


def check_thresholds(machine_id: str) -> str:
    with open(SENSOR_DATA_PATH, "r") as f:
        data = json.load(f)
    machine = next(
        (m for m in data["machines"]
         if m["machine_id"] == machine_id or m["name"] == machine_id),
        None,
    )
    if not machine:
        return json.dumps({"error": f"Machine not found: {machine_id}"})
    results = {
        "machine_id": machine["machine_id"],
        "name": machine["name"],
        "status": machine["status"],
        "anomalies": [],
        "all_readings": {},
    }
    for sensor, reading in machine["readings"].items():
        value = reading["value"]
        threshold = machine["thresholds"][sensor]
        in_spec = threshold["min"] <= value <= threshold["max"]
        results["all_readings"][sensor] = {
            "value": value, "unit": reading["unit"],
            "min": threshold["min"], "max": threshold["max"], "in_spec": in_spec,
        }
        if not in_spec:
            direction = "above max" if value > threshold["max"] else "below min"
            ref = threshold["max"] if value > threshold["max"] else threshold["min"]
            pct = abs(value - ref) / ref * 100
            results["anomalies"].append({
                "sensor": sensor, "value": value,
                "unit": reading["unit"], "deviation": f"{pct:.1f}% {direction}",
            })
    return json.dumps(results, indent=2)


def ensure_agents_deployed() -> tuple:
    """Create both agents if not already deployed; reuse existing ones."""
    print("=== Step 1: Ensure Agents Are Deployed ===")

    from azure.ai.projects import AIProjectClient
    from azure.ai.projects.models import FunctionTool, PromptAgentDefinition
    from azure.identity import DefaultAzureCredential

    check_thresholds_tool = FunctionTool(
        name="check_thresholds",
        description="Check sensor readings against thresholds for a given machine.",
        parameters={
            "type": "object",
            "properties": {
                "machine_id": {"type": "string", "description": "Machine ID e.g. MX-001"},
            },
            "required": ["machine_id"],
        },
        strict=False,
    )

    client = AIProjectClient(
        endpoint=PROJECT_CONNECTION_STRING,
        credential=DefaultAzureCredential(),
    )
    existing_names = {a.name for a in client.agents.list()}

    if ANOMALY_AGENT_NAME not in existing_names:
        client.agents.create_version(
            agent_name=ANOMALY_AGENT_NAME,
            definition=PromptAgentDefinition(
                model=MODEL_DEPLOYMENT_NAME,
                instructions=(
                    "You are an industrial sensor anomaly detection expert for TireForge Industries. "
                    "When asked to check machines, use the check_thresholds tool for each machine ID. "
                    "Report every sensor reading that is out of spec: machine name, sensor, current value, "
                    "threshold violated, and deviation percentage. "
                    "Use WARNING or CRITICAL labels. Be concise and structured."
                ),
                tools=[check_thresholds_tool],
            ),
        )
        print(f"  Deployed: {ANOMALY_AGENT_NAME}")
    else:
        print(f"  Found existing: {ANOMALY_AGENT_NAME}")

    if DIAGNOSIS_AGENT_NAME not in existing_names:
        client.agents.create_version(
            agent_name=DIAGNOSIS_AGENT_NAME,
            definition=PromptAgentDefinition(
                model=MODEL_DEPLOYMENT_NAME,
                instructions=(
                    "You are a mechanical fault diagnosis expert for TireForge Industries. "
                    "Given anomalies from a machine, identify the most likely root cause and recommend "
                    "specific maintenance actions. Estimate urgency: IMMEDIATE, WITHIN 24H, or MONITOR. "
                    "Format: LIKELY CAUSE: ... / MAINTENANCE ACTIONS: ... / URGENCY: ..."
                ),
            ),
        )
        print(f"  Deployed: {DIAGNOSIS_AGENT_NAME}")
    else:
        print(f"  Found existing: {DIAGNOSIS_AGENT_NAME}")

    client.close()
    return ANOMALY_AGENT_NAME, DIAGNOSIS_AGENT_NAME


def run_anomaly_scan(anomaly_agent_name: str) -> str:
    """Call the anomaly detection agent for all machines; handle function call loop."""
    print("\n=== Step 2a: Anomaly Scan ===")

    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential
    from openai.types.responses.response_input_param import FunctionCallOutput

    client = AIProjectClient(
        endpoint=PROJECT_CONNECTION_STRING,
        credential=DefaultAzureCredential(),
    )
    openai_client = client.get_openai_client()
    agent_ref = {"agent_reference": {"name": anomaly_agent_name, "type": "agent_reference"}}

    conversation = openai_client.conversations.create()
    response = openai_client.responses.create(
        input=(
            f"Check all machines: {', '.join(MACHINES)}. "
            "Report every sensor reading that is out of spec."
        ),
        conversation=conversation.id,
        extra_body=agent_ref,
    )

    while any(item.type == "function_call" for item in response.output):
        tool_outputs = []
        for item in response.output:
            if item.type == "function_call":
                args = json.loads(item.arguments)
                result = check_thresholds(args.get("machine_id", ""))
                tool_outputs.append(
                    FunctionCallOutput(
                        type="function_call_output",
                        call_id=item.call_id,
                        output=result,
                    )
                )
        response = openai_client.responses.create(
            input=tool_outputs,
            conversation=conversation.id,
            extra_body=agent_ref,
        )

    report = response.output_text
    openai_client.conversations.delete(conversation_id=conversation.id)
    client.close()
    return report


def run_fault_diagnosis(diagnosis_agent_name: str, machine_id: str, anomalies: list) -> str:
    """Call the fault diagnosis agent for a single machine."""
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    client = AIProjectClient(
        endpoint=PROJECT_CONNECTION_STRING,
        credential=DefaultAzureCredential(),
    )
    openai_client = client.get_openai_client()
    agent_ref = {"agent_reference": {"name": diagnosis_agent_name, "type": "agent_reference"}}

    anomaly_text = "\n".join(
        f"  - {a['sensor']}: {a['value']} {a['unit']} ({a['deviation']})"
        for a in anomalies
    )
    input_text = (
        f"Machine {machine_id} has the following out-of-spec readings:\n"
        f"{anomaly_text}\n"
        "Diagnose the fault and recommend maintenance actions."
    )

    conversation = openai_client.conversations.create()
    response = openai_client.responses.create(
        input=input_text,
        conversation=conversation.id,
        extra_body=agent_ref,
    )
    diagnosis = response.output_text
    openai_client.conversations.delete(conversation_id=conversation.id)
    client.close()
    return diagnosis


def run_factory_health_workflow(anomaly_agent: str, diagnosis_agent: str) -> dict:
    """Orchestrate: anomaly scan -> per-machine diagnosis -> consolidated report."""
    anomaly_report = run_anomaly_scan(anomaly_agent)
    print(anomaly_report)

    print("\n=== Step 2b: Fault Diagnosis ===")
    diagnoses = {}
    machines_with_anomalies = []

    for machine_id in MACHINES:
        result = json.loads(check_thresholds(machine_id))
        if result.get("anomalies"):
            machines_with_anomalies.append(machine_id)
            print(f"  Diagnosing {machine_id}...")
            diagnosis = run_fault_diagnosis(diagnosis_agent, machine_id, result["anomalies"])
            diagnoses[machine_id] = diagnosis

    return {
        "anomaly_report": anomaly_report,
        "machines_with_anomalies": machines_with_anomalies,
        "diagnoses": diagnoses,
        "total_machines": len(MACHINES),
        "problematic_machines": len(machines_with_anomalies),
    }


def print_factory_report(report: dict):
    print("\n" + "=" * 60)
    print("TIREFORGE FACTORY HEALTH REPORT")
    print("=" * 60)
    print(f"  Machines checked   : {report['total_machines']}")
    print(f"  Machines affected  : {report['problematic_machines']}")

    if report["machines_with_anomalies"]:
        print(f"  Affected machines  : {', '.join(report['machines_with_anomalies'])}")
        print("\n--- Fault Diagnoses ---")
        for machine_id, diagnosis in report["diagnoses"].items():
            print(f"\n{machine_id}:")
            print(diagnosis)
    else:
        print("\n  All machines operating within normal parameters.")

    print("=" * 60)


def create_workflow_agent(workflow_agent_name: str = "factory-health-workflow") -> str:
    """
    Create a workflow agent via the SDK using WorkflowAgentDefinition.

    The workflow appears in the Foundry portal under Build → Agents (kind: workflow).
    Requires allow_preview=True on AIProjectClient.

    Note: WorkflowAgentDefinition agents are visible in the Foundry portal
    and can be invoked from the portal UI. Programmatic invocation via the
    Responses API returns a 'wfresp_' tracking object.

    Returns:
        The workflow agent name.
    """
    from azure.ai.projects import AIProjectClient
    from azure.ai.projects.models import WorkflowAgentDefinition
    from azure.identity import DefaultAzureCredential

    client = AIProjectClient(
        endpoint=PROJECT_CONNECTION_STRING,
        credential=DefaultAzureCredential(),
        allow_preview=True,
    )

    # Exact portal YAML format: flat InvokeAzureAgent actions with agent.name,
    # conversationId, input/output, and a final EndConversation action.
    workflow_yaml = (
        "kind: Workflow\n"
        f"name: {workflow_agent_name}\n"
        "description: TireForge factory health check - detect anomalies then diagnose faults\n"
        "trigger:\n"
        "  kind: OnConversationStart\n"
        "  id: trigger_start\n"
        "  actions:\n"
        "    - kind: InvokeAzureAgent\n"
        "      id: step_detect\n"
        "      agent:\n"
        "        name: anomaly-detection-agent\n"
        "      conversationId: =System.ConversationId\n"
        "      input:\n"
        '        messages: ""\n'
        "      output:\n"
        "        autoSend: true\n"
        "    - kind: InvokeAzureAgent\n"
        "      id: step_diagnose\n"
        "      agent:\n"
        "        name: fault-diagnosis-agent\n"
        "      conversationId: =System.ConversationId\n"
        "      input:\n"
        '        messages: ""\n'
        "      output:\n"
        "        autoSend: true\n"
        "    - kind: EndConversation\n"
        "      id: step_end\n"
    )

    existing_names = {a.name for a in client.agents.list()}
    if workflow_agent_name in existing_names:
        result = client.agents.create_version(
            agent_name=workflow_agent_name,
            definition=WorkflowAgentDefinition(workflow=workflow_yaml),
            description="TireForge factory health workflow (SDK-created)",
        )
        print(f"  Updated workflow agent: {result.name} (version {result.version})")
    else:
        result = client.agents.create_version(
            agent_name=workflow_agent_name,
            definition=WorkflowAgentDefinition(workflow=workflow_yaml),
            description="TireForge factory health workflow (SDK-created)",
        )
        print(f"  Created workflow agent: {result.name} (version {result.version})")
    print(f"  Visible in Foundry portal → Build → Agents (kind: workflow)")
    client.close()
    return result.name


def run_portal_workflow(workflow_name: str) -> str:
    """
    Invoke a WorkflowAgentDefinition agent via the Responses API.

    Embeds the sensor data directly in the input so the anomaly-detection-agent
    can analyse all machines without needing to call the check_thresholds tool
    (workflow steps cannot handle function-call loops). Both agents execute
    sequentially.

    Returns:
        The workflow's combined text output.
    """
    import time
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    client = AIProjectClient(
        endpoint=PROJECT_CONNECTION_STRING,
        credential=DefaultAzureCredential(),
        allow_preview=True,
    )
    openai_client = client.get_openai_client()

    print(f"\n=== Portal Workflow: {workflow_name} ===")

    portal_base = PROJECT_CONNECTION_STRING.split("/api/projects/")[0] if "/api/projects/" in PROJECT_CONNECTION_STRING else ""
    if portal_base:
        print(f"\n  View in Foundry portal:")
        print(f"  {portal_base.replace('services.ai.azure.com', 'ai.azure.com')}/build/agents")

    print(f"\n  Workflow steps:")
    print(f"    1. anomaly-detection-agent  — detect sensor anomalies across all machines")
    print(f"    2. fault-diagnosis-agent    — diagnose root cause for anomalous machines")

    # Embed sensor data in the input so agents don't need tool calls.
    # The anomaly-detection-agent is instructed to call check_thresholds per machine,
    # but workflow steps cannot handle function-call loops. We provide all readings
    # upfront and explicitly instruct the agent to work from the provided data.
    with open(SENSOR_DATA_PATH, "r") as f:
        sensor_data = json.load(f)
    machines_text = json.dumps(sensor_data["machines"], indent=2)
    query = (
        "All sensor readings for today are provided below — do NOT call check_thresholds. "
        "Analyse the data directly from this message.\n\n"
        + machines_text
        + "\n\nFor each machine, compare every sensor reading against its normal thresholds "
        "and report: machine name/ID, status (normal/warning/critical), and each out-of-spec "
        "reading with current value, threshold violated, and deviation. "
        "Then diagnose root causes and recommend remediation for any anomalous machines."
    )

    conversation = openai_client.conversations.create()
    print(f"\n  Submitting workflow run (background)...")

    resp = openai_client.responses.create(
        conversation=conversation.id,
        extra_body={"agent_reference": {"name": workflow_name, "type": "agent_reference"}},
        input=query,
        background=True,
    )
    print(f"  Response ID : {resp.id}")
    print(f"  Initial status: {resp.status}")

    output_text = ""
    for attempt in range(12):
        time.sleep(8)
        r = openai_client.responses.retrieve(resp.id)
        tokens = getattr(r.usage, "total_tokens", 0)
        print(f"  [{attempt + 1}] status={r.status}  tokens={tokens}")
        if r.status in ("completed", "failed", "cancelled"):
            output_text = r.output_text
            break

    if output_text:
        print("\nWorkflow output:")
        print(output_text)
    else:
        print(
            "\n  Note: Workflow invocation returned no text output via the API.\n"
            "  The agent is deployed and visible in Foundry portal → Build → Agents."
        )

    openai_client.conversations.delete(conversation_id=conversation.id)
    client.close()
    return output_text


def main():
    if not PROJECT_CONNECTION_STRING:
        print("PROJECT_CONNECTION_STRING not set. Run challenge 0 first!")
        sys.exit(1)

    # --- Part A: Python orchestration (agents called step-by-step from code) ---
    anomaly_agent, diagnosis_agent = ensure_agents_deployed()
    report = run_factory_health_workflow(anomaly_agent, diagnosis_agent)
    print_factory_report(report)

    print("\nWorkflow complete! Agents remain deployed for future runs.")

    # --- Part B: SDK workflow creation + portal invocation ---
    print("\n" + "=" * 60)
    print("CREATING WORKFLOW AGENT VIA SDK")
    print("=" * 60)
    workflow_name = WORKFLOW_AGENT_NAME if WORKFLOW_AGENT_NAME and not WORKFLOW_AGENT_NAME.startswith("<") else "factory-health-workflow"
    workflow_name = create_workflow_agent(workflow_agent_name=workflow_name)

    print("\n" + "=" * 60)
    print("INVOKING WORKFLOW (BACKGROUND POLL)")
    print("=" * 60)
    run_portal_workflow(workflow_name)

    print("\n" + "=" * 60)
    print("CHALLENGE 4 COMPLETE")
    print("=" * 60)
    print("  Part A: Multi-agent SDK orchestration  ✓")
    print(f"  Part B: Workflow agent deployed        ✓  ({workflow_name})")
    print("          → View in Foundry portal → Build → Agents")


if __name__ == "__main__":
    main()
