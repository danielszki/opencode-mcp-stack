# GeoJSON map portal with bbox query

A "search on a map" UI can expose a custom spatial API — for example, a catalog of locations displayed on a Leaflet, Mapbox GL, or OpenLayers map. The frontend sends the visible map bounds and selected filters, then receives GeoJSON features.

If your target speaks ArcGIS REST, see `arcgis-feature-server.md` instead. This page covers custom APIs whose request schema must be discovered from observed traffic.

## When you see this

- Map interactions trigger requests containing a geographic bounding box.
- Responses contain GeoJSON features with `properties` and `geometry`.
- Panning, zooming, or changing a filter changes the returned features.
- No standard ArcGIS path (`/arcgis/rest/services/...`) appears in the requests.

## How it works

The server returns the features inside the requested rectangle. A larger bounding box may cover the whole dataset, but pagination or smaller spatial slices can still be required.

**The endpoint, request keys, and `total` field below are illustrative.** Map them to the observed API before using the code. The first example assumes offset pagination and an accurate total for the matching bounding box.

```python
import httpx

ENDPOINT = "https://locations.example.com/api/search"
WORLD_BBOX = {"west": -180, "south": -90, "east": 180, "north": 90}

def fetch_all(client: httpx.Client, page_size: int = 1000):
    offset = 0
    while True:
        response = client.post(
            ENDPOINT,
            json={"bbox": WORLD_BBOX, "offset": offset, "limit": page_size},
            timeout=120,
        )
        response.raise_for_status()
        payload = response.json()
        features = payload["features"]
        if not features and offset < payload["total"]:
            raise RuntimeError("Pagination stopped before the reported total")
        yield from features
        offset += len(features)
        if offset >= payload["total"]:
            return
```

Check two behaviors before relying on a single wide bounding box:

1. **Result caps.** Compare the reported total with the features actually returned. If the API ignores pagination, subdivide the bounds instead.
2. **Clustering.** At wide zoom levels, some APIs return aggregates instead of individual locations. Use smaller bounds and confirm that the response contains individual records.

## Bbox quadtree fallback

When pagination is unavailable, recursively subdivide a bounding box until each response contains all matching features. This illustrative example assumes an accurate `total` for each box; without that count, establish a separate way to detect truncation before treating a slice as complete.

```python
def quadtree_fetch(client, bbox: dict, cap: int = 5000, max_depth: int = 16):
    response = client.post(
        ENDPOINT,
        json={"bbox": bbox, "offset": 0, "limit": cap},
        timeout=120,
    )
    response.raise_for_status()
    payload = response.json()
    features = payload["features"]
    if payload["total"] <= len(features):
        yield from features
        return
    if max_depth <= 0:
        raise RuntimeError("Spatial slices remain truncated; another extraction path is needed")

    midx = (bbox["west"] + bbox["east"]) / 2
    midy = (bbox["south"] + bbox["north"]) / 2
    for west, south, east, north in [
        (bbox["west"], bbox["south"], midx, midy),
        (midx, bbox["south"], bbox["east"], midy),
        (bbox["west"], midy, midx, bbox["north"]),
        (midx, midy, bbox["east"], bbox["north"]),
    ]:
        sub = {"west": west, "south": south, "east": east, "north": north}
        yield from quadtree_fetch(client, sub, cap, max_depth - 1)
```

Deduplicate features by stable ID at the end — features on shared boundaries may be returned twice. If many records share a location, spatial splitting alone may never avoid the cap; use another filter or a bulk endpoint.

## Discovering the request schema

Capture map requests in a HAR and compare the bodies before and after panning, zooming, and changing filters. Identify which values describe bounds, pagination, and filters. Preserve the names and formats observed on the current target instead of borrowing a schema from another site.

```bash
# Inspect a few POST bodies from a local capture.
python3 -c "import json,sys; r=json.load(open(sys.argv[1])); \
  print(json.dumps([e['request']['postData'] for e in r['log']['entries'] \
                    if e['request']['method']=='POST' and 'postData' in e['request']][:3], indent=2))" capture.har
```

## Gotchas

- **Coordinate order:** GeoJSON uses `[longitude, latitude]`; confirm the request's coordinate order against a known point.
- **Projection:** Check the coordinate reference system before constructing bounds. Transform coordinates when the API uses a projected system.
- **Truncation:** A successful response does not establish completeness. Validate counts and pagination, and inspect whether results are clustered.
- **Filter formats:** Derive date and numeric formats from observed requests; do not assume units or serialization.
- **Pagination:** Verify that changing the offset actually changes the returned records before relying on it.
- **Authentication and throttling:** Carry the required session state from the observed request and respect the target's rate limits.

## Related

- `arcgis-feature-server.md` — documented Esri ArcGIS APIs
- `../discovery/har-driven-workflow.md` — recover an endpoint and its request schema from a session
- `spa-frameworks.md` — API discovery for map interfaces rendered by an SPA
