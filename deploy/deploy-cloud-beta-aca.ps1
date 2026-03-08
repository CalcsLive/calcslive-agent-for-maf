param(
    [string]$ConfigPath = ".\deploy\config.aca.dev.json"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Az {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,
        [switch]$AllowFailure
    )

    Write-Host "> $Command"
    $output = Invoke-Expression $Command 2>&1
    $exitCode = $LASTEXITCODE

    if (-not $AllowFailure -and $exitCode -ne 0) {
        $message = ($output | Out-String).Trim()
        throw "Azure CLI command failed (exit=$exitCode): $Command`n$message"
    }

    return $output
}

function Test-AzLogin {
    try {
        Invoke-Az -Command "az account show -o none"
        return $true
    }
    catch {
        return $false
    }
}

function Ensure-EnvVar {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )
    $value = [Environment]::GetEnvironmentVariable($Name)
    if ([string]::IsNullOrWhiteSpace($value)) {
        throw "Missing required environment variable: $Name"
    }
    return $value
}

function Ensure-AzProvider {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Namespace
    )

    Write-Host "Ensuring provider registration: $Namespace"
    Invoke-Az -Command "az provider register --namespace '$Namespace' -o none"

    for ($i = 0; $i -lt 20; $i++) {
        $state = Invoke-Az -Command "az provider show --namespace '$Namespace' --query registrationState -o tsv"
        if (($state | Out-String).Trim() -eq "Registered") {
            return
        }
        Start-Sleep -Seconds 3
    }

    throw "Provider '$Namespace' is not in Registered state yet. Try again in a minute."
}

Write-Host "Loading ACA config from $ConfigPath..."
$config = Get-Content $ConfigPath -Raw | ConvertFrom-Json

if (-not (Test-AzLogin)) {
    throw "Azure CLI is not logged in. Run: az login"
}

Write-Host "Setting subscription $($config.subscriptionId)..."
Invoke-Az -Command "az account set --subscription '$($config.subscriptionId)'"

Write-Host "Ensuring required Azure CLI extension..."
Invoke-Az -Command "az config set extension.use_dynamic_install=yes_without_prompt -o none"
Invoke-Az -Command "az extension add --name containerapp --upgrade -o none"

Ensure-AzProvider -Namespace "Microsoft.App"
Ensure-AzProvider -Namespace "Microsoft.OperationalInsights"
Ensure-AzProvider -Namespace "Microsoft.ContainerRegistry"
Ensure-AzProvider -Namespace "Microsoft.Insights"

Write-Host "Ensuring resource group $($config.resourceGroup)..."
Invoke-Az -Command "az group create --name '$($config.resourceGroup)' --location '$($config.location)' -o none"

Write-Host "Ensuring Container Apps environment $($config.environmentName)..."
$envExists = Invoke-Az -Command "az containerapp env show --name '$($config.environmentName)' --resource-group '$($config.resourceGroup)' -o json" -AllowFailure
if (-not $envExists) {
    Invoke-Az -Command "az containerapp env create --name '$($config.environmentName)' --resource-group '$($config.resourceGroup)' --location '$($config.location)' -o none"
}

$calcsliveApiKey = Ensure-EnvVar -Name "CALCSLIVE_API_KEY"

$envVars = @(
    "CALCSLIVE_API_URL=$($config.calcsliveApiUrl)",
    "CALCSLIVE_API_KEY=$calcsliveApiKey",
    "CALCSLIVE_DEBUG=0"
)

$inferenceEndpoint = [Environment]::GetEnvironmentVariable("AZURE_AI_INFERENCE_ENDPOINT")
$inferenceKey = [Environment]::GetEnvironmentVariable("AZURE_AI_INFERENCE_KEY")
$inferenceModel = [Environment]::GetEnvironmentVariable("AZURE_AI_INFERENCE_MODEL")
if (-not [string]::IsNullOrWhiteSpace($inferenceEndpoint) -and -not [string]::IsNullOrWhiteSpace($inferenceKey)) {
    $envVars += "AZURE_AI_INFERENCE_ENDPOINT=$inferenceEndpoint"
    $envVars += "AZURE_AI_INFERENCE_KEY=$inferenceKey"
    if (-not [string]::IsNullOrWhiteSpace($inferenceModel)) {
        $envVars += "AZURE_AI_INFERENCE_MODEL=$inferenceModel"
    }
}

$projectPath = (Resolve-Path $config.projectPath).Path
$envArgs = ($envVars | ForEach-Object { '"' + $_ + '"' }) -join " "

Write-Host "Deploying Container App from source path $projectPath ..."
Invoke-Az -Command @"
az containerapp up \
  --name '$($config.appName)' \
  --resource-group '$($config.resourceGroup)' \
  --location '$($config.location)' \
  --environment '$($config.environmentName)' \
  --source '$projectPath' \
  --ingress '$($config.ingress)' \
  --target-port $($config.targetPort) \
  --min-replicas $($config.minReplicas) \
  --max-replicas $($config.maxReplicas) \
  --cpu $($config.cpu) \
  --memory '$($config.memory)' \
  --env-vars $envArgs \
  -o none
"@

$fqdn = Invoke-Az -Command "az containerapp show --name '$($config.appName)' --resource-group '$($config.resourceGroup)' --query properties.configuration.ingress.fqdn -o tsv"
Write-Host "Done. App URL: https://$fqdn"
