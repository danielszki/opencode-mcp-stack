# Tableau Public / Tableau Server dashboards

Public Tableau vizzes render as a canvas with no scrapeable DOM, but the data is delivered as JSON over a well-defined internal protocol. The trick is a **two-phase handoff**: bootstrap a real session in a browser to get the config + session id, then drive the data API with a lightweight client. The `tableauscraper` library wraps the protocol; you supply the session.

## When you see this

- URL under `public.tableau.com/views/<workbook>/<sheet>` or an `<iframe>`/`<tableau-viz>` embed pointing there.
- Network shows `…/bootstrapSession/sessions/<id>` and `…/sessions/<id>/commands/tabsrv/…` requests.
- A `tsConfigContainer` script/element in the page holding a JSON config blob.
- The visible chart is a `<canvas>` — no table elements to select.

---

## How it works

1. The embed loads and POSTs to **`/bootstrapSession/sessions/<sessionId>`**.
2. The response is **two concatenated JSON documents** prefixed by byte lengths: `<len>;{...info...}<len>;{...data...}`. The second doc holds the initial worksheet data (the "dataDictionary" + "presModel").
3. Further interactions (change a filter, select a mark) POST to `/sessions/<id>/commands/tabsrv/...` and return updated data.

`tableauscraper` speaks all of this — but it needs a **live session id + config**, which you bootstrap with a real browser.

---

## Pattern — bootstrap in browser, then hand off to tableauscraper

```python
import re, json
from playwright.sync_api import sync_playwright
from tableauscraper import TableauScraper

VIZ_URL = "https://public.tableau.com/views/<workbook>/<sheet>"

def bootstrap_and_scrape(viz_url: str):
    captured = {"bootstrap": None, "cookies": {}, "config": None}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(locale="en-US", viewport={"width": 1400, "height": 900})
        page = ctx.new_page()

        # 1. Grab the bootstrapSession response
        def on_response(resp):
            if "bootstrapSession" in resp.url:
                captured["bootstrap"] = resp.text()
        page.on("response", on_response)

        page.goto(viz_url, wait_until="networkidle")

        # 2. Pull the viz config out of the DOM (holds session id, sheet id, api version)
        captured["config"] = page.evaluate(
            "() => { const el = document.querySelector('#tsConfigContainer'); return el ? el.textContent : null; }"
        )
        # 3. Carry the cookies over to the lightweight client
        captured["cookies"] = {c["name"]: c["value"] for c in ctx.cookies()}
        browser.close()

    # 4. Parse the dual-JSON bootstrap payload
    info, data = _split_bootstrap(captured["bootstrap"])

    # 5. Hand the live session to tableauscraper for filter-driven extraction
    ts = TableauScraper()
    ts.loads(viz_url)                       # or feed it the captured session/cookies
    workbook = ts.getWorkbook()
    for ws in workbook.worksheets:
        print(ws.name, ws.data.shape)       # each worksheet → a pandas DataFrame
    return workbook


def _split_bootstrap(text: str):
    """Bootstrap payload is `<len>;{json}<len>;{json}` — return (info, data) dicts."""
    m = re.match(r"(\d+);(.*)", text, re.S)
    # First length-prefixed doc, then the rest is the second length-prefixed doc.
    # Robust approach: read the integer, slice that many chars, repeat.
    def read_one(s):
        mm = re.match(r"(\d+);", s)
        n = int(mm.group(1)); start = mm.end()
        return s[start:start+n], s[start+n:]
    first, rest = read_one(text)
    second, _ = read_one(rest)
    return json.loads(first), json.loads(second)
```

## Iterating filters (enumerate every value)

The whole reason to keep the session live: change a filter and re-read. `tableauscraper` exposes this directly:

```python
ws = workbook.getWorksheet("Sheet 1")
filters = ws.getFilters()                          # discover filter columns + values
for value in filters[0]["values"]:                 # e.g. each store / category / year
    updated = ws.setFilter(filters[0]["column"], value)
    df = updated.getWorksheet("Sheet 1").data
    # ... collect df per filter value
```

This is how you enumerate every value of a dashboard filter (e.g. one region, store, or category at a time): bootstrap once, then loop the filter reading each worksheet's data.

---

## Gotchas

- **Session ids expire** — bootstrap fresh each run; don't cache the session across runs.
- **The bootstrap payload is dual-JSON with byte-length prefixes**, not a single object. Parse by reading the length, not by regex-splitting on `{`.
- **`X-Tsi-Active-Tab` / api-version headers** may be needed on command requests — `tableauscraper` sets them, but if you hand-roll, copy them from the config blob (`tsConfigContainer`).
- **Filter values can be paginated/virtualized** in huge dashboards — read the filter's full domain from the data model, don't assume the first response lists them all.
- **Tableau Server (non-public)** behind auth: bootstrap after logging in with the browser, then carry cookies — same handoff.

---

## Related

- `site-patterns/embedded-bi-dashboard.md` — Power BI / Looker / Metabase (sibling BI stacks)
- `browser-automation/browser-techniques.md` — network-listener + cookie handoff mechanics
- `browser-automation/session-cache.md` — persisting the harvested session
- `discovery/har-driven-workflow.md` — capturing the bootstrap + command requests
