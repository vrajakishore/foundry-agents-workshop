# Microsoft Foundry hands-on workshop: agents that act

Code companion for the Microsoft Foundry hands-on workshop. You build agents in your own Azure subscription that read live machine data, decide, call tools and work together as a hosted agent.

📽️ **Slides:** https://vrajakishore.github.io/foundry-agents-workshop/

## What you'll build

A predictive-maintenance system for a fictional tyre plant, TireForge Industries:

- An **anomaly detection agent** that checks sensor readings with a `check_thresholds` function tool
- A **fault diagnosis agent** that finds the likely root cause and recommends an action
- A **knowledge base** in Foundry IQ that grounds each diagnosis in maintenance manuals and past incidents (full day)
- A **maintenance planner agent** that analyses sensor history with Code Interpreter and calls an MCP server only after you approve (full day)
- **Traces** of every model and tool call in Application Insights
- An **evaluation run** that scores the agent's answers, a **correctness check** against the expected status, and a **red-team scan** (full day)
- A **multi-agent orchestration** in Microsoft Agent Framework that asks you to approve each work order, deployed as a Foundry hosted agent

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

The full scenario is in [factory/README.md](factory/README.md).

| # | Challenge | What you do | Full-day lab |
| --- | --- | --- | --- |
| 0 | [Verify your setup](factory/challenge-0-setup/README.md) | Check the project, model and `.env` from the prerequisites | Lab 1 |
| 1 | [Build agents](factory/challenge-1-build/README.md) | Create the anomaly detection and fault diagnosis agents | Lab 1 |
| 1b | [Ground in knowledge](factory/challenge-1b-knowledge/README.md) | Connect a Foundry IQ knowledge base to the diagnosis agent | Lab 2 |
| 1c | [Tools, MCP and approvals](factory/challenge-1c-tools/README.md) | Analyse sensor history with Code Interpreter and approve MCP tool calls | Lab 3 |
| 2 | [Monitor](factory/challenge-2-monitor/README.md) | Trace your agents in Application Insights | Lab 4 |
| 3 | [Evaluate](factory/challenge-3-evaluate/README.md) | Score quality, check correctness and red-team the diagnosis agent | Lab 4 |
| 4 | [Orchestrate and deploy](factory/challenge-4-deploy/README.md) | Chain both agents in code, approve work orders, deploy as a hosted agent | Lab 5 and Deploy |

When you finish, see the [wrap-up](factory/wrapup.md) for ideas on where to go next.

## Repository layout

| Path | Contents |
| --- | --- |
| `docs/` | The slides, published with GitHub Pages |
| `factory/` | The lab: one folder per challenge |
| `PREREQUISITES.md` | Setup for administrators and participants |
| `FACILITATOR.md` | Full-day agenda, dry-run checklist and fallbacks |

## Clean up

Every participant's project is in the shared `foundry-workshop` resource group. After the workshop, your Azure administrator deletes it:

```bash
az group delete --name foundry-workshop --yes --no-wait
```

## Credits

The lab in `factory/` is adapted from the factory scenario in [microsoft/FrontierWeekHack](https://github.com/microsoft/FrontierWeekHack) (MIT licence). In this version, you set up in the Foundry portal instead of running a deployment script, and the repository adds `smoke_test.py`, `.env.template` and the full-day labs.

## Licence

[MIT](LICENSE)
