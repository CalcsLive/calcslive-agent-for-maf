# Submission Evidence Tracker

Use this file as the single source of truth for final hackathon submission evidence.

## Project

- Name: CalcsLive Agent - Unit-aware Calculation Carrier for Excel in MAF
- Repo: `calcslive-agent-for-maf`
- Owner: e3d

## Requirement Mapping

| Requirement | Status | Evidence | Notes |
|-------------|--------|----------|-------|
| Microsoft Foundry / Agent Framework / Azure MCP | 🟡 | `azure-agent/agent_core.py`, `excel-mcp/manifest.json`, `docs/odr-validation-log-2026-02-27.md` | Local-first flow complete; hosted MAF proof still pending |
| Azure deployment | 🟡 | Azure endpoint in `.env`, runtime screenshot/log (TBD) | Add portal screenshot + invocation log |
| Public GitHub repo | ✅ | repo URL + commit history | Ensure public visibility before submit |
| Demo video (2 min) | 🟡 | `demo/demo_script.md`, final MP4 (TBD) | Add timestamps below |
| Architecture diagram | ✅ | `docs/architecture.png`, `docs/reference-architecture.md` | Keep diagram synced with implementation |

## Core MVP Proofs

| Scenario | Status | Evidence Artifact |
|----------|--------|-------------------|
| Load article to Excel with metadata + table | ✅ | UI screenshot + terminal logs |
| Prefill outputs after load | ✅ | screenshot before/after load |
| Manual recalc updates outputs | ✅ | UI prompt + output screenshot |
| Reactive live recalc on Excel cell change | ✅ | watcher logs + output screenshot |
| ODR custom server registration | ✅ | `docs/odr-validation-log-2026-02-27.md` |
| ODR full invocation | ⛔ | blocked (`AccessStatus=DeniedBySystem`) | include as known platform constraint |

## Commands Executed (verifiable)

```bash
python excel-bridge/main.py
streamlit run azure-agent/app.py
python -m py_compile azure-agent/agent_core.py
python -m py_compile excel-bridge/main.py
python -m py_compile excel-bridge/live_watcher.py
odr --version
odr mcp list
```

## Screenshot / Clip Inventory

| ID | File | Description | Included in Video |
|----|------|-------------|-------------------|
| SS-01 | `demo/` (TBD) | Excel loaded table with metadata | ☐ |
| SS-02 | `demo/` (TBD) | Prefilled outputs after load | ☐ |
| SS-03 | `demo/` (TBD) | Manual recalc success | ☐ |
| SS-04 | `demo/` (TBD) | Live mode status + watcher events | ☐ |
| SS-05 | `demo/` (TBD) | ODR version and registration evidence | ☐ |

## Video Timestamp Plan

| Time | Segment | Proof |
|------|---------|-------|
| 00:00-00:15 | Problem framing | mixed-unit Excel risk |
| 00:15-00:35 | Architecture | `docs/architecture.png` |
| 00:35-00:55 | Load article | metadata + table creation |
| 00:55-01:20 | Prefill + manual recalc | output update in Excel |
| 01:20-01:45 | Reactive live mode | change input -> auto update |
| 01:45-02:00 | Close and roadmap | system-level capability claim |

## Open Evidence Items

- [ ] Add Azure portal screenshot + successful hosted invocation evidence.
- [ ] Add final MP4 filename and checksum.
- [ ] Add final screenshots in `demo/` and fill file paths above.
- [ ] Confirm all links and paths are valid from repo root.
