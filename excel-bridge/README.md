# CalcsLive Excel Bridge

The Excel bridge is the local COM + REST layer that allows the unified CalcsLive Agent app to interact with the active Excel workbook.

It is the key piece that enables:

- sending reviewed CalcsLive calculations into Excel
- reading compatible Excel-authored PQ tables back into the agent
- reactive recalculation after spreadsheet edits

## What It Enables

### Forward flow

`CalcsLive article -> Excel`

- load article metadata into Excel
- write PQ table structure
- support interactive spreadsheet editing

### Reverse flow

`Excel PQ table -> reviewed CalcsLive script`

- read a compatible Excel-authored PQ table
- convert it into `pqs`, `inputs`, and `outputs`
- send it back into the unified app for review and persistence

## Run Locally

```bash
python main.py
```

Bridge URL:

```text
http://localhost:8001
```

## Expected Excel Table Structure

The bridge looks for semantic columns such as:

- `Description`
- `Symbol`
- `Expression`
- `Value`
- `Unit`

Optional:
- left-side row number column (`#`)

### Row rules

- Input row:
  - `Expression` blank
  - `Value` and `Unit` populated
- Output row:
  - `Expression` populated
  - `Unit` populated
  - `Value` optional or pre-existing

The bridge can now auto-detect compatible PQ tables even when no `ArticleID` is present.

## Main Endpoints

### Health and bridge status

- `GET /excel/health`

### Reading / detection

- `GET /excel/find-article-id`
- `GET /excel/find-pq-table`
- `GET /excel/pq-for-calcslive`
- `POST /excel/read-pq-table`

### Writing / setup

- `POST /excel/setup-from-article`
- `POST /excel/write-pq-results`
- `POST /excel/write-pq-values`

### Reactive live mode

- `POST /excel/live-mode/start`
- `POST /excel/live-mode/stop`
- `GET /excel/live-mode/status`

## Unified App Relationship

The unified app (`azure-agent/app.py`) checks this bridge at runtime.

- if the bridge is reachable, Excel-specific UI appears
- if not, the app continues in cloud/web calculation mode only

## Notes

- Requires desktop Excel on Windows
- Uses COM automation via `pywin32`
- Intended as the flagship local downstream integration for CalcsLive calculation articles
