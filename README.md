# CalcsLive Agent for Microsoft AI Dev Days Hackathon

**Azure-moderated human + AI workflow for creating reusable unit-aware calculations, with Excel as a flagship bi-directional integration.**

![Architecture Diagram](docs/architecture.png)

## What This Project Does

CalcsLive Agent helps users create **live, reusable, unit-aware calculations from natural language**.

The core workflow is **AI-Human Co-Authoring**:

1. A user describes a calculation in natural language.
2. Azure AI drafts a CalcsLive-compatible PQ script.
3. CalcsLive runs a stateless review of the script.
4. The human user refines the result with project context and domain knowledge.
5. The approved script is persisted as a reusable CalcsLive article.

That article then becomes a reusable asset that can be used through multiple CalcsLive modes:

- `edit`
- `calculate`
- `table`
- `view`

When Excel is available, the same calculation can also be sent into Excel, used interactively, and read back out again in the reverse direction.

## Why It Matters

This project is not just “AI generating a formula.”

It demonstrates:

- **AI-Human Co-Authoring** instead of AI slop
- **CalcsLive as reusable unit-aware infrastructure**
- **Azure AI as the moderator/orchestrator**
- **Excel as a connected local execution surface**

The result is a system-level workflow where unit-aware calculations can move between cloud/web and desktop/local contexts.

## Core Value Proposition

### Main superpower

Create a live unit-aware calculation in under a minute using natural language, human review, and deterministic CalcsLive execution.

### Excel value proposition

Revitalize and simplify calculations in Excel with **composable unit-aware calculations**.

- Existing and new spreadsheets can be enhanced with unit-aware live calculations.
- Excel cell references can connect CalcsLiverated PQ tables with the rest of the spreadsheet.
- Excel-authored calculation tables can be converted back into reusable CalcsLive content.

## Supported Workflows

### 1. Natural language -> review -> create live calculation

This is the main workflow and the strongest differentiator.

- user describes a calculation
- agent drafts a PQ script
- CalcsLive reviews it statelessly
- human refines title, description, units, and logic as needed
- approved script becomes a reusable live article

### 2. Create -> send to Excel -> reactive spreadsheet use

- reviewed article is sent into Excel through the bridge
- Excel gets metadata + PQ table structure
- user edits values/units directly in Excel
- CalcsLive-backed recalculation updates outputs reactively

### 3. Excel-authored table -> review -> create article

- user prepares a compatible PQ table in Excel
- bridge reads the table into the app
- app reviews it as a CalcsLive script
- user refines it and persists it as a reusable live article

See `deliverables/workflows.md` for the full workflow narrative.

## Architecture Summary

The project uses a unified Streamlit moderator app as the main entrypoint.

- **Azure AI** moderates the workflow
- **CalcsLive** provides deterministic unit-aware execution and article storage
- **Excel Bridge** provides local bi-directional spreadsheet integration when available
- **Excel Desktop** acts as a familiar downstream working surface
- **MCP work** provides proof of extensibility toward broader tool and agent interoperability

## Hackathon Alignment

### Core requirements

| Requirement | Status | Notes |
|---|---|---|
| AI Technology | ✅ | Azure AI-moderated agent workflow + MAF-aligned orchestration + MCP-oriented integration story |
| Azure Deployment | ✅ | Unified app deployed to Azure Container Apps |
| GitHub Development | ✅ | Public GitHub repo + VS Code-based development workflow |

### Best-fit categories

Primary:
- **Build AI Applications & Agents**

Strong secondary:
- **Best Multi-Agent System**
- **Best Azure Integration**

## Microsoft Technologies Used

- Azure Container Apps for deployment
- Azure AI / Microsoft AI platform-backed orchestration
- Microsoft Agent Framework-aligned moderator architecture
- Azure MCP / MCP-oriented extensibility direction
- GitHub + VS Code development workflow

## Running Locally

### Prerequisites

- Windows with Microsoft Excel installed
- Python 3.9+
- Azure AI inference endpoint + key
- CalcsLive API key

### Environment

Set env vars in `azure-agent/.env`:

```env
AZURE_AI_INFERENCE_ENDPOINT=https://your-endpoint.openai.azure.com
AZURE_AI_INFERENCE_KEY=your_key_here
CALCSLIVE_API_KEY=your_calcslive_token
```

### Start local Excel bridge

```bash
python excel-bridge/main.py
```

### Start unified app

```bash
python -m streamlit run azure-agent/app.py
```

Or use the developer helper:

```powershell
.\dev.ps1 local
```

For local CalcsLive API testing:

```powershell
.\dev.ps1 local -UseLocalCalcsLiveApi
```

## Cloud Deployment

The unified app is deployable to Azure Container Apps.

- Main app entrypoint: `azure-agent/app.py`
- ACA deploy script: `deploy/deploy-cloud-beta-aca.ps1`
- Dev helper: `.\dev.ps1 deploy`
- Rollout guide: `docs/cloud-beta-rollout.md`

## Repository Structure

- `azure-agent/` — unified app, orchestration logic, shared CalcsLive tools
- `excel-bridge/` — local Excel COM + REST bridge
- `excel-mcp/` — MCP wrapper / proof of extensibility
- `docs/` — architecture and supporting documentation
- `demo/` — screenshots and test artifacts
- `deliverables/` — final submission materials and working drafts

## Key Submission Assets

- Architecture narrative: `deliverables/architecture-content.md`
- Workflow narrative: `deliverables/workflows.md`
- Submission draft: `deliverables/submission-summary.md`
- Demo plan: `deliverables/demo-outline.md`
- Final checklist: `deliverables/final-checklist.md`

## Scope Notes

Current known limits:

- cloud deployment does not automatically connect to a private local Excel bridge
- full Excel MCP parity is not required for the working demo path
- broader plugin-style downstream integrations are future work
