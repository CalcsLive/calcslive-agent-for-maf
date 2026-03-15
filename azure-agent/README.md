# Unified CalcsLive Agent App

This folder contains the unified Streamlit application and agent orchestration logic for the project.

## What This App Does

The unified app supports both:

- **cloud/web mode**: create and review CalcsLive calculations, then persist them as reusable articles
- **local + Excel mode**: the same app detects the Excel bridge and enables bi-directional Excel workflows

Core workflow:

1. User describes a calculation in natural language.
2. Azure AI moderates script generation.
3. CalcsLive runs stateless script review.
4. User refines the result through **AI-Human Co-Authoring**.
5. Approved script is persisted as a reusable CalcsLive article.
6. When Excel is available, the article can be sent into Excel or read back from Excel-authored PQ tables.

## Main Files

- `app.py` — unified Streamlit app entrypoint
- `app_cloud.py` — compatibility wrapper for deployments that still reference the old cloud entrypoint
- `agent_core.py` — Azure AI orchestration and tool registration
- `calcslive_tools.py` — shared CalcsLive API functions
- `app_shared.py` — shared UI helpers for review/presentation
- `agent.py` — CLI-oriented agent entrypoint and legacy/testing support

## Local Run

### Prerequisites

- Python 3.9+
- Azure AI inference credentials
- CalcsLive API key
- Optional: local Excel bridge + open Excel workbook for Excel workflows

### Environment

Create `azure-agent/.env`:

```env
AZURE_AI_INFERENCE_ENDPOINT=https://your-endpoint.openai.azure.com
AZURE_AI_INFERENCE_KEY=your_key_here
AZURE_AI_INFERENCE_MODEL=gpt-4.1-mini
CALCSLIVE_API_KEY=your_calcslive_token
```

Optional local API testing:

```env
CALCSLIVE_API_URL=http://localhost:3000/api/v1
```

### Start the app directly

```bash
python -m streamlit run app.py
```

### Start through the developer helper

```powershell
.\dev.ps1 cloud
```

With Excel bridge:

```powershell
.\dev.ps1 local
```

With local CalcsLive API override:

```powershell
.\dev.ps1 local -UseLocalCalcsLiveApi
```

## Unified Behavior

### If Excel bridge is available

The app will show:

- `Bridge to/from Excel`
- Excel auto-update options
- Excel review/load actions

### If Excel bridge is not available

The app will still support:

- natural-language calculation creation
- stateless review
- article creation
- web-mode links (`edit`, `calculate`, `table`, `view`)

## Deployment

The cloud deployment now runs the unified app directly.

- Docker entrypoint: `app.py`
- Azure Container Apps deploy script: `deploy/deploy-cloud-beta-aca.ps1`
- Rollout guide: `docs/cloud-beta-rollout.md`
