"""Checks that your code can reach your Foundry project: creates a temporary agent, asks it one question, then deletes it."""

import os

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()
endpoint = os.environ["PROJECT_CONNECTION_STRING"]
model = os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-5.4")

with (
    DefaultAzureCredential() as credential,
    AIProjectClient(endpoint=endpoint, credential=credential) as project,
    project.get_openai_client() as openai,
):
    agent = project.agents.create_version(
        agent_name="workshop-smoke-test",
        definition=PromptAgentDefinition(model=model, instructions="Answer in one sentence."),
    )
    response = openai.responses.create(
        input="What does high vibration on a machine usually indicate?",
        extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
    )
    print("Agent says:", response.output_text)
    project.agents.delete_version(agent_name=agent.name, agent_version=agent.version)
    print("Smoke test passed.")
