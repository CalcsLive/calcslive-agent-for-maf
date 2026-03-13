import streamlit as st
from agent_core import CalcsLiveAgent, EXCEL_BRIDGE_URL, LAST_TABLE_CONTEXT, load_article_to_excel, read_excel_pq_table
from calcslive_tools import CALCSLIVE_API_KEY, CALCSLIVE_API_URL
from app_shared import calc_table_rows, review_summary, review_table_title, tool_arguments_from_messages
import time
import httpx
import json
from pathlib import Path


UNIFIED_SYSTEM_MESSAGE = """You are the CalcsLive Agent.

You help users design, review, persist, and run unit-aware calculations with CalcsLive. When Excel bridge access is available, you also help users move calculations to and from Excel.

Preferred workflow for new calculations:
1. Understand the calculation goal.
2. Discover units or resolve ambiguous aliases when needed.
3. Define the input quantities clearly, including sensible initial values and units for each input PQ.
4. Build a PQ script using unit-agnostic formulas.
5. Run the script first with `run_calcslive_script` for review.
6. Do not create/persist the article automatically from chat unless the user explicitly says to persist immediately.
7. Prefer the UI approval flow: review script -> create article -> load article to Excel.

Excel workflow (when Excel bridge is available):
1. Load a created article into Excel.
2. Let the user edit values/units in Excel.
3. Use recalculation/live mode to keep outputs updated.
4. If the user already laid out a compatible PQ table in Excel, read that table, review it as a CalcsLive script, and let the user persist it.

Important:
- Prefer review-first behavior.
- Avoid inventing article IDs or claiming persistence succeeded unless a create tool actually succeeds.
- Use category-first unit mapping and warn on ambiguous units.
- Every PQ must include a meaningful human-readable `description`.
- Do not use the raw symbol itself as the description unless the user explicitly asks for terse labels.
"""


UNIFIED_GREETING = (
    "Hi! I can help you design a CalcsLive calculation, review it, persist it, "
    "and, when Excel is connected, bridge it to and from Excel with automatic updates."
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


def _excel_bridge_available() -> bool:
    health = _bridge_get("/excel/health")
    return bool(health.get("success"))

APP_ICON_PATH = Path(__file__).resolve().parent.parent / "assets" / "images" / "e3d-logo3.png"

st.set_page_config(
    page_title="CalcsLive Agent",
    page_icon=str(APP_ICON_PATH),
    layout="wide",
)

# Render main UI elements
st.title("🧮 CalcsLive Agent")

excel_bridge_available = _excel_bridge_available()
if excel_bridge_available:
    st.markdown("Design and review CalcsLive calculations, create persistent articles, and bridge them to/from Excel when connected.")
else:
    st.markdown("Design and review CalcsLive calculations and create persistent articles. Excel bridge features will appear automatically when available.")

# Initialize the Azure Agent in session state
if "agent" not in st.session_state:
    try:
        st.session_state.agent = CalcsLiveAgent()
        st.session_state.agent.system_message = UNIFIED_SYSTEM_MESSAGE
        st.success(f"Connected to Azure AI (Mode: {st.session_state.agent.mode})", icon="✅")
    except Exception as e:
        st.error(f"Failed to initialize Agent: {str(e)}", icon="🚨")

# Initialize chat history
if "messages" not in st.session_state:
    # Initialize with the system prompt, but we will not render this specific message in the UI loop
    if "agent" in st.session_state:
        st.session_state.messages = [{"role": "system", "content": UNIFIED_SYSTEM_MESSAGE}]
        # Add a friendly greeting
        st.session_state.messages.append({"role": "assistant", "content": UNIFIED_GREETING})
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
    st.subheader("App Options")
    if excel_bridge_available:
        live_mode = st.checkbox("Auto-update Excel results", value=True, key="live_mode")
        debounce_interval = st.slider("Update debounce (seconds)", 1, 30, 3, key="live_debounce")
    with st.expander("Sample Prompts", expanded=True):
        st.caption("Copy one of these to get started:")
        st.text_area(
            "Prompt 1",
            value="Please calculate the acceleration for a car to go from 0 to 100 km per hour in 3 seconds and the distance covered.",
            height=70,
        )
        st.text_area(
            "Prompt 2",
            value="Calculate the mass of a steel sphere.",
            height=70,
        )
        st.text_area(
            "Prompt 3",
            value="Calculate the stress and deflection of simple HSS beam with fixed support at both ends under uniform distributed load.",
            height=90,
        )
        st.text_area(
            "Prompt 4",
            value="Calculate the Earth escape velocity.",
            height=70,
        )
    with st.expander("CalcsLive Help", expanded=False):
        st.caption("Use these references when refining units, PQ symbols, formulas, or supported math functions.")
        st.markdown("- [Overall Help](https://calcslive.com/help)")
        st.markdown("- [PQ Guide](https://calcslive.com/help/pq-guide)")
        st.markdown("- [Units Reference](https://calcslive.com/help/units-reference)")
        st.markdown("- [Math Reference](https://calcslive.com/help/math-reference)")
    with st.expander("Advanced / Debug", expanded=False):
        if excel_bridge_available:
            st.caption("Uses Excel COM SheetChange events in bridge; no polling in UI.")
        st.markdown(f"- CalcsLive API: `{CALCSLIVE_API_URL}`")
        st.markdown(f"- Excel Bridge: `{EXCEL_BRIDGE_URL}`")
        st.markdown(f"- Excel bridge available: `{excel_bridge_available}`")
        if excel_bridge_available:
            st.button("Refresh live status")
            if st.session_state.live_last_status:
                st.markdown(f"- Live mode: {st.session_state.live_last_status}")
            if LAST_TABLE_CONTEXT:
                st.json({"tableContext": LAST_TABLE_CONTEXT})
            if st.session_state.live_status_raw:
                st.json({"watcherStatus": st.session_state.live_status_raw})
            if st.session_state.live_last_result:
                st.json({"lastResult": st.session_state.live_last_result})
    if st.button("Clear chat"):
        if "agent" in st.session_state:
            st.session_state.agent.system_message = UNIFIED_SYSTEM_MESSAGE
            st.session_state.messages = [{"role": "system", "content": UNIFIED_SYSTEM_MESSAGE}]
            st.session_state.messages.append({"role": "assistant", "content": UNIFIED_GREETING})
        else:
            st.session_state.messages = []
        st.session_state.review_candidate = None
        st.session_state.review_result = None
        st.session_state.last_created_article = None
        st.session_state.review_table_title = "Calculation Table"
        st.rerun()

# Start/stop bridge live watcher when checkbox state changes.
if excel_bridge_available and st.session_state.get("live_mode") and not st.session_state.get("live_bridge_enabled"):
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

if excel_bridge_available and not st.session_state.get("live_mode") and st.session_state.get("live_bridge_enabled"):
    stop_result = _bridge_post("/excel/live-mode/stop", {})
    if stop_result.get("success"):
        st.session_state.live_bridge_enabled = False
        st.session_state.live_last_status = "Live mode stopped"
    else:
        st.session_state.live_last_status = f"Failed to stop live mode: {stop_result.get('error')}"

# Pull watcher status for display.
status_result = _bridge_get("/excel/live-mode/status") if excel_bridge_available else {"success": False}
if excel_bridge_available and status_result.get("success"):
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

if excel_bridge_available:
    with st.expander("Bridge to/from Excel", expanded=False):
        send_col, get_col, spacer_col = st.columns([2, 2, 6])
        st.caption("Two-way bridge: send a reviewed CalcsLive calc to Excel, or read + convert + review an Excel table as a CalcsLive script.")
        st.markdown(
            "**How to use this bridge**\n"
            "- **Send Calc to Excel**: First review and create a calculation article in the app. Then send that created article into Excel so the bridge writes the metadata block and PQ table structure for interactive use.\n"
            "- **Get Calc from Excel**: Prepare a compatible PQ table in Excel, then let the bridge read it, convert it into a stateless CalcsLive script review payload, and show the reviewed result back in the app before you persist it as a new article.\n"
            "- **Excel table structure expected**: the bridge looks for columns matching Description, Symbol, Expression, Value, and Unit. A left-side row number column is allowed. For inputs, leave Expression blank and provide initial Value + Unit. For outputs, provide an Expression and desired Unit.\n"
            "- **Recommended flow for Excel-originated calculations**: lay out the PQ rows in Excel using the same table structure, click **Get Calc from Excel**, review warnings/results, adjust Article Title and Description if needed, then click **Create Article**."
        )
        created_article = st.session_state.last_created_article.get("article", {}) if st.session_state.last_created_article else {}
        created_article_id = created_article.get("id")
        with send_col:
            send_to_excel_clicked = st.button("Send Calc to Excel", disabled=not bool(created_article_id))
        with get_col:
            get_from_excel_clicked = st.button("Get Calc from Excel")

        if send_to_excel_clicked and created_article_id:
            with st.spinner("Loading created article into Excel..."):
                load_result = load_article_to_excel(article_id=created_article_id)
            if load_result.get("success"):
                st.success(f"Loaded `{created_article_id}` into Excel.")
            else:
                st.error(load_result.get("error", "Load failed"))
                if load_result.get("details"):
                    st.json(load_result.get("details"))

        if get_from_excel_clicked:
            with st.spinner("Reading Excel table and running stateless script review..."):
                excel_payload = read_excel_pq_table()
                if excel_payload.get("success"):
                    review_payload = {
                        "pqs": excel_payload.get("pqs", []),
                        "inputs": excel_payload.get("inputs", {}),
                        "outputs": excel_payload.get("outputs", {}),
                    }
                    review_result = st.session_state.agent.execute_tool("run_calcslive_script", review_payload)
                    if review_result.get("success"):
                        st.session_state.review_candidate = review_payload
                        st.session_state.review_result = review_result
                        st.session_state.review_table_title = "Calculation Table"
                        st.success("Excel table converted and reviewed as a CalcsLive script.")
                        st.rerun()
                    else:
                        st.error(review_result.get("error", "Run script failed"))
                        if review_result.get("details"):
                            st.json(review_result.get("details"))
                else:
                    st.error(excel_payload.get("error", "Failed to read Excel table"))
                    if excel_payload.get("details"):
                        st.json(excel_payload.get("details"))

with st.expander("Reviewed CalcsLive Script", expanded=bool(st.session_state.review_result)):
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

with st.expander("Create Calculation Article", expanded=bool(st.session_state.review_candidate)):
    if st.session_state.review_candidate:
        candidate = st.session_state.review_candidate
        create_btn_col, spacer_col = st.columns([2, 8])
        with create_btn_col:
            create_clicked = st.button("Create Article", type="primary")

        st.caption("The last reviewed `run_calcslive_script` payload is ready for approval.")
        title_value = st.text_input("Article Title", value=candidate.get("title", ""), key="persist_title")
        description_value = st.text_area("Article Description", value=candidate.get("description", ""), key="persist_description", height=80)
        candidate["title"] = title_value
        candidate["description"] = description_value
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
        article_id = article.get("id")
        if article_id:
            base = "https://www.calcslive.com"
            st.markdown(
                "**Modes:** "
                f"[edit]({base}/editor/{article_id}) | "
                f"[calculate]({base}/calculate/{article_id}) | "
                f"[table]({base}/table/{article_id}) | "
                f"[view]({base}/view/{article_id})"
            )
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
                            st.session_state.review_table_title = (
                                tool_args.get("title")
                                or result.get("title")
                                or "Calculation Table"
                            )
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
