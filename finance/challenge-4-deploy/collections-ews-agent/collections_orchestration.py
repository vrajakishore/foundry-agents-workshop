"""Woodgrove Finance early-warning check: a sequential multi-agent orchestration built with Microsoft Agent Framework.

early-warning-agent  ->  collections-advisor-agent  ->  create_collections_case (needs human approval)

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
ACCOUNTS_PATH = HERE / "loan_accounts.json"

# Locally, settings come from finance/.env or factory/.env. When hosted, Foundry sets
# FOUNDRY_PROJECT_ENDPOINT and azure.yaml sets AZURE_AI_MODEL_DEPLOYMENT_NAME.
for folder in HERE.parents:
    candidates = [c for c in (folder / ".env", folder / "factory" / ".env") if c.exists()]
    if candidates:
        load_dotenv(candidates[0])
        break


@tool(approval_mode="never_require")
def check_account_signals(
    account_id: Annotated[str, Field(description="Loan account ID, for example 'UBL-1003'.")],
) -> str:
    """Check a loan account's early-warning signals against the limits for its product."""
    accounts = json.loads(ACCOUNTS_PATH.read_text(encoding="utf-8"))["accounts"]
    account = next((a for a in accounts if a["account_id"] == account_id), None)
    if account is None:
        return json.dumps({"error": f"Account '{account_id}' not found"})

    above_limit = []
    for name, signal in account["signals"].items():
        value, limit = signal["value"], account["limits"][name]["max"]
        if value > limit:
            above_limit.append(f"{name} is {value} {signal['unit']}, {value - limit} above the limit of {limit}")

    return json.dumps(
        {
            "account_id": account["account_id"],
            "product": account["product_name"],
            "outstanding_inr": account["outstanding_inr"],
            "emis_paid": account["emis_paid"],
            "signals": {name: signal["value"] for name, signal in account["signals"].items()},
            "above_limit": above_limit,
        }
    )


@tool(approval_mode="always_require")
def create_collections_case(
    account_id: Annotated[str, Field(description="Loan account ID, for example 'UBL-1003'.")],
    procedure: Annotated[
        Literal["COL-PRC-04", "COL-PRC-05"],
        Field(description="COL-PRC-05 priority resolution for CRITICAL accounts. COL-PRC-04 payment discussion."),
    ],
    urgency: Annotated[Literal["IMMEDIATE", "WITHIN 7 DAYS"], Field(description="How soon the first contact must happen.")],
    summary: Annotated[str, Field(description="One line: the situation and the next best action. No ID numbers.")],
) -> str:
    """Open a collections case and assign it to a collections officer. A collections manager must approve it first."""
    # Simulated. In production this would call your collections or loan management system.
    case_id = f"CASE-{account_id}-{datetime.now(timezone.utc):%Y%m%d%H%M}"
    return json.dumps(
        {"case_id": case_id, "account_id": account_id, "procedure": procedure, "urgency": urgency,
         "summary": summary, "status": "assigned"}
    )


EARLY_WARNING_INSTRUCTIONS = """
You are the early-warning analyst for Woodgrove Finance, a retail lender.
The monthly scan covers five accounts: HL-1001, LAP-1002, UBL-1003, UCL-1004 and PL-1005.
Use the check_account_signals tool for every account, unless the user names specific accounts.
Set each account's status with these rules. Apply them exactly:
- NORMAL: every signal is at or below its limit.
- WATCH: one or two signals are above their limits, and days_past_due is 30 or less.
- CRITICAL: days_past_due is more than 30, or three or more signals are above their limits.
For each account, report the account ID, the product, the status and every signal above its limit.
Be concise and structured. Report facts only.
Never mention cases or collection actions; the collections advisor handles them.
"""

ADVISOR_INSTRUCTIONS = """
You are a collections advisor for Woodgrove Finance, a retail lender.
Read the early-warning report in the conversation. For each WATCH or CRITICAL account:
1. Name the most likely situation:
   - Bureau score drop and new credit enquiries, no days past due: probably borrowing elsewhere. Early outreach call. No top-up.
   - Two or more EMI bounces with a stable bureau score: check the payment mandate first.
   - Days past due from 1 to 30 with bounces: cash-flow strain. Payment discussion.
   - CRITICAL: severe repayment stress. Priority resolution and a payment plan assessment.
2. Recommend the next best action and who must do it.
3. Set urgency: IMMEDIATE (contact within 24 hours), WITHIN 7 DAYS or MONITOR.
Before you write your answer, call create_collections_case once for every CRITICAL account,
with procedure COL-PRC-05 and urgency IMMEDIATE.
A collections manager must approve each call, so never skip it and never invent a case.
Report a case as opened only if the tool returned a case_id, and quote that ID.
If the call was rejected, say the case was rejected.
You never approve waivers or payment plans. Contact only the borrower, a co-borrower or a guarantor, between 08:00 and 19:00.
Never use age, gender, religion, caste, marital status or location in a decision.
Format each account as: ACCOUNT, LIKELY SITUATION, NEXT BEST ACTION, URGENCY.
Finish with a short portfolio summary that lists the cases opened or rejected.
"""


def text_only(conversation: list[Message]) -> list[Message]:
    """Give the next agent the user request and the early-warning report as plain text, without the first agent's tool calls."""
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
    early_warning_agent = Agent(
        client=client,
        name="early-warning-agent",
        instructions=EARLY_WARNING_INSTRUCTIONS,
        tools=[check_account_signals],
    )
    advisor_agent = Agent(
        client=client,
        name="collections-advisor-agent",
        instructions=ADVISOR_INSTRUCTIONS,
        tools=[create_collections_case],
    )
    return SequentialBuilder(
        name="collections-early-warning",
        participants=[
            early_warning_agent,
            AgentExecutor(advisor_agent, id="collections-advisor-agent", context_mode="custom", context_filter=text_only),
        ],
        output_from="all",
    ).build()
