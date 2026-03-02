"""Event-driven Excel watcher for automatic CalcsLive recalculation.

This module runs a COM event listener on Excel SheetChange and triggers
deterministic read -> calculate -> write flow with debounce.
"""

from __future__ import annotations

import os
import threading
import time
from typing import Any

import httpx
import pythoncom
import win32com.client

from excel_api import find_article_id, find_pq_table, read_pq_table, write_pq_results, write_pq_values


CALCSLIVE_API_URL = os.getenv("CALCSLIVE_API_URL", "https://www.calcslive.com/api/v1").rstrip("/")
CALCSLIVE_API_KEY = os.getenv("CALCSLIVE_API_KEY", "")
LIVE_WATCHER_DEBUG = os.getenv("LIVE_WATCHER_DEBUG", "1").strip().lower() in {"1", "true", "yes", "on"}


def _debug(message: str, data: Any = None) -> None:
    if not LIVE_WATCHER_DEBUG:
        return
    if data is None:
        print(f"[LiveWatcher] {message}")
    else:
        print(f"[LiveWatcher] {message}: {data}")


def _extract_calc_outputs(calc_result: dict[str, Any]) -> dict[str, Any]:
    if not calc_result.get("success"):
        return {}
    data = calc_result.get("data")
    if not isinstance(data, dict):
        return {}
    if isinstance(data.get("outputs"), dict):
        return data["outputs"]
    nested = data.get("data")
    if isinstance(nested, dict) and isinstance(nested.get("outputs"), dict):
        return nested["outputs"]
    if isinstance(nested, dict):
        calc = nested.get("calculation")
        if isinstance(calc, dict) and isinstance(calc.get("outputs"), dict):
            return calc["outputs"]
    calc = data.get("calculation")
    if isinstance(calc, dict) and isinstance(calc.get("outputs"), dict):
        return calc["outputs"]
    return {}


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str], timeout: float = 30.0) -> dict[str, Any]:
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, json=payload, headers=headers)

        if response.status_code >= 400:
            try:
                details = response.json()
            except Exception:
                details = response.text
            return {
                "success": False,
                "statusCode": response.status_code,
                "error": "HTTP request failed",
                "details": details,
            }

        try:
            data = response.json()
        except Exception:
            return {
                "success": False,
                "statusCode": response.status_code,
                "error": "Expected JSON response but received non-JSON payload",
                "details": response.text,
            }
        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _calculate_with_calcslive(
    pqs: list[dict[str, Any]],
    inputs: dict[str, Any],
    outputs: dict[str, Any],
    article_id: str | None,
    api_key: str,
) -> dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    run_candidates: list[tuple[str, dict[str, Any]]] = []

    if article_id:
        article_payload: dict[str, Any] = {
            "articleId": article_id,
            "inputs": inputs or {},
        }
        if outputs:
            article_payload["outputs"] = outputs
        run_candidates.append((f"{CALCSLIVE_API_URL}/calculate", article_payload))

    run_script_payload: dict[str, Any] = {"pqs": pqs, "inputs": inputs}
    if outputs:
        run_script_payload["outputs"] = outputs
    if article_id:
        run_script_payload["articleId"] = article_id
    run_candidates.append((f"{CALCSLIVE_API_URL}/articles/uac-script/run", run_script_payload))

    _debug("Calc candidates", [url for url, _ in run_candidates])

    failures: list[dict[str, Any]] = []
    for url, payload in run_candidates:
        attempt = _post_json(url, payload, headers=headers)
        if attempt.get("success"):
            data = attempt.get("data")
            if isinstance(data, dict) and data.get("success") is False:
                failures.append({"url": url, "error": data.get("error"), "details": data})
                continue
            return {"success": True, "data": data}

        failures.append(
            {
                "url": url,
                "statusCode": attempt.get("statusCode"),
                "error": attempt.get("error"),
                "details": attempt.get("details"),
            }
        )

    return {
        "success": False,
        "error": "All CalcsLive calculation endpoints failed",
        "details": failures,
    }


class _ExcelEvents:
    def OnSheetChange(self, sh, target):  # noqa: N802 (COM callback name)
        if _ACTIVE_WATCHER is not None:
            _ACTIVE_WATCHER.handle_sheet_change(sh, target)


_ACTIVE_WATCHER: "LiveRecalcWatcher | None" = None


class LiveRecalcWatcher:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._event_sink: Any = None
        self._excel_app: Any = None

        self.enabled = False
        self.auto_detect = True
        self.start_row: int | None = None
        self.header_row: int | None = None
        self.sheet_name: str | None = None
        self.debounce_seconds = 1.5
        self.api_key = CALCSLIVE_API_KEY

        self._dirty_since: float | None = None
        self._last_change_cell: str | None = None
        self._suppress_events = False

        self.last_recalc_at: float | None = None
        self.last_error: str | None = None
        self.last_result: dict[str, Any] | None = None
        self.last_values_written = 0
        self.event_count = 0
        self.last_event_at: float | None = None
        self.last_event_sheet: str | None = None
        self.last_event_address: str | None = None
        self.heartbeat_at: float | None = None

    def start(
        self,
        auto_detect: bool = True,
        start_row: int | None = None,
        header_row: int | None = None,
        sheet_name: str | None = None,
        debounce_seconds: float = 1.5,
        api_key: str | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            self.auto_detect = auto_detect
            self.start_row = start_row
            self.header_row = header_row
            self.sheet_name = sheet_name
            self.debounce_seconds = max(0.5, float(debounce_seconds))
            if api_key is not None:
                self.api_key = api_key

            if self._thread and self._thread.is_alive():
                self.enabled = True
                return {"success": True, "message": "Live watcher already running", "status": self.status()}

            self._stop_event.clear()
            self.enabled = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            _debug("Watcher thread started")

        return {"success": True, "message": "Live watcher started", "status": self.status()}

    def stop(self) -> dict[str, Any]:
        with self._lock:
            self.enabled = False
            self._stop_event.set()
            thread = self._thread

        if thread and thread.is_alive():
            thread.join(timeout=3.0)

        with self._lock:
            self._thread = None

        return {"success": True, "message": "Live watcher stopped", "status": self.status()}

    def status(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "running": bool(self._thread and self._thread.is_alive()),
            "autoDetect": self.auto_detect,
            "startRow": self.start_row,
            "headerRow": self.header_row,
            "sheetName": self.sheet_name,
            "debounceSeconds": self.debounce_seconds,
            "lastChangeCell": self._last_change_cell,
            "lastRecalcAt": self.last_recalc_at,
            "lastError": self.last_error,
            "lastValuesWritten": self.last_values_written,
            "lastResult": self.last_result,
            "eventCount": self.event_count,
            "lastEventAt": self.last_event_at,
            "lastEventSheet": self.last_event_sheet,
            "lastEventAddress": self.last_event_address,
            "heartbeatAt": self.heartbeat_at,
            "hasAuthToken": bool(self.api_key),
        }

    def handle_sheet_change(self, sh, target) -> None:
        if not self.enabled or self._suppress_events:
            return

        try:
            changed_sheet = str(sh.Name)
            if self.sheet_name and changed_sheet.lower() != self.sheet_name.lower():
                return
            self._last_change_cell = str(target.Address)
            self.last_event_sheet = changed_sheet
            self.last_event_address = self._last_change_cell
            self.last_event_at = time.time()
            self.event_count += 1
            _debug("SheetChange event", {
                "sheet": changed_sheet,
                "address": self._last_change_cell,
                "eventCount": self.event_count,
            })
        except Exception:
            return

        self._dirty_since = time.time()

    def _run_loop(self) -> None:
        global _ACTIVE_WATCHER
        pythoncom.CoInitialize()
        _debug("Watcher loop started")
        try:
            while not self._stop_event.is_set():
                try:
                    self._excel_app = win32com.client.GetActiveObject("Excel.Application")
                    self._event_sink = win32com.client.DispatchWithEvents(self._excel_app, _ExcelEvents)
                    _ACTIVE_WATCHER = self
                    _debug("Connected to Excel events")
                    break
                except Exception as e:
                    self.last_error = f"Waiting for Excel: {e}"
                    _debug("Waiting for Excel", str(e))
                    time.sleep(1.0)

            while not self._stop_event.is_set():
                pythoncom.PumpWaitingMessages()
                self.heartbeat_at = time.time()
                try:
                    self._maybe_recalculate()
                except Exception as e:
                    self.last_error = f"Watcher loop error: {e}"
                    self.last_result = {
                        "success": False,
                        "phase": "watcher",
                        "details": {"error": str(e)},
                    }
                    _debug("Watcher loop error", str(e))
                time.sleep(0.1)
        finally:
            _ACTIVE_WATCHER = None
            self._event_sink = None
            self._excel_app = None
            _debug("Watcher loop stopped")
            pythoncom.CoUninitialize()

    def _maybe_recalculate(self) -> None:
        if not self._dirty_since:
            return
        if time.time() - self._dirty_since < self.debounce_seconds:
            return

        self._dirty_since = None
        self._run_recalculation()

    def _read_table(self) -> dict[str, Any]:
        if self.auto_detect or self.start_row is None or self.header_row is None:
            table = find_pq_table(self.sheet_name)
            source = "auto"
        else:
            table = read_pq_table(self.start_row, self.header_row, self.sheet_name)
            source = "explicit"

        if not table.get("success"):
            return table

        article_id = table.get("articleId")
        if not article_id:
            article_info = find_article_id(self.sheet_name)
            if article_info.get("success"):
                article_id = article_info.get("articleId")

        _debug("Read table context", {"source": source, "articleId": article_id, "sheet": table.get("sheetName")})

        pqs = table.get("pqs", [])
        inputs: dict[str, Any] = {}
        outputs: dict[str, Any] = {}
        definitions: list[dict[str, Any]] = []

        for pq in pqs:
            sym = pq.get("sym")
            if not sym:
                continue

            unit = str(pq.get("unit") or "")
            value = pq.get("value")
            expression = str(pq.get("expression") or "")
            description = str(pq.get("description") or "")

            item = {"sym": sym, "unit": unit, "description": description}
            if expression:
                item["expression"] = expression
                outputs[sym] = {"unit": unit}
            else:
                item["value"] = value if value is not None else 0
                if value is not None:
                    try:
                        numeric = float(value)
                    except Exception:
                        numeric = value
                    inputs[sym] = {"value": numeric, "unit": unit}

            definitions.append(item)

        return {
            "success": True,
            "articleId": article_id,
            "sheetName": table.get("sheetName"),
            "valueCol": table.get("columns", {}).get("value"),
            "rowMapping": {pq.get("sym"): pq.get("row") for pq in pqs if pq.get("sym")},
            "pqs": definitions,
            "inputs": inputs,
            "outputs": outputs,
        }

    def _run_recalculation(self) -> None:
        _debug("Recalc triggered", {"cell": self._last_change_cell, "sheet": self.last_event_sheet})
        table = self._read_table()
        if not table.get("success"):
            self.last_error = f"Read failed: {table.get('error')}"
            self.last_result = {"success": False, "phase": "read", "details": table}
            _debug("Read failed", table)
            return

        calc = _calculate_with_calcslive(
            table.get("pqs", []),
            table.get("inputs", {}),
            table.get("outputs", {}),
            table.get("articleId"),
            self.api_key,
        )
        if not calc.get("success"):
            self.last_error = f"Calculate failed: {calc.get('error')}"
            self.last_result = {"success": False, "phase": "calculate", "details": calc}
            _debug("Calculate failed", calc)
            return

        outputs = _extract_calc_outputs(calc)
        values = {
            sym: details.get("value")
            for sym, details in outputs.items()
            if isinstance(details, dict) and "value" in details
        }

        row_mapping = table.get("rowMapping", {})
        value_col = table.get("valueCol")

        self._suppress_events = True
        try:
            if row_mapping and value_col:
                rows = [
                    {"row": row_mapping[sym], "value": value}
                    for sym, value in values.items()
                    if sym in row_mapping
                ]
                write = write_pq_values(rows, value_col, table.get("sheetName"))
            else:
                write = write_pq_results(values, table.get("sheetName"))
        finally:
            self._suppress_events = False

        if not write.get("success"):
            self.last_error = f"Write failed: {write.get('error')}"
            self.last_result = {"success": False, "phase": "write", "details": write}
            _debug("Write failed", write)
            return

        self.last_recalc_at = time.time()
        self.last_values_written = int(write.get("valuesWritten") or len(values))
        self.last_error = None
        self.last_result = {
            "success": True,
            "phase": "complete",
            "articleId": table.get("articleId"),
            "outputs": values,
            "write": write,
        }
        _debug("Recalc complete", {"valuesWritten": self.last_values_written, "outputs": values})


live_recalc_watcher = LiveRecalcWatcher()
