# Challenge 1b: Ground the advice in policy

Time: ~60 minutes (full-day Lab 2)

## Objectives

By the end of this challenge, you will have:

- ✅ A **Foundry IQ knowledge base** with Woodgrove's collections policy, restructuring guideline and case history
- ✅ The **Collections Advisor Agent** connected to the knowledge base
- ✅ Answers that name the right procedure, approver and similar case, with citations

## Context

In Challenge 1, the advisor used only its instructions. It can say "escalate the account". It can't say "follow COL-PRC-05, offer option RS-B and ask the retail credit risk manager to approve it", because that information is in Woodgrove's documents.

The [knowledge](./knowledge) folder has three fictional documents:

| File | Contents |
| --- | --- |
| `woodgrove-collections-policy.md` | Signals, status rules, procedures COL-PRC-01 to 05, conduct rules, approval matrix, data and fairness rules |
| `woodgrove-restructuring-guideline.md` | Payment plan eligibility, options RS-A to RS-C, documents and approvers |
| `woodgrove-case-history.md` | Five past cases with their signals, actions, outcomes and lessons |

**Foundry IQ** gives your agent a knowledge base in Azure AI Search. The knowledge base plans the query, searches the documents, reranks the results and returns passages with sources. The same pattern works for policy libraries in SharePoint, with each user's permissions.

## Choose your path

| Path | Use it when |
| --- | --- |
| **A. Foundry IQ in the portal** (recommended) | Your administrator completed section 4b of [PREREQUISITES.md](../../PREREQUISITES.md) for the finance track |
| **B. File Search in code** (fallback) | Foundry IQ or the search service isn't available to you |

---

## Path A: Foundry IQ in the portal

> [!NOTE]
> Portal labels can change. If a label is different, choose the closest match. Ask your facilitator if you can't find a step.

Get these values from your facilitator:

- The search service name, for example `contoso-workshop-search`
- The storage account name, for example `contosoworkshopkb`
- The container name: `woodgrove-knowledge`

### Step 1: Connect the search service to your project

1. In the [Foundry portal](https://ai.azure.com), open **your own** project (`<your-alias>-workshop`).
2. Select **Build**, then **Knowledge**.
3. Select **Connect** (or **Create a knowledge base**) and choose the search service.
4. For authentication, select **API key**.

### Step 2: Create a knowledge source

1. Select **Add knowledge source**, then **Azure Blob Storage**.
2. Select the storage account and the `woodgrove-knowledge` container.
3. Name the knowledge source `<your-alias>-woodgrove-docs`. Use your alias, because all participants share the search service.
4. If the portal asks for an embedding model, select one in your project. Deploy `text-embedding-3-small` if you have none.
5. Select **Create**. Wait until the documents are indexed. This takes a few minutes.

### Step 3: Create a knowledge base

1. Select **Create knowledge base** and name it `<your-alias>-woodgrove-kb`.
2. Add the knowledge source from Step 2.
3. If you can select a model for query planning, select **gpt-5.4**.
4. In the retrieval instructions, enter: *"Prefer the collections policy for procedures and approvals. Prefer the restructuring guideline for payment plans. Use the case history for similar cases."*
5. Select **Create**.

### Step 4: Test the knowledge base

In the test pane, ask:

> *Who approves a waiver of ₹7,500 in bounce charges?*

The answer must say **zonal collections head** and cite `woodgrove-collections-policy.md`.

### Step 5: Connect the knowledge base to your agent

1. Select **Build → Agents** and open `collections-advisor-agent`.
2. In **Knowledge** (or **Tools**), select **Add**, then **Foundry IQ** and `<your-alias>-woodgrove-kb`.
3. Add this text to the end of the agent instructions:

    ```text
    Before you recommend an action, search the Woodgrove knowledge base.
    Name the procedure ID (COL-PRC-01 to COL-PRC-05) and the urgency from the collections policy.
    For a payment plan, check each eligibility condition in the restructuring guideline and name the option and the approver.
    If a case in the case history matches the pattern, name the case ID.
    Cite the source document for each fact. If the knowledge base has no answer, say so.
    ```

4. Select **Save**. This creates a new agent version.

### Step 6: Compare the answers

Ask the agent in the playground:

> *UBL-1003 is an unsecured business loan. It is 46 days past due, with 4 EMI bounces in 6 months, a bureau score drop of 66 points and 5 new credit enquiries. Outstanding ₹11,84,000. 15 EMIs paid. Never restructured. The borrower says a large buyer pays his invoices late. What do we do, and can we offer a payment plan?*

Compare the answer with Challenge 1. Check that the new answer:

- names **COL-PRC-05** priority resolution, with contact **within 24 hours**
- says the account is **eligible** for a payment plan (46 ≤ 60 days, 15 ≥ 6 EMIs, no earlier restructuring, documented buyer delay)
- recommends option **RS-B (step-up EMI)** and lists Form **RS-1**, 6 months of bank statements and 2 GST returns
- says the **retail credit risk manager** approves it (outstanding is below ₹25,00,000), and that the agent can't approve it
- names **CASE-2025-118** as a similar case
- shows citations

Then ask a question that the documents can't answer: *"What interest rate does Woodgrove charge on gold loans?"* The agent must say that it has no information.

---

## Path B: File Search in code

This path uploads the same documents to a vector store and gives a new agent the **File Search** tool. It needs only `az login`.

```bash
cd finance/challenge-1b-knowledge
python knowledge_agent.py
```

The script creates `collections-advisor-kb-agent`, asks four questions (UBL-1003, PL-1005, the LAP-1002 waiver and the gold loan rate), prints each answer with its sources, then deletes the agent and the vector store. Add `--keep` to keep them.

Expected answers:

| Question | The answer must say |
| --- | --- |
| UBL-1003 | COL-PRC-05, IMMEDIATE, eligible, RS-B, retail credit risk manager, CASE-2025-118 |
| PL-1005 | COL-PRC-03 early outreach call within 7 days. **No top-up.** CASE-2025-131 |
| LAP-1002 waiver of ₹7,500 | Zonal collections head. The agent can't approve it |
| Gold loan rate | No information in the documents |

---

## Talk about it

- **Policies change.** When the policy team updates a document in SharePoint or Blob Storage, the knowledge base re-indexes it. You don't change the agent.
- **Who can see what?** With SharePoint sources, Foundry IQ can filter results by the user's permissions. A branch officer and a credit risk manager can get different documents.
- **Keys or identities?** This lab uses an API key. In production, use the project's managed identity with the **Search Index Data Reader** role.

## Success criteria

- [ ] The knowledge base names the zonal collections head for the ₹7,500 waiver, with a citation
- [ ] The advisor names COL-PRC-05, option RS-B, the approver and CASE-2025-118 for UBL-1003
- [ ] The advisor says "no information" for the gold loan rate

## Learn more

- [Connect a Foundry IQ knowledge base to Foundry Agent Service](https://learn.microsoft.com/azure/foundry/agents/how-to/foundry-iq-connect)
- [Connect a Foundry IQ (Azure AI Search) index to Foundry agents](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/ai-search)
