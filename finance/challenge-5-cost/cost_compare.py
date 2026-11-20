"""
Challenge 5: what does one account check cost, and which model is good enough?

Usage:
    python cost_compare.py
    python cost_compare.py --models gpt-5.4,gpt-5.4-mini --accounts-per-month 1000000
    python cost_compare.py --usd-to-inr 88.5        # also show the cost in rupees, at your exchange rate
    python cost_compare.py --min-accuracy 1.0       # the accuracy a model needs to be recommended

For each model deployment, the script creates a temporary prompt agent with the early-warning rules,
sends the 12 test cases from Challenge 3 and records the accuracy, the tokens and the time of each call.
Then it prices one account check and projects the monthly cost for your portfolio.
"""

import ast
import json
import os
import re
import sys
import time
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
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
HERE = Path(__file__).resolve().parent
DATASET = HERE.parent / "challenge-3-evaluate" / "eval_portal.jsonl"
RESULTS = HERE / "cost_results.json"

# Global Standard list prices in USD per 1 million tokens, read in November 2026.
# Check the Azure OpenAI pricing page before you share any number with a customer.
# Data Zone Standard costs about 10% more. The Batch API costs 50% less.
# Add a model with --price name=input,cached_input,output (for example --price my-model=0.75,0.075,4.50).
PRICES_USD_PER_1M = {
    "gpt-5.4": (2.50, 0.25, 15.00),
    "gpt-5.4-mini": (0.75, 0.075, 4.50),
    "gpt-5.4-nano": (0.20, 0.02, 1.25),
}

INSTRUCTIONS = """
You are the early-warning analyst for Woodgrove Finance, a retail lender.
The user gives you an account's signals and limits. Set the status with these rules. Apply them exactly:
- NORMAL: every signal is at or below its limit. A value equal to the limit is within the limit.
- WATCH: one or two signals are above their limits, and days_past_due is 30 or less.
- CRITICAL: days_past_due is more than 30, or three or more signals are above their limits.
Use only the signals. Never use the borrower's age, gender, religion, caste, marital status or location.
List the signals above their limits in one short line.
End with one line in this format: STATUS: normal, STATUS: watch or STATUS: critical
"""


def arg(name: str, default: str | None = None) -> str | None:
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def parse_status(text: str) -> str:
    match = re.search(r"STATUS:\s*\**\s*(normal|watch|critical)", text, re.IGNORECASE)
    return match.group(1).lower() if match else "unknown"


def price_for(model: str):
    if model in PRICES_USD_PER_1M:
        return PRICES_USD_PER_1M[model]
    for name in sorted(PRICES_USD_PER_1M, key=len, reverse=True):
        if model.startswith(name):
            return PRICES_USD_PER_1M[name]
    return None


def usage_of(response) -> tuple[int, int, int]:
    usage = getattr(response, "usage", None)
    if usage is None:
        return 0, 0, 0
    details = getattr(usage, "input_tokens_details", None)
    cached = getattr(details, "cached_tokens", 0) or 0
    return usage.input_tokens or 0, cached, usage.output_tokens or 0


def test_model(project, openai, model: str, rows: list[dict]) -> dict:
    agent_name = "cost-test-" + re.sub(r"[^a-zA-Z0-9-]", "-", model)
    agent = project.agents.create_version(
        agent_name=agent_name, definition=PromptAgentDefinition(model=model, instructions=INSTRUCTIONS)
    )
    reference = {"agent_reference": {"name": agent.name, "type": "agent_reference"}}
    correct = missed_critical = tokens_in = tokens_cached = tokens_out = 0
    seconds = 0.0
    try:
        for row in rows:
            expected = ast.literal_eval(row["ground_truth"])["classification"]
            started = time.perf_counter()
            response = openai.responses.create(input=row["query"], extra_body=reference)
            seconds += time.perf_counter() - started
            predicted = parse_status(response.output_text)
            correct += predicted == expected
            missed_critical += expected == "critical" and predicted != "critical"
            used_in, used_cached, used_out = usage_of(response)
            tokens_in, tokens_cached, tokens_out = tokens_in + used_in, tokens_cached + used_cached, tokens_out + used_out
            print(f"  {row['query'].split(' ')[1]:<10} expected {expected:<9} got {predicted:<9} "
                  f"tokens in {used_in:>5} out {used_out:>5}")
    finally:
        project.agents.delete_version(agent_name=agent.name, agent_version=agent.version)

    n = len(rows)
    result = {
        "model": model, "accuracy": correct / n, "missed_critical": missed_critical,
        "avg_input_tokens": tokens_in / n, "avg_cached_tokens": tokens_cached / n,
        "avg_output_tokens": tokens_out / n, "avg_seconds": seconds / n, "cost_per_check_usd": None,
    }
    price = price_for(model)
    if price:
        p_in, p_cached, p_out = price
        result["cost_per_check_usd"] = (
            (result["avg_input_tokens"] - result["avg_cached_tokens"]) * p_in
            + result["avg_cached_tokens"] * p_cached
            + result["avg_output_tokens"] * p_out
        ) / 1_000_000
    return result


def main() -> None:
    if not PROJECT_CONNECTION_STRING:
        print("PROJECT_CONNECTION_STRING is not set. Complete Challenge 0 first.")
        sys.exit(1)

    for item in [sys.argv[i + 1] for i, a in enumerate(sys.argv) if a == "--price"]:
        name, values = item.split("=")
        PRICES_USD_PER_1M[name] = tuple(float(v) for v in values.split(","))

    default_models = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-5.4") + ",gpt-5.4-mini"
    models = list(dict.fromkeys(m.strip() for m in arg("--models", default_models).split(",") if m.strip()))
    accounts_per_month = int(arg("--accounts-per-month", "1000000"))
    min_accuracy = float(arg("--min-accuracy", "1.0"))
    usd_to_inr = float(arg("--usd-to-inr")) if arg("--usd-to-inr") else None

    rows = [json.loads(line) for line in DATASET.read_text(encoding="utf-8").splitlines() if line.strip()]
    project = AIProjectClient(endpoint=PROJECT_CONNECTION_STRING, credential=DefaultAzureCredential())
    openai = project.get_openai_client()

    results = []
    for model in models:
        print(f"\n=== {model} ===")
        try:
            results.append(test_model(project, openai, model, rows))
        except Exception as error:  # a model that is not deployed must not stop the comparison
            print(f"  Skipped {model}: {error}")
    project.close()
    if not results:
        print("No model ran. Check the deployment names with --models.")
        sys.exit(1)

    money = lambda usd: f"${usd:,.2f}" + (f" (₹{usd * usd_to_inr:,.0f})" if usd_to_inr else "")
    print(f"\nProjection for {accounts_per_month:,} account checks per month\n")
    print(f"{'model':<16} {'accuracy':>8} {'missed':>6} {'tokens in':>9} {'out':>6} {'sec':>5} "
          f"{'per check':>10}  monthly (standard) / monthly (batch)")
    for r in results:
        line = (f"{r['model']:<16} {r['accuracy']:>8.0%} {r['missed_critical']:>6} {r['avg_input_tokens']:>9.0f} "
                f"{r['avg_output_tokens']:>6.0f} {r['avg_seconds']:>5.1f} ")
        if r["cost_per_check_usd"] is None:
            print(line + f"{'no price':>10}  add one with --price")
            continue
        monthly = r["cost_per_check_usd"] * accounts_per_month
        r["monthly_standard_usd"], r["monthly_batch_usd"] = monthly, monthly * 0.5
        print(line + f"${r['cost_per_check_usd']:>9.5f}  {money(monthly)} / {money(monthly * 0.5)}")

    good_enough = [r for r in results if r["accuracy"] >= min_accuracy and r["missed_critical"] == 0
                   and r["cost_per_check_usd"] is not None]
    if good_enough:
        best = min(good_enough, key=lambda r: r["cost_per_check_usd"])
        print(f"\nCheapest model with accuracy of at least {min_accuracy:.0%} and no missed critical account: {best['model']}")
    else:
        print(f"\nNo priced model reached {min_accuracy:.0%} accuracy with no missed critical account.")
    print("Prices are list prices. Your agreement, Data Zone (+10%) and Batch (-50%) change them.")

    RESULTS.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Details saved to {RESULTS.name}")


if __name__ == "__main__":
    main()
