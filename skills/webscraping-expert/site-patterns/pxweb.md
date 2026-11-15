# PX-Web API (statistics offices)

PX-Web is the query engine behind many national statistics bureaus — Statistics Finland (StatFi), Statistics Sweden (SCB), Norway (SSB), Denmark, and others. Data is organized as a **navigable table tree**; each leaf table is queried by **POSTing a variable selection** and getting back JSON-stat (or CSV/px). Once you know the shape, it's a clean, documented API.

## When you see this

- URL path contains `/api/v1/<lang>/...` under a statistics-bureau domain.
- GET on a node returns a **list of sub-nodes or table ids**; GET on a table returns its **variable metadata**.
- Data is retrieved by **POST** with a `{"query": [...], "response": {"format": "json-stat2"}}` body.

---

## How it works

1. **Navigate the tree** (GET) from the database root down to a table id.
2. **GET the table** → metadata: the list of `variables`, each with `code`, `text`, `values` (codes), `valueTexts` (labels).
3. **POST a selection** → the data for the chosen slice, in your requested format.

```python
import httpx

BASE = "https://statistics.example.com/api/v1/en"  # illustrative; use the observed API root
TABLE_PATH = "<table_path>"  # discover a leaf table by navigating the API tree

def px_table_meta(table_path: str) -> dict:
    r = httpx.get(f"{BASE}/{table_path}", timeout=60); r.raise_for_status()
    return r.json()          # {"title":..., "variables":[{"code","text","values","valueTexts"}, ...]}

def px_fetch(table_path: str, selection: dict[str, list[str]]) -> dict:
    """selection: {variable_code: [value_codes]}. Use ['*'] to select all values of a variable."""
    body = {
        "query": [
            {"code": code, "selection": {"filter": "item", "values": values}}
            for code, values in selection.items()
        ],
        "response": {"format": "json-stat2"},
    }
    r = httpx.post(f"{BASE}/{table_path}", json=body, timeout=120)
    r.raise_for_status()
    return r.json()

meta = px_table_meta(TABLE_PATH)
# Start with one value per dimension; choose the required codes from the metadata.
selection = {
    variable["code"]: variable["values"][:1]
    for variable in meta["variables"]
}
data = px_fetch(TABLE_PATH, selection)
```

## Parsing the response (JSON-stat2)

JSON-stat is a dense cube: a flat `value` array indexed by the cross-product of dimension sizes. Use `pyjstat` to explode it to tidy rows:

```python
from pyjstat import pyjstat
df = pyjstat.from_json_stat(data)[0]     # → tidy DataFrame, one row per cell, labels resolved
```

---

## Gotchas

- **Per-query cell cap.** PX-Web rejects requests exceeding a cell limit (often ~100k–1M cells). If `['*'] × ['*'] × ['*']` is too big, **slice by one variable** (usually year or region) and loop — accumulate to bronze.
- **`filter: "item"`** selects explicit value codes; `"all"` selects everything; `"top"`/`"agg"` exist for top-N and aggregations. Start with `"item"` + `["*"]` and narrow if capped.
- **Rate limits are real** and modest (e.g. ~30 requests/10s on some instances). Add `time.sleep()` between slices; respect any documented cap.
- **`json-stat2` vs `json-stat`** — request v2 (`json-stat2`); `pyjstat` reads both but v2 is cleaner.
- **Codes vs labels** — the cube carries dimension codes; keep both `values` and `valueTexts` from the metadata so silver can map codes → human labels.
- **Bronze rule**: persist the raw JSON-stat response per slice. Explode to rows in silver.

---

## Related

- `site-patterns/sdmx-jsonstat.md` — SDMX-JSON / JSON-stat from OECD/Eurostat/ECB (sibling format)
- `site-patterns/odata.md` — OData statistics APIs (e.g. CBS Netherlands)
- `reference/libraries.md` — `pyjstat` for JSON-stat, `sdmx1` for SDMX
