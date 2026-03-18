# Developer Setup Guide - CalcsLive Agent with Excel

This guide covers what's needed to clone the repo and get the CalcsLive Agent working with Excel on your desktop.

## Quick Summary

| Component | Required? | What You Need | Cost |
|-----------|-----------|---------------|------|
| **Windows + Excel** | Yes (for Excel features) | Excel 2016+ installed | Your existing license |
| **Python** | Yes | Python 3.9+ | Free |
| **Azure AI** | Yes | Azure subscription + AI endpoint | Pay-as-you-go (~$0.01-0.03/request) |
| **CalcsLive API** | Yes | API key from calcslive.com | Free tier available |
| **Tunnel Service** | Only for cloud→local Excel | ngrok, Cloudflare Tunnel, etc. | Free tiers available |

## Architecture Context

### Local-Only Mode (Simplest)
```
┌─────────────────────────────────────────────────────────────┐
│  Your Windows PC                                            │
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │ Streamlit App   │◄──►│ Excel Bridge    │                 │
│  │ localhost:8501  │    │ localhost:8001  │                 │
│  └────────┬────────┘    └────────┬────────┘                 │
│           │                      │                          │
│           │                      ▼                          │
│           │             ┌─────────────────┐                 │
│           │             │ Excel Desktop   │                 │
│           │             └─────────────────┘                 │
└───────────┼─────────────────────────────────────────────────┘
            │
            ▼ (HTTPS)
┌───────────────────────┐    ┌───────────────────────┐
│ Azure AI Endpoint     │    │ CalcsLive API         │
│ (LLM orchestration)   │    │ (Unit-aware calcs)    │
└───────────────────────┘    └───────────────────────┘
```

**This is the recommended path for developers wanting Excel features.**

### Cloud + Local Excel Mode (Current Limitation)
```
┌─────────────────────────────────────────────────────────────┐
│  Azure Container Apps                                       │
│  ┌─────────────────┐                                        │
│  │ Streamlit App   │ ──── Can't reach localhost:8001 ──X    │
│  └─────────────────┘                                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Your Windows PC                                            │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │ Tunnel Service  │◄──►│ Excel Bridge    │◄──►│ Excel │    │
│  │ (ngrok, etc.)   │    │ localhost:8001  │                 │
│  └─────────────────┘    └─────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

**The container runs in Azure, so it cannot access your local Excel bridge without a tunnel.**

---

## Step-by-Step Setup

### 1. Clone the Repository

```bash
git clone https://github.com/AgoraDesign/calcslive-agent-for-maf.git
cd calcslive-agent-for-maf
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r azure-agent/requirements.txt
pip install -r excel-bridge/requirements.txt
```

### 3. Get Azure AI Access

You need an Azure AI endpoint for the LLM orchestration (the "agent" part).

**Option A: Azure OpenAI Service (Recommended)**
1. Create Azure account at https://azure.microsoft.com
2. Create an Azure OpenAI resource in Azure Portal
3. Deploy a model (e.g., `gpt-4o`, `gpt-4o-mini`)
4. Get your endpoint URL and API key from the resource

**Option B: Azure AI Foundry**
1. Go to https://ai.azure.com
2. Create a project
3. Deploy a model
4. Get endpoint and key

**Cost estimate**: ~$0.01-0.03 per agent interaction (depends on model and conversation length)

### 4. Get CalcsLive API Key

1. Create account at https://www.calcslive.com
2. Go to Settings → API Keys
3. Generate a new API key

**Cost**: Free tier includes generous limits for development

### 5. Configure Environment

Create `azure-agent/.env`:

```env
# Azure AI (pick one approach)
AZURE_AI_INFERENCE_ENDPOINT=https://your-resource.openai.azure.com
AZURE_AI_INFERENCE_KEY=your_azure_ai_key

# CalcsLive
CALCSLIVE_API_KEY=your_calcslive_api_key

# Optional: Use local CalcsLive API for development
# CALCSLIVE_API_URL=http://localhost:3000/api
```

### 6. Start the Services

**Terminal 1 - Excel Bridge:**
```bash
cd excel-bridge
python main.py
```
Should show: `Uvicorn running on http://127.0.0.1:8001`

**Terminal 2 - Streamlit App:**
```bash
cd azure-agent
python -m streamlit run app.py
```
Should open browser at `http://localhost:8501`

### 7. Test the Setup

1. Open Excel with a blank workbook
2. In the Streamlit app, check the sidebar shows "Excel bridge available"
3. Try a prompt: "Calculate the mass of a steel sphere"
4. After review, click "Create Article" then "Send Calc to Excel"

---

## Cloud Deployment with Local Excel (Advanced)

If you want to use the Azure-hosted app with your local Excel, you need a tunnel.

### Using ngrok

```bash
# Install ngrok
# Windows: winget install ngrok

# Start Excel bridge
python excel-bridge/main.py

# In another terminal, expose it
ngrok http 8001
```

ngrok will give you a public URL like `https://abc123.ngrok.io`

Then you'd need to configure the cloud app to use that URL instead of `localhost:8001`. Currently this requires modifying `EXCEL_BRIDGE_URL` in the code.

### The Friction Problem

This tunnel approach has friction:
1. Extra software to install (ngrok)
2. URL changes each session (unless paid tier)
3. Security considerations (exposing local service)
4. Configuration complexity

---

## Future: Nuxt 3 Client-Side Architecture

A Nuxt 3 (or similar client-side) implementation could solve the tunnel problem:

```
┌─────────────────────────────────────────────────────────────┐
│  User's Browser (runs on their PC)                          │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Nuxt 3 App (client-side JavaScript)                 │    │
│  │                                                     │    │
│  │ - Can call localhost:8001 (Excel Bridge) ✓          │    │
│  │ - Can call Azure AI (via server proxy or direct)    │    │
│  │ - Can call CalcsLive API                            │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

**Why this works:**
- The browser runs on the user's machine
- JavaScript in the browser CAN make requests to `localhost`
- No tunnel needed - the client IS local

**Implementation considerations:**
- Azure AI calls may need CORS handling or server proxy
- CalcsLive API calls work directly (CORS enabled)
- Excel bridge calls work directly from browser
- Static hosting possible (Vercel, Netlify, Azure Static Web Apps)

---

## Troubleshooting

### "Excel bridge not available"
- Ensure Excel is open with a workbook
- Check `python excel-bridge/main.py` is running
- Verify http://localhost:8001/excel/health returns success

### "Azure AI connection failed"
- Verify endpoint URL format (should end in `.openai.azure.com`)
- Check API key is correct
- Ensure model is deployed in Azure

### "CalcsLive API error"
- Verify API key is valid
- Check https://www.calcslive.com is accessible
- Try the free tier limits haven't been exceeded

### Excel COM errors on Windows
- Run as administrator if needed
- Ensure no other COM automation is blocking Excel
- Try closing and reopening Excel

---

## Development Without Excel

You can still use the core CalcsLive Agent features without Excel:

1. Natural language → CalcsLive calculation
2. Script review and iteration
3. Article creation and persistence

The Excel bridge features simply won't appear in the UI when the bridge isn't available.

---

## Summary: What Each Piece Does

| Component | Purpose | Required For |
|-----------|---------|--------------|
| **Streamlit App** | Main UI, chat interface, workflow orchestration | Everything |
| **Azure AI** | LLM for natural language understanding, tool selection | Agent behavior |
| **CalcsLive API** | Unit-aware calculation engine, article storage | Core calculation features |
| **Excel Bridge** | COM automation for Excel read/write | Excel integration only |
| **Excel Desktop** | Spreadsheet interface for interactive use | Excel integration only |

---

## Questions?

- CalcsLive documentation: https://www.calcslive.com/help
- Azure AI documentation: https://learn.microsoft.com/azure/ai-services/openai/
- Project issues: https://github.com/AgoraDesign/calcslive-agent-for-maf/issues
