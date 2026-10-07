# Microsoft Foundry hands-on workshop: agents that act

Code companion for the Microsoft Foundry hands-on workshop. You build agents in your own Azure subscription that read live machine data, decide, call tools and run as a multi-agent workflow.

📽️ **Slides:** https://vrajakishore.github.io/foundry-agents-workshop/

## What you'll build

A predictive-maintenance system for a fictional tyre plant, TireForge Industries:

- An **anomaly detection agent** that checks sensor readings with a `check_thresholds` function tool
- A **fault diagnosis agent** that finds the likely root cause and recommends an action
- **Traces** of every model and tool call in Application Insights
- An **evaluation run** that scores the agent's answers
- A **multi-agent workflow**, in code and in the Foundry portal

## Before the workshop

Complete [PREREQUISITES.md](PREREQUISITES.md):

- **Part 1** is for your Azure administrator.
- **Part 2** (about 30 minutes) is for each participant. You create your project, model and first agent in the Foundry portal, then prepare your workstation.

## Getting started

### GitHub Codespaces (recommended)

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/vrajakishore/foundry-agents-workshop)

When the codespace is ready, sign in to Azure:

```bash
az login --use-device-code
```

### Your own laptop

You need Python 3.10+, Azure CLI 2.80+ and Git.

```powershell
git clone https://github.com/vrajakishore/foundry-agents-workshop.git
cd foundry-agents-workshop
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
az login
```

### Connect to your project

```powershell
cp factory/.env.template factory/.env
```

Fill in the two values in `factory/.env` (see [PREREQUISITES.md](PREREQUISITES.md), section 10), then run:

```powershell
python factory/smoke_test.py
```

## Lab challenges

The full scenario is in [factory/README.md](factory/README.md).

| # | Challenge | What you do | Workshop session |
| --- | --- | --- | --- |
| 0 | [Verify your setup](factory/challenge-0-setup/README.md) | Check the project, model and `.env` from the prerequisites | 2 |
| 1 | [Build agents](factory/challenge-1-build/README.md) | Create the anomaly detection and fault diagnosis agents | 3 |
| 2 | [Monitor](factory/challenge-2-monitor/README.md) | Trace your agents in Application Insights | 5 |
| 3 | [Evaluate](factory/challenge-3-evaluate/README.md) | Score the agent's answers for coherence and fluency | 5 |
| 4 | [Orchestrate](factory/challenge-4-deploy/README.md) | Run a multi-agent workflow in code, then build it in the portal | 6 |

When you finish, see the [wrap-up](factory/wrapup.md) for ideas on where to go next.

## Repository layout

| Path | Contents |
| --- | --- |
| `docs/` | The slides, published with GitHub Pages |
| `factory/` | The lab: one folder per challenge |
| `PREREQUISITES.md` | Setup for administrators and participants |

## Clean up

Every participant's project is in the shared `foundry-workshop` resource group. After the workshop, your Azure administrator deletes it:

```bash
az group delete --name foundry-workshop --yes --no-wait
```

## Credits

The lab in `factory/` is adapted from the factory scenario in [microsoft/FrontierWeekHack](https://github.com/microsoft/FrontierWeekHack) (MIT licence). In this version, you set up in the Foundry portal instead of running a deployment script, and the repository adds `smoke_test.py` and `.env.template`.

## Licence

[MIT](LICENSE)
