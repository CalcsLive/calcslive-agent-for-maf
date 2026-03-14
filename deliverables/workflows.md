# Supported Workflows

This document defines the supported end-user workflows for the CalcsLive Agent submission. It is the source of truth for demo planning, screenshots, GIFs, README polish, architecture narration, and submission copy.

## Core Product Narrative

The centerpiece of this project is **CalcsLive** as a reusable, web-native, unit-aware calculation infrastructure.

The main workflow is not just "AI creates a formula." It is:

1. a user describes a desired calculation in natural language,
2. Azure AI helps draft the calculation structure,
3. CalcsLive provides deterministic unit-aware review and execution,
4. the human user refines the script with project context and domain knowledge,
5. the approved result is turned into a live reusable calculation article,
6. that article can then power multiple systems such as CalcsLive web modes, Excel, and future downstream tools.

This is a strong example of **AI-Human Co-Authoring** rather than AI-generated slop:

- the LLM contributes speed, synthesis, and structure
- the human contributes quality control, context, and engineering judgment
- CalcsLive contributes deterministic unit-aware execution and reusable delivery

## Product Scope

CalcsLive Agent is a moderator-style AI application that connects:

- **CalcsLive** as the unit-aware engine and reusable article store
- a unified Azure-hosted / local Streamlit app as the main user interface
- a local Excel bridge for spreadsheet interaction when Excel is available

The same unified app supports both cloud-only and local-with-Excel modes.

This means the architecture already demonstrates interoperability across:

- **cloud/web agent experiences**, where the user interacts with a hosted AI workflow
- **desktop/local agent experiences**, where Excel participates through the bridge API

Partial MCP implementation further supports the narrative that the system is designed for broader tool and agent interoperability, not just one hardcoded UI path.

## Why This Matters

The superpower of the app is the ability to create **live, web-accessible, unit-aware calculations from natural language in under a minute**, while keeping a human review loop in place.

Once a reviewed calculation is created in CalcsLive, it becomes a reusable asset with its own URL and multiple usage modes:

- `edit`
- `calculate`
- `table`
- `view`

This means the output is not trapped inside one UI or one workbook. It becomes reusable across the web and across systems.

## Modes

### Cloud Mode

Available when the app is running without access to the local Excel bridge.

Capabilities:
- create and review stateless calculation scripts
- discover units / resolve ambiguous unit aliases through CalcsLive tools
- iterate with the user during review to improve the script
- persist reviewed scripts as CalcsLive calculation articles
- open created calculations in multiple CalcsLive modes (`edit`, `calculate`, `table`, `view`)

### Local + Excel Mode

Available when the local Excel bridge is reachable.

Capabilities:
- all cloud capabilities
- send created calculations to Excel
- read calculations from Excel back into reviewed CalcsLive script form
- reactive recalculation in Excel after edits
- convert Excel-authored calculation structures into reusable CalcsLive content

## Workflow 1: Natural Language -> Review -> Create Live Calculation

This is the **main workflow** and the strongest differentiator.

### User goal

Create a high-quality live unit-aware calculation from natural language, using human review to refine the generated result before it becomes a reusable calculation article.

### Steps

1. User enters a natural-language request.
2. Azure AI moderator interprets the problem and drafts a PQ script.
3. The script is sent to CalcsLive using `run_calcslive_script` for stateless review.
4. User reviews:
   - generated title
   - description
   - calculation table
   - warnings
   - category metadata
5. User refines the script through follow-up prompts and domain-specific corrections.
6. The review cycle can repeat until the calculation is satisfactory.
7. User clicks `Create Article`.
8. App persists the reviewed script using `create_calcslive_article_from_script`.
9. The new article becomes accessible in CalcsLive web modes.

### Outcome

In less than a minute, the user can create a live, reusable, unit-aware calculation asset with its own web URL.

### Why this is powerful

- LLM helps generate the calculation quickly
- human review keeps quality high
- CalcsLive ensures unit-aware deterministic behavior
- the result becomes reusable beyond the current chat session

## Workflow 2: Create -> Send to Excel -> Reactive Spreadsheet Use

This demonstrates how CalcsLive can upgrade spreadsheets with unit awareness.

### User goal

Use a newly created live calculation directly inside Excel while preserving CalcsLive as the source-of-truth infrastructure.

### Steps

1. User completes Workflow 1 and creates a new calculation article.
2. User clicks `Send Calc to Excel`.
3. The bridge loads the article into Excel as metadata + PQ table.
4. User edits spreadsheet values and/or units.
5. Excel bridge detects changes.
6. Updated table data is sent back through CalcsLive.
7. Returned outputs are written into Excel.

### Outcome

Excel becomes a unit-aware engineering workspace backed by a reusable CalcsLive article.

### Meaning in the bigger picture

This shows CalcsLive acting as an **infrastructural atomic unit-awareness carrier** for Excel.

### Additional strength of the Excel workflow

- Excel cell references can be used to connect a CalcsLiverated PQ table with the rest of the spreadsheet document.
- This means the user is not limited to isolated calculations; the unit-aware PQ table can participate in broader spreadsheet models.
- As a result, CalcsLiverated content can become **composable** inside Excel.

## Workflow 3: Excel-authored Table -> Review -> Create

This demonstrates the reverse direction and supports users who already work in spreadsheets.

### User goal

Start from an Excel-authored calculation structure, review it as a CalcsLive script, and convert it into a reusable live calculation article.

### Expected Excel structure

The bridge looks for a compatible table with these semantic columns:

- `Description`
- `Symbol`
- `Expression`
- `Value`
- `Unit`

Optional:
- left-side row number column (`#`)

### Row rules

- Input row:
  - `Expression` blank
  - `Value` and `Unit` populated
- Output row:
  - `Expression` populated
  - `Unit` populated
  - `Value` optional or pre-existing

### Steps

1. User lays out a compatible PQ table in Excel.
2. User clicks `Get Calc from Excel`.
3. Bridge reads the Excel table and converts it into `pqs`, `inputs`, and `outputs`.
4. App runs `run_calcslive_script` for review.
5. User reviews and refines the result in the same human-in-the-loop workflow.
6. User adjusts title/description if needed.
7. User clicks `Create Article`.

### Outcome

An Excel-authored calculation becomes a reusable CalcsLive article accessible on the web and across systems.

### Meaning in the bigger picture

This proves the workflow is bi-directional:

- CalcsLive can enhance Excel
- Excel can seed new CalcsLive content

## Cloud and Local Coverage

Workflow 1 works in both cloud and local deployments and is the core feature of the app.

- In cloud mode, Workflow 1 delivers the main value: rapid creation of reviewed, reusable, live unit-aware calculations.
- In local mode, Workflow 1 combines with Workflows 2 and 3 to extend the same calculation assets into and out of Excel.

## User Mental Model

- `Reviewed CalcsLive Script` = AI-Human Co-Authoring quality stage
- `Create Calculation Article` = persistence stage
- `Bridge to/from Excel` = interoperability stage

This ordering is intentional and reflects the moderator-agent design.

## Win-Win-Win Framing

This project creates a win for three ecosystems:

- **Azure**: provides the AI moderation/orchestration layer
- **CalcsLive**: provides the deterministic unit-aware infrastructure and reusable article system
- **Excel**: gains bi-directional access to unit-aware live calculations

## System-Angle Agentic Narrative

This project should be framed as a system-level agentic solution, not just a single app integration.

- The **web/cloud side** demonstrates Azure AI moderation, AI-Human Co-Authoring, and live calculation creation.
- The **desktop/local side** demonstrates Excel as a connected execution surface through the bridge API.
- **CalcsLive** serves as the reusable unit-aware infrastructure layer that ties the system together.
- **MCP work** serves as proof that the architecture is extensible toward broader tool and agent interoperability.

In other words, the project already shows that the same solution can operate across both cloud/web and desktop/local agent contexts.

## What To Emphasize In Submission

Recommended emphasis order:

1. Natural language -> human review -> live calculation creation
2. Live web-native CalcsLive article with multiple modes
3. Send to Excel -> reactive recalculation
4. Excel-authored table -> review -> create
5. Future extensibility to CAD, n8n, and other systems

## Strong Proof Artifact

Use artifacts like:

- `deliverables/samples/3MMMT258D-23V (table).pdf`

to show that a reviewed calculation can quickly become a complete live unit-aware web app in CalcsLive table mode.

## Current Non-Goals / Deferred Work

- automatic reconnect from cloud app directly to a private local Excel bridge
- full Excel MCP parity for the complete review/create lifecycle
- persisted override/edit API for existing saved article instances
- generalized plugin system beyond Excel (future path: CAD, Sheets, others)
