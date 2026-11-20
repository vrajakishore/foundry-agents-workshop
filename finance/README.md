# 🏦 Scenario: Collections Early Warning — Woodgrove Finance

> **Woodgrove Finance is a fictional retail lender.** All accounts, documents and cases in this track are synthetic.
> They contain no real customers, names or ID numbers.

## Background

**Woodgrove Finance** is a retail lender with branches in many cities. It offers home loans, loans against property, used car loans, unsecured business loans and personal loans.

Every month, the early-warning system checks four signals for each active loan account:

| Signal | Meaning | Limit |
| --- | --- | --- |
| `days_past_due` | Days since the oldest unpaid EMI was due | 0 |
| `emi_bounces_6m` | EMI payment mandates that bounced in the last 6 months | 1 |
| `bureau_score_drop_90d` | Fall in the credit bureau score over 90 days | 50 (secured loans), 40 (unsecured loans) |
| `credit_enquiries_90d` | New credit enquiries from other lenders in 90 days | 3 |

The status rules are simple and strict:

- **NORMAL**: every signal is at or below its limit.
- **WATCH**: one or two signals are above their limits, and `days_past_due` is 30 or less.
- **CRITICAL**: `days_past_due` is more than 30, or three or more signals are above their limits.

This month's scan covers five accounts:

| Account | Product | Status | Why |
| --- | --- | --- | --- |
| **HL-1001** | Home loan | NORMAL | All signals within limits |
| **LAP-1002** | Loan against property | WATCH | 15 days past due, 2 bounces |
| **UBL-1003** | Unsecured business loan | CRITICAL | 46 days past due, 4 bounces, bureau score down 66, 5 enquiries |
| **UCL-1004** | Used car loan | NORMAL | Two signals exactly at their limits |
| **PL-1005** | Personal loan | WATCH | No overdue amount, but bureau score down 62 and 6 enquiries |

## Your mission

Build an AI agent system that:

1. **Finds early warning signs**: checks each account's signals against its limits and sets the status.
2. **Recommends the next best action**: names the likely situation, the procedure and the urgency, grounded in Woodgrove's collections policy.
3. **Keeps people in control**: opens a collections case only after a collections manager approves it. It never approves a waiver or a payment plan.
4. **Treats borrowers fairly and protects their data**: it uses only the signals, never a borrower's age, gender, religion, caste or location, and never reveals ID numbers.

## Challenges

| # | Challenge | What you do | Time |
|---|-----------|-------------|------|
| 0 | [Verify setup](./challenge-0-setup/README.md) | Check your project, model and `.env` | 5 min |
| 1 | [Build agents](./challenge-1-build/README.md) | Create the Early-Warning Agent and the Collections Advisor Agent | 45 min |
| 1b | [Ground in knowledge](./challenge-1b-knowledge/README.md) | Connect a Foundry IQ knowledge base with the collections policy, the restructuring guideline and past cases | 60 min |
| 1c | [Tools, MCP and approvals](./challenge-1c-tools/README.md) | Find the earliest warning sign with Code Interpreter. Approve each MCP tool call | 60 min |
| 2 | [Monitor](./challenge-2-monitor/README.md) | Trace every agent call with Application Insights | 15 min |
| 3 | [Evaluate](./challenge-3-evaluate/README.md) | Score quality and correctness, check fairness and red-team the advisor | 30 min |
| 4 | [Orchestrate and deploy](./challenge-4-deploy/README.md) | Chain both agents with Agent Framework, approve each case and deploy as a hosted agent | 45 min + 30 min |
| 5 | [Cost](./challenge-5-cost/README.md) | Measure the tokens per account check, compare models and project the monthly cost | 30 min |

### Full-day agenda (09:00–17:00)

| Time | Session | Challenge |
| --- | --- | --- |
| 09:00–09:30 | Welcome, objectives and environment check | 0 |
| 09:30–10:15 | Microsoft Foundry platform and model overview | Slides |
| 10:15–11:00 | Build the first agent | 1 |
| 11:15–12:15 | Ground with enterprise knowledge (Foundry IQ) | 1b |
| 13:00–14:00 | Add tools and actions | 1c |
| 14:00–14:45 | Evaluation, safety and tracing | 2 and 3 |
| 15:00–15:45 | Agent orchestration | 4, Part 1 |
| 15:45–16:15 | Security, production readiness and cost | 5, and the deploy demo (4, Part 2) |
| 16:15–17:00 | Use-case mapping and next steps | Discussion |

On a second day, participants deploy the hosted agent themselves (Challenge 4, Part 2) and adapt the labs to their own use case.

## Why the challenges are in this order

**Build first.** A collections agent with vague instructions makes confident but wrong calls. It can call a CRITICAL account "normal", or chase a borrower who only has a mandate problem. The `check_account_signals` tool and strict status rules ground the agent in the facts of each loan.

**Then ground and extend.** The advisor can only name the right procedure, approver and similar case if it can read Woodgrove's policy and case history. Foundry IQ gives it that knowledge with citations. Code Interpreter finds trends that one snapshot can't show. Approvals keep a person in control of every tool that you don't own.

**Then monitor.** When the advisor recommends priority resolution for UBL-1003, did it read the real signals? Traces answer that. In a regulated business, traces are also your audit record.

**Then evaluate.** Evaluation shows whether the status is **correct**, whether two borrowers with the same signals get the **same** status, and what happens when someone tries to misuse the agent.

**Then deploy and cost it.** A hosted agent with an approval step is something a collections team can trust. A cost per account check is something a business owner can approve.

## Before production

This lab shows the patterns. A production system also needs:

- **Data protection.** Use synthetic or masked data in every test environment. Keep personal data out of prompts, traces and evaluation datasets. Map your controls to your data protection law, for example India's Digital Personal Data Protection (DPDP) Act.
- **Model risk management.** Version each agent, keep the evaluation results for each version and gate each release on accuracy and fairness.
- **Regulatory guidance.** Map your controls to your regulator's AI guidance, for example the Reserve Bank of India's FREE-AI framework (August 2025).
- **Network and identity.** Private networking, managed identities and least-privilege roles. See the security session in the slides.
