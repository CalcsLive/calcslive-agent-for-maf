# Cloud Beta Rollout (Minimum Friction)

This guide helps you deploy the cloud-hosted parts first so testers can try article creation without local Excel setup.

## 1) What runs locally vs in Azure

- Local (your machine):
  - Source code edits in VS Code
  - Azure CLI + PowerShell script execution
  - Secret environment variables used by deploy script
- Azure cloud:
  - App Service plan + Web App
  - Streamlit cloud UI (`app_cloud.py`)
  - Runtime environment variables (App Settings)
- Not included in this cloud beta:
  - Excel bridge (`excel-bridge`) and COM watcher
  - Local workbook reactive loop

## 2) Files added for deployment

- `azure-agent/app_cloud.py`
  - Cloud-only Streamlit UI for creating CalcsLive articles from PQ JSON.
- `deploy/config.dev.json`
  - Non-secret deployment configuration (resource names, region, startup command).
- `deploy/deploy-cloud-beta.ps1`
  - Repeatable script that provisions Azure resources, sets app settings, packages code, and deploys.

## 3) One-time prerequisites

1. Install Azure CLI and sign in:

```powershell
az login
```

2. Confirm the target subscription exists for your account:

```powershell
az account list --output table
```

3. Edit `deploy/config.dev.json`:
   - Set `appName` to a globally unique name (e.g., `calcslive-beta-yourname-01`).
   - Keep `projectPath` as `azure-agent`.

## 4) Set local secrets for deploy

Set required secret in your current PowerShell session:

```powershell
$env:CALCSLIVE_API_KEY = "<your-calcslive-api-key>"
$env:CALCSLIVE_API_KEY = "mcp_4f76b38c1f4e7a8518f0de964dd9f5e4847898ba19be392ddfd4fb68bf7b702a"
```

Optional (only if you want NL/LLM features in cloud app later):

```powershell
$env:AZURE_AI_INFERENCE_ENDPOINT = "<your-endpoint>"
$env:AZURE_AI_INFERENCE_KEY = "<your-key>"
$env:AZURE_AI_INFERENCE_MODEL = "gpt-4.1-mini"
```

## 5) Run deployment script

From repo root:

```powershell
pwsh .\deploy\deploy-cloud-beta.ps1
```

What this script does:

1. Sets Azure subscription from config.
2. Creates resource group if missing.
3. Creates App Service plan if missing.
4. Creates Web App if missing.
5. Applies startup command for Streamlit.
6. Writes app settings into Azure (including secrets from your local env).
7. Packages `azure-agent` code, excluding `.env`, `.pyc`, caches.
8. Zip deploys package to Web App.
9. Restarts app and prints final URL.

## 6) Verify deployment

Open the URL printed by script, or check in portal:

```text
https://<appName>.azurewebsites.net 
// eg: 
https://calcslive-beta-26009-01.azurewebsites.net
```

In app:

1. Keep default PQ JSON.
2. Click **Create CalcsLive Article**.
3. Confirm returned article URL and ID.

## 7) Re-deploy after changes

You only need:

```powershell
pwsh .\deploy\deploy-cloud-beta.ps1
```

No need to retype resource create commands.

## 8) Useful operations

Tail logs:

```powershell
az webapp log config --name <appName> --resource-group <rg> --application-logging filesystem --level information
az webapp log tail --name <appName> --resource-group <rg>
```

Update settings only (no code deploy):

```powershell
pwsh .\deploy\deploy-cloud-beta.ps1 -SkipCodeDeploy
```

## 9) Beta rollout recommendation

1. Canary with 2-3 trusted users.
2. Private beta with 10-20 users.
3. Collect:
   - article create success rate
   - median + p95 latency
   - top failure reasons
4. Keep Excel workflow in separate "local advanced mode" during hackathon.

## 10) Troubleshooting (known)

### A) `Operation cannot be completed without additional quota` (Basic VMs)

Cause:
- App Service Linux `B1` needs Basic compute quota in that region.
- Some subscriptions/free tiers have `Current Limit (Basic VMs): 0`.

What to do:
1. Request quota increase for Basic/App Service compute in your subscription + region.
2. Or use another subscription/region with available quota.
3. Or switch to a different Azure hosting model (for example Azure Container Apps consumption).

Important:
- This error is **hosting compute quota**, not LLM token quota.

### B) `'3.11' is not recognized as a command`

Cause:
- PowerShell can mis-handle `PYTHON|3.11` when not quoted correctly.

Status:
- `deploy/deploy-cloud-beta.ps1` now quotes runtime arguments to avoid this.

### C) App/Web resource not found after a failed plan create

Cause:
- Earlier script version continued after CLI failures.

Status:
- `deploy/deploy-cloud-beta.ps1` now fails fast on Azure CLI errors.

### D) Security note for logs

If you accidentally pasted API keys in logs/issues:
1. Rotate the exposed key immediately in CalcsLive.
2. Update local env with the new key.
3. Redeploy app settings with `-SkipCodeDeploy`.
