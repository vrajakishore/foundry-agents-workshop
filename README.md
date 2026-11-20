# Microsoft Foundry hands-on workshop: agents that act

Code companion for the Microsoft Foundry hands-on workshop. You build agents in your own Azure subscription that read live business data, decide, call tools and work together as a hosted agent.

📽️ **Slides:** https://vrajakishore.github.io/foundry-agents-workshop/

## Choose a scenario track

Both tracks teach the same Foundry skills with the same setup, project and `.env` file. Choose the story that your audience knows.

| Track | Scenario | Folder | Good for |
| --- | --- | --- | --- |
| **Factory** | Predictive maintenance for a fictional tyre plant, TireForge Industries | [`factory/`](factory/README.md) | Manufacturing, automotive, energy, utilities |
| **Finance** | Collections early warning for a fictional retail lender, Woodgrove Finance | [`finance/`](finance/README.md) | Banks, non-banking finance companies, insurers, fintechs |

## What you'll build

| Building block | Factory track | Finance track |
| --- | --- | --- |
| An agent that checks live records with a **function tool** | Anomaly detection agent, `check_thresholds` | Early-warning agent, `check_account_signals` |
| An agent that **recommends an action** | Fault diagnosis agent | Collections advisor agent |
| A **Foundry IQ knowledge base** with citations (full day) | Maintenance manual, incident history, policy | Collections policy, restructuring guideline, case history |
| **Code Interpreter** and an **MCP server with approvals** (full day) | 24 hours of sensor history | 12 months of account history |
| **Traces** in Application Insights | ✓ | ✓ |
| **Evaluation**, a **correctness check** and a **red-team scan** | ✓ | ✓, plus a **fairness pair** check |
| A **multi-agent orchestration** with a human approval, deployed as a **hosted agent** | Approve each work order | Approve each collections case |
| A **cost lab**: tokens, model comparison and a monthly projection | | ✓ |

## Workshop formats

| Format | Length | Labs |
| --- | --- | --- |
| Half day | 3 hours | Challenges 0, 1, 2, 3 (portal evaluation only) and 4 |
| Full-day build lab | 09:00–17:00 | All challenges, including 1b, 1c and the full Challenge 3 |

Facilitators: see [FACILITATOR.md](FACILITATOR.md) for the full-day agenda, the dry-run checklist and the fallbacks.

## Before the workshop

Complete [PREREQUISITES.md](PREREQUISITES.md):

- **Part 1** is for your Azure administrator. For the full-day lab, the administrator also completes section 4b.
- **Part 2** (about 30 minutes) is for each participant. You create your project, model and first agent in the Foundry portal, then prepare your workstation.

## Getting started

### GitHub Codespaces (recommended)

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/vrajakishore/foundry-agents-workshop)

When the codespace is ready, sign in to Azure:

```bash
az login --use-device-code
```

### Your own laptop

You need Python 3.11 or later, Azure CLI 2.80+ and Git. For challenge 4 you also need Azure Developer CLI (`azd`) 1.37.0+ with the `microsoft.foundry` extension.

```powershell
git clone https://github.com/vrajakishore/foundry-agents-workshop.git
cd foundry-agents-workshop
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
azd ext install microsoft.foundry
az login
```

### Connect to your project

```powershell
cp factory/.env.template factory/.env
```

Fill in the two values in `factory/.env` (see [PREREQUISITES.md](PREREQUISITES.md), section 10). Use the endpoint of **your own** project (`<your-alias>-workshop`): everyone shares the resource group, but not the project. Then run:

```powershell
python factory/smoke_test.py
```

Can't run `az login`? Set the optional `FOUNDRY_API_KEY` in `factory/.env` (section 10). The smoke test and the challenge 4 local run use the key, and challenges 1, 2 and 4 have **No `az login`?** portal steps for the rest.

## Lab challenges

The full scenarios are in [factory/README.md](factory/README.md) and [finance/README.md](finance/README.md).

| # | Challenge | What you do | Factory | Finance | Full-day lab |
| --- | --- | --- | --- | --- | --- |
| 0 | Verify your setup | Check the project, model and `.env` from the prerequisites | [Open](factory/challenge-0-setup/README.md) | [Open](finance/challenge-0-setup/README.md) | Lab 1 |
| 1 | Build agents | Create two agents and a function tool | [Open](factory/challenge-1-build/README.md) | [Open](finance/challenge-1-build/README.md) | Lab 1 |
| 1b | Ground in knowledge | Connect a Foundry IQ knowledge base | [Open](factory/challenge-1b-knowledge/README.md) | [Open](finance/challenge-1b-knowledge/README.md) | Lab 2 |
| 1c | Tools, MCP and approvals | Analyse history with Code Interpreter and approve MCP tool calls | [Open](factory/challenge-1c-tools/README.md) | [Open](finance/challenge-1c-tools/README.md) | Lab 3 |
| 2 | Monitor | Trace your agents in Application Insights | [Open](factory/challenge-2-monitor/README.md) | [Open](finance/challenge-2-monitor/README.md) | Lab 4 |
| 3 | Evaluate | Score quality, check correctness and red-team the agent | [Open](factory/challenge-3-evaluate/README.md) | [Open](finance/challenge-3-evaluate/README.md) | Lab 4 |
| 4 | Orchestrate and deploy | Chain both agents in code, approve each action, deploy as a hosted agent | [Open](factory/challenge-4-deploy/README.md) | [Open](finance/challenge-4-deploy/README.md) | Lab 5 and Deploy |
| 5 | Cost | Measure tokens, compare models and project the monthly cost | | [Open](finance/challenge-5-cost/README.md) | Production readiness |

When you finish, see the [wrap-up](factory/wrapup.md) for ideas on where to go next.

## Repository layout

| Path | Contents |
| --- | --- |
| `docs/` | The slides, published with GitHub Pages |
| `factory/` | The factory track: one folder per challenge |
| `finance/` | The finance track: one folder per challenge |
| `PREREQUISITES.md` | Setup for administrators and participants |
| `FACILITATOR.md` | Full-day agenda, dry-run checklist and fallbacks |

## Clean up

Every participant's project is in the shared `foundry-workshop` resource group. After the workshop, your Azure administrator deletes it:

```bash
az group delete --name foundry-workshop --yes --no-wait
```

## Credits

The lab in `factory/` is adapted from the factory scenario in [microsoft/FrontierWeekHack](https://github.com/microsoft/FrontierWeekHack) (MIT licence). In this version, you set up in the Foundry portal instead of running a deployment script, and the repository adds `smoke_test.py`, `.env.template` and the full-day labs. The `finance/` track uses the same patterns with a new scenario and synthetic data.

## Licence

[MIT](LICENSE)
