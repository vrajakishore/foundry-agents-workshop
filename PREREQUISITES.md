# Microsoft Foundry Hands-on Workshop
## Prerequisites

Each participant creates their own **Microsoft Foundry project** and a first agent in the Foundry portal, in your Azure subscription. Your Azure administrator completes **Part 1** at least **1 working day before** the workshop. Each participant completes **Part 2** (about 30 minutes) the **day before**.

> **Full-day build lab:** Labs 2, 3 and 4 need more setup. Your administrator also completes section 4b at least **2 working days before** the workshop. For the half-day format, skip section 4b. See [FACILITATOR.md](FACILITATOR.md) for the full-day plan.

# Part 1 — Azure administrator

## 1. Subscription and resource group

- Use a **sandbox or development subscription** (not production) with a valid billing method.
- Register the required resource providers and create one resource group for the workshop:

```powershell
az account set --subscription "<subscription-id>"
foreach ($ns in "Microsoft.CognitiveServices","Microsoft.Insights","Microsoft.OperationalInsights","Microsoft.Storage","Microsoft.Search") { az provider register --namespace $ns }
az group create --name foundry-workshop --location swedencentral
```

- If Azure Policy restricts regions, resource types, public network access or tags, **exempt the `foundry-workshop` resource group**.

## 2. Region and model quota

- **Region:** `swedencentral` (recommended). Alternatives: `eastus2`, `westeurope`.
- **Model:** each participant deploys `gpt-5.4`, Global Standard, with **10K tokens per minute**. For example, 15 participants need **150K TPM** in the region.
- **Fallback model:** `gpt-5.4-mini`, with the same quota. `gpt-5-mini` also works, but it retires earlier.
- **Full-day lab:** the AI Red Teaming Agent (Lab 4) runs only in some regions. `swedencentral` and `eastus2` are supported. `westeurope` is not. Check the [region list](https://learn.microsoft.com/azure/foundry/how-to/develop/run-scans-ai-red-teaming-agent) before you choose another region.
- **Policy allows only India regions?** Use `southindia`. Before you create resources, open **Manage → Quota** in the Foundry portal and check that `gpt-5.4` has quota there. A Global Standard deployment can process prompts in any Azure region. A Data Zone Standard deployment keeps processing inside the Asia Pacific data zone and costs about 10% more. If the AI Red Teaming Agent isn't supported in the region, the facilitator shows that step as a demo.
- **Finance track, Challenge 5 (optional):** participants also deploy `gpt-5.4-mini` with **10K TPM** to compare two models. Plan the extra quota.

Check your available quota:

```powershell
az cognitiveservices usage list --location swedencentral --query "[?contains(name.value,'gpt-5')].{quota:name.value, used:currentValue, limit:limit}" -o table
```

If quota is short, request an increase from the **Quota** page in the Foundry portal now, because approval isn't instant.

## 3. Give participants access

Add all participants to one **Microsoft Entra security group**, then assign these roles to the group:

| Role | Scope | Lets participants |
| --- | --- | --- |
| **Contributor** | `foundry-workshop` resource group | Create their Foundry project, deploy a model and connect tracing |
| **Foundry Project Manager** | `foundry-workshop` resource group | Create, run and evaluate agents, create project connections, and deploy hosted agents |
| **Cognitive Services Usages Reader** | Subscription | See available quota when deploying a model |

> **Important:** Participants need **both** Contributor and Foundry Project Manager. Contributor alone can't build agents, and the last lab needs Foundry Project Manager to deploy a hosted agent. Only an **Owner** or **User Access Administrator** can assign these roles.

```powershell
$sub   = "<subscription-id>"
$group = "<participants-group-object-id>"
$rg    = "/subscriptions/$sub/resourceGroups/foundry-workshop"
az role assignment create --role "Contributor" --assignee-object-id $group --assignee-principal-type Group --scope $rg
az role assignment create --role "eadc314b-1a2d-4efa-be10-5d325db5065e" --assignee-object-id $group --assignee-principal-type Group --scope $rg   # Foundry Project Manager
az role assignment create --role "Cognitive Services Usages Reader" --assignee-object-id $group --assignee-principal-type Group --scope "/subscriptions/$sub"
```

These roles apply to the whole resource group, so every participant can open every other participant's project. The labs assume **one project per participant**, so ask everyone to name their project and Application Insights resource with their alias (sections 5 and 7).

Role assignments can take up to 10 minutes to apply. Then send participants the **resource group name** (`foundry-workshop`) and **region** (`swedencentral`).

## 4. Network

If participants are on a corporate network or proxy, allow:

- **Foundry:** `ai.azure.com`, `*.services.ai.azure.com`, `*.cognitiveservices.azure.com`, `*.openai.azure.com`
- **Azure:** `login.microsoftonline.com`, `management.azure.com`, `portal.azure.com`
- **Monitoring:** `*.applicationinsights.azure.com`, `*.monitor.azure.com`
- **Full-day lab:** `*.search.windows.net`, `*.blob.core.windows.net`, `learn.microsoft.com` (the MCP server in Lab 3)
- **Code:** `github.com`, `*.githubusercontent.com`, `*.github.dev`, `aka.ms`, `pypi.org`, `files.pythonhosted.org`

If your tenant blocks **device-code sign-in**, participants can't sign in from GitHub Codespaces and should use their own laptop instead.

## 4b. Full-day lab only: knowledge for Lab 2

Lab 2 grounds an agent in company documents with **Foundry IQ**: TireForge maintenance documents in the factory track, or Woodgrove Finance policies in the finance track. Foundry IQ uses **Azure AI Search**. Create one search service and one storage account for all participants.

1. Create an **Azure AI Search** service in the `foundry-workshop` resource group:
    - **Name:** `<org>-workshop-search` (it must be unique in Azure).
    - **Region:** the workshop region.
    - **Pricing tier:** **Basic** or higher. The Free tier doesn't support the lab.
    - After creation, open **Settings → Semantic ranker** and select the **Free** plan.
2. Create a **storage account** in the same resource group, for example `<org>workshopkb`. Create a blob container for your track:
    - Factory track: `tireforge-knowledge`
    - Finance track: `woodgrove-knowledge`
3. Upload the three files for your track to the container:
    - Factory track: [factory/challenge-1b-knowledge/knowledge](factory/challenge-1b-knowledge/knowledge)
    - Finance track: [finance/challenge-1b-knowledge/knowledge](finance/challenge-1b-knowledge/knowledge)

```powershell
az search service create --name <org>-workshop-search --resource-group foundry-workshop --location swedencentral --sku basic --semantic-search free
az storage account create --name <org>workshopkb --resource-group foundry-workshop --location swedencentral --sku Standard_LRS
az storage container create --name tireforge-knowledge --account-name <org>workshopkb --auth-mode login
az storage blob upload-batch --destination tireforge-knowledge --source factory/challenge-1b-knowledge/knowledge --account-name <org>workshopkb --auth-mode login
```

For the finance track, replace the last two commands with:

```powershell
az storage container create --name woodgrove-knowledge --account-name <org>workshopkb --auth-mode login
az storage blob upload-batch --destination woodgrove-knowledge --source finance/challenge-1b-knowledge/knowledge --account-name <org>workshopkb --auth-mode login
```

If your region is not `swedencentral`, change `--location` in the commands.

> **Note:** The `upload-batch` command needs **Storage Blob Data Contributor** on the storage account for your own account. If you don't have it, upload the files in the Azure portal instead.

The lab connects to the search service with an **API key**. Participants have Contributor on the resource group, so the portal can read the key for them. You don't need to assign search data roles for the lab.

> **Keyless option:** For production, use Microsoft Entra ID instead of keys. Then assign **Search Index Data Reader** on the search service to each project's managed identity, after the participants create their projects. See [Connect a Foundry IQ knowledge base to Foundry Agent Service](https://learn.microsoft.com/azure/foundry/agents/how-to/foundry-iq-connect).

If Foundry IQ isn't available to you, Lab 2 has a **File Search** path that needs no search service.

# Part 2 — Participant

Sign in to the Foundry portal at **https://ai.azure.com** with your work account and make sure the **New Foundry** toggle at the top of the page is **on**.

## 5. Create your project

1. In the upper-left, select the project name, then select **Create new project**.
2. Enter the project name `<your-alias>-workshop`, for example `asmith-workshop`. Use your own alias so the name is unique.
3. Expand **Advanced options**:
    - **Resource group:** select **`foundry-workshop`**. Don't create a new one, because you only have access to this one.
    - **Location:** select **Sweden Central**, or the region your administrator gave you.
4. Select **Create**. Creation takes a few minutes.

> **Use only your own project.** Everyone creates a project in the same `foundry-workshop` resource group, so the Foundry portal and the Azure portal also list your colleagues' projects and Application Insights resources. Open only the ones that start with your alias. The labs create agents with fixed names such as `anomaly-detection-agent`, so two people in one project overwrite each other's agents, traces and evaluation runs. Never reuse a colleague's project, even if you can open it.

## 6. Deploy the model

1. Select **Discover** in the upper-right navigation, then **Models** in the left pane.
2. Search for and select **gpt-5.4**.
3. Select **Deploy → Custom settings**.
4. Keep the deployment name **gpt-5.4**, set **Deployment type** to **Global Standard** and **Tokens per minute** to **10K**, then select **Deploy**.
5. The playground opens. Send *"Hello"* and check that you get a reply.
6. **Finance track only (optional):** repeat steps 2 to 4 for **gpt-5.4-mini**. Challenge 5 compares the cost and accuracy of the two models.

## 7. Connect tracing

1. Select **Build** in the upper-right navigation, then **Agents** in the left pane.
2. Select the **Traces** tab, then select **Connect**.
3. Select **Create new**, choose the **`foundry-workshop`** resource group, name it `<your-alias>-appinsights`, and finish the wizard.

If you don't see **Connect**, select **Manage → Project details → Connected resources → Add connection → Application Insights** instead.

## 8. Create your first agent

1. Select **Build → Agents → Create agent**.
2. Enter the name `machine-helper` and select **Create**.
3. Select the **gpt-5.4** model and enter these instructions: *"You help factory technicians troubleshoot machines. Answer in two sentences."*
4. Select **Save**.
5. In the chat pane, ask *"What does high vibration on a machine usually indicate?"* and check that the agent replies.

## 9. Prepare your workstation

The lab code is in https://github.com/vrajakishore/foundry-agents-workshop. Choose **one** option.

**Option A — GitHub Codespaces (recommended, nothing to install)**

1. Sign in to GitHub and open https://github.com/vrajakishore/foundry-agents-workshop.
2. Select **Code → Codespaces → Create codespace on main**. Wait a few minutes while the required packages install.
3. In the terminal, run `az login --use-device-code`.

**Option B — Your own laptop**

Install **Python 3.11 or later** (3.12 or 3.13 recommended), **Azure CLI 2.80+**, **Azure Developer CLI (`azd`) 1.37.0+**, **Git** and **VS Code**, then run:

```powershell
git clone https://github.com/vrajakishore/foundry-agents-workshop.git
cd foundry-agents-workshop
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
azd ext install microsoft.foundry
az login
```

Python 3.10 reached end of life in October 2026. Don't use it for the workshop.

## 10. Connect your code to your project

From the repository folder, copy the template to a new `.env` file in the **`factory`** folder:

```powershell
cp factory/.env.template factory/.env
```

Open `factory/.env` and fill in these two values:

- **`PROJECT_CONNECTION_STRING`:** in the Foundry portal, select **Home**. Copy the **Project endpoint**. It must end with `/api/projects/<your-alias>-workshop`. If it shows another name, you're in a colleague's project: select your own project in the upper-left and copy the endpoint again. The variable name says "connection string", but it holds the project endpoint.
- **`APPLICATIONINSIGHTS_CONNECTION_STRING`:** in the Azure portal (**https://portal.azure.com**), open **Resource groups → foundry-workshop**. Select `<your-alias>-appinsights`, then copy the **Connection String** from the **Overview** page.

**Can't run `az login`?** If your administrator allows API keys, also set **`FOUNDRY_API_KEY`**: in the Foundry portal, select **Home** and copy the **Project API key**. A key only reaches the model, so for the labs that build agents you use the portal steps in each lab. Leave it empty if `az login` works.

Then run this check, which creates a test agent, asks it a question and deletes it. With an API key, it only asks the model a question:

```powershell
python factory/smoke_test.py
```

**You're ready when** your agent replies in the portal and the script prints `Smoke test passed.`

## If something fails

| You see | Fix |
| --- | --- |
| Permission error when creating the project | Under **Advanced options**, select the **`foundry-workshop`** resource group. If it still fails, ask your administrator for **Contributor** on it |
| `PermissionDenied` when creating or deploying an agent | Ask your administrator for the **Foundry Project Manager** role. Wait 10 minutes, then sign in again |
| Quota error when deploying the model | Set a lower **Tokens per minute**, or deploy `gpt-5.4-mini` instead |
| `RequestDisallowedByPolicy` | Ask your administrator to exempt the `foundry-workshop` resource group from the policy |
| `KeyError: 'PROJECT_CONNECTION_STRING'` | Your `.env` file isn't in the `factory` folder |
| You see agents, traces or evaluations you didn't create | You're in a colleague's project. Select your own `<your-alias>-workshop` project in the portal and put its endpoint in `factory/.env` |
| `DefaultAzureCredential failed to retrieve a token` | Run `az login --tenant <tenant-id>` |
| `AuthenticationTypeDisabled` when using an API key | API keys are turned off for your project. Empty `FOUNDRY_API_KEY` in `.env` and run `az login` |
| `azd ai agent` says the command is unknown | Run `azd update`. Then run `azd ext install microsoft.foundry`. With azd older than 1.37.0, run `azd ext install azure.ai.agents` |
| `pip` can't find a version that matches | Your Python is too old. Use Python 3.11 or later |
| Portal shows hub or "classic" screens | Turn on **New Foundry** at the top of the portal |

## After the workshop

Administrators can delete everything with one command, and should also remove the subscription-level **Cognitive Services Usages Reader** assignment:

```powershell
az group delete --name foundry-workshop --yes --no-wait
```

**Useful links:** [Workshop repository](https://github.com/vrajakishore/foundry-agents-workshop) · [Foundry roles (RBAC)](https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry) · [Create a Foundry project](https://learn.microsoft.com/azure/foundry/how-to/create-projects) · [Connect agents to Foundry IQ](https://learn.microsoft.com/azure/foundry/agents/how-to/foundry-iq-connect)
