param(
    [Parameter(Position = 0, Mandatory = $false)]
    [string]$Command = "help",

    [Parameter(Mandatory = $false)]
    [string]$ConfigPath = ".\deploy\config.aca.dev.json",

    [Parameter(Mandatory = $false)]
    [switch]$SkipCodeDeploy,

    [Parameter(Mandatory = $false)]
    [switch]$UseLocalCalcsLiveApi
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptRoot = $PSScriptRoot

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return "py"
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return "python"
    }
    throw "Python launcher not found. Install Python and ensure 'py' or 'python' is on PATH."
}

function Test-BridgeHealth {
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8001/excel/health" -Method Get -TimeoutSec 2
        return [bool]($response.success)
    }
    catch {
        return $false
    }
}

function Wait-BridgeReady {
    param(
        [int]$TimeoutSeconds = 15
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-BridgeHealth) {
            return $true
        }
        Start-Sleep -Seconds 1
    }
    return $false
}

function Start-Excel-Bridge {
    $python = Get-PythonCommand
    $bridgeScript = Join-Path $scriptRoot "excel-bridge\main.py"

    if (-not (Test-Path $bridgeScript)) {
        throw "Bridge script not found: $bridgeScript"
    }

    if (Test-BridgeHealth) {
        Write-Host "Excel Bridge already running at http://127.0.0.1:8001" -ForegroundColor Yellow
        return
    }

    Write-Host "Starting Excel Bridge API in background window..." -ForegroundColor Green
    Start-Process -FilePath $python -ArgumentList @($bridgeScript) -WorkingDirectory $scriptRoot -WindowStyle Normal | Out-Null

    if (Wait-BridgeReady -TimeoutSeconds 20) {
        Write-Host "Excel Bridge is ready." -ForegroundColor Green
    }
    else {
        Write-Host "Excel Bridge started, but health endpoint is not ready yet." -ForegroundColor Yellow
    }
}

function Stop-Bridge {
    $processes = Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -and $_.CommandLine -match "excel-bridge[\\/]main\.py"
    }

    if (-not $processes) {
        Write-Host "No bridge process found." -ForegroundColor Yellow
        return
    }

    foreach ($proc in $processes) {
        Write-Host "Stopping bridge process PID $($proc.ProcessId)..." -ForegroundColor Green
        Stop-Process -Id $proc.ProcessId -Force
    }
}

function Start-Streamlit {
    param(
        [Parameter(Mandatory = $true)]
        [string]$AppPath
    )

    $python = Get-PythonCommand
    if (-not (Test-Path $AppPath)) {
        throw "Streamlit app not found: $AppPath"
    }

    if ($UseLocalCalcsLiveApi) {
        $localApiUrl = "http://localhost:3000/api/v1"
        [Environment]::SetEnvironmentVariable("CALCSLIVE_API_URL", $localApiUrl, "Process")
        Write-Host "Using local CalcsLive API: $localApiUrl" -ForegroundColor Yellow
    }

    Set-Location $scriptRoot
    & $python -m streamlit run $AppPath
}

function Invoke-DeployAca {
    $deployScript = Join-Path $scriptRoot "deploy\deploy-cloud-beta-aca.ps1"
    if (-not (Test-Path $deployScript)) {
        throw "Deploy script not found: $deployScript"
    }

    Set-Location $scriptRoot
    & $deployScript -ConfigPath $ConfigPath
}

function Import-DotEnvForLogin {
    $envPaths = @(
        (Join-Path $scriptRoot ".env"),
        (Join-Path $scriptRoot "azure-agent\.env")
    )

    foreach ($path in $envPaths) {
        if (-not (Test-Path $path)) { continue }

        Write-Host "Loading env from $path" -ForegroundColor Gray
        $lines = Get-Content $path
        foreach ($line in $lines) {
            $trimmed = $line.Trim()
            if ([string]::IsNullOrWhiteSpace($trimmed) -or $trimmed.StartsWith("#")) { continue }
            if ($trimmed.StartsWith("export ")) { $trimmed = $trimmed.Substring(7).Trim() }

            $match = [regex]::Match($trimmed, '^(?<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?<value>.*)$')
            if (-not $match.Success) { continue }

            $key = $match.Groups["key"].Value
            $value = $match.Groups["value"].Value.Trim()
            if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
                if ($value.Length -ge 2) { $value = $value.Substring(1, $value.Length - 2) }
            }

            if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($key, "Process"))) {
                [Environment]::SetEnvironmentVariable($key, $value, "Process")
            }
        }
    }
}

function Invoke-AzLogin {
    Import-DotEnvForLogin

    $appId = [Environment]::GetEnvironmentVariable("AZURE_SP_APP_ID", "Process")
    $password = [Environment]::GetEnvironmentVariable("AZURE_SP_PASSWORD", "Process")
    $tenant = [Environment]::GetEnvironmentVariable("AZURE_SP_TENANT", "Process")

    if ([string]::IsNullOrWhiteSpace($appId) -or [string]::IsNullOrWhiteSpace($password) -or [string]::IsNullOrWhiteSpace($tenant)) {
        Write-Host "Service principal credentials not found in environment." -ForegroundColor Yellow
        Write-Host "Add these to .env or azure-agent/.env:" -ForegroundColor Yellow
        Write-Host "  AZURE_SP_APP_ID=<appId>"
        Write-Host "  AZURE_SP_PASSWORD=<password>"
        Write-Host "  AZURE_SP_TENANT=<tenantId>"
        Write-Host ""
        Write-Host "To create a service principal, run:" -ForegroundColor Cyan
        Write-Host "  az ad sp create-for-rbac --name `"calcslive-deploy-sp`" --role Contributor --scopes /subscriptions/<subscriptionId>"
        throw "Missing service principal credentials"
    }

    Write-Host "Logging in with service principal..." -ForegroundColor Green
    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $output = az login --service-principal -u $appId -p $password --tenant $tenant -o table 2>&1
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $prevEAP

    if ($exitCode -ne 0) {
        throw "az login failed: $output"
    }

    Write-Host $output
    Write-Host "Logged in successfully." -ForegroundColor Green
}

function Invoke-DeployAppService {
    $deployScript = Join-Path $scriptRoot "deploy\deploy-cloud-beta.ps1"
    if (-not (Test-Path $deployScript)) {
        throw "Deploy script not found: $deployScript"
    }

    Set-Location $scriptRoot
    if ($SkipCodeDeploy) {
        & $deployScript -ConfigPath ".\deploy\config.dev.json" -SkipCodeDeploy
    }
    else {
        & $deployScript -ConfigPath ".\deploy\config.dev.json"
    }
}

function Show-Status {
    Write-Host "CalcsLive Agent Dev Status" -ForegroundColor Cyan
    Write-Host "- Repo Root: $scriptRoot"
    Write-Host "- Python Command: $(Get-PythonCommand)"
    Write-Host "- Excel Bridge Health: $(if (Test-BridgeHealth) { 'UP' } else { 'DOWN' })"
}

function Show-Help {
    Write-Host "CalcsLive Agent - Developer CLI" -ForegroundColor Cyan
    Write-Host "Usage: .\dev.ps1 COMMAND [options]`n"
    Write-Host "Commands:"
    Write-Host "  local               Start Excel bridge + unified Streamlit app (azure-agent\app.py)."
    Write-Host "  cloud               Start unified Streamlit app without auto-starting Excel bridge."
    Write-Host "  bridge-start        Start Excel Bridge only."
    Write-Host "  bridge-stop         Stop Excel Bridge process(es)."
    Write-Host "  status              Show local dev status (python + bridge health)."
    Write-Host "  deploy              Deploy to Azure Container Apps (config.aca.dev.json by default)."
    Write-Host "  deploy-appservice   Deploy to Azure App Service (legacy path)."
    Write-Host "  az-login            Login to Azure with service principal (reads from .env)."
    Write-Host "  help                Show this help menu.`n"
    Write-Host "Options:"
    Write-Host "  -ConfigPath PATH  Deploy config path (used by 'deploy')."
    Write-Host "  -SkipCodeDeploy     Skip code package deploy for App Service command only." 
    Write-Host "  -UseLocalCalcsLiveApi  Force Streamlit app to use http://localhost:3000/api/v1 for local API testing."
    Write-Host "  (Deploy scripts auto-load .env or azure-agent/.env and prompt for missing CALCSLIVE_API_KEY.)"
    Write-Host "`nExamples:"
    Write-Host "  .\dev.ps1 local"
    Write-Host "  .\dev.ps1 cloud -UseLocalCalcsLiveApi"
    Write-Host "  .\dev.ps1 az-login                                         # Login with SP from .env"
    Write-Host "  .\dev.ps1 deploy -ConfigPath .\deploy\config.aca.dev.json"
    Write-Host "  .\dev.ps1 deploy-appservice -SkipCodeDeploy"
}

switch ($Command.ToLower()) {
    "local" {
        Start-Excel-Bridge
        Start-Streamlit -AppPath (Join-Path $scriptRoot "azure-agent\app.py")
    }
    "cloud" {
        Start-Streamlit -AppPath (Join-Path $scriptRoot "azure-agent\app.py")
    }
    "bridge-start" {
        Start-Excel-Bridge
    }
    "bridge-stop" {
        Stop-Bridge
    }
    "status" {
        Show-Status
    }
    "deploy" {
        Invoke-DeployAca
    }
    "deploy-appservice" {
        Invoke-DeployAppService
    }
    "az-login" {
        Invoke-AzLogin
    }
    "help" {
        Show-Help
    }
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Show-Help
        exit 1
    }
}
