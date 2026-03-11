import json
from typing import Any


def tool_arguments_from_messages(messages: list[dict[str, Any]], tool_name: str) -> dict[str, Any] | None:
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


def review_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "warnings": result.get("warnings") or [],
        "categoryMetadata": result.get("categoryMetadata") or {},
        "outputs": result.get("outputs") or {},
        "inputs": result.get("inputs") or {},
        "humanReadable": result.get("humanReadable") or {},
    }


def calc_table_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
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


def review_table_title(session_state: Any) -> str:
    return session_state.get("review_table_title") or "Calculation Table"
