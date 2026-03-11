import json
from typing import Any

import streamlit as st

from agent_core import CalcsLiveAgent
from calcslive_tools import CALCSLIVE_API_URL, create_calcslive_article_from_script


CLOUD_SYSTEM_MESSAGE = """You are the CalcsLive Cloud Beta assistant.

You help users design, review, and persist unit-aware CalcsLive calculations without Excel.

Preferred workflow:
1. Understand the user's calculation goal.
2. Discover units or resolve ambiguous aliases when needed.
3. Build a PQ script using unit-agnostic formulas.
4. Run the script first with `run_calcslive_script` so the user can review warnings, unit mapping, and outputs.
5. Only create a persistent article with `create_calcslive_article_from_script` after the user confirms.

Rules:
- Prefer category-first unit mapping and include `categoryId` when useful.
- Use pure physics formulas without hard-coded conversion factors.
- Every PQ must include a meaningful human-readable `description` written for engineers/users.
- Do not leave descriptions blank and do not use the symbol itself as the description unless the user explicitly requests terse notation.
- If the user asks to save/persist/create immediately, you may create directly.
- Otherwise default to review-first behavior.
"""


def _tool_arguments_from_messages(messages: list[dict[str, Any]], tool_name: str) -> dict[str, Any] | None:
    for message in reversed(messages):
        if message.get("role") != "assistant":
            continue
        for tool_call in reversed(message.get("tool_calls", []) or []):
            fn = tool_call.get("function", {})
            if fn.get("name") != tool_name:
                continue
            try:
                return json.loads(fn.get("arguments") or "{}")
            except json.JSONDecodeError:
                return None
    return None


def _review_summary(result: dict[str, Any]) -> dict[str, Any]:
    warnings = result.get("warnings") or []
    category_metadata = result.get("categoryMetadata") or {}
    outputs = result.get("outputs") or {}
    human_readable = result.get("humanReadable") or {}
    return {
        "warnings": warnings,
        "categoryMetadata": category_metadata,
        "outputs": outputs,
        "inputs": result.get("inputs") or {},
        "humanReadable": human_readable,
    }


def _calc_table_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    inputs = result.get("inputs") or {}
    outputs = result.get("outputs") or {}

    for sym, pq in inputs.items():
        if not isinstance(pq, dict):
            continue
        rows.append(
            {
                "Kind": "Input",
                "Description": pq.get("description") or sym,
                "Symbol": sym,
                "Expression": "",
                "Value": pq.get("value"),
                "Unit": pq.get("unit") or "",
            }
        )

    for sym, pq in outputs.items():
        if not isinstance(pq, dict):
            continue
        rows.append(
            {
                "Kind": "Output",
                "Description": pq.get("description") or sym,
                "Symbol": sym,
                "Expression": pq.get("expression") or "",
                "Value": pq.get("value"),
                "Unit": pq.get("unit") or "",
            }
        )

    return rows


def _review_table_title() -> str:
    return st.session_state.get("review_table_title") or "Calculation Table"


st.set_page_config(page_title="CalcsLive Cloud Beta", layout="wide")

st.title("CalcsLive Cloud Beta")
st.caption("Review stateless script calculations first, then persist approved ones as CalcsLive articles.")

if "cloud_agent" not in st.session_state:
    st.session_state.cloud_agent = CalcsLiveAgent()
    st.session_state.cloud_agent.system_message = CLOUD_SYSTEM_MESSAGE

if "cloud_messages" not in st.session_state:
    st.session_state.cloud_messages = [
        {"role": "system", "content": CLOUD_SYSTEM_MESSAGE},
        {
            "role": "assistant",
            "content": (
                "Hi! Ask me to design or run a calculation script, for example: "
                "`Create a motor power calc from torque and rotational speed, review first.`"
            ),
        },
    ]

if "review_candidate" not in st.session_state:
    st.session_state.review_candidate = None

if "review_result" not in st.session_state:
    st.session_state.review_result = None

if "last_created_article" not in st.session_state:
    st.session_state.last_created_article = None
if "review_table_title" not in st.session_state:
    st.session_state.review_table_title = "Calculation Table"

with st.sidebar:
    st.subheader("Cloud Beta")
    st.markdown(f"- API Base: `{CALCSLIVE_API_URL}`")
    st.markdown("- Mode: Review-first script run, then explicit create")
    if st.button("Clear chat"):
        st.session_state.cloud_messages = [
            {"role": "system", "content": CLOUD_SYSTEM_MESSAGE},
            {
                "role": "assistant",
                "content": (
                    "Hi! Ask me to design or run a calculation script, for example: "
                    "`Create a motor power calc from torque and rotational speed, review first.`"
                ),
            },
        ]
        st.session_state.review_candidate = None
        st.session_state.review_result = None
        st.session_state.last_created_article = None
        st.session_state.review_table_title = "Calculation Table"
        st.rerun()

for message in st.session_state.cloud_messages:
    if message["role"] in {"system", "tool"} or "tool_calls" in message:
        continue
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

with st.expander("Reviewed Script", expanded=bool(st.session_state.review_result)):
    if st.session_state.review_result:
        summary = _review_summary(st.session_state.review_result)
        hr = summary["humanReadable"]
        if isinstance(hr, dict) and hr.get("summary"):
            st.markdown(f"**Summary:** {hr.get('summary')}")
        if summary["warnings"]:
            st.warning("Warnings were returned. Review them before saving.")
            st.json(summary["warnings"])
        table_rows = _calc_table_rows(st.session_state.review_result)
        if table_rows:
            st.markdown(f"**{_review_table_title()}**")
            st.table(table_rows)
        if summary["categoryMetadata"]:
            with st.expander("Category Metadata", expanded=False):
                st.json(summary["categoryMetadata"])
    else:
        st.caption("Run a script in chat first to review the generated calculation here.")

with st.expander("Persist Reviewed Calc", expanded=bool(st.session_state.review_candidate)):
    if st.session_state.review_candidate:
        candidate = st.session_state.review_candidate
        article = st.session_state.last_created_article.get("article", {}) if st.session_state.last_created_article else {}

        create_btn_col, spacer_col = st.columns([2, 8])
        with create_btn_col:
            create_clicked = st.button("Create Article", type="primary")

        st.caption("This uses the last successfully reviewed script payload.")
        st.code(json.dumps(candidate, indent=2), language="json")
        if create_clicked:
            with st.spinner("Creating article in CalcsLive..."):
                create_result = create_calcslive_article_from_script(
                    pqs=candidate.get("pqs", []),
                    title=candidate.get("title"),
                    description=candidate.get("description"),
                    access_level=candidate.get("accessLevel") or candidate.get("access_level"),
                    category=candidate.get("category"),
                    tags=candidate.get("tags"),
                    inputs=candidate.get("inputs", {}),
                    outputs=candidate.get("outputs", {}),
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
        st.caption("Run a script in chat first. After a successful review, the payload will appear here for confirmation-based create.")

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

        created_rows = _calc_table_rows(created)
        if created_rows:
            st.table(created_rows)

        warnings = created.get("warnings") or []
        if warnings:
            st.warning("Warnings")
            st.json(warnings)

        with st.expander("Raw response", expanded=False):
            st.json(created)

if prompt := st.chat_input("Ask to run or create a calculation script..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.cloud_messages.append({"role": "user", "content": prompt})
    refresh_for_review = False

    with st.chat_message("assistant"):
        with st.spinner("Running cloud agent..."):
            updated_messages, executed_tools = st.session_state.cloud_agent.chat_interact(st.session_state.cloud_messages)
            st.session_state.cloud_messages = updated_messages

            if executed_tools:
                st.markdown("**Executed Tools**")
                for tool_name, result in executed_tools:
                    success = "success" if result.get("success", True) else "failed"
                    st.markdown(f"- `{tool_name}`: {success}")

                    if tool_name == "run_calcslive_script" and result.get("success"):
                        tool_args = _tool_arguments_from_messages(updated_messages, "run_calcslive_script")
                        if tool_args:
                            st.session_state.review_candidate = tool_args
                            st.session_state.review_result = result
                            st.session_state.review_table_title = tool_args.get("title") or "Calculation Table"
                            refresh_for_review = True

                    if tool_name == "create_calcslive_article_from_script" and result.get("success"):
                        st.session_state.last_created_article = result

            final_response = updated_messages[-1].get("content", "")
            if final_response:
                st.markdown(final_response)
            else:
                st.markdown("Finished execution.")

    if refresh_for_review:
        st.rerun()
