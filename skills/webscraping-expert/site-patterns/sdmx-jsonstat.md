# Statistical data APIs — SDMX and JSON-stat

National statistics offices, central banks, supranational bodies (UN, OECD, IMF, World Bank), and regional government statistical portals expose their datasets through two standardized formats: **SDMX** (Statistical Data and Metadata Exchange) and **JSON-stat**. Both are designed for multi-dimensional cube data (e.g. "GDP by country, year, sector"), which is why they look unlike normal record-array APIs.

If your target serves statistics, expect one of these two — and a query shape that filters on **dimensions** rather than on rows.

## When you see this

**SDMX signals:**
- Path contains `/rest/data/`, `/sdmx/data/`, or `/sdmx-json/data/`
- A "DSD" (Data Structure Definition) endpoint sits alongside: `/datastructure/`, `/dataflow/`
- Query path follows the SDMX REST convention: `/data/<FLOW>/<KEY>?startPeriod=YYYY&endPeriod=YYYY`, where `<KEY>` is a dotted dimension filter like `M.NORM.EUR..A` (one position per dimension, blank = all values)
- `Accept: application/vnd.sdmx.data+json;version=1.0.0` or `application/vnd.sdmx.structurespecificdata+xml;version=2.1` headers
- Response is JSON with `dataSets`, `structure.dimensions.{observation,series}`, `attributes`

**JSON-stat signals:**
- Path includes `/json-stat/`, `/jsonstat/`, or returns `Content-Type: application/json` with a body whose top level is `{"version": "2.0", "class": "dataset", "id": [...], "size": [...], "dimension": {...}, "value": [...]}`
- "PxWeb" anywhere in the path (`/api/v1/<lang>/.../<table>`) — PxWeb is a common backend that emits JSON-stat by default
- Body has `dimension`, `size`, and `value` keys at the top level

**Generic statistics-API signals (apply to both):**
- Query is by **dimension filter**, not by row offset — there's usually no `?page=`/`?offset=` parameter
- Dataset metadata endpoint exposes the available dimensions, their value codes, and human-readable labels
- Responses can be very large for unfiltered queries (full multi-dimensional cube)

## How it works — the cube model

Both formats represent data as an **N-dimensional cube** with one numeric value per cell. The dimensions might be:

- `GEO` (country/region code, e.g. `DE`, `FR`, `IT`)
- `TIME_PERIOD` (year, quarter, month, e.g. `2024`, `2024-Q3`, `2024-10`)
- `INDICATOR` / `MEASURE` (what's being measured, e.g. `GDP_GROWTH`, `UNEMPLOYMENT`)
- Plus any domain-specific axes (`SECTOR`, `AGE_GROUP`, `SEX`, `UNIT`)

A query selects a sub-cube by fixing some dimensions and leaving others open. The server returns the values in a compact array that you must "unflatten" against the dimension metadata to make sense of.

## JSON-stat decoding

A JSON-stat response carries:
- `id`: ordered list of dimension names (e.g. `["geo", "time", "indicator"]`)
- `size`: parallel list of how many values each dimension has (e.g. `[27, 10, 3]` → 27*10*3 = 810 cells)
- `dimension`: object mapping dimension name → `{label, category: {index: {code: position}, label: {code: human-readable}}}`
- `value`: a single flat array of length `prod(size)`, row-major

Decoding involves walking the flat array and mapping each index back to dimension values:

```python
import itertools

def decode_jsonstat(payload: dict):
    dim_ids = payload["id"]
    sizes = payload["size"]
    dims = payload["dimension"]
    values = payload["value"]

    # For each dimension, build position -> code mapping
    coord_lookups = []
    for name in dim_ids:
        index = dims[name]["category"]["index"]
        # index may be {"code": pos} or a list of codes in position order
        if isinstance(index, dict):
            ordered = sorted(index.items(), key=lambda kv: kv[1])
            codes = [code for code, _ in ordered]
        else:
            codes = list(index)
        coord_lookups.append(codes)

    # value array is row-major over dim_ids
    for flat_idx, value in enumerate(values):
        if value is None:
            continue
        coords = []
        remaining = flat_idx
        for size in reversed(sizes):
            coords.append(remaining % size)
            remaining //= size
        coords.reverse()
        record = {dim_ids[i]: coord_lookups[i][coords[i]] for i in range(len(dim_ids))}
        record["value"] = value
        yield record
```

**Common variants:**
- `value` is sometimes an object `{"0": 1.23, "5": 4.56, ...}` (sparse) instead of an array. Treat keys as flat indices into the dense cube.
- `dimension.<name>.category.unit` carries per-cell units (currency code, percentage marker, scale factor) — read this when comparing values across rows.

## SDMX-JSON decoding

SDMX is structurally similar but more elaborate. The relevant pieces of a response:

- `data.structures[0].dimensions.{series, observation}` — list of dimensions split into "series" (fixed per series) and "observation" (the time axis usually)
- `data.dataSets[0].series` — keys are colon-joined dimension positions (e.g. `"0:0:1"`), values contain `observations` keyed by observation position
- Each dimension entry has `values: [{id, name, ...}]` — index into this with the position to get the value code

```python
def decode_sdmx_json(payload: dict):
    structure = payload["data"]["structures"][0]
    series_dims = structure["dimensions"]["series"]
    obs_dims = structure["dimensions"]["observation"]

    for series_key, series in payload["data"]["dataSets"][0]["series"].items():
        positions = [int(p) for p in series_key.split(":")]
        series_coords = {
            series_dims[i]["id"]: series_dims[i]["values"][positions[i]]["id"]
            for i in range(len(series_dims))
        }
        for obs_key, obs_values in series["observations"].items():
            obs_pos = int(obs_key)
            obs_coords = {
                obs_dims[i]["id"]: obs_dims[i]["values"][obs_pos]["id"]
                for i in range(len(obs_dims))
            }
            yield {**series_coords, **obs_coords, "value": obs_values[0]}
```

In practice, use the Python library `sdmx1` (or `pandasdmx` for older code) — it handles the format variations and produces a pandas DataFrame. Only roll your own decoder if you can't take the dependency.

## Pattern — full dataset pull

The general flow is:

1. **Discover dimensions** — GET the dataset metadata endpoint, list the dimensions and their valid value codes
2. **Decide on slicing** — most statistics APIs cap response size by total cells. A single request asking for "all geos × all years × all indicators" may be rejected. Loop over one dimension (e.g. year) and request smaller cubes
3. **Decode each response** using one of the helpers above
4. **Stream to storage** — these datasets can be millions of rows when fully expanded; don't materialize the whole thing in memory

```python
import httpx

DATAFLOW = "CONSUMER_PRICES_M"
BASE = f"https://ec.example.eu/eurostat/api/dissemination/statistics/1.0/data/{DATAFLOW}"

with httpx.Client(headers={"Accept": "application/json"}, timeout=120) as client:
    meta = client.get(f"{BASE}?format=json").json()
    # Inspect meta to discover dimensions and their value codes...
    for year in range(2000, 2026):
        params = {"sinceTimePeriod": str(year), "untilTimePeriod": str(year)}
        payload = client.get(BASE, params=params).json()
        yield from decode_jsonstat(payload)
```

## Gotchas

- **Dimension code != human label.** The data carries codes (`DE`, `M`, `Q1`), not labels (`"Germany"`, `"Monthly"`, `"Quarter 1"`). The label map lives in the metadata. Always join codes to labels at the end, not inline during decode.
- **`null` values are meaningful** — typically "no data" or "confidential". Don't treat them as zero. Some platforms also use sentinel codes (`":"`, `"NA"`, `"-"`) that look like strings.
- **Sparse vs dense `value` array.** A dataset with 27×10×100 = 27 000 cells but only 8 000 actual observations may return a sparse object. Don't assume dense — check the type.
- **Time period codes vary by frequency.** Annual: `2024`. Quarterly: `2024-Q3` or `2024Q3`. Monthly: `2024-10` or `2024M10`. Weekly: `2024-W42` or `2024W42`. Read the frequency dimension first and adjust your parser.
- **Server caps on cube size** are common and undocumented. Eurostat caps responses around ~50 000 observations; some PxWeb installs cap at 1 000. Hit the cap → server returns a 400 or a truncated body. Slice your query smaller.
- **Authentication is rare for public stats but exists for premium APIs** (e.g. IMF's commercial endpoints, some central-bank historical series). Headers usually go `Ocp-Apim-Subscription-Key` or `X-API-Key`.
- **CORS-protected query params.** The browser-facing endpoint sometimes requires a specific `Origin` or `Referer` from the official dashboard. If your direct request gets a 403 the official dashboard handles cleanly, try mirroring those headers.
- **Don't trust the "download CSV" button as a substitute** — it often pre-aggregates / filters to defaults that don't match the API's full data. The API is authoritative.

## Related

- `paginated-facet-search-api.md` — when the stats portal also exposes a record-array search alongside the cube API (open-data portals often do both)
- `ckan-dkan.md` — government open-data catalogs may *list* statistical datasets but link out to a JSON-stat / SDMX endpoint for the actual data
- `../parsing/document-extraction.md` — when the same numbers are also published as PDF tables and you need both as cross-checks
