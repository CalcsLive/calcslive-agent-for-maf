# main.py
# FastAPI server for Excel COM automation bridge
# Runs on localhost:8001 for CalcsLive Agent integration

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Any, Dict
import uvicorn

from excel_api import (
    get_health,
    read_range,
    write_cell,
    write_range,
    read_pq_table,
    write_pq_values,
    write_pq_results,
    setup_pq_table_from_article,
    find_article_id,
    find_pq_table
)
from live_watcher import live_recalc_watcher

VERSION = "0.2.0"

app = FastAPI(
    title="CalcsLive Excel Bridge",
    description="HTTP bridge for Excel COM automation with CalcsLive integration",
    version=VERSION
)

# CORS for CalcsLive dashboard and Azure-hosted agent
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "https://calcslive.com",
        "https://www.calcslive.com",
        "*"  # Allow Azure agent to connect
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ Pydantic Models ============

class ReadRangeRequest(BaseModel):
    range: str
    sheetName: Optional[str] = None


class WriteCellRequest(BaseModel):
    cell: str
    value: Any
    sheetName: Optional[str] = None


class WriteRangeRequest(BaseModel):
    range: str
    values: List[List[Any]]
    sheetName: Optional[str] = None


class ReadPqTableRequest(BaseModel):
    startRow: int = 2
    headerRow: int = 1
    sheetName: Optional[str] = None


class PqResult(BaseModel):
    row: int
    value: Any


class WritePqValuesRequest(BaseModel):
    results: List[Dict[str, Any]]
    valueCol: int = 4
    sheetName: Optional[str] = None


class PqDefinition(BaseModel):
    sym: str
    unit: str
    description: Optional[str] = ""
    expression: Optional[str] = ""
    value: Optional[float] = None


class SetupFromArticleRequest(BaseModel):
    pqs: List[PqDefinition]
    startRow: int = 2
    startCol: int = 1
    includeHeaders: bool = True
    writeMetadata: bool = False
    articleMetadata: Optional[Dict[str, Any]] = None
    sheetName: Optional[str] = None


class LiveModeStartRequest(BaseModel):
    autoDetect: bool = True
    startRow: Optional[int] = None
    headerRow: Optional[int] = None
    debounceSeconds: float = 1.5
    sheetName: Optional[str] = None


# ============ Endpoints ============

@app.get("/")
def root():
    """Root health check endpoint."""
    return {
        "status": "ok",
        "service": "CalcsLive Excel Bridge",
        "version": VERSION
    }


@app.get("/excel/health")
def health_check():
    """
    Check Excel connection health.
    Returns connection status and active document info.
    """
    result = get_health()
    return result


@app.post("/excel/read-range")
def api_read_range(request: ReadRangeRequest):
    """
    Read values from an Excel range.

    Example request:
    {
        "range": "A1:E10",
        "sheetName": "Sheet1"  // optional
    }
    """
    result = read_range(request.range, request.sheetName)

    if not result.get("success"):
        raise HTTPException(status_code=503, detail=result.get("error"))

    return result


@app.post("/excel/write-cell")
def api_write_cell(request: WriteCellRequest):
    """
    Write a value to a single Excel cell.

    Example request:
    {
        "cell": "D5",
        "value": 123.456,
        "sheetName": "Sheet1"  // optional
    }
    """
    result = write_cell(request.cell, request.value, request.sheetName)

    if not result.get("success"):
        raise HTTPException(status_code=503, detail=result.get("error"))

    return result


@app.post("/excel/write-range")
def api_write_range(request: WriteRangeRequest):
    """
    Write values to an Excel range.

    Example request:
    {
        "range": "A1:C3",
        "values": [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
        "sheetName": "Sheet1"  // optional
    }
    """
    result = write_range(request.range, request.values, request.sheetName)

    if not result.get("success"):
        raise HTTPException(status_code=503, detail=result.get("error"))

    return result


@app.post("/excel/read-pq-table")
def api_read_pq_table(request: ReadPqTableRequest):
    """
    Read Physical Quantity (PQ) table from Excel.
    Expects columns: Description | Symbol | Expression | Value | Unit

    Example request:
    {
        "startRow": 2,     // first data row
        "headerRow": 1,    // header row
        "sheetName": "Calc"  // optional
    }

    Returns list of PQs with their values and whether they are inputs/outputs.
    """
    result = read_pq_table(request.startRow, request.headerRow, request.sheetName)

    if not result.get("success"):
        raise HTTPException(status_code=503, detail=result.get("error"))

    return result


@app.post("/excel/write-pq-values")
def api_write_pq_values(request: WritePqValuesRequest):
    """
    Write calculated PQ values back to Excel.

    Example request:
    {
        "results": [
            {"row": 5, "value": 0.0965},
            {"row": 6, "value": 96.5}
        ],
        "valueCol": 4,  // D column
        "sheetName": "Calc"  // optional
    }
    """
    result = write_pq_values(request.results, request.valueCol, request.sheetName)

    if not result.get("success"):
        raise HTTPException(status_code=503, detail=result.get("error"))

    return result


@app.post("/excel/setup-from-article")
def api_setup_from_article(request: SetupFromArticleRequest):
    """
    Setup a PQ table in Excel from a CalcsLive article structure.
    Creates columns: Description | Symbol | Expression | Value | Unit

    Example request:
    {
        "pqs": [
            {"sym": "D", "unit": "in", "description": "Diameter"},
            {"sym": "H", "unit": "cm", "description": "Height"},
            {"sym": "V", "unit": "L", "expression": "pi*D^2/4*H", "description": "Volume"}
        ],
        "startRow": 2,
        "startCol": 1,
        "includeHeaders": true,
        "sheetName": "Calc"  // optional
    }
    """
    # Convert Pydantic models to dicts
    pqs_dict = [pq.model_dump() for pq in request.pqs]

    result = setup_pq_table_from_article(
        pqs_dict,
        request.startRow,
        request.startCol,
        request.includeHeaders,
        request.writeMetadata,
        request.articleMetadata,
        request.sheetName
    )

    if not result.get("success"):
        raise HTTPException(status_code=503, detail=result.get("error"))

    return result


@app.post("/excel/live-mode/start")
def api_live_mode_start(request: LiveModeStartRequest):
    """Start event-driven live recalculation watcher on Excel sheet changes."""
    result = live_recalc_watcher.start(
        auto_detect=request.autoDetect,
        start_row=request.startRow,
        header_row=request.headerRow,
        sheet_name=request.sheetName,
        debounce_seconds=request.debounceSeconds,
    )
    if not result.get("success"):
        raise HTTPException(status_code=503, detail=result.get("error", "Failed to start live mode"))
    return result


@app.post("/excel/live-mode/stop")
def api_live_mode_stop():
    """Stop event-driven live recalculation watcher."""
    return live_recalc_watcher.stop()


@app.get("/excel/live-mode/status")
def api_live_mode_status():
    """Get current live recalculation watcher status and last run info."""
    return {"success": True, "status": live_recalc_watcher.status()}


# ============ Auto-Detection Endpoints (ArticleID-relative) ============

@app.get("/excel/find-article-id")
def api_find_article_id(sheetName: Optional[str] = None):
    """
    Find ArticleID in the spreadsheet.
    Searches for 'ArticleID' label and returns the adjacent cell's value.

    Returns:
    {
        "articleId": "3MLCVKCU3-2K8",
        "labelCell": "B7",
        "valueCell": "C7",
        "suggestedHeaderRow": 9,
        "suggestedDataStartRow": 10
    }
    """
    result = find_article_id(sheetName)

    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))

    return result


@app.get("/excel/find-pq-table")
def api_find_pq_table(sheetName: Optional[str] = None):
    """
    Auto-detect PQ table by finding ArticleID first.
    Returns the full PQ table with article info and row mappings.

    Returns:
    {
        "articleId": "3MLCVKCU3-2K8",
        "pqs": [...],
        "headerRow": 9,
        "dataStartRow": 10,
        "columns": {"description": 2, "symbol": 3, ...}
    }
    """
    result = find_pq_table(sheetName)

    if not result.get("success"):
        raise HTTPException(status_code=503, detail=result.get("error"))

    return result


class WritePqResultsRequest(BaseModel):
    results: Dict[str, Any]  # {"V": 0.0965, "m": 96.5}
    sheetName: Optional[str] = None


@app.post("/excel/write-pq-results")
def api_write_pq_results(request: WritePqResultsRequest):
    """
    Write CalcsLive calculation results back to the auto-detected PQ table.
    Uses find_pq_table() to locate the Value column.

    Example request:
    {
        "results": {"V": 0.0965, "m": 96.5},
        "sheetName": "Sheet1"  // optional
    }
    """
    result = write_pq_results(request.results, request.sheetName)

    if not result.get("success"):
        raise HTTPException(status_code=503, detail=result.get("error"))

    return result


# ============ CalcsLive Integration Endpoints ============

@app.get("/excel/pq-for-calcslive")
def api_get_pq_for_calcslive(
    auto: bool = True,
    startRow: int = 2,
    headerRow: int = 1,
    sheetName: Optional[str] = None
):
    """
    Read PQ table and format for CalcsLive API input.
    Returns inputs ready for calcslive_run_script or calcslive_calculate.

    Args:
        auto: If True (default), auto-detect table from ArticleID position.
              If False, use explicit startRow/headerRow.
        startRow: First data row (only used if auto=False)
        headerRow: Header row (only used if auto=False)
        sheetName: Optional sheet name

    Returns:
    {
        "articleId": "3MLCVKCU3-2K8",
        "inputs": {"D": {"value": 2, "unit": "in"}, "H": {"value": 3, "unit": "cm"}},
        "outputs": {"V": {"unit": "L"}, "m": {"unit": "lbm"}},
        "pqs": [full PQ definitions for calcslive_run_script],
        "rowMapping": {"D": 10, "H": 11, ...}
    }
    """
    if auto:
        result = find_pq_table(sheetName)
    else:
        result = read_pq_table(startRow, headerRow, sheetName)

    if not result.get("success"):
        raise HTTPException(status_code=503, detail=result.get("error"))

    pqs = result.get("pqs", [])

    # Build CalcsLive-compatible structures
    inputs = {}
    outputs = {}
    pq_definitions = []

    for pq in pqs:
        sym = pq.get("sym")
        unit = pq.get("unit", "")
        value = pq.get("value")
        expression = pq.get("expression", "")
        description = pq.get("description", "")

        pq_def = {
            "sym": sym,
            "unit": unit,
            "description": description
        }

        if expression:
            # Output PQ - has expression
            pq_def["expression"] = expression
            outputs[sym] = {"unit": unit}
        else:
            # Input PQ - has value
            pq_def["value"] = value if value is not None else 0
            if value is not None:
                inputs[sym] = {"value": float(value), "unit": unit}

        pq_definitions.append(pq_def)

    return {
        "success": True,
        "articleId": result.get("articleId"),
        "inputs": inputs,
        "outputs": outputs,
        "pqs": pq_definitions,
        "rowMapping": {pq["sym"]: pq["row"] for pq in pqs},
        "valueCol": result.get("columns", {}).get("value")
    }


if __name__ == "__main__":
    print(f"Starting CalcsLive Excel Bridge v{VERSION}")
    print()
    print("Auto-Detection Endpoints (recommended):")
    print("  GET  /excel/find-article-id    - Find ArticleID in sheet")
    print("  GET  /excel/find-pq-table      - Auto-detect and read PQ table")
    print("  GET  /excel/pq-for-calcslive   - Get PQ data for CalcsLive API")
    print("  POST /excel/write-pq-results   - Write results by symbol name")
    print()
    print("Manual Endpoints:")
    print("  GET  /              - Health check")
    print("  GET  /excel/health  - Excel connection status")
    print("  POST /excel/read-range - Read Excel range")
    print("  POST /excel/write-cell - Write to cell")
    print("  POST /excel/read-pq-table - Read PQ table (explicit rows)")
    print("  POST /excel/write-pq-values - Write values (explicit rows)")
    print("  POST /excel/setup-from-article - Setup PQ table from article")
    print("  POST /excel/live-mode/start - Start event-driven auto-recalc watcher")
    print("  POST /excel/live-mode/stop - Stop auto-recalc watcher")
    print("  GET  /excel/live-mode/status - Get watcher status")
    print()
    uvicorn.run(app, host="127.0.0.1", port=8001)
