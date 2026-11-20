# Challenge 1b: Ground the diagnosis in knowledge

Time: ~60 minutes (full-day Lab 2)

## Objectives

By the end of this challenge, you will have:

- ✅ A **Foundry IQ knowledge base** with TireForge maintenance manuals, incident history and policy
- ✅ The **Fault Diagnosis Agent** connected to the knowledge base
- ✅ Answers that name the correct procedure and cite the source documents

## Context

In Challenge 1, the Fault Diagnosis Agent used only general knowledge and its system prompt. It can say "check the bearings". It can't say "follow procedure CP-PRC-07 and replace valve TF-CP-PRV3", because that information is in TireForge documents.

The [knowledge](./knowledge) folder has three fictional documents:

| File | Contents |
| --- | --- |
| `tireforge-maintenance-manual.md` | Failure modes, procedures and part numbers for each machine |
| `tireforge-incident-history.md` | Past incidents, root causes and lessons |
| `tireforge-maintenance-policy.md` | Urgency levels, work order rules and quality holds |

**Foundry IQ** gives your agent a knowledge base in Azure AI Search. When the agent calls it, the knowledge base plans the query, searches the documents, reranks the results and returns passages with sources.

## Choose your path

| Path | Use it when |
| --- | --- |
| **A. Foundry IQ in the portal** (recommended) | Your administrator completed section 4b of [PREREQUISITES.md](../../PREREQUISITES.md) |
| **B. File Search in code** (fallback) | Foundry IQ or the search service isn't available to you |

Both paths ground the same agent in the same documents.

---

## Path A: Foundry IQ in the portal

> [!NOTE]
> Portal labels can change. If a label is different, choose the closest match. Ask your facilitator if you can't find a step.

Get these values from your facilitator:

- The search service name, for example `contoso-workshop-search`
- The storage account name, for example `contosoworkshopkb`
- The container name: `tireforge-knowledge`

### Step 1: Connect the search service to your project

1. In the [Foundry portal](https://ai.azure.com), open **your own** project (`<your-alias>-workshop`).
2. Select **Build**, then **Knowledge** in the left pane.
3. Select **Connect** (or **Create a knowledge base**) and choose the search service that your facilitator gave you.
4. For authentication, select **API key**. The portal reads the key for you.

### Step 2: Create a knowledge source

1. Select **Add knowledge source** (or **Create knowledge source**).
2. Select **Azure Blob Storage**.
3. Select the storage account and the `tireforge-knowledge` container.
4. Name the knowledge source `<your-alias>-tireforge-docs`. Use your alias, because all participants share the search service.
5. If the portal asks for an embedding model or a chat model, select the models in your project. Deploy `text-embedding-3-small` if the portal asks for an embedding model and you don't have one.
6. Select **Create**. Wait until the status shows that the documents are indexed. This takes a few minutes.

### Step 3: Create a knowledge base

1. Select **Create knowledge base**.
2. Name it `<your-alias>-tireforge-kb`.
3. Add the knowledge source from step 2.
4. If you can select a model for query planning and answer synthesis, select **gpt-5.4**.
5. In the retrieval instructions, enter: *"Prefer the maintenance manual for procedures. Prefer the incident history for root causes."*
6. Select **Create**.

### Step 4: Test the knowledge base

Use the test pane of the knowledge base. Ask:

> *Which procedure applies when the CP-003 curing press has high pressure and high vibration?*

The answer must name **CP-PRC-07** and cite `tireforge-maintenance-manual.md`.

### Step 5: Connect the knowledge base to your agent

1. Select **Build → Agents**, then open `fault-diagnosis-agent`.
2. In **Knowledge** (or **Tools**), select **Add**, then select **Foundry IQ** and your knowledge base `<your-alias>-tireforge-kb`.
3. Add this text to the end of the agent instructions:

    ```text
    Before you recommend an action, search the TireForge knowledge base.
    Name the procedure ID and the part numbers from the manual.
    If an incident in the history matches the pattern, name the incident ID.
    Cite the source document for each fact. If the knowledge base has no answer, say so.
    ```

4. Select **Save**. This creates a new version of the agent.

### Step 6: Compare the answers

Ask the agent in the playground:

> *CP-003 reads temperature 198.5 °C, pressure 18.2 bar, vibration 7.3 mm/s and 0 rpm. Diagnose the fault and recommend actions.*

Compare the answer with the answer from Challenge 1. Check that the new answer:

- names procedure **CP-PRC-07**
- names part numbers **TF-CP-PRV3** and **TF-CP-SK12**
- names incident **INC-2025-014** as a similar case
- tells the operator to stop the press now, not at the end of the cycle
- shows citations

Then ask a question that the documents can't answer, for example *"What is the warranty period for the CP-003 press?"*. The agent must say that it has no information. It must not make up an answer.

---

## Path B: File Search in code

This path uploads the same documents to a vector store and gives a new agent the **File Search** tool. It needs only `az login`.

```bash
cd factory/challenge-1b-knowledge
python knowledge_agent.py
```

The script:

1. Uploads the three documents to a vector store.
2. Creates the agent `fault-diagnosis-kb-agent` with the File Search tool.
3. Asks three questions and prints each answer with its sources.
4. Deletes the agent and the vector store. Add `--keep` to keep them, so you can test the agent in the portal.

---

## Talk about it

- **Foundry IQ or File Search?** File Search is quick for a few files and one agent. Foundry IQ is for knowledge that many agents share. It also supports SharePoint, OneLake and web sources, with permissions.
- **Who can see what?** With SharePoint sources, Foundry IQ can filter results by the permissions of the user. Plan this before a pilot.
- **Keys or identities?** This lab uses an API key. In production, use the project's managed identity with the **Search Index Data Reader** role.

## Success criteria

- [ ] The knowledge base answers the test question with procedure CP-PRC-07 and a citation
- [ ] The Fault Diagnosis Agent names the procedure, the part numbers and incident INC-2025-014
- [ ] The agent says "no information" for a question that the documents can't answer

## Learn more

- [Connect a Foundry IQ knowledge base to Foundry Agent Service](https://learn.microsoft.com/azure/foundry/agents/how-to/foundry-iq-connect)
- [Connect a Foundry IQ (Azure AI Search) index to Foundry agents](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/ai-search)
