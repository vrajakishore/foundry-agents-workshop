# Microsoft Foundry Hands-on Workshop
## Prerequisites

Each participant creates their own **Microsoft Foundry project** and a first agent in the Foundry portal, in your Azure subscription. Your Azure administrator completes **Part 1** at least **1 working day before** the workshop. Each participant completes **Part 2** (about 30 minutes) the **day before**.

# Part 1 — Azure administrator

## 1. Subscription and resource group

- Use a **sandbox or development subscription** (not production) with a valid billing method.
- Register the required resource providers and create one resource group for the workshop:

```powershell
az account set --subscription "<subscription-id>"
foreach ($ns in "Microsoft.CognitiveServices","Microsoft.Insights","Microsoft.OperationalInsights","Microsoft.Storage") { az provider register --namespace $ns }
az group create --name foundry-workshop --location swedencentral
```

- If Azure Policy restricts regions, resource types, public network access or tags, **exempt the `foundry-workshop` resource group**.

## 2. Region and model quota

- **Region:** `swedencentral` (recommended). Alternatives: `eastus2`, `westeurope`.
- **Model:** each participant deploys `gpt-5.4`, Global Standard, with **10K tokens per minute**. For example, 15 participants need **150K TPM** in the region.
- **Fallback model:** `gpt-5-mini`, with the same quota.

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
| **Foundry Project Manager** | `foundry-workshop` resource group | Create, run and evaluate agents, and deploy them as hosted agents |
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

Role assignments can take up to 10 minutes to apply. Then send participants the **resource group name** (`foundry-workshop`) and **region** (`swedencentral`).

## 4. Network

If participants are on a corporate network or proxy, allow:

- **Foundry:** `ai.azure.com`, `*.services.ai.azure.com`, `*.cognitiveservices.azure.com`, `*.openai.azure.com`
- **Azure:** `login.microsoftonline.com`, `management.azure.com`, `portal.azure.com`
- **Monitoring:** `*.applicationinsights.azure.com`, `*.monitor.azure.com`
- **Code:** `github.com`, `*.githubusercontent.com`, `*.github.dev`, `aka.ms`, `pypi.org`, `files.pythonhosted.org`

If your tenant blocks **device-code sign-in**, participants can't sign in from GitHub Codespaces and should use their own laptop instead.

# Part 2 — Participant

Sign in to the Foundry portal at **https://ai.azure.com** with your work account and make sure the **New Foundry** toggle at the top of the page is **on**.

## 5. Create your project

1. In the upper-left, select the project name, then select **Create new project**.
2. Enter a project name, for example `<your-alias>-workshop`.
3. Expand **Advanced options**:
    - **Resource group:** select **`foundry-workshop`**. Don't create a new one, because you only have access to this one.
    - **Location:** select **Sweden Central**, or the region your administrator gave you.
4. Select **Create**. Creation takes a few minutes.

## 6. Deploy the model

1. Select **Discover** in the upper-right navigation, then **Models** in the left pane.
2. Search for and select **gpt-5.4**.
3. Select **Deploy → Custom settings**.
4. Keep the deployment name **gpt-5.4**, set **Deployment type** to **Global Standard** and **Tokens per minute** to **10K**, then select **Deploy**.
5. The playground opens. Send *"Hello"* and check that you get a reply.

## 7. Connect tracing

1. Select **Build** in the upper-right navigation, then **Agents** in the left pane.
2. Select the **Traces** tab, then select **Connect**.
3. Select **Create new**, choose the **`foundry-workshop`** resource group, and finish the wizard.

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

Install **Python 3.10+**, **Azure CLI 2.80+**, **Azure Developer CLI (`azd`) 1.27.1+**, **Git** and **VS Code**, then run:

```powershell
git clone https://github.com/vrajakishore/foundry-agents-workshop.git
cd foundry-agents-workshop
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
azd ext install azure.ai.agents
az login
```

## 10. Connect your code to your project

From the repository folder, copy the template to a new `.env` file in the **`factory`** folder:

```powershell
cp factory/.env.template factory/.env
```

Open `factory/.env` and fill in these two values:

- **`PROJECT_CONNECTION_STRING`:** in the Foundry portal, select **Home**. Copy the **Project endpoint**.
- **`APPLICATIONINSIGHTS_CONNECTION_STRING`:** in the Azure portal (**https://portal.azure.com**), open **Resource groups → foundry-workshop**. Select your **Application Insights** resource, then copy the **Connection String** from the **Overview** page.

Then run this check, which creates a test agent, asks it a question and deletes it:

```powershell
python factory/smoke_test.py
```

**You're ready when** your agent replies in the portal and the script prints `Smoke test passed.`

## If something fails

| You see | Fix |
| --- | --- |
| Permission error when creating the project | Under **Advanced options**, select the **`foundry-workshop`** resource group. If it still fails, ask your administrator for **Contributor** on it |
| `PermissionDenied` when creating or deploying an agent | Ask your administrator for the **Foundry Project Manager** role. Wait 10 minutes, then sign in again |
| Quota error when deploying the model | Set a lower **Tokens per minute**, or deploy `gpt-5-mini` instead |
| `RequestDisallowedByPolicy` | Ask your administrator to exempt the `foundry-workshop` resource group from the policy |
| `KeyError: 'PROJECT_CONNECTION_STRING'` | Your `.env` file isn't in the `factory` folder |
| `DefaultAzureCredential failed to retrieve a token` | Run `az login --tenant <tenant-id>` |
| Portal shows hub or "classic" screens | Turn on **New Foundry** at the top of the portal |

## After the workshop

Administrators can delete everything with one command, and should also remove the subscription-level **Cognitive Services Usages Reader** assignment:

```powershell
az group delete --name foundry-workshop --yes --no-wait
```

**Useful links:** [Workshop repository](https://github.com/vrajakishore/foundry-agents-workshop) · [Foundry roles (RBAC)](https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry) · [Create a Foundry project](https://learn.microsoft.com/azure/foundry/how-to/create-projects)
