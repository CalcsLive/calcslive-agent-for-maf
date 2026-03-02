# ODR Runbook (Excel Bridge + CalcsLive)

This runbook is designed for a fast, repeatable verification session.

## 1) Preflight

Run from repo root:

```powershell
odr --version
odr mcp --help
odr mcp list
```

Expected:
- ODR returns `0.1.1` (or newer)
- MCP subcommands available (`run`, `list`, `add`, `remove`, `configure`)
- At least one server listed (e.g., File Explorer MCP)

## 2) Start Excel Bridge

In terminal A:

```powershell
python excel-bridge/main.py
```

In terminal B, verify bridge health:

```powershell
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8001/excel/health', timeout=5).read().decode())"
```

Expected:
- JSON response with connection status (Excel open + workbook info)

## 3) Understand Current Limitation

Current `excel-bridge` is REST, not MCP protocol. ODR registration expects an MCP server.

Implication:
- `odr mcp add ... --uri http://127.0.0.1:8001` will fail unless the endpoint speaks MCP.

## 4) Quick Registration Probe (diagnostic)

```powershell
odr mcp add calcslive-excel-bridge --uri http://127.0.0.1:8001
```

Interpretation:
- `Failed to connect to remote server.` means endpoint is reachable/not reachable and/or not MCP-compliant.
- If this fails while bridge is up, protocol mismatch is confirmed.

## 5) Create MCP Wrapper (recommended next step)

Build a small MCP server process (`excel-mcp`) that maps MCP tools to existing REST endpoints.

Status in this repo:
- `excel-mcp/server.py` (wrapper implementation)
- `excel-mcp/manifest.json` (ODR registration manifest)

- `excel.health` -> `GET /excel/health`
- `excel.read_pq_for_calcslive` -> `GET /excel/pq-for-calcslive`
- `excel.write_pq_results` -> `POST /excel/write-pq-results`

Then register MCP wrapper with ODR using either:
- manifest file (`odr mcp add <manifest-path>`), or
- remote MCP URI (`odr mcp add <name> --uri <mcp-uri>`) if wrapper exposes MCP HTTP transport.

Example manifest registration:

```powershell
odr mcp add "C:\E3d\E3dProjs\2026\26009-calcslive-agent-for-maf\excel-mcp\manifest.json"
```

## 6) Validation Flow After MCP Wrapper Exists

1. `odr mcp add ...`
2. `odr mcp list` confirms server registration
3. Agent uses ODR-registered Excel MCP tools
4. Run prompt: "Calculate the values and write them back to Excel"
5. Verify output cells updated (`V`, `m`)

If `odr mcp list` or `odr mcp run --proxy <id>` returns `AccessStatus=DeniedBySystem`:
- Registration still may be successful.
- This indicates ODR policy/client context does not allow direct CLI access for the custom server.
- Capture this as evidence and proceed via supported host/test-mode guidance.

## 7) Evidence Commands for Recording

```powershell
odr --version
odr mcp list
```

And in agent chat:
- `Check Excel`
- `please get PQs for calcslive`
- `Calculate the values and write them back to Excel`

## 8) Fallback if ODR Path Blocks

Use stable MVP path:
- local Excel bridge + Azure-backed agent (`azure-agent/agent.py`)
- keep ODR as bonus evidence with runtime/version + roadmap statement

## 9) Happy Path Closed-Loop (Current MVP)

Use this when validating the core user scenario end-to-end.

### Prerequisites

1. Start Excel and open workbook (e.g., `ExampleCalc-01.xlsx`).
2. Start bridge:

```powershell
python excel-bridge/main.py
```

3. Start Streamlit app:

```powershell
streamlit run azure-agent/app.py
```

### Scenario A: Load + Prefill

Prompt in UI:

```text
please load calculation 3MLCVKCU3-2K8 to Excel sheet Sheet2 at B9
```

Expected:
- Metadata rows appear above table (including ArticleID and editor URL).
- PQ table appears at requested anchor.
- Initial output values are prefilled.

### Scenario B: Manual Recalculate

1. Edit one input value and/or unit in Excel.
2. Prompt:

```text
please recalculate
```

Expected:
- Agent reads current table state.
- CalcsLive recalculates outputs.
- Output value cells update in place.

### Scenario C: Live Mode Auto-Recalc

1. Enable **Live Mode** in sidebar.
2. Change input value/unit or output unit in Excel.
3. Wait poll + debounce interval.

Expected:
- Live Mode status changes to auto-recalc success.
- Outputs update without manual prompt.
