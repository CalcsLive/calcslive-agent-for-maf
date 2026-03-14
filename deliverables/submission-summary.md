# Submission Summary Draft

## Project Name

CalcsLive Agent - Unit-aware Calculation Carrier for Excel in MAF

## One-line Summary

An Azure-orchestrated moderator agent that turns spreadsheets into a bi-directional, unit-aware engineering workflow using CalcsLive and Excel.

## Problem

Excel is one of the most common tools for engineering and technical calculations, but it is fundamentally unit-blind. Users can easily mix inches, millimeters, kilograms, liters, and custom engineering units in the same spreadsheet without any native guardrails. This creates avoidable risk, rework, and calculation errors.

At the same time, many technical calculations begin in one place and need to move across multiple contexts: reviewed by a user, persisted as reusable logic, loaded into a spreadsheet, edited interactively, and recalculated reliably.

## Solution

CalcsLive Agent makes CalcsLive the unit-aware calculation engine behind a moderator-style AI workflow.

The app supports an **AI-Human Co-Authoring** lifecycle:

1. A user describes a calculation in natural language.
2. The agent generates and reviews a CalcsLive-compatible PQ script.
3. The user validates warnings, units, and expressions before persistence.
4. The reviewed script is persisted as a reusable CalcsLive article.
5. When Excel is available, the same article can be sent into Excel, edited there, and recalculated reactively.

The system also supports the reverse direction:

- a compatible Excel table can be read back into the agent,
- converted into a reviewed CalcsLive script,
- and persisted as a new reusable article.

This creates a two-way bridge between spreadsheet work and reusable, unit-aware calculation definitions.

It also demonstrates a broader systems pattern: a practical agentic architecture that interoperates across both **cloud/web** and **desktop/local** environments.

- Azure AI moderates the workflow in the web/cloud layer
- CalcsLive provides the reusable unit-aware infrastructure layer
- Excel participates as a desktop/local execution surface through the bridge API
- partial MCP implementation provides proof toward broader agent-to-agent and tool interoperability

## Why It Matters

- reduces spreadsheet risk from mixed-unit calculations
- allows AI-Human Co-Authoring before persistence
- makes calculations reusable across interfaces instead of trapped in one workbook
- demonstrates how AI agents can moderate engineering workflows rather than just generate text
- shows how the same solution can operate across cloud/web and desktop/local agent contexts

## Core Features

- natural-language calculation generation
- stateless script review as part of AI-Human Co-Authoring
- persistence of reviewed scripts as CalcsLive articles
- multiple article modes (`edit`, `calculate`, `table`, `view`)
- Excel bridge for loading structured calculation tables into spreadsheets
- reactive recalculation after Excel edits
- reverse flow from Excel-authored PQ table back into CalcsLive review/create workflow

## Microsoft Technologies Used

- Azure-hosted deployment via Azure Container Apps
- Azure AI / Microsoft AI platform-backed agent orchestration in the app
- Microsoft Agent Framework-aligned moderator/orchestration architecture
- Azure MCP / MCP-oriented extensibility story through toolized local and API integrations
- GitHub + VS Code development workflow

## Architecture Summary

The project uses a unified Streamlit moderator app as the main user entrypoint.

- In cloud mode, the app supports review and persistence of CalcsLive scripts.
- In local mode, the same app detects the Excel bridge and enables bi-directional spreadsheet workflows.
- CalcsLive acts as the source-of-truth unit-aware engine and article store.
- Excel acts as a familiar interactive workspace for engineering calculations.
- Azure AI serves as the moderation/orchestration layer across both web and desktop-connected workflows.
- The architecture demonstrates interoperability between cloud/web agents and local/desktop execution surfaces.

## Best-Fit Categories

Primary:
- Build AI Applications & Agents

Strong secondary alignment:
- Best Multi-Agent System
- Best Azure Integration

## Differentiator

This project is not just “AI inside Excel.” It demonstrates a moderator-agent workflow where reviewed, unit-aware calculation logic can move between CalcsLive and Excel in both directions. The result is a system-level unit-awareness story for spreadsheets with reusable calculation definitions.

## Known Limits / Honest Scope

- cloud deployment does not automatically connect to a private local Excel bridge
- full Excel MCP parity is not required for the working demo path
- some advanced persistence/edit workflows are intentionally deferred after hackathon

## What Reviewers Should See in the Demo

1. Generate and review a new calculation
2. Create the article
3. Send it to Excel
4. Change Excel inputs and show reactive recalculation
5. Read an Excel-authored table back into the app and persist it as a new article
