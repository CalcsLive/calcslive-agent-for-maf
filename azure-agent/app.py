import streamlit as st
from agent_core import CalcsLiveAgent, EXCEL_BRIDGE_URL, LAST_TABLE_CONTEXT, load_article_to_excel
from calcslive_tools import CALCSLIVE_API_KEY
from app_shared import calc_table_rows, review_summary, review_table_title, tool_arguments_from_messages
import time
import httpx
import json


LOCAL_SYSTEM_MESSAGE = """You are the CalcsLive Excel Agent.

You help users design, review, persist, load, and run unit-aware calculations with CalcsLive and Excel.

Preferred workflow for new calculations:
1. Understand the calculation goal.
2. Discover units or resolve ambiguous aliases when needed.
3. Build a PQ script using unit-agnostic formulas.
4. Run the script first with `run_calcslive_script` for review.
5. Do not create/persist the article automatically from chat unless the user explicitly says to persist immediately.
6. Prefer the UI approval flow: review script -> create article -> load article to Excel.

Excel workflow:
1. Load a created article into Excel.
2. Let the user edit values/units in Excel.
3. Use recalculation/live mode to keep outputs updated.

Important:
- Prefer review-first behavior.
- Avoid inventing article IDs or claiming persistence succeeded unless a create tool actually succeeds.
- Use category-first unit mapping and warn on ambiguous units.
- Every PQ must include a meaningful human-readable `description`.
- Do not use the raw symbol itself as the description unless the user explicitly asks for terse labels.
"""


LOCAL_GREETING = (
    "Hi! I can help you design a CalcsLive calculation, review it, persist it, "
    "load it into Excel, and keep Excel outputs updated."
)
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
st.markdown("Automate unit-aware calculations between your Excel spreadsheets and CalcsLive. Use chat to design/review a calc, then persist and load it into Excel.")

# Initialize the Azure Agent in session state
if "agent" not in st.session_state:
    try:
        st.session_state.agent = CalcsLiveAgent()
        st.session_state.agent.system_message = LOCAL_SYSTEM_MESSAGE
        st.success(f"Connected to Azure AI (Mode: {st.session_state.agent.mode})", icon="✅")
    except Exception as e:
        st.error(f"Failed to initialize Agent: {str(e)}", icon="🚨")

# Initialize chat history
if "messages" not in st.session_state:
    # Initialize with the system prompt, but we will not render this specific message in the UI loop
    if "agent" in st.session_state:
        st.session_state.messages = [{"role": "system", "content": LOCAL_SYSTEM_MESSAGE}]
        # Add a friendly greeting
        st.session_state.messages.append({"role": "assistant", "content": LOCAL_GREETING})
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
if "review_candidate" not in st.session_state:
    st.session_state.review_candidate = None
if "review_result" not in st.session_state:
    st.session_state.review_result = None
if "last_created_article" not in st.session_state:
    st.session_state.last_created_article = None
if "review_table_title" not in st.session_state:
    st.session_state.review_table_title = "Calculation Table"

with st.sidebar:
    st.subheader("Live Mode")
    live_mode = st.checkbox("Enable auto-recalc (event-driven)", value=False, key="live_mode")
    debounce_interval = st.slider("Debounce (seconds)", 1, 30, 3, key="live_debounce")
    st.caption("Uses Excel COM SheetChange events in bridge; no polling in UI.")
    st.button("Refresh live status")
    if st.button("Clear chat"):
        if "agent" in st.session_state:
            st.session_state.agent.system_message = LOCAL_SYSTEM_MESSAGE
            st.session_state.messages = [{"role": "system", "content": LOCAL_SYSTEM_MESSAGE}]
            st.session_state.messages.append({"role": "assistant", "content": LOCAL_GREETING})
        else:
            st.session_state.messages = []
        st.session_state.review_candidate = None
        st.session_state.review_result = None
        st.session_state.last_created_article = None
        st.session_state.review_table_title = "Calculation Table"
        st.rerun()

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
    if CALCSLIVE_API_KEY:
        payload["authToken"] = CALCSLIVE_API_KEY
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

with st.expander("Reviewed Script", expanded=bool(st.session_state.review_result)):
    if st.session_state.review_result:
        summary = review_summary(st.session_state.review_result)
        human_readable = summary["humanReadable"]
        if isinstance(human_readable, dict) and human_readable.get("summary"):
            st.markdown(f"**Summary:** {human_readable.get('summary')}")
        if summary["warnings"]:
            st.warning("Warnings were returned. Review before persisting or loading into Excel.")
            st.json(summary["warnings"])
        table_rows = calc_table_rows(st.session_state.review_result)
        if table_rows:
            st.markdown(f"**{review_table_title(st.session_state)}**")
            st.table(table_rows)
        if summary["categoryMetadata"]:
            with st.expander("Category Metadata", expanded=False):
                st.json(summary["categoryMetadata"])
    else:
        st.caption("Run a script first to review warnings, categories, and outputs here.")

with st.expander("Persist / Load", expanded=bool(st.session_state.review_candidate)):
    if st.session_state.review_candidate:
        candidate = st.session_state.review_candidate
        article = st.session_state.last_created_article.get("article", {}) if st.session_state.last_created_article else {}
        article_id = article.get("id")

        create_btn_col, load_btn_col, spacer_col = st.columns([2, 2, 6])
        with create_btn_col:
            create_clicked = st.button("Create Article", type="primary")
        with load_btn_col:
            load_clicked = st.button("Load To Excel", disabled=not bool(article_id))

        st.caption("The last reviewed `run_calcslive_script` payload is ready for approval.")
        st.code(json.dumps(candidate, indent=2), language="json")

        if create_clicked:
            with st.spinner("Creating article in CalcsLive..."):
                create_result = st.session_state.agent.execute_tool(
                    "create_calcslive_article_from_script",
                    {
                        "pqs": candidate.get("pqs", []),
                        "title": candidate.get("title"),
                        "description": candidate.get("description"),
                        "accessLevel": candidate.get("accessLevel") or candidate.get("access_level"),
                        "category": candidate.get("category"),
                        "tags": candidate.get("tags"),
                        "inputs": candidate.get("inputs", {}),
                        "outputs": candidate.get("outputs", {}),
                    },
                )

            if create_result.get("success"):
                st.session_state.last_created_article = create_result
                if isinstance(st.session_state.review_candidate, dict):
                    article = create_result.get("article", {})
                    if isinstance(article, dict) and article.get("title"):
                        st.session_state.review_candidate["title"] = article.get("title")
                        st.session_state.review_table_title = article.get("title")
                article = create_result.get("article", {})
                st.success("Article created successfully.")
                if article.get("url"):
                    st.markdown(f"- URL: {article.get('url')}")
                if article.get("id"):
                    st.markdown(f"- ID: `{article.get('id')}`")
                st.rerun()
            else:
                st.error(create_result.get("error", "Create failed"))
                if create_result.get("details"):
                    st.json(create_result.get("details"))

        if article_id and load_clicked:
            with st.spinner("Loading created article into Excel..."):
                load_result = load_article_to_excel(article_id=article_id)
            if load_result.get("success"):
                st.success(f"Loaded `{article_id}` into Excel.")
            else:
                st.error(load_result.get("error", "Load failed"))
                if load_result.get("details"):
                    st.json(load_result.get("details"))
    else:
        st.caption("Ask the agent to create and review a calculation script first.")

if st.session_state.last_created_article:
    with st.expander("Last Created Article", expanded=True):
        created = st.session_state.last_created_article
        article = created.get("article", {}) if isinstance(created.get("article"), dict) else {}
        human_readable = created.get("humanReadable", {}) if isinstance(created.get("humanReadable"), dict) else {}
        if article.get("title"):
            st.markdown(f"**Title:** {article.get('title')}")
        if article.get("id"):
            st.markdown(f"**ID:** `{article.get('id')}`")
        if article.get("url"):
            st.markdown(f"**URL:** {article.get('url')}")
        if human_readable.get("summary"):
            st.markdown(f"**Summary:** {human_readable.get('summary')}")

        created_rows = calc_table_rows(created)
        if created_rows:
            st.table(created_rows)

        warnings = created.get("warnings") or []
        if warnings:
            st.warning("Warnings")
            st.json(warnings)

        with st.expander("Raw response", expanded=False):
            st.json(created)

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
    refresh_for_review = False

    # Display assistant response
    with st.chat_message("assistant"):
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
                    if tool_name == "run_calcslive_script" and result.get("success"):
                        tool_args = tool_arguments_from_messages(updated_messages, "run_calcslive_script")
                        if tool_args:
                            st.session_state.review_candidate = tool_args
                            st.session_state.review_result = result
                            st.session_state.review_table_title = tool_args.get("title") or "Calculation Table"
                            refresh_for_review = True
                    if tool_name == "create_calcslive_article_from_script" and result.get("success"):
                        st.session_state.last_created_article = result
                    
                tool_output += "\n"
                st.markdown(tool_output)

            # Look for the final text response from the assistant added to the end of the history
            final_response = updated_messages[-1].get("content", "")
            if final_response:
                st.markdown(final_response)
            else:
                st.markdown("*(Finished execution with no final text response)*")

    if refresh_for_review:
        st.rerun()
