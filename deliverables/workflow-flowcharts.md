# Workflow Flowcharts

Use these as direct inputs for visual workflow diagrams in slides, PNGs, or docs.

## Workflow 1 — Main Creation Flow

### Purpose

Show the core differentiator: human + AI cooperation creates a high-quality live unit-aware calculation in under a minute.

### Flow

```text
User enters natural-language calculation request
    ↓
Azure AI moderator generates PQ script draft
    ↓
CalcsLive stateless run_script review
    ↓
Reviewed script shown to user
    ↓
User refines with project context / domain knowledge
    ↓
Run review again if needed
    ↓
User approves
    ↓
CalcsLive create_article
    ↓
Reusable live calculation article created
    ↓
Accessible in edit / calculate / table / view modes
```

### Key annotation

- `This review loop is where human judgment improves AI-generated calculation quality.`

## Workflow 2 — Send to Excel

### Purpose

Show how a reusable CalcsLive calculation upgrades spreadsheets with unit awareness.

### Flow

```text
Reviewed script approved
    ↓
Create CalcsLive article
    ↓
User clicks Send Calc to Excel
    ↓
Agent loads article metadata + PQ structure through Excel bridge
    ↓
Excel sheet populated with metadata block and PQ table
    ↓
User edits spreadsheet values/units
    ↓
Reactive recalculation writes updated outputs back to Excel
```

### Key annotation

- `Excel becomes a unit-aware working surface while CalcsLive remains the source of truth.`

## Workflow 3 — Get from Excel

### Purpose

Show that Excel can also serve as the starting point for reusable calculation creation.

### Flow

```text
User lays out compatible PQ table in Excel
    ↓
User clicks Get Calc from Excel
    ↓
Excel bridge reads Description / Symbol / Expression / Value / Unit
    ↓
Agent converts table into CalcsLive review payload
    ↓
CalcsLive stateless run_script review
    ↓
User reviews warnings/results and edits title/description if needed
    ↓
User clicks Create Article
    ↓
Excel-authored calc becomes reusable CalcsLive article
```

### Key annotation

- `Existing spreadsheet knowledge can be converted into reusable web-native calculation assets.`

## Workflow 4 — Cloud-Only Use

### Purpose

Show that the system remains useful even without local Excel connectivity.

### Flow

```text
User opens cloud-hosted app
    ↓
Natural-language calculation request
    ↓
Review-first stateless script execution
    ↓
User approves
    ↓
Create CalcsLive article
    ↓
Use resulting article directly through web modes
```

### Key annotation

- `Cloud-only mode still delivers the core superpower: fast creation of live unit-aware calculations.`

## Recommended Visual Style

- Keep each flowchart simple and vertical
- Use 5–8 boxes max per flow where possible
- Use one accent color for human review steps
- Use one accent color for CalcsLive execution/persistence steps
- Use one accent color for Excel-specific steps

## Suggested Labels for Boxes

### Human steps
- `Describe`
- `Review`
- `Refine`
- `Approve`

### AI moderation steps
- `Generate`
- `Moderate`
- `Bridge`

### CalcsLive steps
- `Run Script`
- `Create Article`
- `Deliver Modes`

### Excel steps
- `Populate Excel`
- `Edit Spreadsheet`
- `Read from Excel`
- `Reactive Update`
