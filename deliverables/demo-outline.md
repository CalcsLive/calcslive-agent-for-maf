# Final Demo Outline

## Target Length

2 minutes maximum

## Goal

Show a clear, working story that combines:

- natural-language live calculation creation
- human-in-the-loop refinement
- persistence into reusable CalcsLive articles
- Excel interoperability as a flagship downstream integration
- reactive unit-aware spreadsheet recalculation

## Recommended Demo Flow

### 0:00 - 0:15 | Problem framing

Say:

"CalcsLive Agent lets a user create a live reusable unit-aware calculation from natural language, with human review & refinement to keep quality high. Excel is one powerful downstream integration of that infrastructure."

Show:
- unified app home screen

### 0:15 - 0:35 | Review-first calculation creation

Action:
- paste a sample prompt: 
  - please calculate mass of a solid cylinder
  - Please change to a topless cylinder with equal thickness.  

Show:
- reviewed CalcsLive script
- generated title/description
- calculation table
- warnings or category metadata if present

Say:

"The agent does not blindly persist. It runs a stateless review first so the user can refine the script with project context and domain knowledge before saving it."

### 0:35 - 0:50 | Persist article

Action:
- click `Create Article`

Show:
- created article summary
- direct links for edit / calculate / table / view

Say:

"Once approved, the reviewed script becomes a reusable CalcsLive article. It is now a live web-native calculation asset, not just a generated formula."

### 0:50 - 1:10 | Send to Excel

Action:
- open `Bridge to/from Excel`
- click `Send Calc to Excel`

Show:
- Excel populated with metadata block and PQ table

Say:

"The same reusable calculation is now bridged into Excel as a structured, unit-aware worksheet. This revitalizes Excel with composable unit-aware calculations."

### 1:10 - 1:35 | Reactive Excel update

Action:
- edit one or more Excel inputs

Show:
- output value updates automatically

Say:

"When spreadsheet values change, the bridge reads the updated PQ table, calls CalcsLive, and writes the new results back into Excel. Because Excel cell references can connect to the PQ table, the calculation becomes composable inside the spreadsheet."

### 1:35 - 1:55 | Reverse flow from Excel

Action:
- show a compatible Excel-authored table
- click `Get Calc from Excel`

Show:
- reviewed script appears in the app

Say:

"The bridge also works in reverse. A compatible Excel table can be read, converted, reviewed, refined, and persisted as a reusable CalcsLive calculation."

### 1:55 - 2:00 | Close

Say:

"This makes CalcsLive a reusable unit-aware calculation infrastructure layer, with Azure AI moderating the workflow across both cloud/web and desktop/local contexts."

## Supporting Visual Assets

- architecture diagram
- workflow diagram
- unified app screenshot
- Excel before/after screenshots
- optional GIF of reactive recalculation
