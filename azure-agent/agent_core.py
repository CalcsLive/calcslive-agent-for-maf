import os
import json
import re
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse, parse_qs
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
EXCEL_BRIDGE_URL = os.getenv("EXCEL_BRIDGE_URL", "http://localhost:8001")
CALCSLIVE_API_URL = os.getenv("CALCSLIVE_API_URL", "https://calcslive.com/api/v1")
CALCSLIVE_API_KEY = os.getenv("CALCSLIVE_API_KEY", "")
CALCSLIVE_DEBUG = os.getenv("CALCSLIVE_DEBUG", "1").strip().lower() in {"1", "true", "yes", "on"}

# Remember last loaded table anchor so recalc targets the same block.
LAST_TABLE_CONTEXT: dict[str, Any] = {}


def _debug(message: str, data: Any = None) -> None:
    """Simple debug logger for local troubleshooting."""
    if not CALCSLIVE_DEBUG:
        return
    if data is None:
        print(f"[CalcsLiveDebug] {message}")
        return
    try:
        serialized = json.dumps(data, default=str)
    except Exception:
        serialized = str(data)
    print(f"[CalcsLiveDebug] {message}: {serialized}")


def _cell_to_row_col(cell_ref: str) -> tuple[int, int] | None:
    """Convert Excel cell reference (e.g. B9) to (row, col)."""
    match = re.fullmatch(r"([A-Za-z]{1,3})(\d{1,5})", cell_ref.strip())
    if not match:
        return None

    col_letters, row_str = match.groups()
    col = 0
    for ch in col_letters.upper():
        col = col * 26 + (ord(ch) - ord("A") + 1)
    return int(row_str), col


def _parse_load_request(user_text: str) -> dict:
    """Parse article load intent for article id, sheet, and anchor cell."""
    text = user_text or ""
    article_match = re.search(r"\b([A-Za-z0-9]{6,}-[A-Za-z0-9]{2,})\b", text)
    anchor_match = re.search(r"\b([A-Za-z]{1,3}\d{1,5})\b", text)

    # Sheet name parsing:
    # - supports: sheet Sheet2
    # - supports quoted names with spaces: sheet "My Sheet"
    quoted_sheet_match = re.search(r"\b(?:sheet|worksheet)\s+[\"']([^\"']+)[\"']", text, re.IGNORECASE)
    simple_sheet_match = re.search(r"\b(?:sheet|worksheet)\s+([A-Za-z0-9_\-]+)", text, re.IGNORECASE)

    sheet_name = None
    if quoted_sheet_match:
        sheet_name = quoted_sheet_match.group(1).strip()
    elif simple_sheet_match:
        sheet_name = simple_sheet_match.group(1).strip()

    parsed: dict[str, Any] = {
        "article_id": article_match.group(1) if article_match else "",
        "sheet_name": sheet_name,
        "start_row": 9,
        "start_col": 2,
    }

    if anchor_match:
        row_col = _cell_to_row_col(anchor_match.group(1))
        if row_col:
            parsed["start_row"], parsed["start_col"] = row_col

    return parsed

def _normalize_inference_base_url(endpoint: str) -> str:
    """Normalize Azure serverless inference endpoint to OpenAI SDK base_url."""
    base_url = endpoint.strip().rstrip("/")
    if base_url.endswith("/chat/completions"):
            base_url = base_url[:-len("/chat/completions")]
    if not base_url.endswith("/v1"):
            if base_url.endswith("/v1/"):
                base_url = base_url[:-1]
            else:
                base_url = f"{base_url}/v1"
    return base_url

def _parse_azure_openai_deployment_endpoint(endpoint: str) -> dict:
    """Parse Azure OpenAI deployment chat-completions endpoint."""
    parsed = urlparse(endpoint.strip())
    path_parts = [p for p in parsed.path.split("/") if p]

    deployment_name = None
    if "deployments" in path_parts:
            idx = path_parts.index("deployments")
            if idx + 1 < len(path_parts):
                deployment_name = path_parts[idx + 1]

    query = parse_qs(parsed.query)
    api_version = query.get("api-version", [None])[0]

    return {
            "azure_endpoint": f"{parsed.scheme}://{parsed.netloc}",
            "deployment": deployment_name,
            "api_version": api_version,
    }


def _post_json(url: str, payload: dict, timeout: float, headers: dict | None = None) -> dict:
    """POST JSON and return standardized dict response."""
    try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(url, json=payload, headers=headers)

            if response.status_code >= 400:
                try:
                    error_body = response.json()
                except Exception:
                    error_body = response.text
                return {
                    "success": False,
                    "statusCode": response.status_code,
                    "error": "HTTP request failed",
                    "details": error_body,
                }

            try:
                data = response.json()
            except Exception:
                return {
                    "success": False,
                    "error": "Expected JSON response but received non-JSON payload",
                    "statusCode": response.status_code,
                    "details": response.text,
                    "url": url,
                }

            return {"success": True, "data": data}

    except httpx.ConnectError:
            return {"success": False, "error": f"Connection failed to {url}"}
    except Exception as e:
            return {"success": False, "error": str(e)}

def _extract_calc_outputs(calc_result: dict) -> dict:
    """Extract outputs map from normalized CalcsLive response."""
    if not calc_result.get("success"):
            return {}
    data = calc_result.get("data")
    if not isinstance(data, dict):
            return {}

    # Common shape: {"outputs": {...}}
    if isinstance(data.get("outputs"), dict):
            return data["outputs"]

    # Common shape: {"data": {"outputs": {...}}}
    nested = data.get("data")
    if isinstance(nested, dict) and isinstance(nested.get("outputs"), dict):
            return nested["outputs"]

    # n8n style: {"data": {"calculation": {"outputs": {...}}}}
    if isinstance(nested, dict):
        calc = nested.get("calculation")
        if isinstance(calc, dict) and isinstance(calc.get("outputs"), dict):
            return calc["outputs"]

    # Alternative style: {"calculation": {"outputs": {...}}}
    calc = data.get("calculation")
    if isinstance(calc, dict) and isinstance(calc.get("outputs"), dict):
        return calc["outputs"]

    return {}


# ============ Excel Bridge Functions ============

def read_excel_pq_table(
    start_row: int | None = None,
    header_row: int | None = None,
    sheet_name: str | None = None,
) -> dict:
    """Read the PQ table from Excel via the bridge."""
    try:
            params: dict[str, Any] = {}
            if start_row is not None and header_row is not None:
                params["auto"] = "false"
                params["startRow"] = start_row
                params["headerRow"] = header_row
            else:
                params["auto"] = "true"

            if sheet_name:
                params["sheetName"] = sheet_name

            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{EXCEL_BRIDGE_URL}/excel/pq-for-calcslive", params=params)
            response.raise_for_status()
            return response.json()
    except httpx.ConnectError:
            return {"success": False, "error": f"Cannot connect to Excel Bridge at {EXCEL_BRIDGE_URL}"}
    except Exception as e:
            return {"success": False, "error": str(e)}

def write_excel_results(results: dict) -> dict:
    """Write calculated results back to Excel."""
    try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    f"{EXCEL_BRIDGE_URL}/excel/write-pq-results",
                    json={"results": results}
                )
            response.raise_for_status()
            return response.json()
    except httpx.ConnectError:
            return {"success": False, "error": f"Cannot connect to Excel Bridge at {EXCEL_BRIDGE_URL}"}
    except Exception as e:
            return {"success": False, "error": str(e)}


def write_excel_results_by_rows(
    results: dict,
    row_mapping: dict,
    value_col: int,
    sheet_name: str | None = None,
) -> dict:
    """Write outputs using explicit rows for deterministic targeting."""
    mapped_results: list[dict[str, Any]] = []
    for symbol, value in results.items():
        row = row_mapping.get(symbol)
        if row is not None:
            mapped_results.append({"row": row, "value": value})

    payload: dict[str, Any] = {
        "results": mapped_results,
        "valueCol": value_col,
    }
    if sheet_name:
        payload["sheetName"] = sheet_name

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(f"{EXCEL_BRIDGE_URL}/excel/write-pq-values", json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.ConnectError:
        return {"success": False, "error": f"Cannot connect to Excel Bridge at {EXCEL_BRIDGE_URL}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_excel_health() -> dict:
    """Check Excel connection health."""
    try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{EXCEL_BRIDGE_URL}/excel/health")
                response.raise_for_status()
                return response.json()
    except httpx.ConnectError:
            return {"success": False, "error": f"Cannot connect to Excel Bridge at {EXCEL_BRIDGE_URL}"}
    except Exception as e:
            return {"success": False, "error": str(e)}

def fetch_and_load_article(article_id: str) -> dict:
    """Compatibility wrapper with default anchor for existing calls."""
    return load_article_to_excel(article_id)


def fetch_calcslive_metadata(article_id: str) -> dict:
    """Fetch article metadata from CalcsLive validate endpoint."""
    if not article_id:
        return {"success": False, "error": "article_id is required"}

    headers = {"Content-Type": "application/json"}
    if CALCSLIVE_API_KEY:
        headers["Authorization"] = f"Bearer {CALCSLIVE_API_KEY}"

    validate_candidates = [
        f"{CALCSLIVE_API_URL.rstrip('/')}/validate",
    ]
    params = {"articleId": article_id}

    try:
        data = None
        with httpx.Client(timeout=15.0) as client:
            for validate_url in validate_candidates:
                response = client.get(validate_url, params=params, headers=headers)
                if response.status_code == 404:
                    continue
                response.raise_for_status()
                data = response.json()
                break

        if data is None:
            return {
                "success": False,
                "error": "CalcsLive validate endpoint not found",
                "details": {"candidates": validate_candidates},
            }
    except httpx.ConnectError:
        return {"success": False, "error": "Cannot connect to CalcsLive API"}
    except Exception as e:
        return {"success": False, "error": str(e)}

    if not data.get("success"):
        return {
            "success": False,
            "error": "CalcsLive validate failed",
            "details": data,
        }

    article = data.get("data", {}).get("article", {})
    input_pqs = article.get("inputPQs", [])
    output_pqs = article.get("outputPQs", [])

    def normalize_input(item: dict) -> dict:
        default_value = item.get("faceValue")
        if default_value is None:
            default_value = item.get("value")
        if default_value is None:
            default_value = item.get("defaultValue")

        return {
            "sym": item.get("symbol") or item.get("sym"),
            "unit": item.get("unit", ""),
            "description": item.get("description") or item.get("name") or "",
            "expression": "",
            "value": default_value,
        }

    def normalize_output(item: dict) -> dict:
        return {
            "sym": item.get("symbol") or item.get("sym"),
            "unit": item.get("unit", ""),
            "description": item.get("description") or item.get("name") or "",
            "expression": item.get("expression", ""),
            "value": None,
        }

    pqs = [normalize_input(pq) for pq in input_pqs] + [normalize_output(pq) for pq in output_pqs]

    response_data = data.get("data", {}) if isinstance(data, dict) else {}
    article_title = (
        article.get("articleTitle")
        or article.get("title")
        or article.get("name")
        or response_data.get("articleTitle")
        or ""
    )

    article_metadata = {
        "title": article_title,
        "articleId": article_id,
        "url": article.get("url") or f"https://www.calcslive.com/editor/{article_id}",
        "creator": article.get("creator") or article.get("createdBy") or "",
        "date": article.get("createdAt") or article.get("updatedAt") or "",
    }

    return {
        "success": True,
        "articleId": article_id,
        "article": article,
        "articleMetadata": article_metadata,
        "pqs": pqs,
        "inputCount": len(input_pqs),
        "outputCount": len(output_pqs),
    }


def load_article_to_excel(
    article_id: str,
    start_row: int = 9,
    start_col: int = 2,
    include_headers: bool = True,
    write_metadata: bool = True,
    prefill_outputs: bool = True,
    sheet_name: str | None = None,
) -> dict:
    """Fetch article metadata and populate an Excel table at a configurable anchor."""
    if not article_id:
        return {"success": False, "error": "article_id is required"}

    metadata = fetch_calcslive_metadata(article_id)
    if not metadata.get("success"):
        return metadata

    payload = {
        "pqs": metadata.get("pqs", []),
        "startRow": start_row,
        "startCol": start_col,
        "includeHeaders": include_headers,
        "writeMetadata": write_metadata,
        "articleMetadata": metadata.get("articleMetadata", {}),
    }
    if sheet_name:
        payload["sheetName"] = sheet_name

    try:
        with httpx.Client(timeout=15.0) as client:
            setup_res = client.post(f"{EXCEL_BRIDGE_URL}/excel/setup-from-article", json=payload)
            setup_res.raise_for_status()
            bridge_data = setup_res.json()
    except httpx.HTTPStatusError as e:
        detail = ""
        try:
            detail = e.response.text
        except Exception:
            detail = str(e)
        return {
            "success": False,
            "error": f"Failed to load article: {e}",
            "details": detail,
            "request": {
                "sheet_name": sheet_name,
                "start_row": start_row,
                "start_col": start_col,
            },
        }
    except httpx.ConnectError:
        return {"success": False, "error": f"Cannot connect to Excel Bridge at {EXCEL_BRIDGE_URL}"}
    except Exception as e:
        return {"success": False, "error": f"Failed to load article: {e}"}

    result: dict[str, Any] = {
        "success": True,
        "message": f"Loaded article {article_id} into Excel",
        "articleId": article_id,
        "inputCount": metadata.get("inputCount", 0),
        "outputCount": metadata.get("outputCount", 0),
        "anchor": {"startRow": start_row, "startCol": start_col},
        "bridgeResponse": bridge_data,
    }

    global LAST_TABLE_CONTEXT
    LAST_TABLE_CONTEXT = {
        "articleId": article_id,
        "startRow": bridge_data.get("dataStartRow", start_row),
        "headerRow": bridge_data.get("headerRow", start_row - 1),
        "startCol": start_col,
        "sheetName": bridge_data.get("sheetName", sheet_name),
    }

    if prefill_outputs:
        # Keep prefill path identical to manual recalc path for consistency.
        prefill_result = recalculate_excel_table()
        result["prefill"] = {
            "attempted": True,
            "success": bool(prefill_result.get("success")),
            "phase": prefill_result.get("phase"),
            "outputs": prefill_result.get("calculatedOutputs", {}),
            "error": prefill_result.get("error"),
            "details": prefill_result.get("details"),
            "writeResult": prefill_result.get("writeResult"),
        }

    return result


def recalculate_excel_table() -> dict:
    """Deterministic closed-loop recalc: read table, calculate, write outputs."""
    health = get_excel_health()
    if not health.get("success"):
        return {"success": False, "phase": "health", "error": health.get("error")}

    start_row = LAST_TABLE_CONTEXT.get("startRow")
    header_row = LAST_TABLE_CONTEXT.get("headerRow")
    sheet_name = LAST_TABLE_CONTEXT.get("sheetName")

    pq_data = read_excel_pq_table(start_row=start_row, header_row=header_row, sheet_name=sheet_name)
    _debug("Recalc read pq_data", {
        "success": pq_data.get("success"),
        "articleId": pq_data.get("articleId"),
        "inputsCount": len(pq_data.get("inputs", {})) if isinstance(pq_data.get("inputs"), dict) else None,
        "outputsCount": len(pq_data.get("outputs", {})) if isinstance(pq_data.get("outputs"), dict) else None,
        "rowMappingCount": len(pq_data.get("rowMapping", {})) if isinstance(pq_data.get("rowMapping"), dict) else None,
        "valueCol": pq_data.get("valueCol"),
        "sheetName": pq_data.get("sheetName"),
    })
    if not pq_data.get("success"):
        return {"success": False, "phase": "read", "error": pq_data.get("error")}

    calc_result = calculate_with_calcslive(
        pq_data.get("pqs", []),
        pq_data.get("inputs", {}),
        pq_data.get("outputs", {}),
        article_id=pq_data.get("articleId") or LAST_TABLE_CONTEXT.get("articleId"),
    )
    if not calc_result.get("success"):
        details = calc_result.get("details")
        error = calc_result.get("error") or "Calculation failed"
        if isinstance(details, list):
            summary = "; ".join(
                f"{d.get('url')} [{d.get('statusCode')}] {d.get('error')}"
                for d in details[:3]
                if isinstance(d, dict)
            )
            if summary:
                error = f"{error} | attempts: {summary}"
        elif details:
            error = f"{error} | details: {str(details)[:400]}"
        _debug("Recalc calculate failed", {"error": error, "details": details})
        return {"success": False, "phase": "calculate", "error": error, "details": details}

    _debug("Recalc calc_result", calc_result)
    outputs = _extract_calc_outputs(calc_result)
    _debug("Recalc extracted outputs", outputs)
    values = {sym: info.get("value") for sym, info in outputs.items() if isinstance(info, dict) and "value" in info}
    _debug("Recalc values to write", values)

    row_mapping = pq_data.get("rowMapping", {})
    value_col = pq_data.get("valueCol")
    _debug("Recalc write target", {"sheetName": sheet_name, "valueCol": value_col, "rowMapping": row_mapping})
    if row_mapping and value_col:
        write_result = write_excel_results_by_rows(values, row_mapping, value_col, sheet_name=sheet_name)
    else:
        write_result = write_excel_results(values)

    if not write_result.get("success"):
        return {"success": False, "phase": "write", "error": write_result.get("error")}

    return {
        "success": True,
        "phase": "complete",
        "articleId": pq_data.get("articleId"),
        "calculatedOutputs": values,
        "writeResult": write_result,
        "debug": {
            "sheetName": sheet_name,
            "valueCol": value_col,
            "rowMapping": row_mapping,
            "extractedOutputs": outputs,
            "valuesToWrite": values,
        },
    }


# ============ CalcsLive Functions ============

def calculate_with_calcslive(
    pqs: list,
    inputs: dict,
    outputs: dict = None,
    article_id: str | None = None,
) -> dict:
    """
    Perform a unit-aware calculation using CalcsLive run_script API.
    """
    payload = {"pqs": pqs}
    if inputs:
            payload["inputs"] = inputs
    if outputs:
            payload["outputs"] = outputs
    if article_id:
            payload["articleId"] = article_id

    headers = {"Content-Type": "application/json"}
    if CALCSLIVE_API_KEY:
            headers["Authorization"] = f"Bearer {CALCSLIVE_API_KEY}"

    run_candidates: list[tuple[str, dict[str, Any]]] = []

    # Prefer article-based endpoint when article ID is available.
    if article_id:
        article_payload: dict[str, Any] = {
            "articleId": article_id,
            "inputs": inputs or {},
        }
        if outputs:
            article_payload["outputs"] = outputs
        run_candidates.append((f"{CALCSLIVE_API_URL.rstrip('/')}/calculate", article_payload))

    # Script execution fallback (without article dependency).
    if pqs:
        script_payload = dict(payload)
        run_candidates.append((f"{CALCSLIVE_API_URL.rstrip('/')}/articles/uac-script/run", script_payload))

    failures: list[dict[str, Any]] = []
    _debug("Calc run candidates", [c[0] for c in run_candidates])
    for run_url, run_payload in run_candidates:
        _debug("Calc attempt payload", {"url": run_url, "payload": run_payload})
        attempt = _post_json(run_url, run_payload, timeout=30.0, headers=headers)
        _debug("Calc attempt response", {"url": run_url, "success": attempt.get("success"), "statusCode": attempt.get("statusCode"), "error": attempt.get("error")})
        if attempt.get("success"):
            data = attempt.get("data")
            if isinstance(data, dict) and data.get("success") is False:
                failures.append(
                    {
                        "url": run_url,
                        "error": data.get("error") or "API returned success=false",
                        "details": data,
                    }
                )
                continue
            _debug("Calc successful raw data", data)
            return {"success": True, "data": data}

        failures.append(
            {
                "url": run_url,
                "statusCode": attempt.get("statusCode"),
                "error": attempt.get("error"),
                "details": attempt.get("details"),
            }
        )

    _debug("Calc all failures", failures)

    auth_failure = next((f for f in failures if f.get("statusCode") == 401), None)
    if auth_failure:
        return {
            "success": False,
            "error": "CalcsLive API requires authentication",
            "details": auth_failure.get("details") or failures,
        }

    return {
        "success": False,
        "error": "All CalcsLive calculation endpoints failed",
        "details": failures,
    }


def create_calcslive_article_from_script(
    pqs: list,
    title: str | None = None,
    description: str | None = None,
    access_level: str | None = None,
    category: str | None = None,
    tags: list[str] | None = None,
    inputs: dict | None = None,
    outputs: dict | None = None,
) -> dict:
    """Create a persistent CalcsLive article from PQ script definitions."""
    if not pqs:
        return {"success": False, "error": "pqs is required and cannot be empty"}

    payload: dict[str, Any] = {
        "pqs": pqs,
        "inputs": inputs or {},
        "outputs": outputs or {},
    }
    if title:
        payload["title"] = title
    if description:
        payload["description"] = description
    if access_level:
        payload["accessLevel"] = access_level
    if category:
        payload["category"] = category
    if tags:
        payload["tags"] = tags

    headers = {"Content-Type": "application/json"}
    if CALCSLIVE_API_KEY:
        headers["Authorization"] = f"Bearer {CALCSLIVE_API_KEY}"

    create_url = f"{CALCSLIVE_API_URL.rstrip('/')}/articles/uac-script/create"
    result = _post_json(create_url, payload, timeout=45.0, headers=headers)
    if not result.get("success"):
        return {
            "success": False,
            "error": result.get("error") or "Create article request failed",
            "statusCode": result.get("statusCode"),
            "details": result.get("details"),
        }

    data = result.get("data")
    if isinstance(data, dict) and data.get("success") is False:
        return {
            "success": False,
            "error": data.get("error") or "CalcsLive create article failed",
            "details": data,
        }

    article = {}
    if isinstance(data, dict):
        article = data.get("data", {}).get("article", {}) if isinstance(data.get("data"), dict) else {}

    return {
        "success": True,
        "data": data,
        "article": {
            "id": article.get("id"),
            "title": article.get("title"),
            "url": article.get("url"),
            "accessLevel": article.get("accessLevel"),
        },
    }


# ============ Agent Core Class ============

class CalcsLiveAgent:
    def __init__(self):
            # Check for serverless inference endpoint first (Models-as-a-Service)
            inference_endpoint = os.getenv("AZURE_AI_INFERENCE_ENDPOINT")
            inference_key = os.getenv("AZURE_AI_INFERENCE_KEY")

            # Fall back to project SDK
            project_endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
            self.model_deployment = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "grok-3-mini")
            inference_model = os.getenv("AZURE_AI_INFERENCE_MODEL", self.model_deployment)

            self.openai_client = None
            self.mode = "Unknown"

            if inference_endpoint and inference_key:
                self.mode = "Serverless Inference"
                if "/openai/deployments/" in inference_endpoint:
                    from openai import AzureOpenAI

                    parsed = _parse_azure_openai_deployment_endpoint(inference_endpoint)
                    api_version = os.getenv("AZURE_AI_INFERENCE_API_VERSION") or parsed.get("api_version") or "2024-05-01-preview"
                    deployment_from_url = parsed.get("deployment")

                    if deployment_from_url:
                            self.model_deployment = deployment_from_url

                    self.openai_client = AzureOpenAI(
                            api_key=inference_key,
                            azure_endpoint=parsed["azure_endpoint"],
                            api_version=api_version,
                    )
                else:
                    from openai import OpenAI
                    base_url = _normalize_inference_base_url(inference_endpoint)
                    self.openai_client = OpenAI(
                            base_url=base_url,
                            api_key=inference_key,
                    )
                    self.model_deployment = inference_model

            elif project_endpoint:
                self.mode = "Azure AI Projects"
                from azure.ai.projects import AIProjectClient
                from azure.identity import DefaultAzureCredential
                
                credential = DefaultAzureCredential()
                project_client = AIProjectClient(
                    endpoint=project_endpoint,
                    credential=credential
                )
                self.openai_client = project_client.get_openai_client()
            else:
                raise ValueError("No Azure endpoint configured. Set AZURE_AI_INFERENCE_ENDPOINT or AZURE_AI_PROJECT_ENDPOINT")

            self.tools = [
                {
                    "type": "function",
                    "function": {
                            "name": "get_excel_health",
                            "description": "Check if Excel is connected and has a workbook open",
                            "parameters": {"type": "object", "properties": {}, "required": []}
                    }
                },
                {
                    "type": "function",
                    "function": {
                            "name": "read_excel_pq_table",
                            "description": "Read the PQ (Physical Quantity) table from Excel including inputs, outputs, and their values/units",
                            "parameters": {"type": "object", "properties": {}, "required": []}
                    }
                },
                {
                    "type": "function",
                    "function": {
                            "name": "write_excel_results",
                            "description": "Write calculated results back to Excel",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "results": {
                                            "type": "object",
                                            "description": "Dict mapping symbol names to values, e.g., {\"V\": 0.0965, \"m\": 212.75}"
                                    }
                                },
                                "required": ["results"]
                            }
                    }
                },
                {
                    "type": "function",
                    "function": {
                            "name": "calculate_with_calcslive",
                            "description": "Perform unit-aware calculation using CalcsLive API",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "pqs": {
                                            "type": "array",
                                            "description": "List of PQ definitions with sym, unit, value (for inputs) or expression (for outputs)"
                                    },
                                    "inputs": {
                                            "type": "object",
                                            "description": "Dict of input values, e.g., {\"D\": {\"value\": 2, \"unit\": \"in\"}}"
                                    },
                                    "outputs": {
                                            "type": "object",
                                            "description": "Optional requested outputs with unit preferences, e.g., {\"V\": {\"unit\": \"L\"}}"
                                    }
                                },
                                "required": ["pqs", "inputs"]
                            }
                    }
                },
                {
                    "type": "function",
                    "function": {
                            "name": "fetch_calcslive_metadata",
                            "description": "Fetch metadata and PQ definitions for an existing CalcsLive article using article ID",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "article_id": {
                                            "type": "string",
                                            "description": "The CalcsLive article ID, e.g., '3M7ALBF4U-3BL'"
                                    }
                                },
                                "required": ["article_id"]
                            }
                    }
                },
                {
                    "type": "function",
                    "function": {
                            "name": "load_article_to_excel",
                            "description": "Fetch a CalcsLive article by ID and construct its input/output PQ table in Excel at a configurable anchor",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "article_id": {
                                            "type": "string",
                                            "description": "The CalcsLive article ID, e.g., '3M7ALBF4U-3BL'"
                                    },
                                    "start_row": {
                                            "type": "integer",
                                            "description": "Data start row for PQ entries (default 9). Header goes one row above."
                                    },
                                    "start_col": {
                                            "type": "integer",
                                            "description": "Start column for Description field (default 2 = column B)."
                                    },
                                    "sheet_name": {
                                            "type": "string",
                                            "description": "Optional target worksheet name. Uses active sheet when omitted."
                                    },
                                    "include_headers": {
                                            "type": "boolean",
                                            "description": "Whether to write header row above table."
                                    },
                                    "write_metadata": {
                                            "type": "boolean",
                                            "description": "Whether to write article metadata rows above the table."
                                    },
                                    "prefill_outputs": {
                                            "type": "boolean",
                                            "description": "Whether to run initial calculation and prefill output values after table creation."
                                    }
                                },
                                "required": ["article_id"]
                            }
                    }
                },
                {
                    "type": "function",
                    "function": {
                            "name": "recalculate_excel_table",
                            "description": "Deterministic closed-loop recalc: read current Excel table, run CalcsLive calculation, and write outputs back",
                            "parameters": {"type": "object", "properties": {}, "required": []}
                    }
                },
                {
                    "type": "function",
                    "function": {
                            "name": "create_calcslive_article_from_script",
                            "description": "Create a persistent CalcsLive article from PQ definitions and optional metadata",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "pqs": {
                                            "type": "array",
                                            "description": "List of PQ definitions with sym, unit, and either value (input) or expression (output)"
                                    },
                                    "title": {"type": "string", "description": "Optional article title"},
                                    "description": {"type": "string", "description": "Optional article description"},
                                    "accessLevel": {"type": "string", "description": "Optional visibility, usually public or private"},
                                    "category": {"type": "string", "description": "Optional article category"},
                                    "tags": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "description": "Optional list of tags"
                                    },
                                    "inputs": {
                                            "type": "object",
                                            "description": "Optional input overrides, e.g. {\"D\": {\"value\": 2, \"unit\": \"in\"}}"
                                    },
                                    "outputs": {
                                            "type": "object",
                                            "description": "Optional output unit preferences, e.g. {\"V\": {\"unit\": \"L\"}}"
                                    }
                                },
                                "required": ["pqs"]
                            }
                    }
                }
            ]

            self.system_message = """You are the CalcsLive Agent, helping users perform unit-aware calculations in Excel.

Your workflow:
1. First, check Excel health to ensure connection
2. If the user asks to "Load an Article", use `load_article_to_excel` to build the physical table structure in Excel using configurable anchor parameters.
3. Read the PQ (Physical Quantity) table from Excel (`read_excel_pq_table`) to get current inputs and output definitions.
4. Use CalcsLive (`calculate_with_calcslive`) to calculate the outputs with proper unit conversions.
5. Write the calculated results back to Excel (`write_excel_results`).
6. If the user wants a brand-new calculation/article, define a PQ script and call `create_calcslive_article_from_script`.

Key concepts:
- PQ = Physical Quantity (value + unit, e.g., "2 inches", "3 cm")
- Inputs = PQs where user provides values (no expression/formula). These are highlighted Yellow in Excel.
- Outputs = PQs with expressions that need calculation. These are highlighted Green in Excel.
- Data-Driven Closed-Loop: The user types numbers/units into Yellow cells then asks to "Update" or "Recalculate"; call `recalculate_excel_table` for deterministic full-cycle execution.
- Do not mention or require `=CalcsLive(...)` formulas in Excel cells; expression text in the Expression column is enough.

Always explain what you're doing. Show your tool results to the user as they happen if it takes multiple steps.
"""

    def execute_tool(self, func_name: str, func_args: dict) -> dict:
            """Execute a tool and return the result."""
            if func_name == "get_excel_health":
                return get_excel_health()
            elif func_name == "fetch_calcslive_metadata":
                return fetch_calcslive_metadata(func_args.get("article_id", ""))
            elif func_name == "load_article_to_excel":
                return load_article_to_excel(
                    article_id=func_args.get("article_id", ""),
                    start_row=func_args.get("start_row", 9),
                    start_col=func_args.get("start_col", 2),
                    include_headers=func_args.get("include_headers", True),
                    write_metadata=func_args.get("write_metadata", True),
                    prefill_outputs=func_args.get("prefill_outputs", True),
                    sheet_name=func_args.get("sheet_name"),
                )
            elif func_name == "recalculate_excel_table":
                return recalculate_excel_table()
            elif func_name == "read_excel_pq_table":
                return read_excel_pq_table()
            elif func_name == "write_excel_results":
                return write_excel_results(func_args.get("results", {}))
            elif func_name == "calculate_with_calcslive":
                return calculate_with_calcslive(
                    func_args.get("pqs", []),
                    func_args.get("inputs", {}),
                    func_args.get("outputs", {}),
                )
            elif func_name == "create_calcslive_article_from_script":
                return create_calcslive_article_from_script(
                    pqs=func_args.get("pqs", []),
                    title=func_args.get("title"),
                    description=func_args.get("description"),
                    access_level=func_args.get("accessLevel") or func_args.get("access_level"),
                    category=func_args.get("category"),
                    tags=func_args.get("tags"),
                    inputs=func_args.get("inputs", {}),
                    outputs=func_args.get("outputs", {}),
                )
            else:
                return {"error": f"Unknown function: {func_name}"}

    def chat_interact(self, messages: List[Dict]) -> Tuple[List[Dict], List[tuple]]:
            """
            Process an agent turn given existing chat history.
            Returns the updated conversation history, and an optional list of executed (tool_name: result) tuples
            for the UI to optionally display.
            """
            
            tool_round = 0
            executed_tools = []

            latest_user = ""
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    latest_user = msg.get("content", "") or ""
                    break

            lowered = latest_user.lower()
            if any(k in lowered for k in ["load calculation", "load article", "populate excel", "setup calculation"]):
                parsed = _parse_load_request(latest_user)
                health = get_excel_health()
                executed_tools.append(("get_excel_health", health))

                if not health.get("success"):
                    messages.append({
                        "role": "assistant",
                        "content": f"I cannot access Excel yet: {health.get('error')}",
                    })
                    return messages, executed_tools

                if not parsed.get("article_id"):
                    messages.append({
                        "role": "assistant",
                        "content": "Please provide a valid article ID (for example: 3M7ALBF4U-3BL).",
                    })
                    return messages, executed_tools

                load_result = load_article_to_excel(
                    article_id=parsed["article_id"],
                    start_row=parsed["start_row"],
                    start_col=parsed["start_col"],
                    include_headers=True,
                    write_metadata=True,
                    sheet_name=parsed.get("sheet_name"),
                )
                executed_tools.append(("load_article_to_excel", load_result))

                if load_result.get("success"):
                    bridge = load_result.get("bridgeResponse", {})
                    target_sheet = bridge.get("sheetName", health.get("sheetName", "active sheet"))
                    prefill = load_result.get("prefill", {})
                    prefill_text = ""
                    if prefill.get("attempted"):
                        if prefill.get("success"):
                            prefill_text = " Initial output values were prefilled successfully."
                        else:
                            prefill_text = f" Prefill was attempted but failed: {prefill.get('error', 'unknown reason')}."
                    messages.append({
                        "role": "assistant",
                        "content": (
                            f"Loaded article `{parsed['article_id']}` into Excel on `{target_sheet}` at "
                            f"row {parsed['start_row']}, col {parsed['start_col']}. "
                            f"You can now change input values/units and ask me to recalculate.{prefill_text}"
                        ),
                    })
                else:
                    messages.append({
                        "role": "assistant",
                        "content": f"I could not load the article: {load_result.get('error')}",
                    })
                return messages, executed_tools

            if any(k in lowered for k in ["recalculate", "re-calculate", "update outputs", "update values", "update the results", "refresh calculation"]):
                recalc_result = recalculate_excel_table()
                executed_tools.append(("recalculate_excel_table", recalc_result))
                if recalc_result.get("success"):
                    outputs = recalc_result.get("calculatedOutputs", {})
                    messages.append({
                        "role": "assistant",
                        "content": f"Recalculation complete. Updated outputs: {outputs}",
                    })
                else:
                    messages.append({
                        "role": "assistant",
                        "content": f"Recalculation failed at {recalc_result.get('phase')}: {recalc_result.get('error')}",
                    })
                return messages, executed_tools
            
            while True:
                tool_round += 1
                if tool_round > 8:
                    messages.append({"role": "assistant", "content": "Stopped after too many tool rounds for one prompt."})
                    return messages, executed_tools

                try:
                    response = self.openai_client.chat.completions.create(
                            model=self.model_deployment,
                            messages=messages,
                            tools=self.tools
                    )
                except Exception as e:
                    messages.append({"role": "assistant", "content": f"Error calling model - {e}"})
                    return messages, executed_tools

                assistant_message = response.choices[0].message

                if assistant_message.tool_calls:
                    messages.append({
                            "role": "assistant",
                            "content": assistant_message.content,
                            "tool_calls": [
                                {
                                    "id": tc.id,
                                    "type": "function",
                                    "function": {
                                            "name": tc.function.name,
                                            "arguments": tc.function.arguments
                                    }
                                }
                                for tc in assistant_message.tool_calls
                            ]
                    })

                    for tool_call in assistant_message.tool_calls:
                            func_name = tool_call.function.name
                            try:
                                func_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                            except json.JSONDecodeError:
                                func_args = {}

                            result = self.execute_tool(func_name, func_args)
                            executed_tools.append((func_name, result))
                            
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(result)
                            })

                    # Continue loop to allow model to observe tool outputs
                    continue
                else:
                    if assistant_message.content:
                            messages.append({
                                "role": "assistant",
                                "content": assistant_message.content
                            })
                    return messages, executed_tools
