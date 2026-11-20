"""
Challenge 1c: tools, MCP and approvals.

Usage:
    python tools_agent.py           # you approve or reject each MCP tool call
    python tools_agent.py --yes     # approve every MCP tool call (for the facilitator dry run)
    python tools_agent.py --keep    # keep the agent, so you can test it in the portal

Creates the maintenance-planner-agent with two hosted tools:
  - Code Interpreter, with sensor_history.csv attached
  - The Microsoft Learn MCP server, with require_approval="always"
Then runs two tasks and saves any chart the agent makes to ./output.
"""

import os
import sys
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import CodeInterpreterTool, MCPTool, PromptAgentDefinition
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from openai.types.responses.response_input_param import McpApprovalResponse

# The class name for the automatic Code Interpreter container changed between SDK versions.
try:
    from azure.ai.projects.models import AutoCodeInterpreterToolParam as _AutoContainer
except ImportError:
    try:
        from azure.ai.projects.models import CodeInterpreterToolAuto as _AutoContainer
    except ImportError:
        _AutoContainer = None


def _find_repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / ".env").exists():
            return parent
    return Path(__file__).resolve().parents[2]


load_dotenv(_find_repo_root() / ".env")

PROJECT_CONNECTION_STRING = os.getenv("PROJECT_CONNECTION_STRING")
MODEL_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-5.4")
HERE = Path(__file__).resolve().parent
CSV_PATH = HERE / "sensor_history.csv"
OUTPUT_DIR = HERE / "output"
AGENT_NAME = "maintenance-planner-agent"
MCP_SERVER_URL = "https://learn.microsoft.com/api/mcp"

INSTRUCTIONS = """
You are a maintenance planner for TireForge Industries.
- For questions about sensor data, use the code interpreter and the file sensor_history.csv.
  The columns are timestamp, machine_id, temperature_c, pressure_bar, vibration_mm_s and rpm.
  Show the numbers you used. Save every chart as a PNG file.
- For questions about Microsoft products, use the microsoft_learn MCP tool. Give the link for each fact.
- Never use the MCP tool for sensor data.
Be concise.
"""

TASKS = [
    "Analyse sensor_history.csv for CP-003. Plot temperature, pressure and vibration over time on three "
    "panels. Draw the upper limits as dashed lines: temperature 180 C, pressure 16 bar, vibration 3.0 mm/s. "
    "Tell me the first timestamp at which each reading went above its limit, and how many hours of warning "
    "the first crossing gave before the last reading. Save the chart as cp003_trend.png.",
    "Search Microsoft Learn: how can a factory send OPC UA machine data to Azure? "
    "Give three short bullet points, each with a link.",
]


def code_interpreter_tool(file_ids: list[str]) -> CodeInterpreterTool:
    if _AutoContainer is not None:
        return CodeInterpreterTool(container=_AutoContainer(file_ids=file_ids))
    return CodeInterpreterTool(container={"type": "auto", "file_ids": file_ids})


def run_with_approvals(openai, conversation_id: str, agent_reference: dict, text: str, auto_approve: bool):
    """Send a request. Ask a person to approve each MCP tool call until the agent finishes."""
    response = openai.responses.create(input=text, conversation=conversation_id, extra_body=agent_reference)
    while True:
        requests = [item for item in response.output if item.type == "mcp_approval_request"]
        if not requests:
            return response
        approvals = []
        for item in requests:
            print("\n[APPROVAL NEEDED] MCP tool call")
            print(f"  Server:    {item.server_label}")
            print(f"  Tool:      {item.name}")
            print(f"  Arguments: {item.arguments}")
            if auto_approve:
                approve = True
                print("  Approved (--yes)")
            else:
                approve = input("  Approve? [y/N] ").strip().lower() == "y"
            approvals.append(
                McpApprovalResponse(type="mcp_approval_response", approve=approve, approval_request_id=item.id)
            )
        response = openai.responses.create(input=approvals, conversation=conversation_id, extra_body=agent_reference)


def save_generated_files(openai, response) -> None:
    """Download each file that Code Interpreter cites in the response."""
    for item in response.output:
        if item.type != "message":
            continue
        for content in item.content or []:
            for annotation in getattr(content, "annotations", None) or []:
                if annotation.type != "container_file_citation":
                    continue
                OUTPUT_DIR.mkdir(exist_ok=True)
                target = OUTPUT_DIR / Path(annotation.filename).name
                data = openai.containers.files.content.retrieve(
                    file_id=annotation.file_id, container_id=annotation.container_id
                )
                target.write_bytes(data.read())
                print(f"Saved {target}")


def main() -> None:
    if not PROJECT_CONNECTION_STRING:
        print("PROJECT_CONNECTION_STRING is not set. Complete Challenge 0 first.")
        sys.exit(1)

    auto_approve = "--yes" in sys.argv
    keep = "--keep" in sys.argv
    project = AIProjectClient(endpoint=PROJECT_CONNECTION_STRING, credential=DefaultAzureCredential())
    openai = project.get_openai_client()

    with open(CSV_PATH, "rb") as f:
        uploaded = openai.files.create(purpose="assistants", file=f)
    print(f"Uploaded {CSV_PATH.name} ({uploaded.id})")

    mcp_tool = MCPTool(
        server_label="microsoft_learn",
        server_url=MCP_SERVER_URL,
        require_approval="always",
        allowed_tools=["microsoft_docs_search"],
    )

    agent = project.agents.create_version(
        agent_name=AGENT_NAME,
        definition=PromptAgentDefinition(
            model=MODEL_DEPLOYMENT_NAME,
            instructions=INSTRUCTIONS,
            tools=[code_interpreter_tool([uploaded.id]), mcp_tool],
        ),
    )
    print(f"Created agent {agent.name} (version {agent.version})")
    agent_reference = {"agent_reference": {"name": agent.name, "type": "agent_reference"}}

    conversation = openai.conversations.create()
    try:
        for task in TASKS:
            print("\n" + "=" * 80)
            print("TASK:", task)
            response = run_with_approvals(openai, conversation.id, agent_reference, task, auto_approve)
            print("\n" + response.output_text)
            save_generated_files(openai, response)
    finally:
        openai.conversations.delete(conversation_id=conversation.id)
        if keep:
            print(f"\nKept agent {agent.name}.")
        else:
            project.agents.delete_version(agent_name=agent.name, agent_version=agent.version)
            print("\nDeleted the agent.")
        openai.files.delete(uploaded.id)
        project.close()


if __name__ == "__main__":
    main()
