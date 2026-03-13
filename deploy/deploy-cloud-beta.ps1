param(
    [string]$ConfigPath = ".\deploy\config.dev.json",
    [switch]$SkipCodeDeploy
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $false

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Invoke-Az {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,
        [switch]$AllowFailure
    )

    Write-Host "> $Command"
    $stdoutFile = [System.IO.Path]::GetTempFileName()
    $stderrFile = [System.IO.Path]::GetTempFileName()

    try {
        Invoke-Expression "$Command 1> \"$stdoutFile\" 2> \"$stderrFile\"" | Out-Null
        $exitCode = $LASTEXITCODE

        $stdout = if (Test-Path $stdoutFile) { Get-Content $stdoutFile -Raw } else { "" }
        $stderr = if (Test-Path $stderrFile) { Get-Content $stderrFile -Raw } else { "" }
        $output = (($stdout + [Environment]::NewLine + $stderr).Trim())

        if (-not $AllowFailure -and $exitCode -ne 0) {
            throw "Azure CLI command failed (exit=$exitCode): $Command`n$output"
        }

        return $output
    }
    finally {
        if (Test-Path $stdoutFile) { Remove-Item $stdoutFile -Force }
        if (Test-Path $stderrFile) { Remove-Item $stderrFile -Force }
    }
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

function New-DeployZip {
    param(
        [Parameter(Mandatory = $true)]
        [string]$SourcePath,
        [Parameter(Mandatory = $true)]
        [string]$ZipPath
    )

    $sourceRoot = (Resolve-Path $SourcePath).Path
    $stageRoot = Join-Path $env:TEMP ("calcslive-stage-" + [guid]::NewGuid().ToString("N"))

    New-Item -ItemType Directory -Path $stageRoot | Out-Null

    $excludedDirNames = @(".venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".git", ".idea", ".vscode")
    $excludedFileNames = @(".env", ".env.local", ".env.production")
    $excludedExtensions = @(".pyc")

    $files = Get-ChildItem -Path $sourceRoot -Recurse -File
    foreach ($file in $files) {
        $relative = $file.FullName.Substring($sourceRoot.Length).TrimStart([char[]]@('\', '/'))

        if ($excludedFileNames -contains $file.Name) {
            continue
        }
        if ($excludedExtensions -contains $file.Extension) {
            continue
        }

        $segments = $relative -split "[\\/]"
        $skip = $false
        foreach ($segment in $segments) {
            if ($excludedDirNames -contains $segment) {
                $skip = $true
                break
            }
        }
        if ($skip) {
            continue
        }

        $target = Join-Path $stageRoot $relative
        $targetDir = Split-Path $target -Parent
        if (-not (Test-Path $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        }
        Copy-Item -Path $file.FullName -Destination $target -Force
    }

    if (Test-Path $ZipPath) {
        Remove-Item $ZipPath -Force
    }
    Compress-Archive -Path (Join-Path $stageRoot "*") -DestinationPath $ZipPath -Force
    Remove-Item -Path $stageRoot -Recurse -Force
}

Write-Host "Loading config from $ConfigPath..."
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

Write-Host "Ensuring resource group $($config.resourceGroup)..."
Invoke-Az -Command "az group create --name '$($config.resourceGroup)' --location '$($config.location)' -o none"

Write-Host "Ensuring App Service plan $($config.planName)..."
$planExists = Invoke-Az -Command "az appservice plan show --name '$($config.planName)' --resource-group '$($config.resourceGroup)' -o json" -AllowFailure
if (-not $planExists) {
    Invoke-Az -Command "az appservice plan create --name '$($config.planName)' --resource-group '$($config.resourceGroup)' --is-linux --sku '$($config.sku)' -o none"
}

Write-Host "Ensuring web app $($config.appName)..."
$webExists = Invoke-Az -Command "az webapp show --name '$($config.appName)' --resource-group '$($config.resourceGroup)' -o json" -AllowFailure
if (-not $webExists) {
    Invoke-Az -Command "az webapp create --name '$($config.appName)' --resource-group '$($config.resourceGroup)' --plan '$($config.planName)' --runtime '$($config.runtime)' -o none"
}

Write-Host "Configuring startup command..."
Invoke-Az -Command "az webapp config set --name '$($config.appName)' --resource-group '$($config.resourceGroup)' --startup-file \"$($config.startupCommand)\" -o none"

$calcsliveApiKey = Ensure-EnvVar -Name "CALCSLIVE_API_KEY"
$appSettings = @(
    "SCM_DO_BUILD_DURING_DEPLOYMENT=true",
    "ENABLE_ORYX_BUILD=true",
    "CALCSLIVE_API_URL=$($config.calcsliveApiUrl)",
    "CALCSLIVE_API_KEY=$calcsliveApiKey",
    "CALCSLIVE_DEBUG=0"
)

$inferenceEndpoint = [Environment]::GetEnvironmentVariable("AZURE_AI_INFERENCE_ENDPOINT")
$inferenceKey = [Environment]::GetEnvironmentVariable("AZURE_AI_INFERENCE_KEY")
$inferenceModel = [Environment]::GetEnvironmentVariable("AZURE_AI_INFERENCE_MODEL")
if (-not [string]::IsNullOrWhiteSpace($inferenceEndpoint) -and -not [string]::IsNullOrWhiteSpace($inferenceKey)) {
    $appSettings += "AZURE_AI_INFERENCE_ENDPOINT=$inferenceEndpoint"
    $appSettings += "AZURE_AI_INFERENCE_KEY=$inferenceKey"
    if (-not [string]::IsNullOrWhiteSpace($inferenceModel)) {
        $appSettings += "AZURE_AI_INFERENCE_MODEL=$inferenceModel"
    }
}

Write-Host "Applying app settings..."
$settingsArgs = ($appSettings | ForEach-Object { '"' + $_ + '"' }) -join " "
Invoke-Az -Command "az webapp config appsettings set --name '$($config.appName)' --resource-group '$($config.resourceGroup)' --settings $settingsArgs -o none"

if (-not $SkipCodeDeploy) {
    $projectPath = (Resolve-Path $config.projectPath).Path
    $zipPath = Join-Path $env:TEMP ($config.appName + "-deploy.zip")

    Write-Host "Packaging source from $projectPath ..."
    New-DeployZip -SourcePath $projectPath -ZipPath $zipPath

    Write-Host "Deploying package to Azure Web App..."
    Invoke-Az -Command "az webapp deploy --resource-group '$($config.resourceGroup)' --name '$($config.appName)' --src-path '$zipPath' --type zip --clean true -o none"

    if (Test-Path $zipPath) {
        Remove-Item $zipPath -Force
    }
}

Write-Host "Restarting web app..."
Invoke-Az -Command "az webapp restart --name '$($config.appName)' --resource-group '$($config.resourceGroup)' -o none"

$hostName = Invoke-Az -Command "az webapp show --name '$($config.appName)' --resource-group '$($config.resourceGroup)' --query defaultHostName -o tsv"
Write-Host "Done. App URL: https://$hostName"
