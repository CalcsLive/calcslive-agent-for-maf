# Terminology Draft

This glossary is intended to help with submission writing, demo narration, architecture callouts, and judge readability.

## Microsoft / Azure / Agent Background

### Azure

Microsoft's cloud platform used here for hosting and AI-backed orchestration.

### Azure Container Apps (ACA)

The Azure service used to deploy the unified CalcsLive Agent app for cloud/browser access.

### Azure AI

The Microsoft AI service layer used to power the agent's orchestration and tool-calling behavior.

### Microsoft Foundry

Microsoft's purpose-built AI platform referenced by the hackathon as a core “hero technology” category.

### MAF (Microsoft Agent Framework)

The agent-oriented design pattern / framework direction used as the architectural basis for the moderator-style orchestrator in this project.

### Moderator Agent

The Azure-hosted agent role that coordinates tools, user review, CalcsLive, and Excel rather than acting as a single monolithic calculator.

### Tool Calling

The pattern where the agent invokes external functions/APIs such as CalcsLive endpoints or the Excel bridge rather than relying only on free-form text generation.

### MCP (Model Context Protocol)

A protocol for exposing tools and external capabilities to AI systems in a consistent way. In this project, MCP is part of the extensibility narrative and partially implemented as proof.

### Azure MCP

The Microsoft/Azure framing around MCP-connected systems and tool interoperability.

### ODR (Windows On-Device Registry)

The Windows mechanism explored for registering MCP servers locally. Used here as a proof path, although the final working demo uses the direct bridge route instead.

### GitHub Copilot / GitHub Development Workflow

The coding workflow expectation in the hackathon context: public GitHub repository, development in VS Code or Visual Studio, and AI-assisted development practices.

## Project Core Terms

### CalcsLive

The unit-aware calculation platform that acts as the deterministic calculation engine and reusable article store.

### CalcsLive Article

A persisted live calculation asset in CalcsLive. It can be accessed through multiple delivery modes and reused across systems.

### CalcsLive Modes

The main ways a created calculation can be used on the web:

- `edit`
- `calculate`
- `table`
- `view`

### Unit-awareness

The ability to understand, validate, and convert between units consistently within a calculation workflow.

### Unit-aware Infrastructure

The idea that unit conversion and unit-consistent execution are centralized in CalcsLive instead of being reimplemented inside every app.

### Atomic Unit-awareness Carrier

A project-specific phrase describing CalcsLive as the reusable infrastructural unit-awareness layer that can empower multiple downstream systems.

### PQ (Physical Quantity)

A quantity defined by:

- symbol
- value
- unit
- optional description
- optional expression

Examples:
- length
- mass
- stress
- velocity

### PQ Table

A structured table of physical quantities used by the bridge and the agent workflow. In Excel, the bridge expects semantic columns such as:

- `Description`
- `Symbol`
- `Expression`
- `Value`
- `Unit`

### Stateless Script Review / `run_script`

The non-persistent execution step where a PQ script is validated and run before turning it into a saved article. This is the core review stage.

### Persistent Article Creation / `create_article`

The step where an approved reviewed script becomes a reusable CalcsLive article.

### Calculation Table

The user-facing reviewed representation of a PQ-based calculation showing inputs, outputs, expressions, values, and units.

### AI-Human Co-Authoring

The preferred project term for the core workflow. The AI drafts and accelerates calculation creation; the human refines with domain knowledge, project context, and quality judgment.

### AI Slop

Low-quality AI-generated content created without enough review, context, or domain grounding. This project explicitly aims to reduce it through AI-Human Co-Authoring.

### Human Quality Gate

The review stage where the user validates warnings, units, descriptions, expressions, and overall fit before persistence.

## Excel / Bridge Terms

### Excel Bridge

The local COM + REST bridge that allows the unified app to interact with the active Excel workbook.

### Bridge to/from Excel

The project phrase for bi-directional interoperability between CalcsLive and Excel:

- send a reviewed/persisted calc into Excel
- read a compatible Excel-authored table back into the app

### CalcsLiverated

A project-specific informal term meaning that spreadsheet content has been enhanced or powered by CalcsLive unit-aware logic.

### Reactive Recalculation

The closed-loop behavior where Excel edits trigger the bridge to reread PQ data, call CalcsLive, and write updated outputs back.

### Composable Unit-aware Calculations

The idea that a CalcsLiverated PQ table can connect to the rest of an Excel document through normal cell references, allowing unit-aware logic to participate in larger spreadsheet models.

## System / Architecture Terms

### Unified App

The single Streamlit app entrypoint that works in both cloud-only and local-with-Excel modes, enabling Excel features only when the bridge is available.

### Cloud/Web Context

The hosted/browser-accessible environment where users can create and review calculations even without local Excel access.

### Desktop/Local Context

The environment where local tools such as Excel participate through the bridge API.

### Cross-context Agentic Interoperability

The ability of the solution to work across both cloud/web and desktop/local execution surfaces under the same moderated workflow.

### Reusable Source-of-Truth Calculation Asset

The idea that a created CalcsLive article becomes the authoritative reusable calculation definition instead of leaving calculation logic trapped in one chat or one workbook.

### Downstream System

A tool or environment that can be powered by CalcsLive-created calculation assets. Excel is the flagship example; future examples include CAD, n8n, and others.

## Messaging Phrases Worth Reusing

These phrases are useful for demo narration and submission writing.

- `AI-Human Co-Authoring instead of AI slop`
- `CalcsLive as reusable unit-aware infrastructure`
- `Azure AI moderates the workflow`
- `Excel as a bi-directional downstream integration`
- `Create a live reusable calculation in under a minute`
- `Revitalize and simplify Excel with composable unit-aware calculations`
- `Cloud/web and desktop/local agent interoperability`
