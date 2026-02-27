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

- Box A1: `User`
- Box A2: `MAF Orchestrator Agent`
- Box A3: `Calc Agent`
- Box A4: `Excel Agent`
- Box A5 (optional stretch): `CAD Agent`

### Swimlane 2: MCP Tool Layer

- Box B1: `CalcsLive MCP`
- Box B2: `Excel MCP (Windows Local Host/ODR)`
- Box B3 (optional stretch): `FreeCAD MCP (Windows Local Host/ODR)`

### Swimlane 3: Execution Targets (Local + Backend)

- Box C1: `CalcsLive Backend\n(Unit Engine + Article Store)`
- Box C2: `Excel Desktop`
- Box C3 (optional stretch): `FreeCAD Desktop`

## Required Arrows

### Control/orchestration arrows (solid)

- `User -> MAF Orchestrator Agent`
- `MAF Orchestrator Agent -> Calc Agent`
- `MAF Orchestrator Agent -> Excel Agent`
- `MAF Orchestrator Agent -> CAD Agent` (if shown)

### Tool invocation arrows (solid)

- `Calc Agent -> CalcsLive MCP`
- `Excel Agent -> Excel MCP (Windows Local Host/ODR)`
- `CAD Agent -> FreeCAD MCP (Windows Local Host/ODR)` (if shown)

### Execution arrows (solid)

- `CalcsLive MCP -> CalcsLive Backend`
- `Excel MCP (Windows Local Host/ODR) -> Excel Desktop`
- `FreeCAD MCP (Windows Local Host/ODR) -> FreeCAD Desktop` (if shown)

### Feedback arrows (dashed back)

- `CalcsLive Backend -> CalcsLive MCP`
- `Excel Desktop -> Excel MCP (Windows Local Host/ODR)`
- `Excel MCP (Windows Local Host/ODR) -> Excel Agent`
- `CalcsLive MCP -> Calc Agent`
- `Calc Agent -> MAF Orchestrator Agent`
- `Excel Agent -> MAF Orchestrator Agent`

## Side Annotations (small callouts)

Add 3 callouts on the right:

1. `CalcsLive Article = Source of Truth`
2. `Unit-aware compute centralized in CalcsLive`
3. `Desktop access via local Windows host (ODR)`

## Numbered Workflow Overlay (small badges 1-6)

Place badges on arrows:

1. User asks to calculate
2. Excel Agent reads PQ table
3. Calc Agent calls CalcsLive MCP
4. CalcsLive returns unit-aware outputs
5. Excel Agent writes results to Excel
6. Orchestrator returns final response

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
