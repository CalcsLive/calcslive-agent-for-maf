# Final Architecture Diagram Content

Use this as the source text for the final submission architecture diagram.

## Diagram Goal

Show that:

- Azure AI moderates the workflow
- human review improves quality and reduces slop/hallucination
- CalcsLive is the reusable unit-aware infrastructure layer
- Excel is one downstream system enhanced by that infrastructure
- the solution can interoperate across both cloud/web and desktop/local agent contexts

## Recommended Title

**CalcsLive Agent: Azure-moderated Human + AI Workflow for Reusable Unit-Aware Calculations**

## Recommended Layout

Use a left-to-right flow with 4 vertical sections.

### Section 1 — Human + Unified App

Box 1:
- `Human User`
- small subtitle: `Project context + domain review`

Box 2:
- `Unified CalcsLive Agent UI`
- small subtitle: `Review-first creation + Excel bridge when available`

Callout near these boxes:
- `AI-Human Co-Authoring improves quality and reduces AI slop`

### Section 2 — Azure AI Moderation Layer

Main box:
- `Azure AI Moderator / Orchestrator`

Inside or below as smaller sub-boxes:
- `Natural-language calculation design`
- `Script review orchestration`
- `Create article orchestration`
- `Bridge coordination`

Arrow labels from UI to Azure layer:
- `Prompt`
- `Review feedback`
- `Approval`

Arrow labels back to UI:
- `Reviewed script`
- `Warnings + outputs`
- `Created article`

### Section 3 — CalcsLive Infrastructure Layer

Main central box:
- `CalcsLive Platform`

Inside as smaller stacked items:
- `Unit-aware engine`
- `67+ unit categories`
- `Stateless script review`
- `Persistent article store`
- `Web delivery modes`

Small horizontal mode list beneath:
- `edit | calculate | table | view`

Key callout:
- `CalcsLive article = reusable source-of-truth calculation asset`

### Section 4 — Connected Systems

Top box:
- `Excel Bridge`
- small subtitle: `Local COM + REST bridge`

Below it:
- `Excel Desktop`
- small subtitle: `Bi-directional spreadsheet workflow`

To the side or below as future boxes with dashed outline:
- `CAD`
- `n8n`
- `Other systems`

Callout:
- `CalcsLive acts as the infrastructural atomic unit-awareness carrier`

## Required Arrows

### Main creation workflow

`Human User -> Unified CalcsLive Agent UI -> Azure AI Moderator / Orchestrator -> CalcsLive Platform`

Return path:

`CalcsLive Platform -> Azure AI Moderator / Orchestrator -> Unified CalcsLive Agent UI -> Human User`

### Excel forward workflow

`CalcsLive Platform -> Azure AI Moderator / Orchestrator -> Excel Bridge -> Excel Desktop`

Label:
- `Send Calc to Excel`

### Excel reverse workflow

`Excel Desktop -> Excel Bridge -> Azure AI Moderator / Orchestrator -> CalcsLive Platform`

Label:
- `Get Calc from Excel`

### Future extensibility workflow

Dashed arrows from `CalcsLive Platform` to:
- `CAD`
- `n8n`
- `Other systems`

## Numbered Overlay (optional)

1. User describes a calculation goal in natural language
2. Azure AI generates and reviews a CalcsLive script
3. Human refines the reviewed script with domain context
4. Approved script is persisted as a reusable CalcsLive article
5. Article is used directly on the web or sent into Excel
6. Excel can also send a compatible calculation table back for review and persistence

## Short Caption

**Azure AI moderates an AI-Human Co-Authoring workflow that turns natural-language requests into reviewed, reusable, unit-aware CalcsLive calculation assets. Those assets can then power both cloud/web and desktop/local experiences, with Excel shown here as a flagship bi-directional integration.**

## Visual Priorities

If time is tight, prioritize showing:

1. Human review loop
2. Azure moderation
3. CalcsLive as infrastructure/source-of-truth
4. Excel bi-directional integration
5. future system extensibility as dashed boxes

## What Not To Overcomplicate

- Do not overload with low-level implementation details
- Do not emphasize ODR limitations in the primary submission diagram
- Do not make Excel the center of the architecture
- Do not frame this as only an Excel plugin
