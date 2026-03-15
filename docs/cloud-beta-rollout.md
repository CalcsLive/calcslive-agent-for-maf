# Unified App Deployment Guide

This guide covers the current deployment and run paths for the **unified** CalcsLive Agent app.

## Current Architecture

There is now one main Streamlit app entrypoint:

- `azure-agent/app.py`

Behavior depends on whether the Excel bridge is reachable:

- **Cloud/web mode**: calculation creation, review, and persistence only
- **Local + Excel mode**: same capabilities plus bi-directional Excel integration

`azure-agent/app_cloud.py` remains only as a thin compatibility wrapper for older deploy references.

## Option 1 - Cloud Deployment (Azure Container Apps)

Recommended cloud path:

```powershell
.\dev.ps1 deploy
```

This uses:

- `deploy/deploy-cloud-beta-aca.ps1`
- `deploy/config.aca.dev.json`
- `azure-agent/Dockerfile`

The container now launches the unified app directly:

- `streamlit run app.py`

### Secrets

Preferred hackathon path:

- put secrets in `azure-agent/.env`
- deploy script auto-loads them

Typical variables:

```env
AZURE_AI_INFERENCE_ENDPOINT=https://your-endpoint.openai.azure.com
AZURE_AI_INFERENCE_KEY=your_key_here
AZURE_AI_INFERENCE_MODEL=gpt-4.1-mini
CALCSLIVE_API_KEY=your_calcslive_token
```

### Notes

- Cloud deployment does **not** automatically connect to a private local Excel bridge
- The deployed app works as a cloud/web calculation creation and persistence interface

## Option 2 - Local Run with Excel Desktop

This is the full local demo path.

### Start local Excel bridge

```powershell
.\dev.ps1 bridge-start
```

or

```powershell
python excel-bridge/main.py
```

### Start unified app with Excel support

```powershell
.\dev.ps1 local
```

### Local CalcsLive API testing (optional)

```powershell
.\dev.ps1 local -UseLocalCalcsLiveApi
```

This points the app to:

```text
http://localhost:3000/api/v1
```

### What appears in the UI when Excel bridge is available

- `Bridge to/from Excel`
- Excel auto-update options
- send/retrieve Excel calculation actions

## Option 3 - Local Run without Excel

To run the unified app as a cloud-style local test without auto-starting the bridge:

```powershell
.\dev.ps1 cloud
```

This still launches `azure-agent/app.py`, but Excel-only UI remains hidden unless the bridge is reachable.

## Developer Commands

Useful commands:

```powershell
.\dev.ps1 help
.\dev.ps1 status
.\dev.ps1 local
.\dev.ps1 cloud
.\dev.ps1 bridge-start
.\dev.ps1 bridge-stop
.\dev.ps1 deploy
```

## Troubleshooting Notes

### Azure CLI warnings during deploy

Deployment scripts have been hardened to tolerate Azure CLI warning output while still failing on real nonzero exit codes.

### Container Apps extension behavior

The ACA deploy script now isolates the Azure CLI extension directory and handles preview-extension warnings more gracefully.

### Excel UI not appearing in the app

The unified app only shows Excel sections when the Excel bridge is reachable.

Check:

```powershell
.\dev.ps1 bridge-start
.\dev.ps1 status
```

### Browser cache / favicon mismatch

If the old title/icon persists after redeploy, use a private/incognito window or hard refresh.
