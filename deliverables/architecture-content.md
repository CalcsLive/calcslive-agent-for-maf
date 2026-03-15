# Architecture Diagram Content

Use this as the source text for the final submission architecture diagram.

## Hackathon Alignment

This diagram must illustrate use of:
- **Azure AI Foundry** (formerly Azure AI Studio) - Model deployment and inference
- **Microsoft Agent Framework** - Agent orchestration pattern
- **Azure MCP** - Tool integration and extensibility
- **GitHub Copilot** - Development workflow
- **Azure Services** - Container Apps, AI inference endpoints

## Diagram Title

**CalcsLive Agent: Azure AI Foundry-Powered Agent for Unit-Aware Calculations**

## Layout: Left-to-Right Flow with 5 Sections

### Section 1 — Development Layer (Left Edge)

Box with GitHub/VS Code icon:
- `GitHub + VS Code`
- subtitle: `GitHub Copilot-assisted development`

Callout:
- `Code, test, deploy workflow`

### Section 2 — Human + Agent UI

Box 1:
- `Human User`
- subtitle: `Domain knowledge + review`

Box 2:
- `CalcsLive Agent UI`
- subtitle: `Streamlit + Agent orchestration`

Callout:
- `AI-Human Co-Authoring reduces AI slop`

### Section 3 — Azure AI Layer (Center - Highlight This)

Main container box with Azure logo:
- `Azure AI Foundry`

Inside as sub-boxes:
- `Azure AI Inference Endpoint`
- `Models-as-a-Service (GPT-4 / Grok)`
- `Agent Orchestration (MAF pattern)`

Below or connected:
- `Azure MCP Integration`
- subtitle: `Tool definitions + extensibility`

Arrow labels into Azure layer:
- `Natural language prompt`
- `Review feedback`

Arrow labels out:
- `Drafted calculation`
- `Refined outputs`

### Section 4 — CalcsLive Platform

Main box:
- `CalcsLive API`

Inside as stacked items:
- `Unit-aware calculation engine`
- `67+ unit categories`
- `Stateless script execution`
- `Article persistence`

Mode list:
- `edit | calculate | table | view`

Callout:
- `CalcsLive article = reusable calculation asset`

### Section 5 — Connected Systems (Right Edge)

Top box:
- `Excel Bridge`
- subtitle: `Local REST + COM automation`

Below:
- `Excel Desktop`
- subtitle: `Bi-directional workflow`

Dashed future boxes:
- `CAD systems`
- `n8n workflows`
- `Other MCP clients`

### Section 6 — Deployment Layer (Bottom)

Horizontal bar:
- `Azure Container Apps`
- subtitle: `Production deployment`

## Data Flow Arrows

### Main Creation Flow
```
Human User → CalcsLive Agent UI → Azure AI Foundry → CalcsLive API
```

### Return Flow
```
CalcsLive API → Azure AI Foundry → CalcsLive Agent UI → Human User
```

### Excel Forward Flow
```
CalcsLive API → Azure AI Foundry (orchestrate) → Excel Bridge → Excel Desktop
```
Label: `Load calculation to Excel`

### Excel Reverse Flow
```
Excel Desktop → Excel Bridge → Azure AI Foundry (orchestrate) → CalcsLive API
```
Label: `Create article from Excel`

### MCP Tool Calls (show as dotted lines)
```
Azure AI Foundry ←→ CalcsLive MCP Tools
Azure AI Foundry ←→ Excel MCP Tools
```

## Microsoft Technology Callouts

Place these as badges or highlighted labels:

1. **Azure AI Foundry** - Central orchestration hub
2. **Azure AI Inference** - Model deployment endpoint
3. **Microsoft Agent Framework** - Agent pattern implementation
4. **Azure MCP** - Tool integration layer
5. **Azure Container Apps** - Production hosting
6. **GitHub Copilot** - Development acceleration

## Numbered Workflow Overlay

1. Developer builds agent with GitHub Copilot assistance
2. Human describes calculation in natural language
3. Azure AI Foundry drafts CalcsLive-compatible script
4. CalcsLive executes stateless review with unit validation
5. Human refines with domain knowledge (AI-Human Co-Authoring)
6. Approved script persists as reusable CalcsLive article
7. Article accessible via web modes or sent to Excel
8. Excel changes trigger reactive recalculation via Azure orchestration

## Visual Emphasis

**Must emphasize (hackathon requirement):**
1. Azure AI Foundry as the central brain
2. Microsoft Agent Framework pattern
3. Azure MCP for tool integration
4. Azure Container Apps for deployment
5. GitHub + Copilot for development

**Secondary emphasis:**
1. AI-Human Co-Authoring loop
2. CalcsLive as unit-aware infrastructure
3. Excel bi-directional integration
4. Future extensibility (dashed)

## Color Scheme Suggestion

- Azure blue (#0078D4) for all Microsoft/Azure components
- Green (#107C10) for human/review elements
- Purple (#5C2D91) for CalcsLive platform
- Gray for future/dashed elements

## Short Caption

**An Azure AI Foundry-powered agent using Microsoft Agent Framework patterns to orchestrate AI-Human Co-Authoring of unit-aware calculations. CalcsLive provides deterministic execution while Azure MCP enables tool extensibility. Deployed on Azure Container Apps with GitHub Copilot-assisted development.**

## Architecture Box Sizes (Relative)

- Azure AI Foundry: LARGEST (central, emphasized)
- CalcsLive API: Medium-large
- Human/UI: Medium
- Excel Bridge/Desktop: Medium
- GitHub/Development: Small
- Azure Container Apps: Thin horizontal bar at bottom
