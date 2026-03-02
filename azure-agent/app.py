import streamlit as st
from agent_core import CalcsLiveAgent, LAST_TABLE_CONTEXT, read_excel_pq_table, recalculate_excel_table
import json
import time


def _read_loaded_table() -> dict:
    """Read table using last loaded anchor context for deterministic polling."""
    if not LAST_TABLE_CONTEXT:
        return {"success": False, "error": "No loaded article context"}

    return read_excel_pq_table(
        start_row=LAST_TABLE_CONTEXT.get("startRow"),
        header_row=LAST_TABLE_CONTEXT.get("headerRow"),
        sheet_name=LAST_TABLE_CONTEXT.get("sheetName"),
    )


def _table_fingerprint(pq_data: dict) -> str:
    """Build hashable JSON fingerprint from input/output unit-aware state."""
    payload = {
        "inputs": pq_data.get("inputs", {}),
        "outputs": pq_data.get("outputs", {}),
    }
    return json.dumps(payload, sort_keys=True, default=str)

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
if "live_last_recalc_ts" not in st.session_state:
    st.session_state.live_last_recalc_ts = 0.0
if "live_last_status" not in st.session_state:
    st.session_state.live_last_status = "Idle"
if "live_last_result" not in st.session_state:
    st.session_state.live_last_result = None

with st.sidebar:
    st.subheader("Live Mode")
    live_mode = st.checkbox("Enable auto-recalc", value=False, key="live_mode")
    poll_interval = st.slider("Poll interval (seconds)", 1, 10, 2, key="live_poll_interval")
    debounce_interval = st.slider("Debounce (seconds)", 1, 30, 3, key="live_debounce")
    st.caption("Auto-recalc runs only when inputs or units change in the loaded table.")

# Live polling/recalc loop (best-effort, no extra dependency)
if st.session_state.get("live_mode") and "agent" in st.session_state:
    table = _read_loaded_table()
    if table.get("success"):
        current_fingerprint = _table_fingerprint(table)
        last_fingerprint = st.session_state.live_last_fingerprint
        now = time.time()

        if last_fingerprint is None:
            st.session_state.live_last_fingerprint = current_fingerprint
            st.session_state.live_last_status = "Live mode armed"
        elif current_fingerprint != last_fingerprint:
            elapsed = now - st.session_state.live_last_recalc_ts
            if elapsed >= st.session_state.live_debounce:
                result = recalculate_excel_table()
                st.session_state.live_last_result = result
                st.session_state.live_last_recalc_ts = now
                st.session_state.live_last_fingerprint = current_fingerprint
                if result.get("success"):
                    st.session_state.live_last_status = f"Auto-recalc OK ({time.strftime('%H:%M:%S')})"
                else:
                    st.session_state.live_last_status = f"Auto-recalc failed: {result.get('phase')}"
            else:
                st.session_state.live_last_status = f"Change detected; waiting debounce ({int(st.session_state.live_debounce - elapsed)}s)"
        else:
            st.session_state.live_last_status = "Watching for changes"
    else:
        st.session_state.live_last_status = f"Live mode waiting: {table.get('error')}"

with st.expander("Live Mode Status", expanded=False):
    st.markdown(f"**Status:** {st.session_state.live_last_status}")
    if LAST_TABLE_CONTEXT:
        st.json({"tableContext": LAST_TABLE_CONTEXT})
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

# Trigger next polling cycle
if st.session_state.get("live_mode"):
    time.sleep(st.session_state.live_poll_interval)
    st.rerun()
