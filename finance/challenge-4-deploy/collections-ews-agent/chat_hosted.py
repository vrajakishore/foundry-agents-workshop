"""Chat with your deployed hosted agent from the terminal. You approve or reject each collections case.

Usage: python chat_hosted.py <agent-name>
"""

import os
import sys
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

for folder in Path(__file__).resolve().parents:
    candidates = [c for c in (folder / ".env", folder / "factory" / ".env") if c.exists()]
    if candidates:
        load_dotenv(candidates[0])
        break

PROMPT = "Run the monthly early-warning check on all five accounts and open collections cases where needed."

agent_name = sys.argv[1] if len(sys.argv) > 1 else input("Hosted agent name: ").strip()
project = AIProjectClient(
    endpoint=os.getenv("FOUNDRY_PROJECT_ENDPOINT") or os.environ["PROJECT_CONNECTION_STRING"],
    credential=DefaultAzureCredential(),
)
client = project.get_openai_client(agent_name=agent_name)

print(f"USER: {PROMPT}")
response = client.responses.create(input=PROMPT)
while True:
    print(f"\n{agent_name}: {response.output_text}")
    approvals = []
    for item in response.output:
        if item.type == "mcp_approval_request":
            answer = input(f"\n[APPROVAL NEEDED] {item.name} {item.arguments}\nApprove? [y/N] ")
            approvals.append({"type": "mcp_approval_response", "approval_request_id": item.id, "approve": answer.strip().lower() == "y"})
    if not approvals:
        break
    response = client.responses.create(previous_response_id=response.id, input=approvals)
