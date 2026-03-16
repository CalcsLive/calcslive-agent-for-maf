# Submission Evidence Tracker

Use this file as the single source of truth for final hackathon submission evidence.

## Project

- Name: CalcsLive Agent - Unit-aware Calculation Carrier for Excel in MAF
- Repo: `calcslive-agent-for-maf`
- Owner: e3d
- Entry points:
  - Local: `http://localhost:8501`
  - Azure: `https://ca-calcslive-beta-26009-01.greensea-202942dd.eastus.azurecontainerapps.io/`
  - CalcsLive embedded path: `https://www.calcslive.com/agent`

## Requirement Mapping

| Requirement | Status | Evidence | Notes |
|-------------|--------|----------|-------|
| Microsoft Foundry / Agent Framework / Azure MCP | ✅ | `azure-agent/agent_core.py`, `excel-mcp/manifest.json`, `docs/odr-validation-log-2026-02-27.md`, `deliverables/architecture.excalidraw` | MAF-aligned moderator workflow, Azure AI deployment, partial MCP proof |
| Azure deployment | ✅ | ACA deployment via `deploy/deploy-cloud-beta-aca.ps1`, hosted app at ACA URL and `calcslive.com/agent` | Add one screenshot if helpful |
| Public GitHub repo | ✅ | repo URL + commit history | Ensure public visibility before submit |
| Demo video (2 min) | ✅ | `https://www.youtube.com/watch?v=5zWMoftyhRE`, `deliverables/demo-outline.md` | Final recorded cut available |
| Architecture diagram | ✅ | `deliverables/architecture.excalidraw`, `deliverables/architecture.png` | Final diagram updated to reflect Azure AI + partial MCP proof |

## Core MVP Proofs

| Scenario | Status | Evidence Artifact |
|----------|--------|-------------------|
| Load article to Excel with metadata + table | ✅ | UI screenshot + terminal logs |
| Prefill outputs after load | ✅ | screenshot before/after load |
| Manual recalc updates outputs | ✅ | UI prompt + output screenshot |
| Reactive live recalc on Excel cell change | ✅ | watcher logs + output screenshot |
| ODR custom server registration | ✅ | `docs/odr-validation-log-2026-02-27.md` |
| ODR full invocation | ⛔ | blocked (`AccessStatus=DeniedBySystem`) | include as known platform constraint |

## Commands Executed (verifiable)

```bash
python excel-bridge/main.py
streamlit run azure-agent/app.py
python -m py_compile azure-agent/agent_core.py
python -m py_compile excel-bridge/main.py
python -m py_compile excel-bridge/live_watcher.py
odr --version
odr mcp list
```

## Screenshot / Clip Inventory

| ID | File | Description | Included in Video |
|----|------|-------------|-------------------|
| SS-01 | `deliverables/architecture.png` | Architecture overview | ☒ |
| SS-02 | `deliverables/workflows.png` | Supported workflows overview | ☒ |
| SS-03 | `deliverables/samples/CalcsLive Agent (Local UI with Excel).pdf` | Unified app local + Excel interaction sample | ☒ |
| SS-04 | `deliverables/CalcsLive Agent Slides.pdf` | Slides deck / supporting visuals | ☒ |
| SS-05 | `deliverables/samples/` | Sample created calculations and Excel template | ☒ |

## Reference Assets

- `deliverables/terminology.md` — glossary for Microsoft AI, CalcsLive, PQ, unit-awareness, AI-Human Co-Authoring, and system-architecture terminology
- `deliverables/CalcsLive Agent Slides.pdf` — supporting visual narrative deck
| SS-06 | `deliverables/calcslive-agent-entry-page-hosted.png` | Hosted app screenshot | ☒ |
| SS-07 | `deliverables/calcslive-agent-entry-page-embed.png` | Embedded app screenshot | ☒ | 

## Video Timestamp Plan

| Time | Segment | Proof |
|------|---------|-------|
| 00:00-00:15 | Problem framing | live unit-aware calculations + AI-Human Co-Authoring |
| 00:15-00:35 | Review and create | reviewed script -> created article |
| 00:35-00:55 | CalcsLive modes | reusable live article on the web |
| 00:55-01:20 | Send to Excel | metadata + PQ table creation |
| 01:20-01:45 | Reactive Excel update | edited input -> auto recalculation |
| 01:45-02:00 | Reverse flow / close | Excel-authored calc + system-level interoperability |
