# Challenge 1c: Tools, MCP and approvals

Time: ~60 minutes (full-day Lab 3)

## Objectives

By the end of this challenge, you will have:

- ✅ An agent that analyses 12 months of account history with **Code Interpreter** and returns a chart
- ✅ The same agent connected to a remote **MCP server**
- ✅ A **human approval** step before every MCP tool call
- ✅ A clear view of which tools run in your code and which run in Foundry

## Context

One snapshot shows that UBL-1003 is CRITICAL today. The risk team asks a better question: **which signal warned us first, and how early?** That needs data analysis over time.

[account_history.csv](./account_history.csv) has one row per account per month, from December 2025 to November 2026. The last row for each account matches `loan_accounts.json` in Challenge 1.

The team also wants guidance on connecting Foundry agents to SharePoint and to remote MCP servers, for example a data warehouse. That guidance is in Microsoft Learn, and Microsoft Learn has an MCP server.

## Tools in this challenge

| Tool | Where it runs | Approval |
| --- | --- | --- |
| `check_account_signals` (Challenge 1) | In your Python code | Your code decides |
| **Code Interpreter** | In a sandbox in Foundry | Not needed. The sandbox has no network access |
| **MCP** (`microsoft_learn`) | On a remote server that someone else operates | `require_approval="always"` |

> [!IMPORTANT]
> Treat tool descriptions and results from a remote MCP server as untrusted input. They can contain hidden instructions. Allow only the tools you need with `allowed_tools`. Require approval for tools that write data or send data out. Never send customer data to an MCP server that you don't control.

## Step 1: Review the code

Open [tools_agent.py](./tools_agent.py) and find:

- **`code_interpreter_tool()`**: attaches `account_history.csv` to a Code Interpreter sandbox.
- **`MCPTool(...)`**: connects to `https://learn.microsoft.com/api/mcp`. `allowed_tools` allows only `microsoft_docs_search`. `require_approval="always"` stops the agent before each call.
- **`INSTRUCTIONS`**: the rule *"Never send account data to the MCP tool."*
- **`run_with_approvals()`**: shows each `mcp_approval_request` and sends your decision back as an `mcp_approval_response`.
- **`save_generated_files()`**: downloads the chart that Code Interpreter makes.

## Step 2: Run the agent

```bash
cd finance/challenge-1c-tools
python tools_agent.py
```

**Task 1** asks which signal warned first for UBL-1003. The agent writes and runs Python in the sandbox. The chart is saved to `output/ubl1003_early_warning.png`. Check the answer:

| Signal | First month above its limit |
| --- | --- |
| `credit_enquiries_90d` above 3 | **July 2026** (4 enquiries) |
| EMI bounces in 6 months above 1 | September 2026 |
| Bureau score more than 40 points below 3 months earlier | September 2026 (694, against 741 in June) |
| `days_past_due` above 0 | October 2026 |

The credit enquiries gave about **3 months of warning** before the first unpaid EMI. Woodgrove's case history (CASE-2025-118) shows the same lesson.

**Task 2** asks a Microsoft product question. The agent stops and asks for approval:

```
[APPROVAL NEEDED] MCP tool call
  Server:    microsoft_learn
  Tool:      microsoft_docs_search
  Arguments: {"query": "..."}
  Approve? [y/N]
```

Read the arguments. Check that they contain **no account data**. Type `y`. The answer has links to Microsoft Learn.

## Step 3: Reject a call

Run the script again. At the approval prompt, type `n`. The agent must say that it couldn't search. It must not make up links.

## Step 4: See it in the portal

Run `python tools_agent.py --keep`. In the [Foundry portal](https://ai.azure.com), open **Build → Agents → portfolio-analyst-agent**:

1. Look at the **Tools** list. You see Code Interpreter and the MCP server.
2. Open **Traces**. Find the `mcp_approval_request` and the Code Interpreter call.
3. Ask in the playground: *"Which account has no days past due but broke its limits anyway, and in which months?"* The answer is **PL-1005**: credit enquiries went above 3 in September 2026 and the bureau score drop went above 40 in October 2026. This is the kind of account that an early-warning system exists to find.

Delete the agent when you finish, or keep it for the wrap-up demo.

## Extend it (optional)

- **Status heat map:** ask the agent to apply the status rules to every account for every month and draw a heat map. UBL-1003 turns WATCH in July and CRITICAL in September, before any EMI was unpaid.
- **Your own API:** add an **OpenAPI** tool for your loan management system, for example a read-only "get repayment schedule" call.
- **Your data platform:** connect a managed or self-hosted MCP server for your data warehouse. Keep `require_approval="always"` until you trust it.

## Talk about it

- Which tools would you allow without approval in production? Which tools must always need approval?
- Who approves? The person who chats with the agent, or a collections manager? Challenge 4 shows a manager approval in a workflow.
- How do you keep an audit record of approvals? Look at the traces from this challenge.

## Success criteria

- [ ] `output/ubl1003_early_warning.png` shows the three panels and the limit lines
- [ ] The agent reports that credit enquiries crossed their limit first, about 3 months before the first unpaid EMI
- [ ] The MCP call runs only after you type `y`, and its arguments contain no account data
- [ ] When you type `n`, the agent doesn't make up an answer

## Learn more

- [Code Interpreter tool](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/code-interpreter)
- [Connect agents to MCP servers](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/model-context-protocol)
