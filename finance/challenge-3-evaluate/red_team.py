"""
Challenge 3, Step 5: red-team the collections advisor agent in the cloud.

Usage:
    python red_team.py                                  # targets collections-advisor-agent
    RED_TEAM_AGENT_NAME=my-agent python red_team.py     # targets another prompt agent

The AI Red Teaming Agent sends adversarial prompts to your agent and scores the replies.
It runs in Foundry, so the results also show in the portal under Evaluations.
A run takes 10 to 30 minutes. Start it early and check it at the end of the lab.

Your project must be in a region that supports the AI Red Teaming Agent, for example swedencentral or eastus2.
If your project is in an India region, check the region list on Microsoft Learn first. If it isn't supported,
your facilitator shows this step as a demo.
"""

import json
import os
import sys
import time
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    AgentTaxonomyInput,
    AzureAIAgentTarget,
    EvaluationTaxonomy,
    RiskCategory,
)
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
AGENT_NAME = os.getenv("RED_TEAM_AGENT_NAME", "collections-advisor-agent")
HERE = Path(__file__).resolve().parent
TIMEOUT_SECONDS = 45 * 60


def latest_version(project_client, agent_name: str) -> str:
    override = os.getenv("RED_TEAM_AGENT_VERSION")
    if override:
        return override
    agent = project_client.agents.get(agent_name=agent_name)
    try:
        return str(agent.versions.latest.version)
    except AttributeError:
        return str(agent["versions"]["latest"]["version"])


def to_plain(value):
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "as_dict"):
        return value.as_dict()
    return value


def main() -> None:
    if not PROJECT_CONNECTION_STRING:
        print("PROJECT_CONNECTION_STRING is not set. Complete Challenge 0 first.")
        sys.exit(1)

    with DefaultAzureCredential() as credential, AIProjectClient(
        endpoint=PROJECT_CONNECTION_STRING, credential=credential
    ) as project_client:
        client = project_client.get_openai_client()
        version = latest_version(project_client, AGENT_NAME)
        target = AzureAIAgentTarget(name=AGENT_NAME, version=version)
        print(f"Target: {AGENT_NAME} (version {version})")

        red_team = client.evals.create(
            name=f"Red team - {AGENT_NAME}",
            data_source_config={"type": "azure_ai_source", "scenario": "red_team"},
            testing_criteria=[
                {
                    "type": "azure_ai_evaluator",
                    "name": "Prohibited Actions",
                    "evaluator_name": "builtin.prohibited_actions",
                    "evaluator_version": "1",
                },
                {
                    "type": "azure_ai_evaluator",
                    "name": "Task Adherence",
                    "evaluator_name": "builtin.task_adherence",
                    "evaluator_version": "1",
                    "initialization_parameters": {"deployment_name": MODEL_DEPLOYMENT_NAME},
                },
                {
                    "type": "azure_ai_evaluator",
                    "name": "Sensitive Data Leakage",
                    "evaluator_name": "builtin.sensitive_data_leakage",
                    "evaluator_version": "1",
                },
            ],
        )
        print(f"Created red team {red_team.id}")

        taxonomy = project_client.beta.evaluation_taxonomies.create(
            name=AGENT_NAME,
            body=EvaluationTaxonomy(
                description="Woodgrove Finance collections workshop red team",
                taxonomy_input=AgentTaxonomyInput(
                    risk_categories=[RiskCategory.PROHIBITED_ACTIONS], target=target
                ),
            ),
        )
        print(f"Created taxonomy {taxonomy.id}")

        run = client.evals.runs.create(
            eval_id=red_team.id,
            name=f"Red team run - {AGENT_NAME}",
            data_source={
                "type": "azure_ai_red_team",
                "item_generation_params": {
                    "type": "red_team_taxonomy",
                    "attack_strategies": ["Flip", "Base64", "IndirectJailbreak"],
                    "num_turns": 3,
                    "source": {"type": "file_id", "id": taxonomy.id},
                },
                "target": target.as_dict(),
            },
        )
        print(f"Started run {run.id}. This takes 10 to 30 minutes.")

        started = time.time()
        while run.status not in ("completed", "failed", "canceled"):
            if time.time() - started > TIMEOUT_SECONDS:
                print("Still running. Check the result in the portal under Evaluations.")
                return
            time.sleep(30)
            run = client.evals.runs.retrieve(run_id=run.id, eval_id=red_team.id)
            print(f"  status: {run.status}")

        items = list(client.evals.runs.output_items.list(run_id=run.id, eval_id=red_team.id))
        output = HERE / f"redteam_output_{AGENT_NAME}.json"
        output.write_text(json.dumps([to_plain(i) for i in items], indent=2, default=str), encoding="utf-8")

        failed = 0
        for item in items:
            results = to_plain(item).get("results") or []
            if any(r.get("passed") is False for r in results if isinstance(r, dict)):
                failed += 1
        print(f"\nRun {run.status}. {len(items)} attacks. {failed} attacks got through (at least one check failed).")
        print(f"Details saved to {output.name}. Open Evaluations in the portal for the full report.")


if __name__ == "__main__":
    main()
