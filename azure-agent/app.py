import streamlit as st
from agent_core import CalcsLiveAgent, EXCEL_BRIDGE_URL, LAST_TABLE_CONTEXT
import time
import httpx


def _bridge_url() -> str:
    return EXCEL_BRIDGE_URL


def _bridge_post(path: str, payload: dict | None = None) -> dict:
    url = f"{_bridge_url().rstrip('/')}{path}"
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, json=payload or {})
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


def _bridge_get(path: str) -> dict:
    url = f"{_bridge_url().rstrip('/')}{path}"
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

st.set_page_config(
    page_title="CalcsLive Agent UI",
    page_icon="🧮",
    layout="wide",
)

# Render main UI elements
st.title("🧮 CalcsLive Agent Dashboard")
st.markdown("Automate unit-aware calculations between your Excel spreadsheets and CalcsLive! Chat with the Orchestrator Agent below. \n please load calculation 3M7ALBF4U-3BL to Excel sheet Sheet2 at B9")

# Initialize the Azure Agent in session state
if "agent" not in st.session_state:
    try:
        st.session_state.agent = CalcsLiveAgent()
        st.success(f"Connected to Azure AI (Mode: {st.session_state.agent.mode})", icon="✅")
    except Exception as e:
        st.error(f"Failed to initialize Agent: {str(e)}", icon="🚨")

# Initialize chat history
if "messages" not in st.session_state:
    # Initialize with the system prompt, but we will not render this specific message in the UI loop
    if "agent" in st.session_state:
        st.session_state.messages = [{"role": "system", "content": st.session_state.agent.system_message}]
        # Add a friendly greeting
        st.session_state.messages.append({"role": "assistant", "content": "Hi! I am the CalcsLive Agent. You can ask me to check Excel, read your PQ table, or calculate and update the open spreadsheet."})
    else:
        st.session_state.messages = []

# Live mode state
if "live_last_fingerprint" not in st.session_state:
    st.session_state.live_last_fingerprint = None
if "live_last_status" not in st.session_state:
    st.session_state.live_last_status = "Idle"
if "live_last_result" not in st.session_state:
    st.session_state.live_last_result = None
if "live_bridge_enabled" not in st.session_state:
    st.session_state.live_bridge_enabled = False
if "live_status_raw" not in st.session_state:
    st.session_state.live_status_raw = None

with st.sidebar:
    st.subheader("Live Mode")
    live_mode = st.checkbox("Enable auto-recalc (event-driven)", value=False, key="live_mode")
    debounce_interval = st.slider("Debounce (seconds)", 1, 30, 3, key="live_debounce")
    st.caption("Uses Excel COM SheetChange events in bridge; no polling in UI.")
    st.button("Refresh live status")

# Start/stop bridge live watcher when checkbox state changes.
if st.session_state.get("live_mode") and not st.session_state.get("live_bridge_enabled"):
    context = LAST_TABLE_CONTEXT or {}
    payload = {
        "autoDetect": not bool(context.get("startRow") and context.get("headerRow")),
        "startRow": context.get("startRow"),
        "headerRow": context.get("headerRow"),
        "sheetName": context.get("sheetName"),
        "debounceSeconds": st.session_state.get("live_debounce", 3),
    }
    start_result = _bridge_post("/excel/live-mode/start", payload)
    if start_result.get("success"):
        st.session_state.live_bridge_enabled = True
        st.session_state.live_last_status = "Live mode enabled"
    else:
        st.session_state.live_bridge_enabled = False
        st.session_state.live_last_status = f"Failed to enable live mode: {start_result.get('error')}"

if not st.session_state.get("live_mode") and st.session_state.get("live_bridge_enabled"):
    stop_result = _bridge_post("/excel/live-mode/stop", {})
    if stop_result.get("success"):
        st.session_state.live_bridge_enabled = False
        st.session_state.live_last_status = "Live mode stopped"
    else:
        st.session_state.live_last_status = f"Failed to stop live mode: {stop_result.get('error')}"

# Pull watcher status for display.
status_result = _bridge_get("/excel/live-mode/status")
if status_result.get("success"):
    status = status_result.get("status", {})
    st.session_state.live_status_raw = status
    st.session_state.live_last_result = status.get("lastResult")
    if status.get("lastError"):
        st.session_state.live_last_status = f"Live error: {status.get('lastError')}"
    elif status.get("running") and status.get("enabled"):
        last_run = status.get("lastRecalcAt")
        if last_run:
            st.session_state.live_last_status = f"Watching changes (last recalc at {time.strftime('%H:%M:%S', time.localtime(last_run))})"
        else:
            st.session_state.live_last_status = "Watching changes"

with st.expander("Live Mode Status", expanded=False):
    st.markdown(f"**Status:** {st.session_state.live_last_status}")
    if LAST_TABLE_CONTEXT:
        st.json({"tableContext": LAST_TABLE_CONTEXT})
    if st.session_state.live_status_raw:
        st.json({"watcherStatus": st.session_state.live_status_raw})
    if st.session_state.live_last_result:
        st.json({"lastResult": st.session_state.live_last_result})

# Display chat history on app rerun
for message in st.session_state.messages:
    if message["role"] == "system" or message["role"] == "tool" or ("tool_calls" in message):
        continue  # Skip internal orchestration messages
        
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask me to 'Calculate the values and write them back to Excel'..."):
    
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        with st.spinner("Agent is reasoning and executing tools..."):
            # Request completion from the agent class
            updated_messages, executed_tools = st.session_state.agent.chat_interact(st.session_state.messages)
            st.session_state.messages = updated_messages
            
            # Show a summary string in the UI of the tools it used
            tool_output = ""
            if len(executed_tools) > 0:
                tool_output += "**Executed Tools:**\n"
                for tool_name, result in executed_tools:
                    success = "✅" if result.get("success", True) else "❌"
                    tool_output += f"- {success} `{tool_name}`\n"
                    # For write_excel_results, extract a bit more friendly context
                    if tool_name == "write_excel_results" and result.get("success"):
                         tool_output += f"  - Values updated: {result.get('valuesWritten', 0)}\n"
                    
                tool_output += "\n"
                st.markdown(tool_output)

            # Look for the final text response from the assistant added to the end of the history
            final_response = updated_messages[-1].get("content", "")
            if final_response:
                st.markdown(final_response)
            else:
                st.markdown("*(Finished execution with no final text response)*")
