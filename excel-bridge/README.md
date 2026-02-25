# CalcsLive Excel Bridge

HTTP bridge for Excel COM automation, enabling unit-aware calculations through CalcsLive.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py
```

Server runs at `http://localhost:8001`

## Expected Excel Structure

The bridge auto-detects the PQ table position from the ArticleID cell:

```
Row 7:  | ArticleID | 3MLCVKCU3-2K8 |           |       |        |
Row 8:  | Description | Symbol | Expression | Value | Unit |
Row 9:  | Diameter    | D      |            | 2     | in   |
Row 10: | Height      | h      |            | 3     | cm   |
Row 11: | Volume      | V      | pi*D^2/4*h |       | L    |
Row 12: | Density     | rho    |            | 1000  | kg/m^3 |
Row 13: | Mass        | m      | rho * V    |       | lbm  |
```

**Key points:**
- "ArticleID" label identifies the calculation
- Headers are 1 row below ArticleID
- Data starts 2 rows below ArticleID
- Inputs: PQs without expressions (user provides values)
- Outputs: PQs with expressions (calculated by CalcsLive)

## Auto-Detection Endpoints (Recommended)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/excel/find-article-id` | GET | Find ArticleID cell and value |
| `/excel/find-pq-table` | GET | Auto-detect and read full PQ table |
| `/excel/pq-for-calcslive` | GET | Get PQ data formatted for CalcsLive API |
| `/excel/write-pq-results` | POST | Write results by symbol name |

## Manual Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/excel/health` | GET | Excel connection status |
| `/excel/read-range` | POST | Read values from Excel range |
| `/excel/write-cell` | POST | Write value to single cell |
| `/excel/read-pq-table` | POST | Read PQ table (explicit rows) |
| `/excel/write-pq-values` | POST | Write values (explicit rows) |

## API Examples

### Find ArticleID

```bash
curl http://localhost:8001/excel/find-article-id
```

Response:
```json
{
  "success": true,
  "articleId": "3MLCVKCU3-2K8",
  "labelCell": "B7",
  "valueCell": "C7",
  "suggestedHeaderRow": 8,
  "suggestedDataStartRow": 9
}
```

### Get PQ Data for CalcsLive

```bash
curl "http://localhost:8001/excel/pq-for-calcslive"
```

Response:
```json
{
  "success": true,
  "articleId": "3MLCVKCU3-2K8",
  "inputs": {
    "D": {"value": 2, "unit": "in"},
    "h": {"value": 3, "unit": "cm"},
    "rho": {"value": 1000, "unit": "kg/m^3"}
  },
  "outputs": {
    "V": {"unit": "L"},
    "m": {"unit": "lbm"}
  },
  "pqs": [...],
  "rowMapping": {"D": 9, "h": 10, "V": 11, "rho": 12, "m": 13},
  "valueCol": 5
}
```

### Write Calculation Results

```bash
curl -X POST http://localhost:8001/excel/write-pq-results \
  -H "Content-Type: application/json" \
  -d '{"results": {"V": 0.0965, "m": 212.75}}'
```

Response:
```json
{
  "success": true,
  "articleId": "3MLCVKCU3-2K8",
  "valuesWritten": 2,
  "details": [
    {"sym": "V", "row": 11, "cell": "E11", "value": 0.0965},
    {"sym": "m", "row": 13, "cell": "E13", "value": 212.75}
  ]
}
```

## Integration with CalcsLive Agent

The agent flow:
1. `GET /excel/pq-for-calcslive` - Read inputs and PQ structure
2. Call CalcsLive MCP `calcslive_run_script` or `calcslive_calculate` with the PQs
3. `POST /excel/write-pq-results` - Write results back by symbol name

## Testing

```bash
# Open Excel with a PQ table spreadsheet first
python test_excel_api.py
```
