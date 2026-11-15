# Paginated facet-search API

A pattern that recurs whenever the frontend has a "search results page with sidebar filters" UI — open-data portals, e-commerce catalogs, document libraries, classifieds. The server exposes a single endpoint that takes a query string + a set of `refine.<field>=<value>` filters and returns a paginated list of records plus the **facet counts** that power the filter sidebar.

The defining quirk: these endpoints almost always have a **hard offset cap** (usually 10 000) below the actual dataset size. Naively iterating `start=0, 100, 200, ...` will silently stop returning rows after the cap is hit, *even if `nhits` reports millions*. The workaround is to slice the query by facet value into sub-queries each smaller than the cap.

## When you see this

- GET endpoint shaped like `/api/records/1.0/search/`, `/api/explore/v2.1/catalog/datasets/<slug>/records`, `/search?q=`, `/catalog/v1/items`
- Query params include `rows=` / `limit=`, `start=` / `offset=`, `facet=<field>` (declare facets to compute), `refine.<field>=<value>` (filter by facet value), `q=<full-text>`, `sort=`
- Response envelope: `{"records": [...], "nhits": <total_int>, "facet_groups": [{"name": "<field>", "facets": [{"name": "<value>", "count": N}, ...]}]}` or `{"results": [...], "total_count": N, "facets": {...}}`
- Frontend has a sidebar with checkbox filters and a "X results" count that updates as filters apply

## How it works

The endpoint is a thin wrapper over a search engine (Elasticsearch, Solr, Algolia, or a custom inverted index). For each request the server runs:

1. The full-text query (`q=`)
2. Filters specified by `refine.<field>=<value>` repeated params (multiple values = OR within field, AND between fields)
3. Paginates via `start` + `rows`
4. Computes facet counts for the `facet=` fields declared in the request — those are what populate the sidebar

The result is `nhits` (total matching documents) + the current page of records + facet groups with count-per-value. You walk pages until `start + len(records) >= nhits`.

## Pattern — simple pagination

```python
import httpx

BASE = "https://example.opendata.example.com/api/records/1.0/search/"

def iter_records(client: httpx.Client, dataset: str, refines: dict | None = None):
    start, page_size = 0, 100
    params = [("dataset", dataset), ("rows", page_size)]
    for k, v in (refines or {}).items():
        params.append((f"refine.{k}", v))
    while True:
        r = client.get(BASE, params=[*params, ("start", start)], timeout=60)
        payload = r.json()
        records = payload.get("records") or payload.get("results", [])
        if not records:
            return
        for rec in records:
            yield rec.get("fields") or rec
        start += page_size
        if start >= payload.get("nhits", payload.get("total_count", 0)):
            return
```

This works **only when the total dataset size is below the offset cap**. Above it, you need the facet-slice approach.

## Bypassing the offset cap by facet-slicing

When `nhits` is, say, 87 000 but the server returns empty pages after `start=10000`, you've hit the cap. The trick: pick a low-cardinality facet (date year, category, region, status) and run the same query *once per facet value*, with `refine.<field>=<value>` applied. Each sub-query has its own `nhits` smaller than the cap, and you walk each separately:

```python
def list_facet_values(client, dataset: str, facet_field: str) -> list[tuple[str, int]]:
    """Discover all values of a facet and their counts via a count-only request."""
    r = client.get(BASE, params={
        "dataset": dataset,
        "rows": 0,                    # don't return any records
        "facet": facet_field,
    }, timeout=60)
    payload = r.json()
    groups = payload.get("facet_groups") or [{"facets": payload.get("facets", {}).get(facet_field, [])}]
    facets = next((g["facets"] for g in groups if g.get("name") == facet_field), [])
    return [(f["name"], f["count"]) for f in facets]

def iter_all_with_facet_slice(client, dataset: str, slice_field: str, cap: int = 10_000):
    """Walk a dataset larger than the offset cap by slicing on a facet field."""
    for value, count in list_facet_values(client, dataset, slice_field):
        if count <= cap:
            yield from iter_records(client, dataset, refines={slice_field: value})
        else:
            # That slice is still too big — drill in with a second facet
            for sub_value, _ in list_facet_values(client, dataset, "<second_facet>"):
                yield from iter_records(client, dataset, refines={slice_field: value, "<second_facet>": sub_value})
```

Pick the facet field strategically: low cardinality (so you don't make thousands of sub-requests) but high enough that each slice fits under the cap. A date year often works; a status-enum often does too.

When even a two-facet slice doesn't shrink enough, the only remaining options are:
- Use the bulk export endpoint if the platform offers one (`/exports/json`, `/exports/csv`, `/download`)
- Switch to the API's `q=` full-text predicate as an artificial slice (`q=a*`, `q=b*`, ...)
- Accept that you can only get a sample and document the limit

## Bulk export — try this first

Many platforms expose a separate `/exports/json` or `/exports/csv` URL on the same dataset that **bypasses the offset cap entirely** — it streams the full result set in one shot (often gzipped). Always check for it before building a facet-slice scraper:

```bash
curl -s 'https://host/api/explore/v2.1/catalog/datasets/<slug>/exports/json?limit=-1' \
  | jq 'length'
```

If it works, you're done — that's a single request for the whole dataset, no pagination needed.

## Gotchas

- **Hard offset cap is invisible.** No error, no warning — pages just become empty. `nhits` keeps reporting the true total. Always test: if `start=cap` returns zero rows but `nhits > cap`, that's the cap.
- **Facet count != record count in a slice.** A facet count is the number of *unique documents* matching that value within the broader filter. When you apply `refine.<field>=<value>` and walk the records, you may get fewer rows than the facet count if some records lack the field. Use the slice's own `nhits` as the truth, not the facet count from the unsliced query.
- **`refine.` parameter syntax varies.** OpenDataSoft uses `refine.field=value`, Algolia uses `facetFilters[]=field:value`, Solr uses `fq=field:value`, Elasticsearch fronts often use `filter[field]=value`. Inspect a real HAR.
- **Multi-value semantics.** `refine.field=A&refine.field=B` is **OR** in OpenDataSoft (matches A or B). Filtering across different fields is **AND**. Confirm by sending two refines and comparing `nhits` to the union you expect.
- **Sort parameter is non-portable.** `sort=-date` (descending) on one platform is `sort=date desc` on another. If you need stable pagination across requests, use a unique-id sort, not a date sort.
- **Geo facets are different.** Some platforms expose `geofilter.distance=lat,lon,radius_m` or `geofilter.polygon=`. These are not facets in the count-by-value sense — they're spatial predicates. Different API.
- **Counts may be approximated** at high cardinality. Elasticsearch backends often return `nhits` as an approximation when the value is large (the `track_total_hits` flag controls this). The number is correct to within a few percent, not exact.

## Related

- `arcgis-feature-server.md` — when the dataset is spatial, the ArcGIS path may be available alongside or instead of this one
- `../discovery/har-driven-workflow.md` — recovering the endpoint shape and refine-param convention from a real session
- `templated-cms-schema-drift.md` — the same SaaS-platform-vendor deployed on many tenants uses the same protocol but the facet field names will differ per dataset
