# CalcsLive Excel MCP Wrapper

This component exposes the existing `excel-bridge` HTTP endpoints as MCP tools.

## Tools

- `excel_health`
- `excel_get_pq_for_calcslive`
- `excel_write_pq_results`

## Local Run (for testing)

1. Start Excel bridge:

```powershell
python excel-bridge/main.py
```

2. Run MCP wrapper (stdio):

```powershell
python excel-mcp/server.py
```

## ODR Registration

Register from manifest path:

```powershell
odr mcp add "C:\E3d\E3dProjs\2026\26009-calcslive-agent-for-maf\excel-mcp\manifest.json"
```

Then verify:

```powershell
odr mcp list
```

## Notes

- This wrapper depends on the Excel bridge being reachable at `EXCEL_BRIDGE_URL` (default `http://127.0.0.1:8001`).
- The manifest uses `py server.py`; if your Python launcher differs, adjust `manifest.json` command/args.
