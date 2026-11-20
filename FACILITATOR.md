# Facilitator guide: full-day build lab

This guide is for the person who runs the full-day workshop (09:00–17:00). It maps the agenda to the labs in this repository. It also gives the checklist for the dry run and the fallbacks.

## Choose the scenario track

| Track | Folder | Use it for | Differences |
| --- | --- | --- | --- |
| Factory | `factory/` | Manufacturing, automotive, energy, utilities | The original lab |
| Finance | `finance/` | Banks, non-banking finance companies, insurers, fintechs | Collections early warning. Adds a fairness check in Challenge 3 and a cost lab (Challenge 5) |

Both tracks use the same prerequisites, project, model and `.env` file. Only the Lab 2 container is different (section 4b of the prerequisites). The tables below use the factory paths. For the finance track, replace `factory/` with `finance/` and use the finance agenda.

### Finance track agenda

| Time | Session | Lab content |
| --- | --- | --- |
| 09:00 | Welcome and environment check | [Challenge 0](finance/challenge-0-setup/README.md) |
| 09:30 | Platform tour and model choice | Slides |
| 10:15 | Lab 1 · First agents in code | [Challenge 1](finance/challenge-1-build/README.md) |
| 11:15 | Lab 2 · Policy knowledge with Foundry IQ | [Challenge 1b](finance/challenge-1b-knowledge/README.md) |
| 13:00 | Lab 3 · Tools, MCP and approvals | [Challenge 1c](finance/challenge-1c-tools/README.md) |
| 14:00 | Lab 4 · Trace, evaluate, check fairness, red-team | [Challenge 2](finance/challenge-2-monitor/README.md) and [Challenge 3](finance/challenge-3-evaluate/README.md) |
| 15:00 | Lab 5 · Multi-agent orchestration with approval | [Challenge 4](finance/challenge-4-deploy/README.md), Part 1 |
| 15:45 | Security, production readiness and cost | [Challenge 5](finance/challenge-5-cost/README.md), and Challenge 4, Part 2 as a demo |
| 16:15 | Use-case mapping and next steps | Discussion |

If there is a second day, participants deploy the hosted agent themselves (Challenge 4, Part 2) and adapt a lab to their own use case.

### When the labs run in the customer's subscription

- [ ] Ask which regions the customer's Azure Policy allows. If it allows only India regions, see section 2 of the prerequisites.
- [ ] Ask whether the policy blocks public network access, Codespaces or `learn.microsoft.com`. Plan the fallbacks below.
- [ ] Use only the synthetic data in this repository. Never load customer data into a workshop project.
- [ ] Agree who deletes the resource group after the event, and when.

## Agenda and labs

| Time | Session | Lab content | Notes |
| --- | --- | --- | --- |
| 09:00 | Welcome and environment check | [Challenge 0](factory/challenge-0-setup/README.md) | Each participant runs `python factory/smoke_test.py` |
| 09:30 | Platform tour and model choice | Slides | Show the agent, the tools catalog, Foundry IQ, traces and evaluations |
| 10:15 | Lab 1 · First agent in code | [Challenge 1](factory/challenge-1-build/README.md) | 45 minutes |
| 11:00 | Break | | |
| 11:15 | Lab 2 · Knowledge with Foundry IQ | [Challenge 1b](factory/challenge-1b-knowledge/README.md) | 60 minutes. Path A in the portal. Path B is the fallback |
| 12:15 | Lunch | | Check that all participants finished Lab 2 |
| 13:00 | Lab 3 · Tools, MCP and approvals | [Challenge 1c](factory/challenge-1c-tools/README.md) | 60 minutes |
| 14:00 | Lab 4 · Trace, evaluate, red-team | [Challenge 2](factory/challenge-2-monitor/README.md) and [Challenge 3](factory/challenge-3-evaluate/README.md) | 45 minutes. See the timing below |
| 14:45 | Break | | |
| 15:00 | Lab 5 · Multi-agent orchestration | [Challenge 4](factory/challenge-4-deploy/README.md), Part 1 | 45 minutes |
| 15:45 | Deploy hosted agent and publish | [Challenge 4](factory/challenge-4-deploy/README.md), Part 2 | 30 minutes. Publishing is a demo |
| 16:15 | Path to production | Slides | Use the red team and evaluation results from Lab 4 |
| 16:45 | Pilot canvas and owners | Discussion | |

### Lab 4 timing

Lab 4 has 45 minutes for two challenges. Use this order:

1. **14:00** Start the red team scan: `python factory/challenge-3-evaluate/red_team.py`. It runs in Foundry for 10 to 30 minutes.
2. **14:02** Challenge 2: traces in Application Insights (15 minutes).
3. **14:17** Challenge 3, Steps 1–4: portal evaluation and the correctness check (20 minutes).
4. **14:37** Challenge 3, Step 5: read the red team results (8 minutes).

If time is short, show Step 5 as a demo on your own project.

## Before the event

### T–10 working days

- [ ] Confirm the date, the number of participants and the region.
- [ ] Send [PREREQUISITES.md](PREREQUISITES.md), Part 1, to the Azure administrator.
- [ ] Ask the Microsoft 365 administrator if participants can publish an agent to Teams. If not, plan publishing as a demo.
- [ ] Check that the region supports the AI Red Teaming Agent and Code Interpreter.

### T–5 working days: dry run

Do the dry run in a project that is the same as a participant project. Use an account with only the participant roles.

1. Create a new codespace from this branch. Or create a new virtual environment on a laptop.
2. Install the packages from `requirements.txt`.
3. Run each lab from start to end:
    - [ ] `python factory/smoke_test.py`
    - [ ] `python factory/challenge-1-build/agents.py`
    - [ ] Challenge 1b, Path A in the portal, and `python factory/challenge-1b-knowledge/knowledge_agent.py`
    - [ ] `python factory/challenge-1c-tools/tools_agent.py --yes`
    - [ ] Challenge 2 traces
    - [ ] Challenge 3 portal evaluation, `score_classification.py` and `red_team.py`
    - [ ] Challenge 4 `run_local.py`, `azd ai agent init`, `azd deploy` and `chat_hosted.py`
    - [ ] Finance track only: the same steps in `finance/`, plus `python finance/challenge-5-cost/cost_compare.py`
    - [ ] Finance track only: write down the real accuracy, tokens and cost from Challenge 5. Use them in the cost session
4. Write down every portal label that differs from the lab text. Fix the text before the event.
5. Freeze the packages that worked:

    ```bash
    pip freeze > requirements.lock.txt
    ```

    Commit the file. Tell participants to install from it on the day.

### T–2 working days

- [ ] The administrator completes section 4b of the prerequisites (search service, storage account, documents). For the finance track, the container is `woodgrove-knowledge`.
- [ ] Check that a participant account can see the search service and the storage container in the Foundry portal.

### T–1 working day

- [ ] All participants completed Part 2 of the prerequisites. Their smoke test passed.
- [ ] Create your own demo project with all labs complete. Keep the agents (`--keep`) for demos.

## Fallbacks

| Problem | Fallback |
| --- | --- |
| Foundry IQ isn't available, or the search service isn't ready | Use Challenge 1b, Path B (File Search in code) |
| A participant can't run `az login` | Use the portal steps in Challenges 1, 2 and 4. Pair the participant with a colleague for Labs 2–3 in code |
| The red team scan fails or the region isn't supported | Show the red team results from your demo project |
| Code Interpreter isn't available in the region | Show Task 1 of Challenge 1c as a demo. Do Task 2 (MCP and approvals) hands-on |
| `learn.microsoft.com` is blocked by the proxy | Show Task 2 of Challenge 1c as a demo |
| `azd ai agent init` fails | Run `azd ai agent doctor`. If it still fails, show Part 2 of Challenge 4 as a demo |
| Model quota is short | Deploy `gpt-5.4-mini` and set `MODEL_DEPLOYMENT_NAME` in `factory/.env` |
| `gpt-5.4-mini` isn't deployed for Challenge 5 | Run `python cost_compare.py --models gpt-5.4`, then show your dry-run table for the comparison |
| The customer's policy allows only India regions | Use `southindia` and check the quota first. Show the red team scan as a demo if the region isn't supported |

## What changed in this version

- **Labs for the full day:** Challenge 1b (Foundry IQ knowledge), Challenge 1c (Code Interpreter, MCP and approvals), a correctness check and a red team scan in Challenge 3.
- **Tools:** azd 1.37.0 or later with the `microsoft.foundry` extension. Python 3.11 or later.
- **Packages:** removed `azure-ai-agents`, which the labs don't use. `azure-ai-projects` now has the same range as Agent Framework 1.13.1.
- **Text fixes:** current Foundry terms in Challenge 1 (Foundry SDK, conversations, Foundry IQ, MCP). The correct dataset path in Challenge 3.
- **Finance track:** a second scenario in `finance/` (Woodgrove Finance, collections early warning) with the same labs, a fairness check in Challenge 3 and a cost lab in Challenge 5. All data is synthetic.

### Optional upgrade

Agent Framework 1.26 and `agent-framework-foundry` 1.16.2 need Python 3.11 or later and `agent-framework-core` 1.24 or later. They support `azure-ai-projects` up to 2.7. Test Challenge 4 before you change the versions in `requirements.txt`.
