"""Checks that your code can reach your Foundry project.

With az login (default): creates a temporary agent, asks it one question, then deletes it.
With FOUNDRY_API_KEY set in .env: asks the model one question. API keys can't create agents.
"""

import os

from dotenv import load_dotenv

load_dotenv()
endpoint = os.environ["PROJECT_CONNECTION_STRING"]
model = os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-5.4")
api_key = os.getenv("FOUNDRY_API_KEY")
question = "What does high vibration on a machine usually indicate?"

if api_key:
    from urllib.parse import urlparse

    from openai import OpenAI

    resource = urlparse(endpoint).hostname.split(".")[0]
    openai = OpenAI(api_key=api_key, base_url=f"https://{resource}.openai.azure.com/openai/v1/")
    response = openai.responses.create(model=model, input=question, instructions="Answer in one sentence.")
    print("Model says:", response.output_text)
    print("Smoke test passed (API key: model only). Build agents in the portal, or run az login for the agent labs.")
else:
    from azure.ai.projects import AIProjectClient
    from azure.ai.projects.models import PromptAgentDefinition
    from azure.identity import DefaultAzureCredential

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
            input=question,
            extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
        )
        print("Agent says:", response.output_text)
        project.agents.delete_version(agent_name=agent.name, agent_version=agent.version)
        print("Smoke test passed.")
