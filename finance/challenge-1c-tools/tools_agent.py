"""
Challenge 1c: tools, MCP and approvals.

Usage:
    python tools_agent.py           # you approve or reject each MCP tool call
    python tools_agent.py --yes     # approve every MCP tool call (for the facilitator dry run)
    python tools_agent.py --keep    # keep the agent, so you can test it in the portal

Creates the portfolio-analyst-agent with two hosted tools:
  - Code Interpreter, with account_history.csv attached
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


def load_settings() -> None:
    """Load .env from this folder upwards. If there is none, use factory/.env from the setup."""
    for folder in Path(__file__).resolve().parents:
        for candidate in (folder / ".env", folder / "factory" / ".env"):
            if candidate.exists():
                load_dotenv(candidate)
                return


load_settings()

PROJECT_CONNECTION_STRING = os.getenv("PROJECT_CONNECTION_STRING")
MODEL_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-5.4")
HERE = Path(__file__).resolve().parent
CSV_PATH = HERE / "account_history.csv"
OUTPUT_DIR = HERE / "output"
AGENT_NAME = "portfolio-analyst-agent"
MCP_SERVER_URL = "https://learn.microsoft.com/api/mcp"

INSTRUCTIONS = """
You are a portfolio risk analyst for Woodgrove Finance, a retail lender.
- For questions about loan accounts, use the code interpreter and the file account_history.csv.
  It has one row per account per month. The columns are snapshot_date, account_id, product, days_past_due,
  emi_bounced (1 if the EMI bounced that month), bureau_score, credit_enquiries_90d and outstanding_inr.
  Show the numbers you used. Save every chart as a PNG file.
- For questions about Microsoft products, use the microsoft_learn MCP tool. Give the link for each fact.
- Never send account data to the MCP tool.
Be concise.
"""

TASKS = [
    "Analyse account_history.csv for UBL-1003. Plot three panels over the 12 months: bureau score, "
    "credit_enquiries_90d and days_past_due. Draw the limits as dashed lines: 3 enquiries and 0 days past due. "
    "Then find the first month in which each signal broke its limit: credit_enquiries_90d above 3; "
    "EMI bounces in the last 6 snapshots (including this one) above 1; the bureau score more than 40 points "
    "below its value 3 snapshots earlier; days_past_due above 0. "
    "How many months of warning did the first signal give before days_past_due first went above 0? "
    "Save the chart as ubl1003_early_warning.png.",
    "Search Microsoft Learn: how can a Microsoft Foundry agent search SharePoint documents and respect "
    "each user's permissions, and how does a Foundry agent connect to a remote MCP server? "
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
