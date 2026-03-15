# CalcsLive Excel MCP Wrapper

This component exposes a subset of the Excel bridge HTTP endpoints as MCP tools.

It serves as proof that the project can participate in an MCP-oriented tool ecosystem, even though the main working demo path uses the unified app + direct bridge route.

## Tools

- `excel_health`
- `excel_get_pq_for_calcslive`
- `excel_write_pq_results`

## Current Status

- useful as proof of MCP-oriented extensibility
- not the primary user-facing demo path
- does **not** yet cover the full run -> review -> create lifecycle on its own

The main submission path instead uses:

- unified app moderation in `azure-agent/app.py`
- direct Excel bridge access through `excel-bridge`
- shared CalcsLive tool functions in `azure-agent/calcslive_tools.py`

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

- This wrapper depends on the Excel bridge being reachable at `EXCEL_BRIDGE_URL` (default `http://localhost:8001`).
- The manifest uses `py server.py`; if your Python launcher differs, adjust `manifest.json` command/args.
- ODR/Windows registration work is part of the architecture and extensibility proof, not the core live submission path.
