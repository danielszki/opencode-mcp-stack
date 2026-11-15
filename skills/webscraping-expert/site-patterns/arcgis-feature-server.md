# ArcGIS REST — FeatureServer / MapServer

Esri's ArcGIS REST API is the single most common GIS endpoint on the public internet — government open-data portals, utilities, cadastres, public-safety dashboards, and any "Leaflet/MapboxGL with administrative boundaries" map you've ever seen. If your target has a map UI sourced from a `*.arcgis.com` host or a self-hosted `/arcgis/rest/...` path, you almost certainly don't need a browser or a parser — there's a documented JSON API behind it.

## When you see this

- URL contains `/arcgis/rest/services/<FOLDER>/<SERVICE>/{FeatureServer,MapServer}/<LAYER_INDEX>/query`
- Host is `services<N>.arcgis.com` (ArcGIS Online tenants), `<org>.maps.arcgis.com`, or a self-hosted `*/arcgis/rest/...` reverse-proxy
- Response is JSON with `{features: [{attributes: {...}, geometry: {...}}], exceededTransferLimit: bool}`
- Layer metadata endpoint `<service>/<layer_index>?f=json` returns `{fields: [...], maxRecordCount: 1000, supportsPagination: true, ...}`

## How it works

ArcGIS exposes each layer as a queryable feature collection. A query is a GET (or POST) to `/<layer>/query` with a SQL-like `where` clause plus optional spatial and pagination params. The server returns JSON or GeoJSON; no auth needed for public services.

The four query params that cover 95% of scraping work:

| Param | Purpose |
|---|---|
| `where` | SQL-like filter, e.g. `where=1=1` (all), `where=CATEGORY='Example'`, `where=DateField>=date'2024-01-01'` (field names and values are illustrative; inspect layer metadata) |
| `outFields` | Comma-separated list of fields to return, or `*` for everything |
| `resultOffset` / `resultRecordCount` | Pagination |
| `f` | Output format: `json` (Esri JSON), `geojson` (RFC 7946), `pjson` (pretty), `html` (browser) |

Dates in `attributes.*` come back as **epoch milliseconds** (integers), not ISO strings — divide by 1000 and convert.

## Pattern — full layer scrape

```python
import httpx

BASE = "https://services2.arcgis.com/<ORG>/arcgis/rest/services/<SERVICE>/FeatureServer/0"

def discover(client: httpx.Client) -> dict:
    """Read layer metadata: field list, geometry type, page size, total count."""
    meta = client.get(f"{BASE}?f=json").json()
    count = client.get(
        f"{BASE}/query",
        params={"where": "1=1", "returnCountOnly": "true", "f": "json"},
    ).json()["count"]
    return {"meta": meta, "count": count, "page_size": meta.get("maxRecordCount", 1000)}

def iter_features(client: httpx.Client, page_size: int = 1000):
    offset = 0
    while True:
        r = client.get(
            f"{BASE}/query",
            params={
                "where": "1=1",
                "outFields": "*",
                "returnGeometry": "false",     # set "true" if you need geometry
                "resultOffset": offset,
                "resultRecordCount": page_size,
                "f": "json",
                "orderByFields": "OBJECTID ASC",
            },
            timeout=60,
        )
        payload = r.json()
        feats = payload.get("features", [])
        if not feats:
            return
        for f in feats:
            yield f["attributes"]
        # Two signals to stop:
        if len(feats) < page_size and not payload.get("exceededTransferLimit"):
            return
        offset += page_size
```

The **count-then-paginate** workflow lets you predict run time and detect partial scrapes — call `returnCountOnly=true` first.

## Spatial filtering (when you need it)

ArcGIS also accepts geometric filters — useful when the layer has millions of features but you only want a region:

```python
params = {
    "where": "1=1",
    "geometry": json.dumps({"xmin": ..., "ymin": ..., "xmax": ..., "ymax": ..., "spatialReference": {"wkid": 4326}}),
    "geometryType": "esriGeometryEnvelope",
    "inSR": 4326,
    "spatialRel": "esriSpatialRelIntersects",
    "outFields": "*",
    "f": "json",
}
```

Other accepted geometry types: `esriGeometryPoint`, `esriGeometryPolyline`, `esriGeometryPolygon`. `wkid: 4326` is plain lat/lon (WGS84).

## Service discovery

When you have a host but don't know the layer path:

- `<host>/arcgis/rest/services?f=json` — list of folders and root services
- `<host>/arcgis/rest/services/<FOLDER>?f=json` — services in a folder
- `<host>/arcgis/rest/services/<SERVICE>/FeatureServer?f=json` — layers in a service (each has an integer index)

Crawl the directory once, snapshot the field schemas, then build your scrape against specific layer indices.

## Gotchas

- **`exceededTransferLimit: true`** in the response means the server truncated your result. You got *some* features but not all — must paginate further with `resultOffset`. If `supportsPagination: false` on the layer metadata, the only way around it is to split the `where` clause into smaller buckets (e.g. by date range or `OBJECTID` ranges).
- **`maxRecordCount` is server-imposed** (typically 1000 or 2000). Asking for `resultRecordCount=5000` silently caps at the server max — no error, just fewer rows than you asked for. Always read the layer metadata first.
- **`returnGeometry=true` is expensive.** Responses balloon 10–100x when geometry is included. Set `false` unless you actually need the shape.
- **Dates are epoch milliseconds**, not seconds and not ISO. `datetime.fromtimestamp(value / 1000, tz=timezone.utc)`. Null dates may come back as `0`, `-1`, or actual `null` depending on the layer.
- **Field name case varies.** Some layers use `OBJECTID`, others `objectid`, `Objectid`, `OID_`. Read the metadata; don't hardcode.
- **`where=1=1` may be rejected** on some services with strict query validators. Try `where=OBJECTID>0` as a fallback.
- **Self-hosted instances behind ArcGIS Server (vs ArcGIS Online)** may require an auth token via `/arcgis/tokens/generateToken` even for "public" data. If you get `{"error": {"code": 499}}`, that's why.
- **`f=geojson` is not universally supported** — older ArcGIS Server installs only emit Esri JSON. The two are convertible but not identical (Esri JSON's `attributes` becomes GeoJSON's `properties`; the geometry encoding differs).

## Related

- `geojson-bbox-map-portal.md` — non-Esri map portals that look superficially similar but speak a custom protocol
- `../discovery/devtools-workflow.md` — finding the FeatureServer URL when only the map UI is visible
- `../parsing/document-extraction.md` — when ArcGIS just hosts a layer of PDF/document URLs (common for document attachments)
