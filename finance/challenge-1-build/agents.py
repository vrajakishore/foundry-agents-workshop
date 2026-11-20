"""
Challenge 1: Build agents (SDK track)
Early-Warning Agent and Collections Advisor Agent for Woodgrove Finance (fictional).

Usage:
    python agents.py

Creates both agents, checks every loan account in loan_accounts.json with the
Early-Warning Agent, then sends the accounts that need action to the Collections Advisor Agent.
"""

import json
import os
import sys
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FunctionTool, PromptAgentDefinition
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from openai.types.responses.response_input_param import FunctionCallOutput


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
ACCOUNTS_PATH = Path(__file__).resolve().parent / "loan_accounts.json"


def _load_accounts() -> list[dict]:
    """Load the loan accounts to send as a batch in the demo requests."""
    return json.loads(ACCOUNTS_PATH.read_text(encoding="utf-8"))["accounts"]


# =============================================================================
# Tool function: check_account_signals
# The agent calls this tool. Your code runs it and returns the result.
# =============================================================================

def check_account_signals(account_id: str) -> str:
    """Compare a loan account's early-warning signals with the limits for its product."""
    account = next((a for a in _load_accounts() if a["account_id"] == account_id), None)
    if account is None:
        return json.dumps({"error": f"Account '{account_id}' not found"})

    result = {
        "account_id": account["account_id"],
        "product": account["product_name"],
        "outstanding_inr": account["outstanding_inr"],
        "emis_paid": account["emis_paid"],
        "previous_restructuring": account["previous_restructuring"],
        "signals": {},
        "above_limit": [],
    }
    for name, signal in account["signals"].items():
        value, limit = signal["value"], account["limits"][name]["max"]
        result["signals"][name] = {"value": value, "unit": signal["unit"], "limit": limit, "within_limit": value <= limit}
        if value > limit:
            result["above_limit"].append(f"{name} is {value} {signal['unit']}, {value - limit} above the limit of {limit}")
    return json.dumps(result, indent=2)


CHECK_ACCOUNT_SIGNALS_TOOL = FunctionTool(
    name="check_account_signals",
    description="Check a loan account's early-warning signals (days past due, EMI bounces, bureau score drop, "
    "credit enquiries) against the limits for its product. Returns every signal that is above its limit.",
    parameters={
        "type": "object",
        "properties": {
            "account_id": {
                "type": "string",
                "description": "The loan account ID, for example 'UBL-1003'.",
            }
        },
        "required": ["account_id"],
        "additionalProperties": False,
    },
    strict=False,
)

EARLY_WARNING_INSTRUCTIONS = """
You are the early-warning analyst for Woodgrove Finance, a retail lender.
Use the check_account_signals tool for every account the user gives you.
Set each account's status with these rules. Apply them exactly:
- NORMAL: every signal is at or below its limit. A value equal to the limit is within the limit.
- WATCH: one or two signals are above their limits, and days_past_due is 30 or less.
- CRITICAL: days_past_due is more than 30, or three or more signals are above their limits.
For each account, report the account ID, the product, the status and every signal above its limit
with its value and the limit. Use 🟡 for WATCH and 🔴 for CRITICAL.
Use only the signals. Never use the borrower's age, gender, religion, caste, marital status or location.
Report facts only. Do not recommend collection actions. Be concise and structured.
"""

ADVISOR_INSTRUCTIONS = """
You are a collections advisor for Woodgrove Finance, a retail lender.
You receive early-warning results for loan accounts. For each WATCH or CRITICAL account:
1. Name the most likely situation from the pattern:
   - Bureau score drop and new credit enquiries, no days past due: the borrower is probably borrowing elsewhere.
   - Two or more EMI bounces with a stable bureau score: check for a payment mandate problem first.
   - Days past due from 1 to 30 with bounces: cash-flow strain. Find the reason.
   - CRITICAL status: severe repayment stress. Escalate.
2. Recommend the next best action and who must do it.
3. Set urgency: IMMEDIATE (contact within 24 hours), WITHIN 7 DAYS or MONITOR.
Rules you must always follow:
- Recommend only. You never approve waivers, payment plans or restructuring. Say who must approve.
- Contact only the borrower, a co-borrower or a guarantor, between 08:00 and 19:00.
- Never suggest threats, shaming, or contact with the borrower's employer, family or neighbours.
- Never include full PAN, Aadhaar or bank account numbers.
- Never use age, gender, religion, caste, marital status or location in a decision.
Format each account as:
ACCOUNT: ...
LIKELY SITUATION: ...
NEXT BEST ACTION: ...
URGENCY: ...
"""


# =============================================================================
# Early-Warning Agent
# =============================================================================

class EarlyWarningAgent:
    def __init__(self):
        self.agent = None
        self.client = None
        self.openai = None

    def create(self):
        """Create the early-warning agent in Foundry."""
        self.client = AIProjectClient(endpoint=PROJECT_CONNECTION_STRING, credential=DefaultAzureCredential())
        self.openai = self.client.get_openai_client()
        self.agent = self.client.agents.create_version(
            agent_name="early-warning-agent",
            definition=PromptAgentDefinition(
                model=MODEL_DEPLOYMENT_NAME,
                instructions=EARLY_WARNING_INSTRUCTIONS,
                tools=[CHECK_ACCOUNT_SIGNALS_TOOL],
            ),
        )
        return self.agent

    def run(self, input_text: str) -> str:
        """Run the agent. Answer each function call until the agent gives its final answer."""
        agent_reference = {"agent_reference": {"name": self.agent.name, "type": "agent_reference"}}
        conversation = self.openai.conversations.create()
        response = self.openai.responses.create(
            input=input_text, conversation=conversation.id, extra_body=agent_reference
        )

        while True:
            function_calls = [item for item in response.output if item.type == "function_call"]
            if not function_calls:
                break
            outputs = []
            for item in function_calls:
                if item.name == "check_account_signals":
                    result = check_account_signals(json.loads(item.arguments)["account_id"])
                else:
                    result = json.dumps({"error": f"Unknown tool '{item.name}'"})
                outputs.append(FunctionCallOutput(type="function_call_output", call_id=item.call_id, output=result))
            response = self.openai.responses.create(
                input=outputs, conversation=conversation.id, extra_body=agent_reference
            )

        self.openai.conversations.delete(conversation_id=conversation.id)
        return response.output_text

    def cleanup(self):
        """Delete the agent version and close the client."""
        if self.agent:
            self.client.agents.delete_version(agent_name=self.agent.name, agent_version=self.agent.version)
        if self.client:
            self.client.close()


# =============================================================================
# Collections Advisor Agent
# =============================================================================

class CollectionsAdvisorAgent:
    def __init__(self):
        self.agent = None
        self.client = None
        self.openai = None

    def create(self):
        """Create the collections advisor agent in Foundry."""
        self.client = AIProjectClient(endpoint=PROJECT_CONNECTION_STRING, credential=DefaultAzureCredential())
        self.openai = self.client.get_openai_client()
        self.agent = self.client.agents.create_version(
            agent_name="collections-advisor-agent",
            definition=PromptAgentDefinition(model=MODEL_DEPLOYMENT_NAME, instructions=ADVISOR_INSTRUCTIONS),
        )
        return self.agent

    def run(self, input_text: str) -> str:
        """Run the agent once. It has no tools."""
        conversation = self.openai.conversations.create()
        response = self.openai.responses.create(
            input=input_text,
            conversation=conversation.id,
            extra_body={"agent_reference": {"name": self.agent.name, "type": "agent_reference"}},
        )
        self.openai.conversations.delete(conversation_id=conversation.id)
        return response.output_text

    def cleanup(self):
        """Delete the agent version and close the client."""
        if self.agent:
            self.client.agents.delete_version(agent_name=self.agent.name, agent_version=self.agent.version)
        if self.client:
            self.client.close()


# =============================================================================
# Main: test both agents
# =============================================================================

def main():
    if not PROJECT_CONNECTION_STRING:
        print("❌ PROJECT_CONNECTION_STRING is not set. Complete Challenge 0 first.")
        sys.exit(1)

    accounts = _load_accounts()
    account_ids = [a["account_id"] for a in accounts]

    print("=== Early-Warning Agent ===")
    early_warning = EarlyWarningAgent()
    early_warning.create()
    print(f"✅ Created: {early_warning.agent.name} (version {early_warning.agent.version})")
    print(f"\nChecking {len(account_ids)} accounts: {', '.join(account_ids)}")
    report = early_warning.run(
        "Run the monthly early-warning check. Use check_account_signals for each account ID in this batch "
        "and return the status summary.\n\n"
        f"BATCH_ACCOUNT_IDS: {json.dumps(account_ids)}"
    )
    print(report)

    print("\n=== Collections Advisor Agent ===")
    advisor = CollectionsAdvisorAgent()
    advisor.create()
    print(f"✅ Created: {advisor.agent.name} (version {advisor.agent.version})")
    flagged = [json.loads(check_account_signals(a["account_id"])) for a in accounts if a["status"] in {"watch", "critical"}]
    print(f"\nAdvising on {len(flagged)} flagged accounts...")
    advice = advisor.run(
        "Recommend the next best action for each flagged account below.\n\n"
        f"EARLY_WARNING_REPORT:\n{report}\n\n"
        f"FLAGGED_ACCOUNT_SIGNALS:\n{json.dumps(flagged, indent=2)}"
    )
    print(advice)

    # Clean-up. Leave it commented out to keep the agents for Challenges 1b, 2 and 3.
    # early_warning.cleanup()
    # advisor.cleanup()


if __name__ == "__main__":
    main()
