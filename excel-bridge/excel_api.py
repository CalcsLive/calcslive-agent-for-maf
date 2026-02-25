# excel_api.py
# Excel COM automation wrapper for CalcsLive integration
# Pattern adapted from Inventor Bridge (25038-calcslive-plug-4-inventor)
# and Google Sheets integration (25035-calcslive-plug-4-google-sheets)

import pythoncom
import win32com.client
from typing import Dict, Any, List, Optional, Tuple


def _col_letter(col: int) -> str:
    """Convert column number (1-based) to Excel letter (A, B, ..., Z, AA, ...)."""
    result = ""
    while col > 0:
        col -= 1
        result = chr(65 + (col % 26)) + result
        col //= 26
    return result


def _cell_address(row: int, col: int) -> str:
    """Convert row/col numbers to Excel cell address (e.g., 'C7')."""
    return f"{_col_letter(col)}{row}"


def get_health() -> Dict[str, Any]:
    """
    Check Excel connection health.

    Returns:
        Dict with health status, document name, and sheet name
    """
    pythoncom.CoInitialize()
    try:
        app = win32com.client.GetActiveObject("Excel.Application")

        if app.ActiveWorkbook is None:
            return {
                "success": True,
                "status": "no_workbook",
                "message": "Excel is running but no workbook is open"
            }

        wb = app.ActiveWorkbook
        ws = wb.ActiveSheet

        return {
            "success": True,
            "status": "connected",
            "workbookName": wb.Name,
            "sheetName": ws.Name,
            "fullPath": wb.FullName if hasattr(wb, 'FullName') else None
        }

    except Exception as e:
        return {
            "success": False,
            "status": "disconnected",
            "error": str(e),
            "errorType": type(e).__name__
        }
    finally:
        pythoncom.CoUninitialize()


def read_range(range_address: str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Read values from an Excel range.

    Args:
        range_address: Excel range (e.g., "A1:E10", "B2:F20")
        sheet_name: Optional sheet name (uses active sheet if not specified)

    Returns:
        Dict with 2D array of values
    """
    pythoncom.CoInitialize()
    try:
        app = win32com.client.GetActiveObject("Excel.Application")
        wb = app.ActiveWorkbook

        if wb is None:
            return {"success": False, "error": "No active workbook"}

        # Get sheet
        if sheet_name:
            try:
                ws = wb.Sheets(sheet_name)
            except:
                return {"success": False, "error": f"Sheet '{sheet_name}' not found"}
        else:
            ws = wb.ActiveSheet

        # Read range
        rng = ws.Range(range_address)
        values = rng.Value

        # Handle single cell vs range
        if values is None:
            data = [[None]]
        elif not isinstance(values, tuple):
            # Single cell
            data = [[values]]
        else:
            # Multiple cells - convert tuple of tuples to list of lists
            data = [list(row) for row in values]

        return {
            "success": True,
            "range": range_address,
            "sheetName": ws.Name,
            "data": data,
            "rowCount": len(data),
            "colCount": len(data[0]) if data else 0
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "errorType": type(e).__name__
        }
    finally:
        pythoncom.CoUninitialize()


def write_cell(cell_address: str, value: Any, sheet_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Write a value to a single Excel cell.

    Args:
        cell_address: Excel cell address (e.g., "D5", "E10")
        value: Value to write
        sheet_name: Optional sheet name

    Returns:
        Dict with success status
    """
    pythoncom.CoInitialize()
    try:
        app = win32com.client.GetActiveObject("Excel.Application")
        wb = app.ActiveWorkbook

        if wb is None:
            return {"success": False, "error": "No active workbook"}

        # Get sheet
        if sheet_name:
            try:
                ws = wb.Sheets(sheet_name)
            except:
                return {"success": False, "error": f"Sheet '{sheet_name}' not found"}
        else:
            ws = wb.ActiveSheet

        # Write to cell
        ws.Range(cell_address).Value = value

        return {
            "success": True,
            "cell": cell_address,
            "sheetName": ws.Name,
            "value": value
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "errorType": type(e).__name__
        }
    finally:
        pythoncom.CoUninitialize()


def write_range(range_address: str, values: List[List[Any]], sheet_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Write values to an Excel range.

    Args:
        range_address: Excel range address (e.g., "A1:E5")
        values: 2D list of values to write
        sheet_name: Optional sheet name

    Returns:
        Dict with success status
    """
    pythoncom.CoInitialize()
    try:
        app = win32com.client.GetActiveObject("Excel.Application")
        wb = app.ActiveWorkbook

        if wb is None:
            return {"success": False, "error": "No active workbook"}

        # Get sheet
        if sheet_name:
            try:
                ws = wb.Sheets(sheet_name)
            except:
                return {"success": False, "error": f"Sheet '{sheet_name}' not found"}
        else:
            ws = wb.ActiveSheet

        # Write to range - convert list to tuple for COM
        rng = ws.Range(range_address)
        rng.Value = values

        return {
            "success": True,
            "range": range_address,
            "sheetName": ws.Name,
            "rowsWritten": len(values),
            "colsWritten": len(values[0]) if values else 0
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "errorType": type(e).__name__
        }
    finally:
        pythoncom.CoUninitialize()


def find_article_id(sheet_name: Optional[str] = None,
                    max_rows: int = 20, max_cols: int = 10) -> Dict[str, Any]:
    """
    Find ArticleID cell in the spreadsheet.
    Searches for a cell containing "ArticleID" (case-insensitive) and returns
    the adjacent cell's value as the actual article ID.

    Args:
        sheet_name: Optional sheet name
        max_rows: Maximum rows to search (default 20)
        max_cols: Maximum columns to search (default 10)

    Returns:
        Dict with articleId, location info, and suggested PQ table position
    """
    pythoncom.CoInitialize()
    try:
        app = win32com.client.GetActiveObject("Excel.Application")
        wb = app.ActiveWorkbook

        if wb is None:
            return {"success": False, "error": "No active workbook"}

        # Get sheet
        if sheet_name:
            try:
                ws = wb.Sheets(sheet_name)
            except:
                return {"success": False, "error": f"Sheet '{sheet_name}' not found"}
        else:
            ws = wb.ActiveSheet

        # Search for "ArticleID" label
        for row in range(1, max_rows + 1):
            for col in range(1, max_cols + 1):
                cell_value = ws.Cells(row, col).Value
                if cell_value and 'articleid' in str(cell_value).lower().replace(' ', '').replace('_', ''):
                    # Found the label - get the value from adjacent cell (same row, next column)
                    article_id = ws.Cells(row, col + 1).Value

                    if article_id:
                        # Calculate PQ table position relative to ArticleID
                        # Headers 1 row below ArticleID, data 2 rows below
                        header_row = row + 1
                        data_start_row = row + 2

                        return {
                            "success": True,
                            "articleId": str(article_id).strip(),
                            "labelCell": _cell_address(row, col),
                            "valueCell": _cell_address(row, col + 1),
                            "labelRow": row,
                            "labelCol": col,
                            "sheetName": ws.Name,
                            "suggestedHeaderRow": header_row,
                            "suggestedDataStartRow": data_start_row,
                            "suggestedStartCol": col  # PQ table starts at same column as ArticleID label
                        }

        return {
            "success": False,
            "error": "ArticleID not found in sheet. Add 'ArticleID' label with the article ID in the next cell."
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "errorType": type(e).__name__
        }
    finally:
        pythoncom.CoUninitialize()


def find_pq_table(sheet_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Auto-detect and read PQ table by finding ArticleID first.
    Uses ArticleID position to determine PQ table location.

    Args:
        sheet_name: Optional sheet name

    Returns:
        Dict with articleId, PQ list, and table metadata
    """
    pythoncom.CoInitialize()
    try:
        app = win32com.client.GetActiveObject("Excel.Application")
        wb = app.ActiveWorkbook

        if wb is None:
            return {"success": False, "error": "No active workbook"}

        # Get sheet
        if sheet_name:
            try:
                ws = wb.Sheets(sheet_name)
            except:
                return {"success": False, "error": f"Sheet '{sheet_name}' not found"}
        else:
            ws = wb.ActiveSheet

        # First, find ArticleID
        article_info = None
        for row in range(1, 21):
            for col in range(1, 11):
                cell_value = ws.Cells(row, col).Value
                if cell_value and 'articleid' in str(cell_value).lower().replace(' ', '').replace('_', ''):
                    article_id = ws.Cells(row, col + 1).Value
                    if article_id:
                        article_info = {
                            "articleId": str(article_id).strip(),
                            "labelRow": row,
                            "labelCol": col
                        }
                        break
            if article_info:
                break

        if not article_info:
            return {
                "success": False,
                "error": "ArticleID not found. Add 'ArticleID' label with the article ID in the next cell."
            }

        # Calculate PQ table position relative to ArticleID
        # Headers 1 row below ArticleID, data 2 rows below
        label_row = article_info["labelRow"]
        label_col = article_info["labelCol"]
        header_row = label_row + 1
        data_start_row = label_row + 2

        # Find headers in the header row (starting from label_col)
        headers = {}
        for col in range(label_col, label_col + 10):
            cell_value = ws.Cells(header_row, col).Value
            if cell_value is None:
                continue

            cell_str = str(cell_value).strip().lower()

            if 'desc' in cell_str or cell_str == 'pq':
                headers['description'] = col
            elif cell_str in ['sym', 'symbol', 'symbols']:
                headers['symbol'] = col
            elif cell_str in ['expr', 'expression', 'formula']:
                headers['expression'] = col
            elif cell_str in ['val', 'value', 'values']:
                headers['value'] = col
            elif cell_str in ['unit', 'units']:
                headers['unit'] = col

        # Verify we found required columns
        required = ['symbol', 'value', 'unit']
        missing = [c for c in required if c not in headers]
        if missing:
            return {
                "success": False,
                "error": f"Missing required columns: {missing}",
                "foundHeaders": list(headers.keys()),
                "headerRow": header_row,
                "articleId": article_info["articleId"]
            }

        # Read PQ data rows
        pqs = []
        row = data_start_row
        max_data_rows = 50

        while row < data_start_row + max_data_rows:
            symbol = ws.Cells(row, headers['symbol']).Value

            # Stop if symbol is empty
            if symbol is None or str(symbol).strip() == "":
                break

            pq = {
                "row": row,
                "sym": str(symbol).strip(),
                "value": ws.Cells(row, headers['value']).Value,
                "unit": str(ws.Cells(row, headers['unit']).Value or "").strip(),
            }

            # Optional columns
            if 'description' in headers:
                pq["description"] = str(ws.Cells(row, headers['description']).Value or "").strip()
            if 'expression' in headers:
                expr = ws.Cells(row, headers['expression']).Value
                pq["expression"] = str(expr).strip() if expr else ""

            # Determine if input or output (has expression = output)
            pq["isInput"] = not bool(pq.get("expression"))

            pqs.append(pq)
            row += 1

        return {
            "success": True,
            "articleId": article_info["articleId"],
            "sheetName": ws.Name,
            "workbookName": wb.Name,
            "articleIdCell": _cell_address(article_info["labelRow"], article_info["labelCol"] + 1),
            "headerRow": header_row,
            "dataStartRow": data_start_row,
            "columns": headers,
            "pqs": pqs,
            "inputCount": sum(1 for pq in pqs if pq.get("isInput")),
            "outputCount": sum(1 for pq in pqs if not pq.get("isInput"))
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "errorType": type(e).__name__
        }
    finally:
        pythoncom.CoUninitialize()


def read_pq_table(start_row: int = 2, header_row: int = 1,
                  sheet_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Read Physical Quantity (PQ) table from Excel with explicit row positions.
    Expects columns: Description | Symbol | Expression | Value | Unit

    For auto-detection based on ArticleID position, use find_pq_table() instead.

    Args:
        start_row: First data row (default 2, assuming row 1 is headers)
        header_row: Header row number (default 1)
        sheet_name: Optional sheet name

    Returns:
        Dict with PQ list and metadata
    """
    pythoncom.CoInitialize()
    try:
        app = win32com.client.GetActiveObject("Excel.Application")
        wb = app.ActiveWorkbook

        if wb is None:
            return {"success": False, "error": "No active workbook"}

        # Get sheet
        if sheet_name:
            try:
                ws = wb.Sheets(sheet_name)
            except:
                return {"success": False, "error": f"Sheet '{sheet_name}' not found"}
        else:
            ws = wb.ActiveSheet

        # Find column indices by looking for headers
        # Standard columns: Description, Symbol, Expression, Value, Unit
        headers = {}
        col = 1
        max_cols = 20  # Search first 20 columns

        while col <= max_cols:
            cell_value = ws.Cells(header_row, col).Value
            if cell_value is None:
                col += 1
                continue

            cell_str = str(cell_value).strip().lower()

            if 'desc' in cell_str or cell_str == 'pq':
                headers['description'] = col
            elif cell_str in ['sym', 'symbol', 'symbols']:
                headers['symbol'] = col
            elif cell_str in ['expr', 'expression', 'formula']:
                headers['expression'] = col
            elif cell_str in ['val', 'value', 'values']:
                headers['value'] = col
            elif cell_str in ['unit', 'units']:
                headers['unit'] = col

            col += 1

        # Verify we found required columns
        required = ['symbol', 'value', 'unit']
        missing = [c for c in required if c not in headers]
        if missing:
            return {
                "success": False,
                "error": f"Missing required columns: {missing}",
                "foundHeaders": list(headers.keys())
            }

        # Read data rows until we hit empty symbol
        pqs = []
        row = start_row
        max_rows = 100  # Safety limit

        while row < start_row + max_rows:
            symbol = ws.Cells(row, headers['symbol']).Value

            # Stop if symbol is empty
            if symbol is None or str(symbol).strip() == "":
                break

            pq = {
                "row": row,
                "sym": str(symbol).strip(),
                "value": ws.Cells(row, headers['value']).Value,
                "unit": ws.Cells(row, headers['unit']).Value or "",
            }

            # Optional columns
            if 'description' in headers:
                pq["description"] = ws.Cells(row, headers['description']).Value or ""
            if 'expression' in headers:
                expr = ws.Cells(row, headers['expression']).Value
                pq["expression"] = str(expr).strip() if expr else ""

            # Determine if this is an input or output PQ
            # If it has an expression, it's an output; otherwise it's an input
            pq["isInput"] = not bool(pq.get("expression"))

            pqs.append(pq)
            row += 1

        return {
            "success": True,
            "sheetName": ws.Name,
            "workbookName": wb.Name,
            "headerRow": header_row,
            "dataStartRow": start_row,
            "columns": headers,
            "pqs": pqs,
            "inputCount": sum(1 for pq in pqs if pq.get("isInput")),
            "outputCount": sum(1 for pq in pqs if not pq.get("isInput"))
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "errorType": type(e).__name__
        }
    finally:
        pythoncom.CoUninitialize()


def write_pq_results(results: Dict[str, Any], sheet_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Write CalcsLive calculation results back to the auto-detected PQ table.
    Uses find_pq_table() to locate the Value column, then writes output values.

    Args:
        results: Dict with symbol -> value mapping from CalcsLive calculation
                 e.g., {"V": 0.0965, "m": 96.5}
        sheet_name: Optional sheet name

    Returns:
        Dict with success status and details of written values
    """
    # First, find the PQ table
    table_info = find_pq_table(sheet_name)
    if not table_info.get("success"):
        return table_info

    pqs = table_info.get("pqs", [])
    value_col = table_info.get("columns", {}).get("value")

    if not value_col:
        return {"success": False, "error": "Value column not found in PQ table"}

    # Map symbols to rows for output PQs only
    writes = []
    for pq in pqs:
        if pq.get("isInput"):
            continue  # Skip inputs

        sym = pq.get("sym")
        if sym in results:
            writes.append({
                "row": pq["row"],
                "value": results[sym],
                "sym": sym
            })

    if not writes:
        return {
            "success": True,
            "message": "No matching output symbols found to write",
            "availableOutputs": [pq["sym"] for pq in pqs if not pq.get("isInput")],
            "providedResults": list(results.keys())
        }

    # Now write the values
    pythoncom.CoInitialize()
    try:
        app = win32com.client.GetActiveObject("Excel.Application")
        wb = app.ActiveWorkbook
        ws = wb.Sheets(table_info["sheetName"]) if table_info.get("sheetName") else wb.ActiveSheet

        written = []
        for write in writes:
            ws.Cells(write["row"], value_col).Value = write["value"]
            written.append({
                "sym": write["sym"],
                "row": write["row"],
                "cell": _cell_address(write["row"], value_col),
                "value": write["value"]
            })

        return {
            "success": True,
            "articleId": table_info.get("articleId"),
            "sheetName": ws.Name,
            "valuesWritten": len(written),
            "details": written
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "errorType": type(e).__name__
        }
    finally:
        pythoncom.CoUninitialize()


def write_pq_values(results: List[Dict[str, Any]], value_col: int = 4,
                    sheet_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Write calculated PQ values back to Excel (explicit column version).
    For auto-detection, use write_pq_results() instead.

    Args:
        results: List of dicts with 'row' and 'value' keys
        value_col: Column number for Value column (default 4, D)
        sheet_name: Optional sheet name

    Returns:
        Dict with success status and count of values written
    """
    pythoncom.CoInitialize()
    try:
        app = win32com.client.GetActiveObject("Excel.Application")
        wb = app.ActiveWorkbook

        if wb is None:
            return {"success": False, "error": "No active workbook"}

        # Get sheet
        if sheet_name:
            try:
                ws = wb.Sheets(sheet_name)
            except:
                return {"success": False, "error": f"Sheet '{sheet_name}' not found"}
        else:
            ws = wb.ActiveSheet

        # Write values
        written = []
        for result in results:
            row = result.get('row')
            value = result.get('value')

            if row is None:
                continue

            ws.Cells(row, value_col).Value = value
            written.append({
                "row": row,
                "value": value,
                "cell": f"{chr(64 + value_col)}{row}"  # Convert col number to letter
            })

        return {
            "success": True,
            "sheetName": ws.Name,
            "valuesWritten": len(written),
            "details": written
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "errorType": type(e).__name__
        }
    finally:
        pythoncom.CoUninitialize()


def setup_pq_table_from_article(pqs: List[Dict[str, Any]],
                                 start_row: int = 2,
                                 start_col: int = 1,
                                 include_headers: bool = True,
                                 sheet_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Setup a PQ table in Excel from a CalcsLive article structure.
    Creates columns: Description | Symbol | Expression | Value | Unit

    Args:
        pqs: List of PQ dicts from CalcsLive article
        start_row: First row to write (default 2 if headers, 1 otherwise)
        start_col: First column (default 1, A)
        include_headers: Whether to write header row
        sheet_name: Optional sheet name

    Returns:
        Dict with success status and table info
    """
    pythoncom.CoInitialize()
    try:
        app = win32com.client.GetActiveObject("Excel.Application")
        wb = app.ActiveWorkbook

        if wb is None:
            return {"success": False, "error": "No active workbook"}

        # Get sheet
        if sheet_name:
            try:
                ws = wb.Sheets(sheet_name)
            except:
                return {"success": False, "error": f"Sheet '{sheet_name}' not found"}
        else:
            ws = wb.ActiveSheet

        current_row = start_row

        # Write headers if requested
        if include_headers:
            headers = ["Description", "Symbol", "Expression", "Value", "Unit"]
            for i, header in enumerate(headers):
                ws.Cells(start_row - 1, start_col + i).Value = header

        # Write PQ data
        for pq in pqs:
            ws.Cells(current_row, start_col).Value = pq.get("description", "")
            ws.Cells(current_row, start_col + 1).Value = pq.get("sym", "")
            ws.Cells(current_row, start_col + 2).Value = pq.get("expression", "")
            # Leave value empty for inputs (user will fill in)
            if pq.get("value") is not None:
                ws.Cells(current_row, start_col + 3).Value = pq.get("value")
            ws.Cells(current_row, start_col + 4).Value = pq.get("unit", "")
            current_row += 1

        return {
            "success": True,
            "sheetName": ws.Name,
            "headerRow": start_row - 1 if include_headers else None,
            "dataStartRow": start_row,
            "dataEndRow": current_row - 1,
            "pqCount": len(pqs)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "errorType": type(e).__name__
        }
    finally:
        pythoncom.CoUninitialize()