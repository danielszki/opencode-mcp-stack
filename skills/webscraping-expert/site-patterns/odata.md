# OData APIs (v2 / v3 / v4)

OData is a standardized REST-query protocol used heavily by statistics offices and government portals (e.g. Statistics Netherlands / CBS, many Microsoft-backed and SAP-backed portals). When you spot it, you get typed, paginated, filterable data with almost no reverse-engineering — the query grammar is a spec.

## When you see this

- Endpoints exposing `$metadata`, and query params starting with `$`: `$filter`, `$select`, `$top`, `$skip`, `$orderby`, `$format`, `$expand`, `$count`.
- Response envelope `{"value": [...], "@odata.nextLink": "..."}` (v4) or `{"d": {"results": [...], "__next": "..."}}` (v2/v3).
- A service document at the root listing entity sets; CBS uses `odata.cbs.nl/ODataApi/odata/<table>/...`.

---

## How it works

The service root lists **entity sets** (tables). Each is queryable with a uniform grammar. `$metadata` (XML) describes the schema — read it once to learn column names and types.

```
GET  <root>/                          → service doc: list of entity sets
GET  <root>/$metadata                 → schema (XML: EntityType, Property, type)
GET  <root>/<EntitySet>?$top=1        → one row (inspect shape)
```

## Pattern — paginated pull with follow-the-nextLink

```python
import httpx

def odata_all(root: str, entity_set: str, *, select: str | None = None,
              filter: str | None = None, page_size: int = 10000) -> list[dict]:
    """Pull every row from an OData entity set, following server-driven paging."""
    params = {"$format": "json", "$top": page_size}
    if select: params["$select"] = select
    if filter: params["$filter"] = filter

    rows: list[dict] = []
    url = f"{root.rstrip('/')}/{entity_set}"
    with httpx.Client(timeout=60, follow_redirects=True) as c:
        while url:
            r = c.get(url, params=params); r.raise_for_status()
            body = r.json()
            batch = body.get("value", body.get("d", {}).get("results", []))  # v4 | v2/v3
            rows.extend(batch)
            # Server-driven paging: follow the next link if present, drop params (baked into link)
            url = body.get("@odata.nextLink") or body.get("d", {}).get("__next")
            params = None
    return rows
```

## Query building blocks

```
$filter=Year eq 2024 and RegionType eq 'Country'      # comparison + boolean
$filter=startswith(Name,'Data') and Value gt 100       # functions
$select=Region,Year,Value                              # projection (smaller payloads)
$orderby=Year desc
$top=1000 & $skip=2000                                 # client paging (prefer $skip/$top or nextLink, not both)
$count=true                                             # ask for total count (v4: @odata.count)
$expand=Dimensions                                     # inline related entities
```

**CBS (Statistics Netherlands) specifics:** a dataset is split into a **typed data table** plus **metadata code tables** (e.g. `RegioS`, `Perioden`). Pull the code tables too and join — the data table stores codes, not labels.

```python
root = "https://odata.cbs.nl/ODataApi/odata/<table_id>"
data     = odata_all(root, "TypedDataSet")
regions  = {r["Key"]: r["Title"] for r in odata_all(root, "RegioS")}
periods  = {p["Key"]: p["Title"] for p in odata_all(root, "Perioden")}
# join data["RegioS"] → regions[...], data["Perioden"] → periods[...]
```

---

## Gotchas

- **Version differs in the envelope**: v4 → `value` + `@odata.nextLink` + `@odata.count`; v2/v3 → `d.results` + `d.__next`. Handle both.
- **`$format=json`** — some v2 services default to XML (Atom). Always request JSON.
- **`$filter` string literals use single quotes**, and datetime/enum syntax varies by version — check `$metadata` for exact types.
- **Server-driven paging wins**: if the response has a next link, follow it and ignore your own `$skip` math (the server may cap page size below your `$top`).
- **Codes vs labels**: statistics OData almost always stores dimension *codes*; fetch the metadata code tables and join, or your bronze is unreadable.
- **Bronze rule**: persist raw rows (codes and all) as returned. Do the code→label join in silver, not during the pull.

---

## Related

- `site-patterns/sdmx-jsonstat.md` — the other big statistics-office format family (SDMX-JSON / JSON-stat)
- `site-patterns/pxweb.md` — PX-Web, common at Nordic statistics offices
- `site-patterns/ckan-dkan.md` — open-data catalog APIs
- `reference/medallion-architecture.md` — why the code→label join belongs in silver
