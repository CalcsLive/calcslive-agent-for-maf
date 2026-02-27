# ODR Verification Checklist

Use this checklist to prove ODR readiness for hackathon evidence.

## A. Environment and Runtime

- [x] Windows 11 25H2 confirmed
- [x] ODR CLI installed and version captured (`odr --version`)
- [x] ODR MCP command surface available (`odr mcp --help`)

## B. Baseline Registry State

- [x] List registered MCP servers (`odr mcp list`)
- [x] Confirm at least one default server is present (File Explorer MCP)

## C. Excel Integration Readiness

- [ ] Excel bridge process running on `http://127.0.0.1:8001`
- [ ] Bridge health endpoint responsive (`/excel/health`)
- [ ] Excel workbook open and bridge can read PQ data

## D. ODR Registration Test

- [x] MCP wrapper exists in repo (`excel-mcp/server.py`, `excel-mcp/manifest.json`)
- [x] Register local/remote MCP endpoint for Excel integration
- [ ] Confirm registration appears in `odr mcp list`
- [ ] Validate tool discovery from registered server

Note: current ODR CLI context reports `AccessStatus=DeniedBySystem` for this custom server; registration succeeded but listing/invocation remains blocked pending policy/test-mode path.

## E. End-to-End Execution Test

- [ ] Execute: read PQ -> calculate via CalcsLive -> write outputs
- [ ] Verify `V` and `m` value cells updated in Excel
- [ ] Repeat with changed input values (at least 2 reruns)

## F. Evidence Capture (Submission)

- [ ] Screenshot: `odr --version`
- [ ] Screenshot: `odr mcp list` showing target server
- [ ] Screenshot/video: agent tool-call sequence
- [ ] Screenshot/video: Excel output cells before and after
- [ ] Link all artifacts in README evidence section

## Go/No-Go Gate

- **Go (include ODR in main demo)**: Sections A-E complete and stable.
- **No-Go (ODR as bonus only)**: Any blocker in C/D/E near demo freeze; continue with stable Azure + local bridge MVP path.
