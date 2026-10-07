# 🎉 Lab Complete — Predictive Maintenance (TireForge Industries)

Congratulations — you've built, instrumented, evaluated, and deployed a production-ready multi-agent AI system from scratch. Here's what you accomplished.

---

## Recap

| # | Challenge | What You Built |
|---|-----------|----------------|
| 0 | **Setup** | Created a Microsoft Foundry project, a GPT model deployment and an Application Insights connection in the Foundry portal |
| 1 | **Build Agents** | Created an **Anomaly Detection Agent** (reads live sensor telemetry — temperature, vibration, pressure — and identifies machines operating outside safe thresholds) and a **Fault Diagnosis Agent** (determines root cause and recommends maintenance actions per machine type) |
| 2 | **Monitor** | Enabled OpenTelemetry GenAI tracing — every model call, tool invocation, and token count is captured as a distributed trace in Application Insights |
| 3 | **Evaluate** | Ran systematic LLM-as-judge evaluations across the full sensor dataset, producing repeatable coherence and fluency scores you can version-track across prompt changes |
| 4 | **Orchestrate and deploy** | Chained both agents with Microsoft Agent Framework, added a human approval before each work order, and deployed the orchestration to Foundry as a hosted agent |

### Skills you practiced

- Designing agent system prompts with clear role boundaries and constraints
- Grounding agents in real sensor telemetry via tool calls (function calling)
- Distributed tracing for AI systems with OpenTelemetry
- LLM-as-judge evaluation with the Azure AI Evaluation SDK
- Multi-agent orchestration with Microsoft Agent Framework, deployed as a Foundry hosted agent
- Human-in-the-loop approval before an agent takes an action

---

## Next Steps

Want to take the TireForge system further? Here are some directions:

- **Add more agents** — a Parts Inventory agent that checks whether replacement components are in stock before recommending maintenance, or a Scheduling agent that finds the earliest maintenance window with minimal production impact
- **Connect real data** — replace the static `sensor_data.json` with a live IoT Hub or Azure Event Hub stream
- **Improve evaluation** — add task-specific evaluators (e.g., "did the agent correctly identify a Curing Press failure from elevated temperature + abnormal pressure combination?") alongside the generic coherence scores
- **Set up CI/CD** — run your evaluation dataset automatically on every prompt change using GitHub Actions and fail the build if quality scores drop below a threshold
- **Explore fine-tuning** — use your traced fault diagnoses as training data to fine-tune a smaller, cheaper model for the initial anomaly detection step

---

## Clean up

Your project lives in the shared `foundry-workshop` resource group, so don't delete the resource group yourself. When the workshop is over, your Azure administrator deletes it:

```bash
az group delete --name foundry-workshop --yes --no-wait
```
