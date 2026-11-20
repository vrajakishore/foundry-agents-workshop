"""
Challenge 3, Step 4: check that the anomaly agent gets the status right.

Usage:
    python score_classification.py                    # uses anomaly-detection-agent
    python score_classification.py --min-accuracy 0.9 # exit code 1 if accuracy is lower (use it as a CI gate)

Coherence and fluency rate how well an answer reads. They don't check that the answer is correct.
This script sends each test case in eval_portal.jsonl to your agent, reads the status the agent gives
(normal, warning or critical) and compares it with the expected classification in ground_truth.
"""

import ast
import json
import os
import re
import sys
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from openai.types.responses.response_input_param import FunctionCallOutput


def _find_repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / ".env").exists():
            return parent
    return Path(__file__).resolve().parents[2]


load_dotenv(_find_repo_root() / ".env")

PROJECT_CONNECTION_STRING = os.getenv("PROJECT_CONNECTION_STRING")
AGENT_NAME = os.getenv("EVAL_AGENT_NAME", "anomaly-detection-agent")
HERE = Path(__file__).resolve().parent
DATASET = HERE / "eval_portal.jsonl"
RESULTS = HERE / "classification_results.json"
LABELS = ("critical", "warning", "normal")

STATUS_SUFFIX = (
    "\n\nUse only the readings and thresholds in this message. "
    "End your answer with one line in this format: STATUS: normal, STATUS: warning or STATUS: critical"
)

# In this check the agent can't read sensor_data.json. The readings are in the question.
TOOL_NOTE = json.dumps({"note": "Evaluation mode. Use the readings and thresholds in the user message."})


def parse_status(text: str) -> str:
    match = re.search(r"STATUS:\s*\**\s*(normal|warning|critical)", text, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    found = [label for label in LABELS if re.search(rf"\b{label}\b", text, re.IGNORECASE)]
    return found[0] if found else "unknown"


def ask(openai, query: str) -> str:
    agent_reference = {"agent_reference": {"name": AGENT_NAME, "type": "agent_reference"}}
    conversation = openai.conversations.create()
    try:
        response = openai.responses.create(
            input=query + STATUS_SUFFIX, conversation=conversation.id, extra_body=agent_reference
        )
        for _ in range(5):
            calls = [item for item in response.output if item.type == "function_call"]
            if not calls:
                break
            outputs = [
                FunctionCallOutput(type="function_call_output", call_id=call.call_id, output=TOOL_NOTE)
                for call in calls
            ]
            response = openai.responses.create(
                input=outputs, conversation=conversation.id, extra_body=agent_reference
            )
        return response.output_text
    finally:
        openai.conversations.delete(conversation_id=conversation.id)


def main() -> None:
    if not PROJECT_CONNECTION_STRING:
        print("PROJECT_CONNECTION_STRING is not set. Complete Challenge 0 first.")
        sys.exit(1)

    min_accuracy = None
    if "--min-accuracy" in sys.argv:
        min_accuracy = float(sys.argv[sys.argv.index("--min-accuracy") + 1])

    rows = [json.loads(line) for line in DATASET.read_text(encoding="utf-8").splitlines() if line.strip()]
    project = AIProjectClient(endpoint=PROJECT_CONNECTION_STRING, credential=DefaultAzureCredential())
    openai = project.get_openai_client()

    results = []
    print(f"Scoring {AGENT_NAME} on {len(rows)} test cases...\n")
    print(f"{'#':>2}  {'machine':<28} {'expected':<9} {'agent':<9} result")
    for number, row in enumerate(rows, start=1):
        expected = ast.literal_eval(row["ground_truth"])["classification"]
        answer = ask(openai, row["query"])
        predicted = parse_status(answer)
        correct = predicted == expected
        machine = row["query"].split(".")[0].replace("Machine: ", "")
        print(f"{number:>2}  {machine:<28} {expected:<9} {predicted:<9} {'PASS' if correct else 'FAIL'}")
        results.append({"query": row["query"], "expected": expected, "predicted": predicted,
                        "correct": correct, "answer": answer})

    accuracy = sum(r["correct"] for r in results) / len(results)
    missed_critical = [r for r in results if r["expected"] == "critical" and r["predicted"] != "critical"]
    print(f"\nAccuracy: {accuracy:.0%}")
    print(f"Critical machines missed: {len(missed_critical)}")
    RESULTS.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Details saved to {RESULTS.name}")
    project.close()

    if min_accuracy is not None and accuracy < min_accuracy:
        print(f"FAILED: accuracy is below {min_accuracy:.0%}")
        sys.exit(1)


if __name__ == "__main__":
    main()
