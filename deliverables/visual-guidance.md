# Visual Guidance

## Recommended Order

1. Final architecture diagram
2. Workflow flowcharts
3. Screenshots
4. GIFs

## Why This Order

- the architecture diagram anchors the project story
- the workflow flowcharts explain how the system is used
- screenshots and GIFs then act as proof for those visuals

## Architecture Diagram Advice

- keep it clean and readable
- do not make Excel the center of the picture
- make CalcsLive the reusable infrastructure layer
- show Azure AI as moderator/orchestrator
- show human review loop clearly
- show Excel as one downstream bridge integration

## Workflow Visual Advice

- use separate simple flowcharts instead of one giant process diagram
- one flowchart per workflow is easier for judges to understand
- add one sentence under each flowchart saying why it matters

## Screenshot Plan

Suggested screenshot set:

1. Unified app main screen with sample prompts and help links
2. Reviewed CalcsLive Script table
3. Created article section with mode links
4. Excel loaded PQ table with row numbers and metadata block
5. Excel reactive recalculation after changing an input
6. Excel-authored table pulled back into reviewed script flow

## GIF Plan

If you make GIFs, the best ones are:

1. natural-language prompt -> reviewed script appears
2. create article -> mode links appear
3. send calc to Excel -> Excel fills in
4. change Excel input -> output updates

Keep GIFs short, focused, and silent-friendly.
