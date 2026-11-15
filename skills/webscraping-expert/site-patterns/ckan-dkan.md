# CKAN / DKAN — open-data catalog API

CKAN is the open-source platform powering thousands of government and institutional open-data portals worldwide (national, regional, and city-level data.gov-style sites, EU member-state portals, university research catalogs). DKAN is its PHP/Drupal sibling, used by some US state and city portals. Both expose a stable REST API with the same shape — `/api/3/action/<action>` returning a JSON envelope.

If your target is "a portal listing thousands of datasets, each with downloadable CSV/XLSX/JSON files", check for CKAN first before writing an HTML scraper. The API saves days.

## When you see this

- Dataset URLs at `/dataset/<slug>` and resource (file) URLs at `/dataset/<slug>/resource/<uuid>`
- Footer or "About" page mentions "CKAN" or "DKAN" by name
- `/api/3/action/<action>` paths return JSON with shape `{"success": true, "help": "...", "result": {...}}`
- The HTML page source includes a `<meta>` tag or footer link to ckan.org / getdkan.org
- A meta-catalog variant: `data.europa.eu/api/hub/search/search` (EU-wide aggregation of national CKAN catalogs) uses a slightly different envelope but the same conceptual model

## How it works

CKAN exposes about thirty named "actions" via `/api/3/action/<action>`. The ones you need for scraping:

| Action | Purpose |
|---|---|
| `package_search` | Full-text + facet search across datasets; returns dataset metadata and resource (file) URLs |
| `package_show?id=<slug-or-uuid>` | Full metadata for a single dataset |
| `package_list` | List of all dataset slugs (use sparingly on large portals — can be very long) |
| `resource_show?id=<resource-uuid>` | Metadata for a specific file resource |
| `datastore_search` | Query a tabular resource that the portal has indexed into its DataStore (Postgres-backed) — returns rows |
| `group_list`, `organization_list`, `tag_list` | Browse by taxonomy |

All actions accept GET with query string OR POST with JSON body. Authentication is rarely needed for read access; when it is, the header is `Authorization: <api-key>`.

## Pattern — walk all datasets

```python
import httpx

BASE = "https://data.example.gov/api/3/action"

def iter_datasets(client: httpx.Client, page_size: int = 100):
    start = 0
    while True:
        r = client.get(
            f"{BASE}/package_search",
            params={"rows": page_size, "start": start},
            timeout=60,
        )
        payload = r.json()
        if not payload["success"]:
            raise RuntimeError(f"CKAN error: {payload.get('error')}")
        result = payload["result"]
        results = result["results"]
        if not results:
            return
        for dataset in results:
            yield dataset
        start += page_size
        if start >= result["count"]:
            return

def iter_resources(dataset: dict):
    """Yield each downloadable file (resource) attached to a dataset."""
    for r in dataset.get("resources", []):
        yield {
            "url": r["url"],
            "format": (r.get("format") or "").lower(),  # csv, xlsx, json, pdf, geojson, ...
            "name": r.get("name"),
            "id": r["id"],
            "size": r.get("size"),
            "last_modified": r.get("last_modified"),
        }
```

`package_search` is the workhorse — most portals support filters via `fq=` (Solr filter query) and faceting via `facet.field=`:

```python
params = {
    "q": "*:*",
    "fq": 'tags:"transport" AND organization:"ministry-of-transport"',
    "facet.field": '["tags", "groups", "organization"]',
    "rows": 100,
    "start": 0,
}
```

## Querying DataStore (when the resource has been indexed)

Some resources are imported into CKAN's DataStore, making them queryable via SQL-like access:

```python
r = client.get(f"{BASE}/datastore_search", params={
    "resource_id": "<resource-uuid>",
    "limit": 100,
    "offset": 0,
    "filters": '{"region": "Lisbon"}',
}).json()
records = r["result"]["records"]
```

Or full SQL when the portal allows it:

```python
r = client.get(f"{BASE}/datastore_search_sql", params={
    "sql": 'SELECT * FROM "<resource-uuid>" WHERE region = \'Lisbon\' LIMIT 100',
}).json()
```

DataStore availability is per-resource — check `dataset["resources"][i]["datastore_active"]`. Many resources are file-only (CSV download links) with no indexed rows.

## Meta-catalogs (cross-portal search)

A few hubs aggregate metadata from many CKAN instances:

- `data.europa.eu/api/hub/search/search` — EU-wide. Body: `{"limit": 100, "page": 0, "facets": {"country": ["DE"]}, "filter": "dataset"}`. Returns dataset records that point back to the originating national portal.
- `commondatastorage.googleapis.com/...` and `dataverse.harvard.edu/api/search` — similar pattern for research data.

These return references, not the data itself — you still pull the actual file from the dataset's home portal.

## Resource file handling

The `resources[*].url` field points to the actual file (CSV, XLSX, PDF, GeoJSON, ZIP, etc.). Two complications:

1. **Some `url` fields point off-site** — to a hosted Excel file on a ministry's own CMS, not to CKAN's own storage. These external links rot. Check the HTTP status; if 404, look for an archived copy on the Internet Archive Wayback Machine via `https://archive.org/wayback/available?url=<url>`.
2. **Format detection by extension is unreliable** — `format: "CSV"` resources sometimes deliver XLSX with the wrong content-type. Trust the file's actual bytes (`python-magic`, sniff the first 8 bytes) over the metadata.

## Selecting the right resource by parsing its name (period/year discovery)

A very common real-world shape: one dataset holds many yearly/monthly files as separate resources, and the *only* reliable way to tell them apart is the resource **name** or **URL** (the `format` is identical, the `created` date is unreliable). Discover the file you want by parsing the period out of the name — don't hardcode a resource UUID that changes each vintage.

```python
import re

def resource_for_year(dataset: dict, year: int, fmt: str = "xlsx") -> dict | None:
    """Pick the resource whose name encodes the target year, matching format."""
    candidates = []
    for r in dataset.get("resources", []):
        if (r.get("format") or "").lower() != fmt.lower():
            continue
        name = f"{r.get('name','')} {r.get('url','')}"
        m = re.search(r"(19|20)\d{2}", name)          # first 4-digit year in name/url
        if m and int(m.group()) == year:
            candidates.append(r)
    # If several match (e.g. revisions), prefer the most recently modified
    return max(candidates, key=lambda r: r.get("last_modified") or "", default=None)
```

A common pattern on government open-data portals: pick the current-year file (e.g. an XLSB export) from the portal's dataset listing, and tolerate a **404 on the current year** (the portal often lags — this year's file may not be published yet); fall back to the latest available year and record the gap rather than crashing.

## Gotchas

- **`success: false` returns HTTP 200** — the envelope reports the error. Always check `payload["success"]` before reading `payload["result"]`.
- **`rows` cap is portal-configurable** — typically 1000 but sometimes 100. Asking for more silently caps. Test by requesting 10 000 and seeing what you get.
- **Pagination uses `start` (offset), not `page`.** Off-by-one errors here are common — `start=100, rows=100` returns rows 100–199 (zero-indexed).
- **Slug vs UUID** — `package_show?id=<slug>` and `package_show?id=<uuid>` both work, but slugs can change (renames) while UUIDs are stable. For long-term scrapers, key on UUID.
- **`fq` (filter query) syntax is Solr-style** — `fq=tags:transport` works, `fq=tags="transport"` does not. Quotes only needed for values with spaces.
- **`facet.field` parameter must be JSON-encoded** when passed via query string — `facet.field=["tags"]`, not `facet.field=tags`. CKAN parses it as JSON.
- **DKAN compatibility is partial.** Most DKAN deployments support `package_search` and `package_show` but not `datastore_search_sql`. Check by hitting the SQL endpoint and seeing if it errors.
- **CORS-restricted endpoints** — a few portals expose `/api/3/action/...` only with a specific `Origin` header. If you get 403, try mirroring the portal's own Origin.
- **No /etag, no /last-modified for the API** — incremental sync requires keying on `metadata_modified` per dataset and filtering with `fq=metadata_modified:[<ISO>:* TO *]` (Solr range syntax). The portal's HTTP layer doesn't help with caching.
- **Datasets that look big can be empty.** A "dataset" in CKAN is metadata; the actual data may be zero resources, broken links, or an HTML "see methodology document" page. Always check `len(dataset["resources"])` before assuming you have data.

## Related

- `paginated-facet-search-api.md` — CKAN's `package_search` is itself a facet-search API; the offset-cap and facet-slice tricks may apply if you outgrow `start=10000`
- `sdmx-jsonstat.md` — statistics offices often list datasets in CKAN but serve the actual numbers via SDMX/JSON-stat; follow the resource URL to know which
- `../parsing/document-extraction.md` — when the resources are PDFs/XLSX rather than queryable data
- `../reliability/concurrency-curl-cffi.md` — large catalogs (10k+ datasets) benefit from concurrent metadata pulls
