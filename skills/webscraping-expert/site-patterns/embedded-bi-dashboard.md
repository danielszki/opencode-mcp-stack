# Embedded BI dashboard

A pattern that recurs whenever someone publishes a "public dashboard" without a documented API — corporate KPI boards, government open-data dashboards, election results, COVID-style trackers, real-estate analytics. The page is an iframe (or first-party embed) of a hosted BI product: Microsoft Power BI public reports, Tableau Public, Looker Studio (formerly Google Data Studio), Metabase public dashboards, Apache Superset embeds, Mode public reports.

These products share an architectural shape: a thin SPA shell that loads a binary visualization runtime, talks to a vendor query endpoint over HTTP/WebSocket, and renders the result into canvases and virtualized DOM lists. There is **no official scraping API**. Two viable techniques work across vendors.

## When you see this

- URL like `app.<vendor>.com/view?r=<token>`, `public.<vendor>.com/views/<workbook>/<sheet>`, `<host>/public/dashboard/<uuid>`, `lookerstudio.google.com/embed/reporting/<id>`, or the parent page contains an `<iframe>` to such a URL
- View-source nearly empty + a single `<div>` mount point + a big JS bundle from a CDN owned by the BI vendor
- DOM has visual containers identifiable by ARIA: `role="group"` with `aria-label="<report-or-visual-name>"`, classes like `*-slicer`, `*-card`, `*-visual`, `.slicerText`, `.visual-container`
- After hydration, the page POSTs to a `/querydata`, `/render-tooltip-server`, `/api/v1/query`, `/dataset/query`, or vendor-named endpoint and the response is a binary or compact-JSON blob (not human-readable rows)
- Often a `<canvas>` element draws the chart rather than HTML elements

## How it works

The BI runtime downloads a **report definition** (visuals, layout, queries) once, then issues query requests for each visual. The frontend never serializes the data to HTML — it draws into canvases and virtualizes lists. Two consequences:

1. The full data set is **never present in the DOM at once**. Only the slice currently scrolled into view is rendered.
2. The query responses use **compact, typed formats** to minimize bytes — repeated values are dictionary-encoded, dates are epoch numbers, numbers may be tagged with type discriminators.

## Two techniques

### (a) Intercept the structured query response (preferred when feasible)

Far cheaper and more accurate than DOM scraping. Drive a real browser to the dashboard, register a network listener on the visualization query endpoint, parse the structured response.

```python
from playwright.sync_api import sync_playwright
import json

QUERY_PATH_HINT = "querydata"  # adjust per vendor: "querydata", "render-tooltip-server", "/api/v1/query"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    captured: list[dict] = []
    def on_response(resp):
        if QUERY_PATH_HINT in resp.url and resp.request.method == "POST":
            try:
                captured.append({"url": resp.url, "body": resp.json()})
            except Exception:
                captured.append({"url": resp.url, "text": resp.text()[:50000]})
    page.on("response", on_response)

    page.goto(DASHBOARD_URL, wait_until="networkidle")
    # Optionally interact: click slicers, change filters — each triggers a new query
    page.wait_for_timeout(3000)
    browser.close()
```

The captured payload is the source of truth. Decode it according to the vendor's wire format — see "Wire formats" below.

### (b) DOM scrape with virtual-scroll handling (when no usable query response exists)

When the visualization is rendered to canvas (no DOM data at all) the intercept path is your only option. When the visualization is a virtualized **list** (DOM exists but only for visible rows), you can scroll it to load every row and read them out.

The non-obvious part: the scroll happens inside a **specific inner element** the runtime virtualizes against, not the page or the visual container. Look for class names like `.scrollbar-inner`, `.scroll-content`, `.virtual-scroll`, `[data-virtuoso-scroller="true"]`.

```python
SCROLL_TARGET = ".scrollbar-inner .scroll-content"  # vendor-dependent
rows: list[str] = []
seen = set()
while True:
    page.evaluate(f"document.querySelector('{SCROLL_TARGET}').scrollTop += 600")
    page.wait_for_timeout(150)
    visible = page.eval_on_selector_all(".slicerText", "els => els.map(e => e.textContent)")
    new = [v for v in visible if v not in seen]
    if not new:
        break
    for v in new:
        seen.add(v)
        rows.append(v)
```

Stop when scrolling for several iterations yields no new rows. This is fragile against vendor updates — the intercept path (a) is preferred when available.

## Wire formats

Each vendor encodes the response differently. Be prepared to write a small decoder.

**Microsoft Power BI (DSR — Data Set Result):**
- Response body has nested `results[*].result.data.dsr.DS[*].PH[*].DM0[]` arrays
- Each `DM0[i]` is a row encoded with `C` (column values), `R` (repeat mask), `Ø` (null mask)
- Column types are declared in `descriptor.Select` — `1`=string, `2`=currency, `3`=float, `7`=datetime (epoch ms), `13`=decimal with trailing `D` literal
- Repeat encoding: when `C` is missing or `R` indicates "reuse previous", look back to the prior row for the value

**Tableau:** server-side rendering with HTML/JSON hybrid; query responses include `secondaryInfo.presModelMap` trees. Tableau's public viz API is documented enough that purpose-built libraries (`tableauscraper`, `TableauScraper`) exist and are usually worth using rather than rolling your own. **Full Tableau playbook (bootstrapSession + tableauscraper session handoff + filter enumeration): `tableau-public.md`.**

**Looker Studio / Metabase / Superset:** the public dashboard format tends to be more straightforward JSON (`{"rows": [{"col0": ..., "col1": ...}, ...], "cols": [...]}`). Decode is usually trivial once you find the right endpoint.

If you find yourself reverse-engineering Power BI DSR from scratch, look first for `python-powerbiclient`, `pbi-tools`, or community parsers; the format is annoying enough that most scrapers have published their decoder.

## Authentication-less embeds

Public/shared dashboards usually have no auth — the embed token in the URL (`?r=`, `?token=`, `?share=`) is the credential, signed at publish time. Treat it as a long-lived API key:

- It does not rotate unless the dashboard owner regenerates the share link
- It works from any IP; no Referer / Origin enforcement in most cases
- Some vendors restrict by domain when the dashboard is "embedded in" rather than "shared by link" — check by hitting the embed URL directly with curl and seeing if you get an HTML shell back

## Gotchas

- **Canvas-only visuals have no scrapable DOM at all.** If `document.querySelectorAll(".some-row")` returns zero from devtools while the chart visibly shows hundreds of points, the data is in a canvas. The only path is intercepting the query response.
- **Slicer / filter dropdowns lazy-load via virtual scroll.** A dropdown showing "2 of 142" items will only have 2 in the DOM. Open the dropdown, scroll its inner virtualization target, accumulate.
- **Query endpoints accept stateful continuation tokens.** If you replay a captured POST body literally, you may get a 400 or a stale snapshot — the body often contains a session-scoped query ID. Capture fresh each run, don't pin payloads across days.
- **Response bodies can be 10–100 MB** for a full dashboard's data. Decode incrementally; don't load the whole JSON into a single Python dict if memory is tight.
- **Date columns: epoch milliseconds, but sometimes shifted to a vendor epoch.** Some BI products emit dates as "days since 1899-12-30" (Excel epoch) or similar. Verify against a known date in the visible UI before trusting bulk decode.
- **The same dashboard can re-render differently on different viewport sizes** (responsive layout). When using technique (b), set a fixed `viewport={"width": 1920, "height": 1080}` to make scrolls predictable.
- **Rate limits are real but undocumented.** Hammering the query endpoint typically triggers 429s after a few hundred requests/minute. Throttle to ~1 query/sec by default.

## Related

- `spa-frameworks.md` — the dashboard's outer page is an SPA; finding the query endpoint follows the same workflow
- `../browser-automation/browser-techniques.md` — when you need a real browser to bootstrap the embed and capture responses
- `../discovery/har-driven-workflow.md` — capturing the query endpoint and response shape from a real session
- `graphql.md` — some BI vendors use GraphQL as their query transport; the playbook there applies
