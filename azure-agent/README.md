# CalcsLive Agent for Excel

AI Agent that orchestrates unit-aware calculations between Excel and CalcsLive using Azure AI Foundry and OpenAI Chat Completions tool calling.

## Prerequisites

1. **Azure AI Foundry** project with a model deployment (e.g., `grok-3-mini`) OR serverless inference endpoint
2. **Azure CLI** logged in (`az login`)
3. **Excel Bridge** running on localhost:8001
4. **Excel** open with a PQ table spreadsheet

## Quick Start

**Terminal 1 - Start the Excel Bridge:**
```cmd
cd c:\E3d\E3dProjs\2026\26009-calcslive-agent-for-maf\excel-bridge
python main.py
```

**Terminal 2 - Open Excel with the demo spreadsheet:**
- Open `.e3d\MS-AI-Hackathon-202603\ExampleCalc-01.xlsx`
- Ensure ArticleID is at C7 and PQ table is below

**Terminal 3 - Run the Agent:**
```cmd
cd c:\E3d\E3dProjs\2026\26009-calcslive-agent-for-maf\azure-agent
python agent.py
```

## Configuration

Create a `.env` file (or copy from `.env.example`):

```env
AZURE_AI_PROJECT_ENDPOINT=https://your-resource.services.ai.azure.com/api/projects/your-project
AZURE_AI_MODEL_DEPLOYMENT_NAME=grok-3-mini
EXCEL_BRIDGE_URL=http://localhost:8001

# Optional serverless inference mode (uses these instead of project endpoint)
# AZURE_AI_INFERENCE_ENDPOINT=https://your-endpoint.models.ai.azure.com/chat/completions
# AZURE_AI_INFERENCE_KEY=your_key
# AZURE_AI_INFERENCE_MODEL=grok-3-mini

# Optional CalcsLive authentication
# CALCSLIVE_API_URL=https://calcslive.com/api/v1
# CALCSLIVE_API_KEY=your_api_key
```

## Usage

### Interactive Mode (default)

```cmd
python agent.py
```

Try these commands:
- "Check Excel connection"
- "Read the PQ table from Excel"
- "Calculate the values"
- "Run the full calculation workflow"

### Local Demo Mode (no Azure)

```cmd
python agent.py --demo
```

This runs the workflow without Azure AI to test the Excel bridge:
1. Check Excel health
2. Read PQ table
3. Attempt CalcsLive calculation (or use dummy values)
4. Write results back

## Agent Tools

The agent has access to these function tools:

| Tool | Description |
|------|-------------|
| `get_excel_health` | Check Excel connection status |
| `read_excel_pq_table` | Read PQ table with inputs/outputs |
| `write_excel_results` | Write calculated values to Excel |
| `calculate_with_calcslive` | Run calculation via CalcsLive API |

## Architecture

```
User Request
     │
     ▼
┌─────────────────────────────────────┐
│  CalcsLive Agent (Azure AI Foundry) │
│  - Uses Chat Completions API        │
│  - Model: grok-3-mini               │
│  - Function calling for tools       │
└─────────────┬───────────────────────┘
              │
     ┌────────┴────────┐
     ▼                 ▼
┌──────────┐    ┌────────────┐
│  Excel   │    │ CalcsLive  │
│  Bridge  │    │   API      │
│ :8001    │    │            │
└────┬─────┘    └────────────┘
     │
     ▼
┌──────────┐
│  Excel   │
│  2016    │
└──────────┘
```

## Technical Details

- **SDK**: Azure AI Projects SDK (`azure-ai-projects`) or serverless OpenAI-compatible endpoint
- **Auth**: DefaultAzureCredential (Azure CLI, Managed Identity, etc.)
- **API**: OpenAI Chat Completions with tool calling
- **Model**: Any model deployed in Azure AI Foundry (grok-3-mini, gpt-4o-mini, etc.)
