# Architecture Diagram - Excalidraw Layout Spec

This file gives a concrete layout for building the final architecture diagram quickly in Excalidraw.

## Canvas

- Canvas size: `1600 x 900`
- Orientation: landscape
- Flow direction: left to right
- Style: clean, flat, readable, low text density

## Top Title

Place centered at top:

`CalcsLive Agent: Azure-moderated Human + AI Workflow for Reusable Unit-Aware Calculations`

Suggested position:
- x: 800
- y: 40

## Main Layout

Use 4 columns with evenly spaced groups.

### Column 1 — Human + App

#### Box A1
- Label:
  - `Human User`
  - `Project context + domain review`
- Position: x `120`, y `220`
- Size: w `240`, h `90`
- Color: light blue

#### Box A2
- Label:
  - `Unified CalcsLive Agent UI`
  - `Review-first creation + Excel bridge when available`
- Position: x `120`, y `370`
- Size: w `260`, h `110`
- Color: light blue

#### Callout C1
- Text:
  - `AI-Human Co-Authoring improves quality and reduces AI slop`
- Position: x `70`, y `520`
- Size: w `320`, h `70`
- Style: note/callout, pale yellow

### Column 2 — Azure AI Moderation

#### Box B1
- Label:
  - `Azure AI Moderator / Orchestrator`
- Position: x `470`, y `260`
- Size: w `280`, h `220`
- Color: medium blue

Inside B1, place small text lines:
- `Natural-language calculation design`
- `Script review orchestration`
- `Create article orchestration`
- `Bridge coordination`

### Column 3 — CalcsLive Infrastructure

#### Box C1
- Label:
  - `CalcsLive Platform`
- Position: x `860`, y `220`
- Size: w `300`, h `260`
- Color: green

Inside C1, stacked items:
- `Unit-aware engine`
- `67+ unit categories`
- `Stateless script review`
- `Persistent article store`
- `Web delivery modes`

#### Mode pill / sublabel
- Text:
  - `edit | calculate | table | view`
- Position: x `900`, y `500`
- Size: w `220`, h `40`
- Color: pale green

#### Callout C2
- Text:
  - `CalcsLive article = reusable source-of-truth calculation asset`
- Position: x `850`, y `570`
- Size: w `320`, h `70`
- Style: note/callout, pale yellow

### Column 4 — Connected Systems

#### Box D1
- Label:
  - `Excel Bridge`
  - `Local COM + REST bridge`
- Position: x `1280`, y `210`
- Size: w `220`, h `90`
- Color: orange

#### Box D2
- Label:
  - `Excel Desktop`
  - `Bi-directional spreadsheet workflow`
- Position: x `1280`, y `360`
- Size: w `220`, h `100`
- Color: orange

#### Future dashed boxes

##### Box D3
- Label: `CAD`
- Position: x `1260`, y `540`
- Size: w `90`, h `55`
- Dashed border
- Color: gray

##### Box D4
- Label: `n8n`
- Position: x `1370`, y `540`
- Size: w `90`, h `55`
- Dashed border
- Color: gray

##### Box D5
- Label: `Other systems`
- Position: x `1315`, y `620`
- Size: w `140`, h `60`
- Dashed border
- Color: gray

#### Callout C3
- Text:
  - `CalcsLive acts as the infrastructural atomic unit-awareness carrier`
- Position: x `1220`, y `710`
- Size: w `320`, h `70`
- Style: note/callout, pale yellow

## Required Arrows

### Main human + AI loop

1. `Human User -> Unified CalcsLive Agent UI`
   - label: `Natural-language request`

2. `Unified CalcsLive Agent UI -> Azure AI Moderator / Orchestrator`
   - label: `Prompt + review feedback`

3. `Azure AI Moderator / Orchestrator -> CalcsLive Platform`
   - label: `run_script / create_article`

4. `CalcsLive Platform -> Azure AI Moderator / Orchestrator`
   - label: `Warnings + outputs + article`

5. `Azure AI Moderator / Orchestrator -> Unified CalcsLive Agent UI`
   - label: `Reviewed script + approval flow`

### Excel forward path

6. `Azure AI Moderator / Orchestrator -> Excel Bridge`
   - label: `Send Calc to Excel`

7. `Excel Bridge -> Excel Desktop`
   - label: `Populate / update sheet`

### Excel reverse path

8. `Excel Desktop -> Excel Bridge`
   - label: `Edited PQ table`

9. `Excel Bridge -> Azure AI Moderator / Orchestrator`
   - label: `Get Calc from Excel`

### Future extensibility path

10. Dashed arrows from `CalcsLive Platform` to:
    - `CAD`
    - `n8n`
    - `Other systems`

## Optional Numbered Badges

Place small circles near arrows:

1. User describes a calc in natural language
2. Azure AI generates and reviews a script
3. Human refines with project context
4. CalcsLive persists a reusable article
5. Article powers Excel or direct web use
6. Excel can also originate a new article through review

## Minimal Legend (optional)

Bottom left small legend:

- Blue = user + moderation
- Green = CalcsLive infrastructure
- Orange = Excel integration
- Dashed = future extensibility

## Fast Build Advice

- Build the boxes first
- Add arrows second
- Add 3 callouts last
- Do not over-style shadows or icons unless time remains
