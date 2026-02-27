"""
MCP wrapper for the local Excel bridge.

This server exposes a small MCP tool surface that forwards requests
to the existing FastAPI Excel bridge at http://127.0.0.1:8001.
"""

from __future__ import annotations

import os
import argparse
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP


BRIDGE_URL = os.getenv("EXCEL_BRIDGE_URL", "http://127.0.0.1:8001").rstrip("/")

mcp = FastMCP("calcslive-excel-mcp")


def _get(path: str, timeout: float = 10.0) -> dict[str, Any]:
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(f"{BRIDGE_URL}{path}")
            response.raise_for_status()
            return response.json()
    except httpx.ConnectError:
        return {
            "success": False,
            "error": f"Cannot connect to Excel bridge at {BRIDGE_URL}",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def _post(path: str, payload: dict[str, Any], timeout: float = 10.0) -> dict[str, Any]:
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(f"{BRIDGE_URL}{path}", json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.ConnectError:
        return {
            "success": False,
            "error": f"Cannot connect to Excel bridge at {BRIDGE_URL}",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def excel_health() -> dict[str, Any]:
    """Check whether the local Excel bridge can access an open Excel workbook."""
    return _get("/excel/health", timeout=5.0)


@mcp.tool()
def excel_get_pq_for_calcslive() -> dict[str, Any]:
    """Read PQ inputs/outputs from Excel in CalcsLive-ready structure."""
    return _get("/excel/pq-for-calcslive", timeout=10.0)


@mcp.tool()
def excel_write_pq_results(results: dict[str, Any]) -> dict[str, Any]:
    """
    Write calculation results back to Excel by symbol.

    Example:
    {"V": 0.0965, "m": 212.75}
    """
    return _post("/excel/write-pq-results", {"results": results}, timeout=10.0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CalcsLive Excel MCP wrapper")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default=os.getenv("EXCEL_MCP_TRANSPORT", "stdio"),
        help="MCP transport mode",
    )
    parser.add_argument(
        "--mount-path",
        default=os.getenv("EXCEL_MCP_MOUNT_PATH", None),
        help="Optional mount path for HTTP transports",
    )
    args = parser.parse_args()

    mcp.run(transport=args.transport, mount_path=args.mount_path)
