# Microsoft AI Dev Days Hackathon - CalcsLive Project Plan

## Project: "CalcsLive Agent - Unit-aware Calculation Carrier for Excel in MAF"

**Repo**: `calcslive-agent-for-maf`

**Concept**: AI Agent that orchestrates between Excel and CalcsLive within Microsoft Agent Framework (MAF), enabling unit-aware engineering calculations directly in spreadsheets.

**Tagline**: "Bring unit-aware calculations to Excel through Microsoft AI Agents"

---

## Hackathon Requirements Checklist

| Requirement | How We Meet It |
|-------------|----------------|
| **Microsoft Foundry / Agent Framework / Azure MCP** | ⚠️ In progress: local-first agent flow complete; explicit hosted MAF artifact proof still pending |
| **Azure Deployment** | ⚠️ In progress: local-first validated, hosted entrypoint pending |
| **GitHub Public Repo** | ✅ New repo created after Feb 10, 2026 |
| **Demo Video (2 min)** | ⚠️ Script outlined, recording pending |
| **Architecture Diagram** | ✅ `docs/architecture.png` generated and aligned to implementation |

---

## Compliance Evidence Matrix (for submission)

| Requirement | Evidence Artifact | Owner | Status |
|-------------|-------------------|-------|--------|
| Agent Framework / Azure MCP | `azure-agent/` orchestration flow + ODR registration logs + demo narration callout | e3d | ⚠️ |
| Azure deployment | Deployed endpoint URL + portal screenshot + successful invocation log | e3d | ⚠️ |
| Public repo | GitHub repo link with commit history after Feb 10 | e3d | ✅ |
| 2-min demo video | `demo/demo_script.md` + final MP4 + timestamps for key steps | e3d | ⚠️ |
| Architecture diagram | `docs/architecture.png` matching shipped implementation | e3d | ✅ |

---

## Environment Update (Current)

- OS: Windows 11 Home 25H2 (Insider Dev Channel)
- ODR: v0.1.1 available locally
- Azure-backed agent path: working (`azure-agent/agent.py`)
- Excel bridge path: working (`excel-bridge/` on `localhost:8001`)
- Streamlit commander path: working (`azure-agent/app.py`)
- Event-driven reactive recalc: working (`excel-bridge/live_watcher.py`)

**Execution modes going forward**
- **Mode A (MVP primary)**: local orchestration + Azure inference + local Excel bridge
- **Mode B (ODR proof path)**: register Excel bridge as ODR local tool and verify one end-to-end workflow

---

## Your Existing Assets (Informing Design)

| Project | Pattern Reusable |
|---------|-----------------|
| CalcsLive MCP Server | MCP tool definitions, API patterns |
| Inventor Integration | COM automation via Python/FastAPI bridge |
| Google Sheets Integration | REST API payload structure, metadata discovery |
| calcs-agent-opencode | Natural language → calculation flow |

**Note**: Existing code cannot be submitted, but patterns and CalcsLive API are fair game.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Excel 2016 Pro (Desktop)                                   │
│  - Engineering spreadsheet with parameters                  │
│  - Values and units in cells                                │
└──────────────────────┬──────────────────────────────────────┘
                       │ COM Automation (pywin32)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Local Bridge Server (Python/FastAPI) - localhost:8001      │
│  - Read/write Excel cells                                   │
│  - Parse ranges for values & units                          │
│  - Similar pattern to Inventor bridge                       │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP REST API
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Azure-Hosted Agent (Microsoft Agent Framework)             │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ Orchestrator│  │ Calc Agent  │  │ Excel Agent │          │
│  │ (Azure      │→ │ (CalcsLive  │  │ (Local      │          │
│  │  OpenAI)    │  │  MCP tools) │  │  Bridge)    │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└──────────────────────┬──────────────────────────────────────┘
                       │ CalcsLive REST API
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  CalcsLive Backend (existing service - OK to use)           │
│  - Unit conversion engine (67+ categories)                  │
│  - Calculation execution                                    │
│  - Metadata discovery for available calculations            │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Architecture: CalcsLive as Source of Truth

```
┌─────────────────────────────────────────────────────────────┐
│  CalcsLive Article (Source of Truth)                        │
│  - Defines calculation: symbols, expressions, units         │
│  - ArticleID for reference                                  │
│  - Reusable across Excel, Inventor, FreeCAD, etc.           │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┬──────────────┐
        ▼              ▼              ▼              ▼
   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
   │ Excel   │   │Inventor │   │ FreeCAD │   │ Other   │
   │ Bridge  │   │ Bridge  │   │ Bridge  │   │ MCP...  │
   └─────────┘   └─────────┘   └─────────┘   └─────────┘
```

**Key Principle**: CalcsLive calculation = atomic element for physical quantities. Programs consume CalcsLive articles to gain unit-aware capability.

---

## Network Topology Decision (Critical)

**Constraint**: Azure-hosted agent cannot directly call `localhost:8001` on the demo laptop.

**Primary demo topology (low risk)**:
- Run Excel Bridge locally on the demo machine (`localhost:8001`)
- Run the agent process locally but backed by Azure model endpoint
- This still demonstrates Azure AI + local Excel orchestration reliably

**Hosted topology (submission bonus)**:
- Add secure relay/tunnel for bridge access (or deploy a bridge-side relay)
- Restrict by auth token + IP allowlist + short-lived session

**Decision Gate**:
- If hosted relay is not production-safe by deadline, ship local bridge + Azure inference path as MVP

**ODR update**:
- Since ODR v0.1.1 is available, add ODR local-tool verification as a near-term objective
- ODR is now part of evidence collection, not only future architecture

---

## User Flow (Demo Scenario)

### The Problem

Standard Excel ignores units - formulas don't know that "2 in" and "3 cm" are different unit systems. CalcsLive solves this with unit-aware calculations.

---

### Core Flow: CalcsLive Article → Excel Consumer

**Step 1**: User creates CalcsLive article (Source of Truth)
- User creates calculation in CalcsLive editor
- Defines: symbols (D, H, rho, V, m), expressions (pi*D^2/4*H, rho*V), units
- Gets ArticleID for reference

**Step 2**: Agent initializes Excel from article (like Google Sheets pattern)
- Agent reads article metadata (title, articleID, URL, creator, date)
- Agent reads PQ structure (symbols, expressions, units, input/output flags)
- Agent populates Excel with structured table:

| Description | Symbol | Expression | Value | Unit |
|-------------|--------|------------|-------|------|
| Diameter | D | | [input] | in |
| Height | H | | [input] | cm |
| Density | rho | | [input] | kg/m³ |
| Volume | V | pi*D^2/4*H | [output] | L |
| Mass | m | rho * V | [output] | lbm |

**Step 3**: User enters input values in Excel

**Step 4**: Agent triggers calculation
- Reads input values/units from Excel
- Calls CalcsLive API with articleID and inputs
- Writes output values back to Excel

**Step 5**: Reuse
- Initialized Excel sheet can be reused
- Change input values → recalculate → get new outputs

---

### Stretch Goal: AI Agent Creates CalcsLive Articles

**User says**: "Create a cylinder volume and mass calculator with diameter, height, and density inputs"

**Agent Actions**:
1. 🔍 Understands intent → cylinder calculation with specified inputs
2. 🧮 Determines PQ structure (symbols, expressions, units)
3. 📝 Creates CalcsLive article via API (new feature needed)
4. 📋 Returns articleID to user
5. ✅ User can now use this article in Excel, Inventor, etc.

---

## Implementation Plan

### Phase 1: Setup (Days 1-3) ~8 hours
- [x] Create new public GitHub repo
- [ ] Set up Azure subscription (free tier)
- [ ] Configure Azure OpenAI resource
- [ ] Research Microsoft Agent Framework SDK (Semantic Kernel)

**Acceptance criteria**
- [ ] Azure endpoint reachable from local machine
- [ ] Agent can complete a tool-call roundtrip (`get_excel_health`)

### Phase 2: Excel Bridge (Days 4-7) ~12 hours
- [x] Python/FastAPI server for Excel COM automation
- [x] Endpoints: `/excel/read-range`, `/excel/write-cell`, `/excel/health`
- [x] Auto-detection endpoints: `/excel/find-article-id`, `/excel/find-pq-table`, `/excel/pq-for-calcslive`
- [x] Write results: `/excel/write-pq-results` (by symbol name)
- [x] Test with sample engineering spreadsheet (ExampleCalc-01.xlsx)

**Acceptance criteria**
- [x] Detect ArticleID and PQ table without manual row config
- [x] Read inputs/outputs in CalcsLive-ready schema
- [x] Write output values by symbol into Excel value column

### Phase 3: Core Agent - MVP Freeze (Article Consumer) (Days 8-12) ~15 hours
- [x] Lock MVP scope: **consumer flow only** (no article creation required)
- [ ] Set up Microsoft Agent Framework project artifacts for hosted path
- [x] Define CalcsLive tools (calculate + validate metadata + script fallback)
- [x] Define Excel tools (health, pq read, result write, setup from article)
- [x] Implement deterministic orchestrator path: load -> read Excel -> call CalcsLive -> write results
- [ ] Deploy hosted entrypoint (Functions or equivalent)

**ODR sub-track (parallel to Phase 3)**
- [x] Confirm ODR runtime health/version and capture evidence
- [x] Register Excel bridge as local tool in ODR
- [ ] Verify discovery of local Excel tool from agent runtime (blocked by policy gate)
- [ ] Execute one ODR-routed flow: read PQ → calculate → write results
- [x] Capture logs/screenshots for compliance evidence

**Acceptance criteria**
- [x] Single prompt executes full workflow end-to-end
- [x] Output cells (`V`, `m`) update correctly for at least 3 reruns
- [ ] End-to-end runtime under 10 seconds on demo sheet (measure and record)
- [ ] One successful ODR local-tool run is recorded with evidence

### Phase 4: Stretch - Article Creator Agent (Days 13-17) ~15 hours
- [ ] Natural language → PQ structure reasoning
- [ ] CalcsLive article creation API (may need new endpoint)
- [ ] Agent flow: user describes calc → agent creates article → returns articleID
- [ ] Integration with Excel setup flow

**Acceptance criteria**
- [ ] Create article from prompt and return articleID
- [ ] Initialize Excel table from created article
- [ ] Stretch excluded from critical demo path if unstable

### Phase 5: Demo & Submission (Days 18-21) ~10 hours
- [ ] Record 2-minute demo video
- [ ] Create architecture diagram
- [ ] Write README with setup instructions
- [ ] Prepare submission materials

**Acceptance criteria**
- [ ] Demo includes one successful full run and one input-change rerun
- [ ] All checklist evidence linked in README
- [ ] Submission package finalized at least 24h before deadline

---

## Critical Path to Deadline (Mar 15)

| Date | Milestone | Output |
|------|-----------|--------|
| Mar 1 | MVP E2E stabilized | Prompt → Excel outputs written reliably |
| Mar 3 | ODR verification checkpoint | ODR local-tool registration + one verified run |
| Mar 5 | Hosted path decision locked | Hosted entrypoint working OR documented local-first rationale |
| Mar 8 | Demo freeze | No new features; only reliability and docs |
| Mar 10 | Video draft complete | First cut 2-min demo with timestamps |
| Mar 12 | Submission artifacts complete | README, architecture image, evidence table |
| Mar 14 | Final rehearsal | Dry run on clean environment |
| Mar 15 | Submit | Final package uploaded |

---

## Demo Reliability Plan (2-minute video)

**Primary path**
1. Show Excel sheet with mixed units
2. Ask agent to check health and calculate
3. Show outputs written in Excel
4. Change one input and rerun

**ODR proof insert (15-25 sec, if stable)**
1. Show ODR runtime/version on machine
2. Show Excel bridge local-tool registration/discovery
3. Run one prompt using the same workflow through registered local tool

**Fallback path (if API or hosted path fails)**
1. Use `python azure-agent/agent.py --demo`
2. Show deterministic bridge read/write and explain Azure path status
3. Preserve core value proposition: unit-aware calculation in Excel workflow

---

## Risk Register

| Risk | Impact | Mitigation | Fallback |
|------|--------|------------|----------|
| ODR integration churn (new runtime) | Medium | Keep ODR test scope minimal and scripted | Use non-ODR MVP path in final demo |
| Azure ↔ local connectivity | High | Keep local-first MVP path; avoid relay dependency | Local bridge + Azure inference local-run demo |
| CalcsLive endpoint contract drift | Medium | Pin endpoint list in code + keep debug logs enabled | Fallback to known working endpoint path |
| CalcsLive auth / API availability | High | Pre-validate keys and sample payloads | Demo mode with deterministic outputs |
| Excel COM instability | Medium | Keep workbook/sheet naming fixed; add health checks | Restart bridge + use backup workbook |
| Last-minute scope creep | Medium | MVP freeze date and strict backlog | Cut stretch features |

---

## Judging Narrative (talk track)

- **Real problem**: Excel formulas ignore units; engineering teams make silent conversion mistakes.
- **Innovation**: CalcsLive article as reusable source of truth, consumed by an AI agent and desktop tools.
- **Execution**: Working bridge + agent orchestration with measurable end-to-end value in a familiar spreadsheet UX, plus ODR local-tool proof.

---

## Success Metrics

- Setup from clone to first successful calc in under 5 minutes
- End-to-end calculation cycle in under 10 seconds
- At least 3 consecutive successful reruns after changing inputs
- Demo run completes without manual cell editing for outputs

---

## Current Delivery Snapshot (Mar 2)

### ✅ Working now
- Article load to Excel with metadata + PQ table at configurable anchor.
- Initial output prefill after load.
- Manual recalc by prompt (deterministic read -> calculate -> write).
- Event-driven reactive recalc via Excel `SheetChange` watcher (no LLM per edit).

### 🟡 Remaining for submission
- Explicit hosted-path MAF artifact/evidence.
- ODR full invocation proof (currently policy-gated).
- Final 2-minute video and evidence linking.

---

## Files to Create (New Repo Structure)

```
calcslive-agent-for-maf/
├── README.md                    # Project overview, setup, demo
├── ARCHITECTURE.md              # Detailed architecture diagram
├── excel-bridge/                # COMPLETED
│   ├── main.py                  # FastAPI server on localhost:8001
│   ├── excel_api.py             # COM automation wrapper with auto-detection
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── test_excel_api.py
│   └── README.md                # Bridge-specific documentation
├── azure-agent/                 # IN PROGRESS
│   ├── agent.py                 # Current interactive orchestrator
│   ├── README.md
│   ├── pyproject.toml
│   ├── .env.example
│   ├── function_app.py          # TODO: hosted entrypoint for Azure
│   ├── agent/
│   │   ├── orchestrator.py      # TODO: structured orchestration layer
│   │   ├── tools/
│   │   │   ├── calcslive.py     # TODO: CalcsLive tool wrappers
│   │   │   └── excel.py         # TODO: Excel bridge tool wrappers
│   │   └── prompts.py           # TODO: prompts/policies
│   └── host.json                # TODO: Azure Functions host config
├── demo/
│   ├── sample_spreadsheet.xlsx  # Engineering demo data
│   └── demo_script.md           # Video script
└── docs/
    └── architecture.png         # Submission diagram
```

---

## Reference Projects

| Project | Path | What to Reuse |
|---------|------|---------------|
| Inventor Bridge | `C:\E3d\E3dProjs\2025\25038-calcslive-plug-4-inventor` | COM automation pattern, FastAPI structure |
| Google Sheets | `C:\E3d\E3dProjs\2025\25035-calcslive-plug-4-google-sheets` | API payload structure, metadata discovery |
| CalcsLive MCP | `C:\E3d\E3dProjs\2025\25050-calcslive-mcp-server` | Tool definitions, CalcsLive API client |
| calcs-agent | `C:\E3d\E3dProjs\2026\26002-calcs-agent-opencode` | NL → calculation flow, prompt engineering |
