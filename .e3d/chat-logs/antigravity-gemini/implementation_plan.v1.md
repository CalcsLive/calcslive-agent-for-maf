# Implementation Plan: Data-Driven Closed-Loop Excel Integrations

## Objective

Enable the user to prompt the commander agent:

`please load calculation <articleId> to Excel`

and get a deterministic closed loop:

1. Load article metadata + PQ table into Excel.
2. Prefill outputs from current/default inputs.
3. Recalculate outputs after user changes values/units.
4. Support reactive mode without VBA macros.

## Current Status (Mar 2)

### ✅ Completed

- Added deterministic article load in `azure-agent/agent_core.py`.
- Added configurable anchor parsing (`sheet`, `row`, `col`) for load requests.
- Added metadata fetch from validate endpoint and map to Excel table structure.
- Added output prefill using the same deterministic recalc pipeline.
- Added deterministic recalc path with explicit row mapping writes.
- Added event-driven reactive mode via Excel COM `SheetChange` watcher:
  - `excel-bridge/live_watcher.py`
  - `POST /excel/live-mode/start`
  - `POST /excel/live-mode/stop`
  - `GET /excel/live-mode/status`
- Streamlit dashboard now controls bridge-side watcher (no UI-side recalc polling).
- Updated auth to Bearer-token-only (legacy payload/query apiKey removed).
- Added article title mapping from `articleTitle` for top metadata row.

### 🟡 In Progress

- Harden endpoint behavior for occasional API v1 `/calculate` internal errors.
- Decide optional endpoint preference strategy for watcher (`calculate` first vs script-first).

### ⛔ Blocked / External

- ODR full custom-server invocation remains blocked by system policy (`DeniedBySystem`) in current CLI context.

## Current Architecture Choice

Reactive recalc is now event-driven at bridge layer (best for future CAD integrations):

- Excel change event -> bridge watcher debounce -> CalcsLive calculate -> Excel writeback.

This avoids commander LLM calls per cell edit and minimizes token cost.

## Validation Checklist

- [x] Load article to Excel at explicit anchor (`Sheet2`, `B9`).
- [x] Metadata rows populated (Title, ArticleID, URL, etc.).
- [x] Output cells prefilled after load.
- [x] Manual prompt recalc updates outputs.
- [x] Live Mode reacts to input/unit edits and updates outputs.
- [x] Watcher status endpoint reports event count + last recalc state.

## Next Steps

1. Add a regression test script for load -> prefill -> manual recalc flow.
2. Add a short operational runbook section for reactive mode troubleshooting.
3. Capture final demo clip with both manual and reactive recalc.
