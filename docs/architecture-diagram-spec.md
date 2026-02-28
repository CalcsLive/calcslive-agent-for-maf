# Architecture Diagram Spec

## Goal

Create one clear architecture image for submission that shows CalcsLive as a reusable unit-aware capability orchestrated by MAF across local desktop tools.

## Canvas

- Orientation: landscape (16:9)
- Suggested size: 1920x1080
- Flow direction: left to right
- Style: clean technical diagram, flat colors, minimal text

## Main Sections (swimlanes)

Use 3 horizontal swimlanes with labels:

1. **User + Orchestration (Cloud)**
2. **MCP Tool Layer**
3. **Execution Targets (Local + Backend)**

## Boxes and Exact Labels

### Swimlane 1: User + Orchestration (Cloud)

- Box A1: `User (Streamlit Web Dashboard)`
- Box A2: `Azure Agent (MAF Orchestrator)`
- Box A3: `Calc Agent logic`
- Box A4: `Excel Agent logic`

### Swimlane 2: MCP Tool & API Layer

- Box B1: `CalcsLive API`
- Box B2: `Local Excel Bridge (REST localhost:8001)`
- Box B3: `Excel MCP Wrapper (Registered to Windows ODR)`
- *Note:* Add a red dashed boundary or lock icon between B2 and B3 labeled: `ODR execution blocked by Secure Boot TestMode policy in Dev Preview`

### Swimlane 3: Execution Targets (Local + Backend)

- Box C1: `CalcsLive Backend\n(Unit Engine + Article Store)`
- Box C2: `Excel 2016 Pro Desktop`

## Required Arrows

### Control/orchestration arrows (solid)

- `User (Streamlit Web Dashboard) <-> Azure Agent (MAF Orchestrator)`
- `Azure Agent (MAF Orchestrator) -> Calc Agent logic`
- `Azure Agent (MAF Orchestrator) -> Excel Agent logic`

### Tool invocation arrows (solid)

- `Calc Agent logic -> CalcsLive API`
- `Excel Agent logic -> Local Excel Bridge (REST localhost:8001)`
- *(Dashed line indicating intended future path)* `Excel Agent logic -.-> Excel MCP Wrapper (Registered to Windows ODR)`

### Execution arrows (solid)

- `CalcsLive API -> CalcsLive Backend`
- `Local Excel Bridge (REST localhost:8001) -> Excel 2016 Pro Desktop`
- `Excel MCP Wrapper (Registered to Windows ODR) -> Local Excel Bridge (REST localhost:8001)`

### Feedback arrows (dashed back)

- `CalcsLive Backend -> CalcsLive API`
- `Excel 2016 Pro Desktop -> Local Excel Bridge (REST localhost:8001)`
- `Local Excel Bridge (REST localhost:8001) -> Excel Agent logic`
- `CalcsLive API -> Calc Agent logic`
- `Calc Agent logic -> Azure Agent (MAF Orchestrator)`
- `Excel Agent logic -> Azure Agent (MAF Orchestrator)`

## Side Annotations (small callouts)

Add 3 callouts on the right:

1. `CalcsLive Article = Source of Truth`
2. `Unit-aware compute centralized in CalcsLive`
3. `Streamlit acts as cross-application System Utility Interface`

## Numbered Workflow Overlay (small badges 1-6)

Place badges on arrows:

1. User interacts with Streamlit to ask for calculation
2. Excel Agent reads PQ table from local REST bridge
3. Calc Agent sends data to CalcsLive API
4. CalcsLive returns unit-aware outputs
5. Excel Agent writes results to Excel via local REST bridge
6. Orchestrator returns final text to Streamlit UI

## Color Key

- Cloud/agent layer: blue tones
- MCP layer: teal/green tones
- Local desktop/backend execution: orange/gray tones
- Dashed arrows: response/data returns

## Export Requirements

- Primary: `docs/architecture.png`
- Optional: `docs/architecture.svg`
- Keep all text readable at 1280px width

## Caption (for README/submission)

`MAF orchestrates specialist agents that use MCP tools to bridge local desktop applications and CalcsLive's unit-aware calculation engine. CalcsLive articles act as reusable source-of-truth definitions across Excel and other engineering tools.`
