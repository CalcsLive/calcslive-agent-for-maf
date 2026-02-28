import streamlit as st
from agent_core import CalcsLiveAgent
import json
import time

st.set_page_config(
    page_title="CalcsLive Agent UI",
    page_icon="🧮",
    layout="wide",
)

# Render main UI elements
st.title("🧮 CalcsLive Agent Dashboard")
st.markdown("Automate unit-aware calculations between your Excel spreadsheets and CalcsLive! Chat with the Orchestrator Agent below.")

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
