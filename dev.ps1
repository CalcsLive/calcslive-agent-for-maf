param(
    [Parameter(Position = 0, Mandatory = $false)]
    [string]$Command = "help",

    [Parameter(Mandatory = $false)]
    [string]$ConfigPath = ".\deploy\config.aca.dev.json",

    [Parameter(Mandatory = $false)]
    [switch]$SkipCodeDeploy
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
    Write-Host "Usage: .\dev.ps1 <command> [options]`n"
    Write-Host "Commands:"
    Write-Host "  local               Start Excel bridge + local Streamlit app (azure-agent\app.py)."
    Write-Host "  cloud               Start cloud-only (no Excel) Streamlit app locally (azure-agent\app_cloud.py)."
    Write-Host "  bridge-start        Start Excel Bridge only."
    Write-Host "  bridge-stop         Stop Excel Bridge process(es)."
    Write-Host "  status              Show local dev status (python + bridge health)."
    Write-Host "  deploy              Deploy to Azure Container Apps (config.aca.dev.json by default)."
    Write-Host "  deploy-appservice   Deploy to Azure App Service (legacy path)."
    Write-Host "  help                Show this help menu.`n"
    Write-Host "Options:"
    Write-Host "  -ConfigPath <path>  Deploy config path (used by 'deploy')."
    Write-Host "  -SkipCodeDeploy     Skip code package deploy for App Service command only." 
    Write-Host "  (Deploy scripts auto-load .env or azure-agent/.env and prompt for missing CALCSLIVE_API_KEY.)"
    Write-Host "`nExamples:"
    Write-Host "  .\dev.ps1 local"
    Write-Host "  .\dev.ps1 deploy -ConfigPath .\deploy\config.aca.dev.json"
    Write-Host "  .\dev.ps1 deploy-appservice -SkipCodeDeploy"
}

switch ($Command.ToLower()) {
    "local" {
        Start-Excel-Bridge
        Start-Streamlit -AppPath (Join-Path $scriptRoot "azure-agent\app.py")
    }
    "cloud" {
        Start-Streamlit -AppPath (Join-Path $scriptRoot "azure-agent\app_cloud.py")
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
    "help" {
        Show-Help
    }
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Show-Help
        exit 1
    }
}
