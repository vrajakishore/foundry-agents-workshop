# Challenge 1c: Tools, MCP and approvals

Time: ~60 minutes (full-day Lab 3)

## Objectives

By the end of this challenge, you will have:

- ✅ An agent that analyses 24 hours of sensor history with **Code Interpreter** and returns a chart
- ✅ The same agent connected to a remote **MCP server**
- ✅ A **human approval** step before every MCP tool call
- ✅ A clear view of which tools run in your code and which run in Foundry

## Context

A good diagnosis needs more than the latest reading. The maintenance team wants to know **when** each reading started to drift. That needs data analysis. The team also wants guidance on how to connect real machines to Azure. That guidance is in Microsoft Learn, and Microsoft Learn has an MCP server.

[sensor_history.csv](./sensor_history.csv) has hourly readings for all five machines over 24 hours. The last row for each machine matches `sensor_data.json` in Challenge 1.

## Tools in this challenge

| Tool | Where it runs | Approval |
| --- | --- | --- |
| `check_thresholds` (Challenge 1) | In your Python code | Your code decides |
| **Code Interpreter** | In a sandbox in Foundry | Not needed. The sandbox has no network access |
| **MCP** (`microsoft_learn`) | On a remote server that someone else operates | `require_approval="always"` |

> [!IMPORTANT]
> Treat tool descriptions and results from a remote MCP server as untrusted input. They can contain hidden instructions. Allow only the tools you need with `allowed_tools`, and require approval for tools that write data or change resources.

## Step 1: Review the code

Open [tools_agent.py](./tools_agent.py) and find:

- **`code_interpreter_tool()`**: attaches `sensor_history.csv` to a Code Interpreter sandbox.
- **`MCPTool(...)`**: connects to `https://learn.microsoft.com/api/mcp`. `allowed_tools` allows only `microsoft_docs_search`. `require_approval="always"` stops the agent before each call.
- **`run_with_approvals()`**: finds each `mcp_approval_request` in the response, shows the tool name and arguments, and sends your decision back as an `mcp_approval_response` in the same conversation.
- **`save_generated_files()`**: downloads the chart that Code Interpreter makes.

## Step 2: Run the agent

```bash
cd factory/challenge-1c-tools
python tools_agent.py
```

**Task 1** asks for a CP-003 trend chart. The agent writes and runs Python in the sandbox. The chart is saved to `output/cp003_trend.png`. Check the answer:

- Vibration went above 3.0 mm/s first, at about **2026-05-12 23:30 UTC**.
- Temperature and pressure went above their limits about 2 and 3 hours later.
- The first crossing gave about **10 hours** of warning before the last reading.

**Task 2** asks a Microsoft product question. The agent stops and asks for approval:

```
[APPROVAL NEEDED] MCP tool call
  Server:    microsoft_learn
  Tool:      microsoft_docs_search
  Arguments: {"query": "..."}
  Approve? [y/N]
```

Read the arguments. Type `y`. The answer has links to Microsoft Learn.

## Step 3: Reject a call

Run the script again. At the approval prompt, type `n`. The agent must tell you that it couldn't search. It must not make up links.

## Step 4: See it in the portal

Run `python tools_agent.py --keep`. In the [Foundry portal](https://ai.azure.com), open **Build → Agents → maintenance-planner-agent**:

1. Look at the **Tools** list. You see Code Interpreter and the MCP server.
2. Open **Traces**. Find the `mcp_approval_request` and the Code Interpreter call.
3. Ask a new question in the playground. If the playground shows an approval prompt for the MCP call, read the arguments, then approve it.

Delete the agent when you finish, or keep it for the wrap-up demo.

## Extend it (optional)

- **Your own API:** add an **OpenAPI** tool for an internal system, such as a parts inventory.
- **Toolbox:** put Code Interpreter and the MCP server in a **Foundry toolbox**. Then any agent or runtime can reuse the same tools through one MCP endpoint.
- **Web Search:** add the Web Search tool to find supplier recalls for a part number.

## Talk about it

- Which tools would you allow without approval in production? Which tools must always need approval?
- Who approves? The person who chats with the agent, or a supervisor? Challenge 4 shows a supervisor approval in a workflow.
- How do you log approvals for audit? Look at the traces from this challenge.

## Success criteria

- [ ] `output/cp003_trend.png` shows the three readings and the limit lines
- [ ] The agent reports that vibration crossed its limit first
- [ ] The MCP call runs only after you type `y`
- [ ] When you type `n`, the agent doesn't make up an answer

## Learn more

- [Code Interpreter tool](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/code-interpreter)
- [Connect agents to MCP servers](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/model-context-protocol)
