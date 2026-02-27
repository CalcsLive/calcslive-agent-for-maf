# 2-Minute Demo Script

## Goal

Show that CalcsLive is a system-level unit-aware capability orchestrated by an agent, demonstrated through Excel and ready to extend to other tools.

## Setup Checklist (before recording)

- Excel open with `ExampleCalc-01.xlsx`
- Excel bridge running (`excel-bridge/main.py`)
- Agent running (`azure-agent/agent.py`) with Azure endpoint configured
- Architecture image available (`docs/architecture.png`)

## Timeline Script (120 seconds)

### 0:00 - 0:15 | Problem framing

**On screen**: Excel sheet with mixed units (`in`, `cm`, `kg/m^3`, target outputs in `L`, `lbm`).

**Say**:
"Excel formulas are not unit-aware. If inputs are in mixed units, results are easy to get wrong. We solve this by making CalcsLive the unit-aware engine behind an agent workflow."

### 0:15 - 0:35 | Architecture snapshot

**On screen**: `docs/architecture.png`

**Say**:
"Here, Microsoft Agent Framework orchestrates specialist agents. They call MCP tools: Excel MCP to read and write spreadsheet values, and CalcsLive MCP to perform unit-aware computation from source-of-truth calculation definitions."

### 0:35 - 0:50 | Agent health + context read

**On screen**: terminal with agent chat.

**Action**: type `Check Excel`.

**Say**:
"First the agent verifies local Excel connectivity through the Excel tool bridge."

**Action**: type `please get PQs for calcslive`.

**Say**:
"Now it reads physical quantities and units from the sheet, classifying inputs and outputs."

### 0:50 - 1:25 | End-to-end calculation

**Action**: type `Calculate the values and write them back to Excel`.

**Say**:
"This single request triggers the orchestration sequence: read sheet values, call CalcsLive for unit-aware calculation, then write output values back into Excel."

**On screen**: show tool calls and final assistant response.

### 1:25 - 1:45 | Recalculation proof

**Action**: change one input value in Excel manually.

**Action**: rerun `Calculate the values and write them back to Excel`.

**Say**:
"Because the workflow is unit-aware and article-driven, we can rerun instantly with changed inputs and get reliable converted outputs."

### 1:45 - 2:00 | Platform vision close

**On screen**: architecture image again.

**Say**:
"The key is that CalcsLive is not tied to one app. Through MCP and MAF orchestration, the same unit-aware capability can be reused by Excel today, and other tools like FreeCAD next."

## Backup/Fallback Lines (if live API hiccups)

- "If cloud calculation is temporarily unavailable, we can still demonstrate deterministic read/write orchestration in local demo mode."
- "The architecture remains the same; only the execution endpoint is switched for demo reliability."

## Suggested Recording Shots

1. Excel sheet close-up (units visible)
2. Terminal tool-call sequence
3. Excel outputs update cells
4. Architecture diagram close
