import json
import os
from typing import Any
from urllib.parse import quote

import httpx
from dotenv import load_dotenv


load_dotenv()

CALCSLIVE_API_URL = os.getenv("CALCSLIVE_API_URL", "https://calcslive.com/api/v1")
CALCSLIVE_API_KEY = os.getenv("CALCSLIVE_API_KEY", "")
CALCSLIVE_DEBUG = os.getenv("CALCSLIVE_DEBUG", "1").strip().lower() in {"1", "true", "yes", "on"}


def _debug(message: str, data: Any = None) -> None:
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


def _post_json(url: str, payload: dict, timeout: float, headers: dict | None = None) -> dict:
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


def _extract_script_payload(data: dict) -> dict:
    if not isinstance(data, dict):
        return {}
    nested = data.get("data")
    if isinstance(nested, dict):
        return nested
    return data


def _normalize_script_result(data: dict) -> dict:
    payload = _extract_script_payload(data)
    calculation = payload.get("calculation") if isinstance(payload.get("calculation"), dict) else {}
    human_readable = payload.get("humanReadable")
    warnings = payload.get("warnings") if isinstance(payload.get("warnings"), list) else []
    category_metadata = payload.get("categoryMetadata") if isinstance(payload.get("categoryMetadata"), dict) else {}

    normalized: dict[str, Any] = {
        "calculation": calculation,
        "inputs": calculation.get("inputs", {}) if isinstance(calculation, dict) else {},
        "outputs": calculation.get("outputs", {}) if isinstance(calculation, dict) else {},
        "warnings": warnings,
        "categoryMetadata": category_metadata,
        "humanReadable": human_readable,
        "raw": payload,
    }

    article = payload.get("article")
    if isinstance(article, dict):
        normalized["article"] = article

    return normalized


def fetch_calcslive_metadata(article_id: str) -> dict:
    headers = {}
    if CALCSLIVE_API_KEY:
        headers["Authorization"] = f"Bearer {CALCSLIVE_API_KEY}"

    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.get(
                f"{CALCSLIVE_API_URL.rstrip('/')}/validate",
                params={"articleId": article_id},
                headers=headers,
            )

        if response.status_code >= 400:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            return {
                "success": False,
                "statusCode": response.status_code,
                "error": "Metadata request failed",
                "details": error_body,
            }

        data = response.json()
        article = data.get("data", {}).get("article", {})
        return {
            "success": True,
            "data": article,
        }
    except httpx.ConnectError:
        return {"success": False, "error": f"Cannot connect to CalcsLive API at {CALCSLIVE_API_URL}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def calculate_with_calcslive(
    pqs: list,
    inputs: dict,
    outputs: dict,
    article_id: str | None = None,
) -> dict:
    payload: dict[str, Any] = {"inputs": inputs or {}}
    if outputs:
        payload["outputs"] = outputs
    if article_id:
        payload["articleId"] = article_id

    headers = {"Content-Type": "application/json"}
    if CALCSLIVE_API_KEY:
        headers["Authorization"] = f"Bearer {CALCSLIVE_API_KEY}"

    run_candidates: list[tuple[str, dict[str, Any]]] = []
    if article_id:
        article_payload: dict[str, Any] = {
            "articleId": article_id,
            "inputs": inputs or {},
        }
        if outputs:
            article_payload["outputs"] = outputs
        run_candidates.append((f"{CALCSLIVE_API_URL.rstrip('/')}/calculate", article_payload))

    if pqs:
        script_payload = dict(payload)
        script_payload["pqs"] = pqs
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


def run_calcslive_script(pqs: list, inputs: dict | None = None, outputs: dict | None = None) -> dict:
    if not pqs:
        return {"success": False, "error": "pqs is required and cannot be empty"}

    payload: dict[str, Any] = {
        "pqs": pqs,
        "inputs": inputs or {},
        "outputs": outputs or {},
    }
    headers = {"Content-Type": "application/json"}
    if CALCSLIVE_API_KEY:
        headers["Authorization"] = f"Bearer {CALCSLIVE_API_KEY}"

    run_url = f"{CALCSLIVE_API_URL.rstrip('/')}/articles/uac-script/run"
    result = _post_json(run_url, payload, timeout=45.0, headers=headers)
    if not result.get("success"):
        return {
            "success": False,
            "error": result.get("error") or "Run script request failed",
            "statusCode": result.get("statusCode"),
            "details": result.get("details"),
        }

    data = result.get("data")
    if isinstance(data, dict) and data.get("success") is False:
        return {
            "success": False,
            "error": (data.get("error") or {}).get("message") if isinstance(data.get("error"), dict) else data.get("error") or "CalcsLive run script failed",
            "details": data,
        }

    normalized = _normalize_script_result(data)
    return {"success": True, **normalized}


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

    normalized = _normalize_script_result(data)
    article = normalized.get("article", {}) if isinstance(normalized.get("article"), dict) else {}
    return {
        "success": True,
        "data": data,
        **normalized,
        "article": {
            "id": article.get("id"),
            "title": article.get("title"),
            "url": article.get("url"),
            "accessLevel": article.get("accessLevel"),
            "createdAt": article.get("createdAt"),
        },
    }


def discover_calcslive_units(search: str | None = None, category: str | None = None, limit: int = 100) -> dict:
    headers: dict[str, str] = {}
    if CALCSLIVE_API_KEY:
        headers["Authorization"] = f"Bearer {CALCSLIVE_API_KEY}"

    params: dict[str, Any] = {"limit": limit}
    if search:
        params["search"] = search
    if category:
        params["category"] = category

    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.get(f"{CALCSLIVE_API_URL.rstrip('/')}/units", params=params, headers=headers)

        if response.status_code >= 400:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            return {
                "success": False,
                "statusCode": response.status_code,
                "error": "Units discovery request failed",
                "details": error_body,
            }

        data = response.json()
    except httpx.ConnectError:
        return {"success": False, "error": "Cannot connect to CalcsLive API"}
    except Exception as e:
        return {"success": False, "error": str(e)}

    payload = data.get("data", {}) if isinstance(data, dict) else {}
    return {
        "success": True,
        "units": payload.get("units", []),
        "categories": payload.get("categories", []),
        "meta": data.get("meta", {}) if isinstance(data, dict) else {},
        "raw": data,
    }


def resolve_calcslive_unit_alias(alias: str, category_hint: str | None = None) -> dict:
    if not alias:
        return {"success": False, "error": "alias is required"}

    headers: dict[str, str] = {}
    if CALCSLIVE_API_KEY:
        headers["Authorization"] = f"Bearer {CALCSLIVE_API_KEY}"

    params: dict[str, Any] = {}
    if category_hint:
        params["categoryHint"] = category_hint

    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.get(
                f"{CALCSLIVE_API_URL.rstrip('/')}/units/resolve/{quote(alias, safe='')}",
                params=params,
                headers=headers,
            )

        if response.status_code >= 400:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            return {
                "success": False,
                "statusCode": response.status_code,
                "error": "Unit alias resolution request failed",
                "details": error_body,
            }

        data = response.json()
    except httpx.ConnectError:
        return {"success": False, "error": "Cannot connect to CalcsLive API"}
    except Exception as e:
        return {"success": False, "error": str(e)}

    return {
        "success": True,
        "alias": alias,
        "isAmbiguous": bool(data.get("isAmbiguous")) if isinstance(data, dict) else False,
        "resolution": data.get("resolution") if isinstance(data, dict) else None,
        "matches": data.get("matches", []) if isinstance(data, dict) else [],
        "raw": data,
    }
