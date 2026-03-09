param(
    [Parameter(Position=0, Mandatory=$false)]
    [string]$Command = "help"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptRoot = $PSScriptRoot

function Show-Help {
    Write-Host "CalcsLive Agent - Developer CLI" -ForegroundColor Cyan
    Write-Host "Usage: .\dev.ps1 <command>`n"
    Write-Host "Available Commands:"
    Write-Host "  local       : Starts both the Excel Bridge API backend and local Streamlit app."
    Write-Host "  cloud-local : Starts the cloud-version of the Streamlit app locally (app_cloud.py)."
    Write-Host "  deploy      : Deploys the containerized app to Azure Container Apps and prints the URL."
    Write-Host "  help        : Shows this help menu."
}

switch ($Command.ToLower()) {
    "local" {
        Write-Host "Starting Excel Bridge API in background window..." -ForegroundColor Green
        Start-Process -FilePath "py" -ArgumentList "excel-bridge\main.py" -WorkingDirectory $scriptRoot -WindowStyle Normal

        Write-Host "Starting Local Streamlit App..." -ForegroundColor Green
        Set-Location $scriptRoot
        py -m streamlit run .\azure-agent\app.py
    }
    "cloud-local" {
        Write-Host "Starting Cloud-Version Streamlit App Locally..." -ForegroundColor Green
        Set-Location $scriptRoot
        py -m streamlit run .\azure-agent\app_cloud.py
    }
    "deploy" {
        Write-Host "Triggering Azure Container Apps Deployment..." -ForegroundColor Green
        Set-Location $scriptRoot
        & .\deploy\deploy-cloud-beta-aca.ps1
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
