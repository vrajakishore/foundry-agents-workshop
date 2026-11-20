# Challenge 5: Cost

Time: ~30 minutes

## Objectives

By the end of this challenge, you will have:

- ✅ Measured the tokens and the cost of one account check
- ✅ Compared two models on accuracy **and** cost
- ✅ Projected the monthly cost for a portfolio of one million accounts
- ✅ A list of the levers that cut the cost without cutting the quality

## What you pay for

| Item | How it is charged | Where to see it |
| --- | --- | --- |
| **Model tokens** | Per million input tokens, cached input tokens and output tokens. Reasoning tokens count as output tokens | Traces (Challenge 2), **Monitor → Cost** in the project, Azure Cost Management |
| **Deployment type** | Global Standard is the list price. Data Zone Standard costs about 10% more and keeps processing inside a data zone. The Batch API costs 50% less and returns results within 24 hours. Provisioned throughput (PTU) is a fixed price for reserved capacity | Azure OpenAI pricing page |
| **Tools** | Some tools have their own charges, for example Code Interpreter sessions, file storage for File Search, and web search calls | Foundry pricing page |
| **Foundry IQ** | The Azure AI Search service tier, charged per hour | Azure AI Search pricing page |
| **Hosted agents** | The compute that runs your hosted agent | Foundry Agent Service pricing page |
| **Monitoring** | Application Insights data that you store | Azure Monitor pricing page |

> [!IMPORTANT]
> The prices in this lab are **list prices** for Global Standard deployments, read in November 2026. Your agreement, your currency and the deployment type change them. Check the pricing pages before you share a number.

## Step 1: Read the cost of one run

1. In the [Foundry portal](https://ai.azure.com), open `early-warning-agent`, then **Traces**.
2. Open the latest run from Challenge 1. Read the input tokens, the output tokens and the estimated cost.
3. Count the model calls in the run. Each tool call adds a model call, and each model call sends the instructions again.
4. Select **Monitor → Cost** in your project (preview). It shows the cost by agent and by model deployment, at the prices you pay. Cost data arrives 8 to 24 hours after use, so today's lab may not show yet. Token counts show within minutes.

## Step 2: Compare models

Deploy `gpt-5.4-mini` in your project if you haven't yet (**Build → Models → Deploy**, Global Standard, 10K TPM). Then run:

```bash
cd finance/challenge-5-cost
python cost_compare.py
```

The script creates a temporary agent for each model with the same early-warning rules, sends the 12 test cases from Challenge 3 and prints a table:

```
model            accuracy missed tokens in    out   sec  per check  monthly (standard) / monthly (batch)
gpt-5.4              ...
gpt-5.4-mini         ...
```

- **accuracy** and **missed** come from the same checks as Challenge 3.
- **per check** is the average cost of one account check.
- **monthly** projects the cost for 1,000,000 account checks a month. Change it with `--accounts-per-month`.

Useful options:

| Option | What it does |
| --- | --- |
| `--models gpt-5.4,gpt-5.4-mini,gpt-5.4-nano` | The deployments to compare |
| `--usd-to-inr 88.5` | Also shows the cost in rupees. Use today's exchange rate |
| `--min-accuracy 1.0` | The accuracy that a model needs before the script recommends it |
| `--price my-model=0.75,0.075,4.50` | Adds a price (input, cached input, output, USD per million tokens) |

Read the result as a business owner: **price the accepted answer, not the token.** A cheaper model that misses one CRITICAL account in twelve is not cheaper.

## Step 3: Size the solution

Use these example numbers, then replace them with your own numbers from Step 2.

| Assumption | Example |
| --- | --- |
| Accounts scanned each month | 1,000,000 |
| Tokens per early-warning check | 450 in, 60 out |
| Accounts flagged WATCH or CRITICAL | 5% (50,000) |
| Tokens per advisor call, with Foundry IQ passages | 3,000 in, 500 out, on gpt-5.4 |

| Design | Monthly model cost (example) |
| --- | --- |
| A. Every step on gpt-5.4 | $2,025 (scan) + $750 (advice) = **$2,775** |
| B. Scan on gpt-5.4-mini, advice on gpt-5.4 | $607.50 + $750 = **$1,357.50** |
| C. Design B, with the overnight scan in the Batch API | $303.75 + $750 = **$1,053.75** |
| D. Status rules in code, advice on gpt-5.4 with 1,200 cached input tokens | $0 + $615 = **$615** |

Design D is the cheapest, and it is also the most accurate: the status rules are fixed, so code applies them with no errors. **Use code for rules. Use a model for judgment, language and documents.**

These are model costs only. Add the search service, monitoring and the hosted agent to get the total cost.

## Step 4: Choose your levers

| Lever | Saving | Trade-off |
| --- | --- | --- |
| Apply fixed rules in code | The whole model cost of that step | You maintain the code |
| Use a smaller model for simple steps | About 70% for gpt-5.4-mini against gpt-5.4 | Test the accuracy first (Step 2) |
| Model router | Sends each request to the cheapest model that can answer it | A small routing fee per million input tokens. Less control over which model answers |
| Prompt caching | Cached input costs 90% less | Put the fixed instructions first and keep them unchanged |
| Batch API | 50% less | Results within 24 hours. Good for an overnight scan, not for a live chat |
| Provisioned throughput (PTU) | A fixed monthly price for steady, high volume | You pay for the capacity even when you don't use it |
| Fewer tool round trips | Each model call sends the instructions again | Give the agent the data it needs in one call where you can |
| Budgets and cost controls | No saving by itself, but no surprises | Set a budget in Azure Cost Management. A Foundry cost control (preview) can alert, or block requests, when spending or tokens reach a limit |

## Talk about it

- Which steps in your process are fixed rules, and which need judgment?
- What is the cost of one wrong answer in your process? Compare it with the cost of a bigger model.
- Who owns the AI budget for each use case, and who gets the alert?

## Success criteria

- [ ] You can read the tokens and the estimated cost of one run in the portal
- [ ] `cost_compare.py` prints the accuracy and the cost for at least one model
- [ ] You can explain why design D is both the cheapest and the most accurate
- [ ] You have picked two levers for your own use case

## Learn more

- [Azure OpenAI pricing](https://azure.microsoft.com/pricing/details/azure-openai/)
- [Cost and FinOps in Microsoft Foundry](https://learn.microsoft.com/azure/foundry/concepts/manage-costs)
- [What is model router?](https://learn.microsoft.com/azure/foundry/openai/concepts/model-router)
