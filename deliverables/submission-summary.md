# Submission Summary

## Project Name

CalcsLive Agent - Azure-Moderated AI-Human Co-Authoring for Live Unit-Aware Calculations

## One-line Summary

An Azure-orchestrated agent workflow that enables humans and AI to co-author live, reusable, unit-aware calculations from natural language—with CalcsLive as the infrastructural engine powering both cloud/web and desktop/local systems.

## The Superpower

**Create a live, web-accessible, unit-aware calculation from natural language in under a minute.**

The result is not trapped in a chat session or a single workbook. It becomes a reusable CalcsLive article with its own URL, accessible across multiple modes (`edit`, `calculate`, `table`, `view`) and connectable to downstream systems like Excel, CAD, and workflow automation tools.

The deployed prototype is already integrated into `calcslive.com/agent` as a user-facing entrypoint, showing how this workflow can be embedded directly into the CalcsLive platform experience.

## Problem

AI can generate calculations quickly, but:

- pure AI output often lacks domain context and project-specific accuracy ("AI slop")
- generated content disappears after the chat session ends
- spreadsheets—despite their power—ignore units entirely, mixing inches, cm, liters, and kg/m³ without guardrails

Meanwhile, unit-aware calculations are essential for engineering, but creating them traditionally requires specialized tools or manual formula work.

## Solution: AI-Human Co-Authoring with CalcsLive Infrastructure

CalcsLive Agent combines three strengths:

| Component | Contribution |
|-----------|--------------|
| **Azure AI** | Speed, synthesis, natural-language understanding |
| **Human User** | Domain knowledge, project context, quality judgment |
| **CalcsLive** | Deterministic unit-aware execution, reusable article storage, web delivery |

The workflow is **AI-Human Co-Authoring**:

1. User describes a calculation in natural language.
2. Azure AI drafts a CalcsLive-compatible PQ script.
3. CalcsLive runs a stateless review, surfacing warnings and outputs.
4. Human refines the script iteratively—adding domain context, correcting units, adjusting logic.
5. Approved script is persisted as a reusable CalcsLive article.
6. The article becomes a live web asset, usable across multiple modes and connectable to multiple systems.

This is **not** AI generating a formula and walking away. It is a moderated workflow where human review ensures quality while AI provides speed—together creating artifacts that persist and interoperate.

## CalcsLive as Infrastructure

CalcsLive is the **infrastructural atomic unit-awareness carrier** in this architecture.

Once a calculation is created:

- it has its own URL and can be accessed directly on the web
- it supports multiple modes for different use cases:
  - `edit` for authoring
  - `calculate` for quick computation
  - `table` for a full interactive unit-aware app
  - `view` for read-only display
- it can be connected to downstream systems like Excel, CAD tools, and workflow engines

This means CalcsLive acts as a reusable source-of-truth layer that brings unit-awareness to any connected system—cloud or desktop, conventional app or AI agent.

## Excel as a Flagship Integration

Excel is the most powerful and widely used calculation tool in the world. It is the go-to environment for engineering, finance, and countless other domains. Our solution does not replace Excel—it **complements, revitalizes, and simplifies** Excel's calculations by adding **unit awareness and composability**.

### Forward workflow (CalcsLive → Excel)

- A reviewed CalcsLive article can be sent into Excel.
- Excel gains a structured PQ table with unit-aware behavior.
- User edits inputs in Excel; CalcsLive recalculates outputs reactively.
- Excel cell references can connect the CalcsLiverated table with the rest of the spreadsheet.

### Reverse workflow (Excel → CalcsLive)

- A compatible PQ table authored in Excel can be read back into the agent.
- The agent reviews it as a CalcsLive script.
- User refines and persists it as a new reusable live article.

This bi-directional bridge allows users to:

1. **Enhance** existing and new Excel documents with composable unit-aware calculations.
2. **Convert** Excel-authored calculation structures into reusable CalcsLive content accessible across the web.

Excel is one flagship integration. The same CalcsLive infrastructure can extend to CAD, n8n, and other systems.

## Win-Win-Win

This project creates value for three ecosystems:

| Ecosystem | Value |
|-----------|-------|
| **Azure** | Demonstrates Azure AI as a moderator/orchestrator in a practical engineering workflow |
| **CalcsLive** | Becomes the unit-aware infrastructure layer powering both cloud and desktop contexts |
| **Excel** | Gains bi-directional access to composable unit-aware live calculations, complementing its native strengths |

## Why It Matters

- **AI-Human Co-Authoring** replaces AI slop with quality-reviewed, context-aware calculations
- **Under-a-minute creation** makes live unit-aware calculations accessible to anyone
- **Reusable articles** ensure work persists beyond the chat session
- **Multi-mode delivery** lets one calculation serve multiple use cases
- **Infrastructure extensibility** means the same unit-awareness can flow to any connected system
- **Excel enhancement** brings unit awareness and composability to the world's most powerful spreadsheet tool

## Core Features

- Natural-language calculation generation
- Stateless script review with warnings and outputs
- Iterative AI-Human Co-Authoring during review
- Persistence as reusable CalcsLive articles
- Multiple article modes (`edit`, `calculate`, `table`, `view`)
- Excel bridge for bi-directional spreadsheet integration
- Reactive recalculation after Excel edits
- Reverse flow from Excel-authored tables to CalcsLive articles

## Microsoft Technologies Used

- Azure Container Apps for deployment
- Azure AI / Microsoft AI platform-backed agent orchestration
- Microsoft Agent Framework-aligned moderator architecture
- Azure MCP / MCP-oriented extensibility direction
- GitHub + VS Code development workflow

## Architecture Summary

The project uses a unified Streamlit moderator app as the main entrypoint.

- **Azure AI** moderates the AI-Human Co-Authoring workflow
- **CalcsLive** provides deterministic unit-aware execution and article storage
- **Excel Bridge** provides local bi-directional spreadsheet integration when available
- **Future systems** (CAD, n8n, etc.) can connect through the same CalcsLive infrastructure

The project also includes partial MCP proof through the Excel MCP wrapper and ODR exploration. Due to current platform constraints in the local ODR route, the live submission path uses the direct REST bridge for reliability while preserving the MCP-oriented extensibility story.

The architecture demonstrates interoperability between cloud/web agents and local/desktop execution surfaces.

## Best-Fit Categories

Primary:
- **Build AI Applications & Agents**

Strong secondary alignment:
- **Best Multi-Agent System**
- **Best Azure Integration**

## Differentiator

This is not "AI inside Excel" or "AI generating formulas."

It is an **AI-Human Co-Authoring workflow** where:

- the human brings domain knowledge and quality judgment
- the AI brings speed and synthesis
- CalcsLive provides deterministic unit-aware infrastructure

The result is reviewed, reusable, unit-aware calculations that persist as web assets and can power multiple systems—including Excel, where they complement and enhance the tool that millions already rely on.

## Known Limits / Honest Scope

- Cloud deployment does not automatically connect to a private local Excel bridge
- Full Excel MCP parity is not required for the working demo path
- Broader plugin-style downstream integrations (CAD, n8n) are future work

## What Reviewers Should See in the Demo

1. Generate and review a new calculation from natural language
2. Refine the script with domain-specific corrections (AI-Human Co-Authoring in action)
3. Create the article and show it accessible on the web in multiple modes
4. Send it to Excel
5. Change Excel inputs and show reactive recalculation
6. Read an Excel-authored table back into the app and persist it as a new article

## Proof Artifact

`deliverables/samples/3MMMT258D-23V (table).pdf`

This shows a CalcsLive article in table mode—created in under a minute through natural language + iterative review. The table mode alone is a fully functional unit-aware calculation app.
