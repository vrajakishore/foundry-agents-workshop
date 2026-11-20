"""
Challenge 1b, Path B: ground the fault diagnosis agent with File Search.

Usage:
    python knowledge_agent.py          # create, test, then delete the agent and vector store
    python knowledge_agent.py --keep   # keep them, so you can test the agent in the portal

Uploads the TireForge documents in ./knowledge to a vector store, creates an agent
with the File Search tool, asks three questions and prints each answer with its sources.
"""

import os
import sys
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FileSearchTool, PromptAgentDefinition
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv


def _find_repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / ".env").exists():
            return parent
    return Path(__file__).resolve().parents[2]


load_dotenv(_find_repo_root() / ".env")

PROJECT_CONNECTION_STRING = os.getenv("PROJECT_CONNECTION_STRING")
MODEL_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-5.4")
KNOWLEDGE_DIR = Path(__file__).resolve().parent / "knowledge"
AGENT_NAME = "fault-diagnosis-kb-agent"

INSTRUCTIONS = """
You are a mechanical fault diagnosis expert for TireForge Industries.
Before you recommend an action, search the TireForge documents with the file search tool.
For each machine with anomalies, give:
LIKELY CAUSE: ...
PROCEDURE: the procedure ID and the part numbers from the maintenance manual
SIMILAR INCIDENT: the incident ID from the incident history, or "none"
URGENCY: IMMEDIATE, WITHIN 24H or MONITOR, as the maintenance policy defines them
Cite the source document for each fact. If the documents have no answer, say so. Do not make up facts.
"""

QUESTIONS = [
    "CP-003 reads temperature 198.5 C, pressure 18.2 bar, vibration 7.3 mm/s and 0 rpm. "
    "Diagnose the fault and recommend actions.",
    "IS-005 shows vibration 5.2 mm/s. All other readings are normal. What do I check first?",
    "What is the warranty period for the CP-003 curing press?",
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

    print("Uploading the TireForge documents to a vector store...")
    vector_store = openai.vector_stores.create(name="tireforge-knowledge")
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
                input=question,
                conversation=conversation.id,
                extra_body=agent_reference,
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
