# ODR Validation Log - 2026-02-27

## Scope

Validate ODR availability and readiness to register an Excel-related local tool path for hackathon evidence.

## Commands Executed and Results

### 1) ODR runtime check

Command:

```powershell
odr --version
```

Result:

```text
0.1.1
```

Status: PASS

---

### 2) ODR MCP command surface check

Command:

```powershell
odr mcp --help
```

Result (summary):
- Commands available: `run`, `list`, `add`, `remove`, `configure`

Status: PASS

---

### 3) Baseline server list

Command:

```powershell
odr mcp list
```

Result (summary):
- Default File Explorer MCP server present (`file-mcp-server`)

Status: PASS

---

### 4) MCP wrapper creation and syntax/startup check

Actions:
- Added `excel-mcp/server.py` (MCP tools mapped to Excel bridge REST)
- Added `excel-mcp/manifest.json` (ODR registration manifest)

Command:

```powershell
python -m py_compile "excel-mcp/server.py"
python "excel-mcp/server.py"
```

Result:
- Syntax check passes.
- Server starts under stdio mode (no import/runtime crash).

Status: PASS

---

### 5) ODR manifest registration (local binary server)

Command:

```powershell
odr mcp add "C:\E3d\E3dProjs\2026\26009-calcslive-agent-for-maf\excel-mcp\manifest.json"
```

Result:
- `success: true` and package identifier `calcslive-excel-mcp-0.1.0` returned.

Status: PASS

---

### 6) ODR access/use from CLI client

Commands:

```powershell
odr mcp list
odr mcp run --proxy calcslive-excel-mcp-0.1.0
```

Result:
- Access denied by system:
  - `AccessStatus=DeniedBySystem`
  - `TestMode=False`
  - `PackageFamilyName='(null)'`

Status: BLOCKED (policy/host access gate)

Interpretation:
- Registration succeeds.
- Direct CLI client access to this custom server is blocked by current ODR policy context.

---

### 7) Excel bridge reachability check

Command:

```powershell
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8001/excel/health', timeout=2).status)"
```

Result:
- Timeout / connection error

Status: FAIL (bridge not running during this check)

---

### 8) ODR add probe against current Excel bridge URI

Command:

```powershell
odr mcp add calcslive-excel-bridge --uri http://127.0.0.1:8001
```

Result:

```json
{
  "success": false,
  "message": "Failed to connect to remote server."
}
```

Status: FAIL (expected for non-MCP REST endpoint)

Interpretation:
- Current Excel bridge endpoint is not currently reachable and/or not MCP protocol-compliant.
- A dedicated MCP wrapper is required for robust ODR registration.

## Overall Assessment

- ODR runtime is present and functional on this machine.
- Custom MCP wrapper exists and registers successfully.
- Runtime access to custom server is currently blocked by ODR system access policy from this CLI context.
- Excel bridge direct URI registration still fails because it is REST, not MCP.

## Next Actions

1. Start and verify Excel bridge health first.
2. Confirm ODR test mode/allowlist guidance for custom servers (Windows docs or supported host app path).
3. Run tool invocation through an ODR-supported client context.
4. Re-run end-to-end validation and capture screenshots/logs.
