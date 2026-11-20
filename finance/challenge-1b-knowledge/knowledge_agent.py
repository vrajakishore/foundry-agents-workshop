"""
Challenge 1b, Path B: ground the collections advisor with File Search.

Usage:
    python knowledge_agent.py          # create, test, then delete the agent and the vector store
    python knowledge_agent.py --keep   # keep them, so you can test the agent in the portal

Uploads the Woodgrove Finance documents in ./knowledge to a vector store, creates an agent
with the File Search tool, asks four questions and prints each answer with its sources.
"""

import os
import sys
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FileSearchTool, PromptAgentDefinition
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv


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
KNOWLEDGE_DIR = Path(__file__).resolve().parent / "knowledge"
AGENT_NAME = "collections-advisor-kb-agent"

INSTRUCTIONS = """
You are a collections advisor for Woodgrove Finance.
Before you recommend an action, search the Woodgrove documents with the file search tool.
For each account, give:
PROCEDURE: the procedure ID from the collections policy (COL-PRC-01 to COL-PRC-05) and what to do
URGENCY: IMMEDIATE, WITHIN 7 DAYS or MONITOR, as the policy defines them
PAYMENT PLAN: eligible or not eligible under the restructuring guideline, with the reason, the option and the documents
APPROVER: who must approve any waiver or payment plan. You never approve anything yourself.
SIMILAR CASE: the case ID from the case history, or "none"
Cite the source document for each fact. If the documents have no answer, say so. Do not make up facts.
"""

QUESTIONS = [
    "UBL-1003 is an unsecured business loan. It is 46 days past due, with 4 EMI bounces in 6 months, "
    "a bureau score drop of 66 points in 90 days and 5 new credit enquiries. Outstanding: ₹11,84,000. "
    "15 EMIs paid. Never restructured. The borrower says a large buyer pays his invoices late. "
    "What do we do, and can we offer a payment plan?",
    "PL-1005 is a personal loan with no overdue amount, but the bureau score fell 62 points and there are "
    "6 new credit enquiries. The branch wants to offer a top-up loan. What do I do?",
    "The borrower of LAP-1002 asks us to waive ₹7,500 of bounce charges. Who can approve it?",
    "What interest rate does Woodgrove Finance charge on gold loans?",
]


def print_sources(response) -> None:
    """Print the file citations in a response."""
    sources = set()
    for item in response.output:
        if item.type != "message":
            continue
        for content in item.content or []:
            for annotation in getattr(content, "annotations", None) or []:
                if annotation.type == "file_citation":
                    sources.add(getattr(annotation, "filename", None) or annotation.file_id)
    print("Sources:", ", ".join(sorted(sources)) if sources else "none")


def main() -> None:
    if not PROJECT_CONNECTION_STRING:
        print("PROJECT_CONNECTION_STRING is not set. Complete Challenge 0 first.")
        sys.exit(1)

    keep = "--keep" in sys.argv
    project = AIProjectClient(endpoint=PROJECT_CONNECTION_STRING, credential=DefaultAzureCredential())
    openai = project.get_openai_client()

    print("Uploading the Woodgrove Finance documents to a vector store...")
    vector_store = openai.vector_stores.create(name="woodgrove-knowledge")
    for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        with open(path, "rb") as f:
            openai.vector_stores.files.upload_and_poll(vector_store_id=vector_store.id, file=f)
        print(f"  uploaded {path.name}")

    agent = project.agents.create_version(
        agent_name=AGENT_NAME,
        definition=PromptAgentDefinition(
            model=MODEL_DEPLOYMENT_NAME,
            instructions=INSTRUCTIONS,
            tools=[FileSearchTool(vector_store_ids=[vector_store.id])],
        ),
    )
    print(f"Created agent {agent.name} (version {agent.version})")
    agent_reference = {"agent_reference": {"name": agent.name, "type": "agent_reference"}}

    try:
        for question in QUESTIONS:
            print("\n" + "=" * 80)
            print("Q:", question)
            conversation = openai.conversations.create()
            response = openai.responses.create(
                input=question, conversation=conversation.id, extra_body=agent_reference
            )
            print(response.output_text)
            print_sources(response)
            openai.conversations.delete(conversation_id=conversation.id)
    finally:
        if keep:
            print(f"\nKept agent {agent.name} and vector store {vector_store.id}.")
        else:
            project.agents.delete_version(agent_name=agent.name, agent_version=agent.version)
            openai.vector_stores.delete(vector_store_id=vector_store.id)
            print("\nDeleted the agent and the vector store.")
        project.close()


if __name__ == "__main__":
    main()
