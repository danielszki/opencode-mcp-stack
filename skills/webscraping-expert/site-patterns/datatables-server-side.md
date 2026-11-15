# DataTables.net — server-side protocol

[DataTables.net](https://datatables.net/) is a JavaScript table widget bundled with thousands of admin panels, product catalogs, and B2B SaaS apps — anywhere a developer needed "a paginated, sortable, searchable table" without designing a custom API. When configured in **server-side mode**, it speaks a recognizable wire protocol you can replay with plain HTTP.

## When you see this

- POST to an endpoint with body containing `draw=N&start=N&length=N` and indexed `columns[0][data]=...&columns[0][searchable]=true&order[0][column]=0&order[0][dir]=asc`
- Response is JSON: `{"draw": N, "recordsTotal": int, "recordsFiltered": int, "data": [[col0, col1, ...], ...]}` or `{"data": [{col_name: val, ...}, ...]}`
- The page that hosts the table loads a `DataTables` script (often `jquery.dataTables.min.js`); view-source contains a `$('#someTable').DataTable({serverSide: true, ajax: ...})` initialization

## How it works

The DataTables widget POSTs the table's current state (page index, sort column, search filters, column visibility) to a single endpoint. The server runs a query against the matching dataset and returns a JSON envelope with the rows for the current view plus two counts:

- `recordsTotal` — total rows before filtering
- `recordsFiltered` — total rows after the current filter applies (== the value you paginate against)

Pagination is **offset-based**: `start` = how many rows to skip, `length` = page size. To walk the whole dataset, increment `start` by `length` until `start >= recordsFiltered`.

The `draw` field is an echo counter: send any integer, the server echoes it back. Used by the widget to discard out-of-order responses; for scraping it's noise.

## Pattern — full table scrape

```python
import httpx

ENDPOINT = "https://app.example.com/api/catalog/rows"  # illustrative endpoint
PAGE_SIZE = 100  # server-side max is often 100 or 500

def _form_body(start: int, length: int, sort_col: int = 0, sort_dir: str = "asc") -> dict:
    body = {
        "draw": "1",
        "start": str(start),
        "length": str(length),
        f"order[0][column]": str(sort_col),
        f"order[0][dir]": sort_dir,
        "search[value]": "",          # global search filter
        "search[regex]": "false",
    }
    # These catalog fields are illustrative. Read the actual columns from the
    # table's DataTable() init in view-source; the names and order must match.
    for i, name in enumerate(["id", "name", "category", "price", "updated_at"]):
        body[f"columns[{i}][data]"] = name
        body[f"columns[{i}][name]"] = ""
        body[f"columns[{i}][searchable]"] = "true"
        body[f"columns[{i}][orderable]"] = "true"
        body[f"columns[{i}][search][value]"] = ""
        body[f"columns[{i}][search][regex]"] = "false"
    return body

def iter_rows(client: httpx.Client):
    start = 0
    total = None
    while True:
        r = client.post(ENDPOINT, data=_form_body(start, PAGE_SIZE), timeout=60)
        payload = r.json()
        if total is None:
            total = payload["recordsFiltered"]
        for row in payload["data"]:
            yield row
        start += PAGE_SIZE
        if start >= total:
            return
```

Response `data` comes in one of two shapes:

```json
// Array-of-arrays (columns declared as positional integers in the init)
"data": [["item-001", "Example item", "Example category", 19.99, "2024-01-15"], ...]

// Array-of-objects (columns declared as named strings in the init)
"data": [{"id": "item-001", "name": "Example item", "category": "Example category", "price": 19.99, "updated_at": "2024-01-15"}, ...]
```

Inspect one response to see which one you have, then pick a row parser accordingly.

## Discovering the column names

DataTables requires the request to declare every column with the **exact name** the server expects. Get it from the page's init script:

```bash
# Most useful one-liner: grep the DataTable() init out of the page source
curl -s 'https://app.example.com/catalog' | grep -oE '\$\(["'\''](#[A-Za-z0-9_-]+)["'\'']\)\.DataTable\([^)]*\)' | head
```

Or open devtools, search the response text for `serverSide` — the `columns: [...]` array beside it lists exactly what to send.

## The two-step "seed then query" requirement

Some DataTables apps use a separate endpoint to **populate server-side session state** (date range, category filter, etc.) before the table will return useful results. An illustrative flow, using fictional paths:

1. GET the page hosting the table — collects an `ASP.NET_SessionId` / `JSESSIONID` cookie
2. POST to `/api/catalog/filters` with the filter values → seeds the session; usually returns a small "OK" response
3. POST to `/api/catalog/rows` (the DataTables endpoint) → now returns filtered rows for the seeded session

Skipping step 2 makes the table return either everything (unfiltered) or zero rows, depending on the app's default. **If the response total seems wrong, suspect a missing seed step.**

## Gotchas

- **`recordsTotal` ≠ `recordsFiltered`.** Paginate against `recordsFiltered`. If a search is active, `recordsTotal` is the unfiltered count and is not what you want to walk.
- **`length: -1` is "all rows"** in the official spec. Most production servers reject it or cap at the configured max. Don't rely on it.
- **Server-side max page size varies wildly** — sometimes 25, sometimes 1000. Try a few values; if the response is shorter than `length`, you've hit the cap.
- **Column-level `search[regex]=true` is almost always disabled server-side** — sending it just makes the filter silently no-op. Test that filters actually filter.
- **CSRF tokens.** ASP.NET MVC and Rails apps wrap the DataTables endpoint with a CSRF token. The token name varies (`__RequestVerificationToken`, `authenticity_token`, `X-CSRF-Token` header). Get it from the page that hosts the table and echo it on every POST.
- **Date columns may be HTML, not values.** The server frequently returns `<a href='/Detail/123'>15 Jan 2024</a>` instead of a raw date. Strip with BeautifulSoup or `re.sub(r"<[^>]+>", "", cell)` before parsing.
- **Detail-page IDs in the row HTML.** Even if the row data looks complete, the *only* way to get the internal record ID is to extract it from the `<a href>` embedded in the first column's HTML. Plan for an N+1 fetch to the detail page.

## Related

- `aspnet-webforms.md` — DataTables is common on ASP.NET MVC apps; the session-seed step is the MVC analog of the WebForms multi-POST flow
- `../discovery/devtools-workflow.md` — finding the DataTables endpoint when only the table UI is visible
- `templated-cms-schema-drift.md` — the same DataTables-based admin template deployed across many tenants will use the same protocol but different column names
