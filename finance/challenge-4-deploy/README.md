# Challenge 4: Orchestrate and deploy

Time: Part 1 ~45 minutes (full-day Lab 5). Part 2 ~30 minutes (facilitator demo, or day 2 hands-on)

## Objectives

By the end of this challenge, you will have:

- ✅ Chained the Early-Warning Agent and the Collections Advisor Agent in code with Microsoft Agent Framework
- ✅ Approved or rejected a collections case before the agent opened it (human in the loop)
- ✅ Deployed the orchestration to Foundry as a hosted agent

> [!NOTE]
> The visual workflow designer in the Foundry portal retires on **1 December 2026**. Microsoft recommends
> Agent Framework for new multi-agent work, so this challenge builds the orchestration in code.

## The flow

```
early-warning-agent      -->  collections-advisor-agent  -->  create_collections_case
 (check_account_signals)        (situation, action, urgency)     (a collections manager approves or rejects)
```

| File | What it does |
|------|--------------|
| `collections_orchestration.py` | The two agents, their tools and the sequential orchestration |
| `run_local.py` | Runs the orchestration in your terminal |
| `main.py` | Entry point that Foundry runs when the orchestration is a hosted agent |
| `chat_hosted.py` | Chats with your hosted agent from the terminal |
| `requirements.txt` | Packages that Foundry installs for the hosted agent |
| `loan_accounts.json` | The same five accounts as Challenge 1 |

All files are in the [collections-ews-agent](./collections-ews-agent/) folder.

---

## Part 1: Run it locally

Part 1 works with `az login` or with `FOUNDRY_API_KEY` in your `.env`.

### Step 1: Review the code

Open [collections_orchestration.py](./collections-ews-agent/collections_orchestration.py) and find:

- **`check_account_signals`**: `approval_mode="never_require"`. It only reads data.
- **`create_collections_case`**: `approval_mode="always_require"`. It writes to a system of record, so a person must approve each call. Its `procedure` and `urgency` parameters accept only fixed values.
- **`build_workflow()`**: chains the two agents with `SequentialBuilder`. The advisor gets the early-warning report as text, without the first agent's tool calls.
- **`make_client()`**: signs in with Entra ID, or uses `FOUNDRY_API_KEY` if you set it. The hosted agent always uses Entra ID.

### Step 2: Run the early-warning check

```bash
cd finance/challenge-4-deploy/collections-ews-agent
python run_local.py
```

The early-warning report prints first. Then the advisor asks to open a case for the CRITICAL account:

```
[APPROVAL NEEDED] create_collections_case {"account_id": "UBL-1003", "procedure": "COL-PRC-05", "urgency": "IMMEDIATE", ...}
Approve? [y/N]
```

Read the summary. Check that it has no ID numbers. Type `y`. The final report quotes the new case ID, for example `CASE-UBL-1003-...`.

### Step 3: Reject a case

Run `python run_local.py` again and type `n`. The report must say that the case was rejected. It must not invent a case ID.

---

## Part 2: Deploy as a hosted agent

Foundry runs your code in a managed sandbox. You don't need Docker or a container registry.

> [!IMPORTANT]
> You need the **Foundry Project Manager** role on your project and `az login`. An API key can't deploy agents. If either is missing, stop after Part 1.

### Step 4: Sign in

Tell `azd` to reuse your Azure CLI sign-in:

```bash
azd config set auth.useAzCliAuth true
```

You need **azd 1.37.0 or later** with the **Microsoft Foundry** extension. Codespaces already has both. On your own laptop, run:

```bash
azd update
azd ext install microsoft.foundry
```

If you can't update azd, run `azd ext install azure.ai.agents` instead.

### Step 5: Set up the agent

From the `collections-ews-agent` folder:

```bash
azd ai agent init --src . --agent-name collections-ews-<yourname>
```

| Prompt | Answer |
|--------|--------|
| Foundry project | Use an existing project. Pick your subscription and **your own** project (`<your-alias>-workshop`) |
| Model | Use an existing model deployment. Pick `gpt-5.4` |
| Protocol | `responses` |
| How to deploy | Source Code (ZIP upload) |
| Runtime | Python 3.13 |
| Entry point | `main.py` |
| Build | Remote build |

Newer azd versions can ask fewer questions or ask them in a different order. Give the same answers.

### Step 6: Deploy

```bash
azd deploy
```

The first deploy takes about 2 minutes while Foundry installs the packages.

### Step 7: Chat with your hosted agent

```bash
python chat_hosted.py collections-ews-<yourname>
```

Approve the case as before. This time `create_collections_case` runs inside Foundry, not on your machine.

In the [Foundry portal](https://ai.azure.com), select **Build → Agents** to see your hosted agent and its traces. To stream its logs, run `azd ai agent monitor --follow`. If a step fails, run `azd ai agent doctor`.

### Step 8: Publish (facilitator demo)

A hosted agent can be published to Microsoft Teams and Microsoft 365 Copilot, so that collections managers approve cases where they already work. Publishing needs approval from your Microsoft 365 administrator, so your facilitator shows this step as a demo.

---

## Talk about it

- Who must approve a case in your organisation? Is it the same person for every amount and every product?
- Which tool calls in your process write to a system of record? Each one needs an approval step or a strict limit.
- How do you connect `create_collections_case` to your real collections system? An OpenAPI tool, an MCP server or an Azure Function?

## Success criteria

- [ ] `run_local.py` opens a case when you approve and reports a rejection when you don't
- [ ] The case summary contains no ID numbers
- [ ] Your orchestration runs as a hosted agent in Foundry
- [ ] `chat_hosted.py` gets an approval request from the hosted agent and returns a case ID
