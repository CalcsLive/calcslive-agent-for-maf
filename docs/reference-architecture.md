# CalcsLive Reference Architecture

## Purpose

Define how CalcsLive becomes a system-level unit-aware capability that can be consumed by multiple agents/tools (Excel, FreeCAD, others) using MCP, orchestrated by Microsoft Agent Framework (MAF), with Windows local execution support (ODR-hosted local MCP servers).

## Guiding Principles

- CalcsLive article is the source of truth for physical quantity (PQ) definitions.
- Unit-awareness is centralized in CalcsLive, not re-implemented per client tool.
- Tools expose capability through MCP contracts; agents orchestrate through MAF.
- Local desktop access (Excel COM, CAD APIs) runs on Windows local hosts.
- Orchestration must be observable, deterministic where possible, and demo-safe.

## Core Building Blocks

### 1) CalcsLive Backend (Domain Engine)

- Stores/serves article definitions.
- Executes unit-aware calculations.
- Handles unit conversion and dimensional consistency.

### 2) CalcsLive MCP Server (Domain Capability)

- Standard MCP interface over CalcsLive APIs.
- Exposes tools for article retrieval, calculation execution, and validation.

### 3) Tool MCP Servers (Context Adapters)

- Excel MCP server (via local bridge/COM wrappers).
- FreeCAD MCP server (via local automation APIs).
- Optional future MCP servers (Inventor, files, PLM, etc.).

### 4) MAF Multi-Agent Layer (Orchestration)

- Orchestrator agent decomposes user intent.
- Specialist agents handle domain/tool concerns:
  - Calc Agent (CalcsLive)
  - Excel Agent
  - CAD Agent
- MAF handles routing, policy, context, and execution flow.

### 5) Windows ODR Local Host (Desktop Boundary)

- Runs local MCP servers that need desktop process access.
- Bridges cloud-orchestrated flows to local applications.
- Enforces local security boundaries for desktop interactions.

## High-Level Architecture

```text
User Intent
   |
   v
MAF Orchestrator Agent (cloud)
   |----> Calc Agent ----> CalcsLive MCP ----> CalcsLive Backend
   |
   |----> Excel Agent ---> Excel MCP (Windows local host/ODR) ---> Excel App
   |
   `----> CAD Agent -----> FreeCAD MCP (Windows local host/ODR) -> FreeCAD
```

## Runtime Topologies

### A. Hackathon MVP (recommended)

- Agent process runs locally with Azure model endpoint.
- Excel bridge/MCP runs locally on Windows.
- CalcsLive API is remote.
- Best for reliability, speed, and demo control.

### B. Hybrid Cloud + Local Desktop

- MAF orchestrator hosted in Azure.
- Local ODR host exposes Excel/CAD MCP endpoints securely.
- Needed for full "cloud agent controls desktop tools" narrative.

## Reference Workflow: Excel + CalcsLive

1. User: "Calculate sheet outputs with units."
2. Orchestrator asks Excel Agent to read PQ table.
3. Excel Agent calls Excel MCP tool: `read_pq_table`.
4. Orchestrator asks Calc Agent to compute.
5. Calc Agent calls CalcsLive MCP tool: `run_script` or `run_article`.
6. Orchestrator asks Excel Agent to write outputs.
7. Excel Agent calls Excel MCP tool: `write_pq_results`.
8. User sees updated values in Excel with requested output units.

## CalcsLive MCP v1 Tool Contract

### Required tools

- `calcslive.get_article(article_id)`
- `calcslive.run_article(article_id, inputs, outputs?)`
- `calcslive.run_script(pqs, inputs, outputs?)`
- `calcslive.convert(value, from_unit, to_unit)`
- `calcslive.validate_pq_schema(pqs)`

### Tool I/O requirements

- Always include value and unit together in responses where applicable.
- Use explicit input/output schemas; avoid free-form text payloads.
- Return structured errors with stable codes:
  - `INVALID_UNIT`
  - `MISSING_INPUT`
  - `DIMENSION_MISMATCH`
  - `ARTICLE_NOT_FOUND`
  - `UPSTREAM_UNAVAILABLE`

## Security and Trust Boundaries

- Cloud agents do not directly access local desktop processes.
- Local ODR host mediates desktop tool access.
- API keys/tokens stored in env/secret stores, never hardcoded.
- Minimal privilege principle for desktop automation endpoints.
- Audit trails: correlation ID across orchestrator and tool calls.

## Observability

- Per-request correlation ID propagated through all tool calls.
- Log tool latency, retries, and failure codes.
- Capture workflow events:
  - read inputs
  - calc request
  - calc response
  - write outputs

## Hackathon Delivery Strategy (to Mar 15)

### Must-show (MVP)

- CalcsLive as unit-aware compute source of truth.
- Agent-driven Excel workflow end-to-end.
- Repeatable rerun with changed inputs.

### Nice-to-have

- One additional tool integration (FreeCAD or second consumer).
- Hosted orchestrator path with local ODR bridge.

### Narrative for judges

- "CalcsLive is not just a calculator endpoint; it is a reusable unit-aware capability exposed via MCP and orchestrated by MAF across desktop and cloud tools."

## Current Status Assessment

You are on the right track for the deadline.

Why:

- You already have the hardest MVP pieces working: Excel read/write bridge + agent tool orchestration + Azure endpoint integration.
- The architecture story is coherent and differentiated: source-of-truth PQ model + multi-tool reuse.

What to prioritize next:

1. Stabilize one deterministic end-to-end prompt path for Excel.
2. Produce one architecture diagram aligned with this document.
3. Add one extra consumer only if MVP is already demo-stable.
