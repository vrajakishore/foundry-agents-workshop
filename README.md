# Microsoft Foundry hands-on workshop: agents that act

Code companion for the Microsoft Foundry hands-on workshop. You build agents in your own Azure subscription that read live machine data, decide, call tools and work together as a hosted agent.

📽️ **Slides:** https://vrajakishore.github.io/foundry-agents-workshop/

## What you'll build

A predictive-maintenance system for a fictional tyre plant, TireForge Industries:

- An **anomaly detection agent** that checks sensor readings with a `check_thresholds` function tool
- A **fault diagnosis agent** that finds the likely root cause and recommends an action
- **Traces** of every model and tool call in Application Insights
- An **evaluation run** that scores the agent's answers
- A **multi-agent orchestration** in Microsoft Agent Framework that asks you to approve each work order, deployed as a Foundry hosted agent

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

You need Python 3.10+, Azure CLI 2.80+ and Git. For challenge 4 you also need Azure Developer CLI (`azd`) 1.27.1+.

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

Can't run `az login`? Set the optional `FOUNDRY_API_KEY` in `factory/.env` (section 10). The smoke test and the challenge 4 local run use the key, and challenges 1, 2 and 4 have **No `az login`?** portal steps for the rest.

## Lab challenges

The full scenario is in [factory/README.md](factory/README.md).

| # | Challenge | What you do | Workshop session |
| --- | --- | --- | --- |
| 0 | [Verify your setup](factory/challenge-0-setup/README.md) | Check the project, model and `.env` from the prerequisites | 2 |
| 1 | [Build agents](factory/challenge-1-build/README.md) | Create the anomaly detection and fault diagnosis agents | 3 |
| 2 | [Monitor](factory/challenge-2-monitor/README.md) | Trace your agents in Application Insights | 5 |
| 3 | [Evaluate](factory/challenge-3-evaluate/README.md) | Score the agent's answers for coherence and fluency | 5 |
| 4 | [Orchestrate and deploy](factory/challenge-4-deploy/README.md) | Chain both agents in code, approve work orders, deploy as a hosted agent | 6 |

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
