param(
    [string]$ConfigPath = ".\deploy\config.aca.dev.json"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

Write-Host "Isolating Azure CLI Extension Directory..."
$env:AZURE_EXTENSION_DIR = Join-Path $PSScriptRoot ".azureext"
if (-not (Test-Path $env:AZURE_EXTENSION_DIR)) {
    New-Item -ItemType Directory -Path $env:AZURE_EXTENSION_DIR | Out-Null
}

function Invoke-Az {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,
        [switch]$AllowFailure,
        [switch]$IsSecret
    )

    if ($IsSecret) {
        Write-Host "> [Command masked to protect secrets]"
    } else {
        Write-Host "> $Command"
    }

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

    $value = [Environment]::GetEnvironmentVariable($Name, "Process")
    if ([string]::IsNullOrWhiteSpace($value)) {
        Write-Host "Missing required environment variable: $Name" -ForegroundColor Yellow
        Write-Host "Set it once in current shell, example:" -ForegroundColor Yellow
        Write-Host ('  $env:{0} = "<your-secret>"' -f $Name) -ForegroundColor Yellow
        $value = Read-Host "Enter value for $Name"
        if ([string]::IsNullOrWhiteSpace($value)) {
            throw "Missing required environment variable: $Name"
        }
        [Environment]::SetEnvironmentVariable($Name, $value, "Process")
    }
    return $value
}

function Import-DotEnv {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Paths
    )

    foreach ($path in $Paths) {
        if (-not (Test-Path $path)) {
            continue
        }

        Write-Host "Loading environment values from $path"
        $lines = Get-Content $path
        foreach ($line in $lines) {
            $trimmed = $line.Trim()
            if ([string]::IsNullOrWhiteSpace($trimmed)) {
                continue
            }
            if ($trimmed.StartsWith("#")) {
                continue
            }
            if ($trimmed.StartsWith("export ")) {
                $trimmed = $trimmed.Substring(7).Trim()
            }

            $match = [regex]::Match($trimmed, '^(?<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?<value>.*)$')
            if (-not $match.Success) {
                continue
            }

            $key = $match.Groups["key"].Value
            $value = $match.Groups["value"].Value.Trim()
            if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
                if ($value.Length -ge 2) {
                    $value = $value.Substring(1, $value.Length - 2)
                }
            }

            if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($key, "Process"))) {
                [Environment]::SetEnvironmentVariable($key, $value, "Process")
            }
        }
    }
}

function Ensure-AzProvider {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Namespace
    )

    Write-Host "Ensuring provider registration: $Namespace"

    $state = Invoke-Az -Command "az provider show --namespace '$Namespace' --query registrationState -o tsv" -AllowFailure
    if (($state | Out-String).Trim() -eq "Registered") {
        return
    }

    Invoke-Az -Command "az provider register --namespace '$Namespace' -o none"

    for ($i = 0; $i -lt 40; $i++) {
        $state = Invoke-Az -Command "az provider show --namespace '$Namespace' --query registrationState -o tsv" -AllowFailure
        if (($state | Out-String).Trim() -eq "Registered") {
            return
        }
        Start-Sleep -Seconds 3
    }

    throw "Provider '$Namespace' is not in Registered state yet. Try again in 2 minutes."
}

Write-Host "Loading ACA config from $ConfigPath..."
$config = Get-Content $ConfigPath -Raw | ConvertFrom-Json

Import-DotEnv -Paths @(
    (Join-Path $repoRoot ".env"),
    (Join-Path $repoRoot "azure-agent\.env")
)

if (-not (Test-AzLogin)) {
    throw "Azure CLI is not logged in. Run: az login"
}

Write-Host "Setting subscription $($config.subscriptionId)..."
Invoke-Az -Command "az account set --subscription '$($config.subscriptionId)'"

Write-Host "Ensuring required Azure CLI extension..."
Invoke-Az -Command "az config set extension.use_dynamic_install=yes_without_prompt -o none" -AllowFailure
Invoke-Az -Command "az extension add --name containerapp --upgrade -o none" -AllowFailure

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

Write-Host "Checking for existing Azure Container Registry..."
$acrName = "acrcalcslivebeta" + ($config.subscriptionId.Substring(0, 4))
$acrExists = Invoke-Az -Command "az acr show --name '$acrName' -o none" -AllowFailure
if (-not $acrExists) {
    Write-Host "Creating Azure Container Registry $acrName (Basic sku)..."
    Invoke-Az -Command "az acr create --name '$acrName' --resource-group '$($config.resourceGroup)' --sku Basic --admin-enabled true -o none"
}

Write-Host "Fetching Azure Container Registry $acrName credentials..."
$acrCredsJson = Invoke-Az -Command "az acr credential show --name '$acrName' -o json"
$acrCreds = $acrCredsJson | ConvertFrom-Json
$acrPassword = $acrCreds.passwords[0].value

$ts = (Get-Date).ToString('yyyyMMdd-HHmmss')
$imageTag = "$acrName.azurecr.io/$($config.appName):$ts"

Write-Host "Logging into Azure Container Registry $acrName with Docker..."
Write-Host "> docker login $acrName.azurecr.io -u $acrName -p [masked]"
$dockerLoginOutput = Invoke-Expression "docker login $acrName.azurecr.io -u $acrName -p $acrPassword" 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "Docker login failed: $dockerLoginOutput"
}

Write-Host "Building Docker image locally ($imageTag) from source path $projectPath ..."
Write-Host "> docker build --no-cache -t $imageTag '$projectPath'"
& docker build --no-cache -t $imageTag "$projectPath"
if ($LASTEXITCODE -ne 0) {
    throw "Docker build failed. Check the console output above for details."
}

Write-Host "Pushing Docker image to ACR ($imageTag) ..."
Write-Host "> docker push $imageTag"
& docker push $imageTag
if ($LASTEXITCODE -ne 0) {
    throw "Docker push failed. Check the console output above for details."
}

Write-Host "Deploying Container App from Image $imageTag ..."
Write-Host "> [Command masked to protect secrets]"

$azArgs = @(
    "containerapp", "up",
    "--name", $config.appName,
    "--resource-group", $config.resourceGroup,
    "--location", $config.location,
    "--environment", $config.environmentName,
    "--image", $imageTag,
    "--ingress", $config.ingress,
    "--target-port", [string]$config.targetPort
)

if ($envVars.Count -gt 0) {
    $azArgs += "--env-vars"
    $azArgs += $envVars
}

$output = & az $azArgs 2>&1
$exitCode = $LASTEXITCODE

if ($exitCode -ne 0) {
    $message = ""
    if ($output) { $message = ($output | Out-String).Trim() }
    throw "az containerapp up failed (exit=$exitCode):`n$message"
}

Write-Host "Updating Container App scaling and resources..."
$azUpdateArgs = @(
    "containerapp", "update",
    "--name", $config.appName,
    "--resource-group", $config.resourceGroup,
    "--min-replicas", [string]$config.minReplicas,
    "--max-replicas", [string]$config.maxReplicas,
    "--cpu", [convert]::ToString($config.cpu, [Globalization.CultureInfo]::InvariantCulture),
    "--memory", $config.memory,
    "-o", "none"
)

$outputUpdate = & az $azUpdateArgs 2>&1
$exitCodeUpdate = $LASTEXITCODE

if ($exitCodeUpdate -ne 0) {
    $updateMessage = ""
    if ($outputUpdate) { $updateMessage = ($outputUpdate | Out-String).Trim() }
    throw "az containerapp update failed (exit=$exitCodeUpdate):`n$updateMessage"
}

$fqdn = Invoke-Az -Command "az containerapp show --name '$($config.appName)' --resource-group '$($config.resourceGroup)' --query properties.configuration.ingress.fqdn -o tsv"
Write-Host "Done. App URL: https://$fqdn"
