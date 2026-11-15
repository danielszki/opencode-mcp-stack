# ASP.NET WebForms

A whole family of legacy enterprise sites (government portals, universities, judicial systems, intranet apps) run on ASP.NET WebForms. They share a recognizable HTTP shape that, once you know it, makes them very scrapeable — but they're nothing like a modern JSON API.

## When you see this

Recognize ASP.NET WebForms by any of these signals:

- URLs end in `.aspx`
- Page source contains hidden inputs named `__VIEWSTATE`, `__VIEWSTATEGENERATOR`, `__EVENTVALIDATION`, `__EVENTTARGET`, `__EVENTARGUMENT`, `__PREVIOUSPAGE`
- JS function `__doPostBack(eventTarget, eventArgument)` is defined inline
- Control names follow a `ctlNN$Container$Control` pattern
- Form action is the same URL the page was served from (POST-to-self)
- Page has a `<form runat="server">` (visible in source as `<form ... id="aspnetForm">`)

## How it works

ASP.NET WebForms simulates desktop-app UI on top of HTTP by **serializing the entire server-side control tree into a hidden field on every page** (`__VIEWSTATE`). Every navigation is a POST back to the same URL, carrying:

- The full opaque VIEWSTATE blob (so the server can reconstruct page state)
- An `__EVENTTARGET` identifying which control was "clicked"
- An optional `__EVENTARGUMENT` (e.g. for paging: `Page$3`)
- `__EVENTVALIDATION` (anti-tampering hash; required)
- Any visible form fields

**Implication for scraping:** you cannot just GET a deep page. You must replay the user's click sequence, carrying the VIEWSTATE forward at each step.

## Pattern — multi-step navigation

A typical flow has 2-4 sequential POSTs before you reach a results page. Each step must echo back ALL hidden fields from the previous response. The control names below are illustrative; discover the target's actual names from its DOM.

```python
from bs4 import BeautifulSoup
from curl_cffi import requests as cffi_requests

def _hidden_fields(soup: BeautifulSoup) -> dict[str, str]:
    """All <input type=hidden> name→value pairs. Echo these in every POST."""
    return {
        inp["name"]: inp.get("value", "")
        for inp in soup.find_all("input", {"type": "hidden"})
        if inp.get("name")
    }

session = cffi_requests.Session()

# Step 1: GET the entry page, capture VIEWSTATE
r1 = session.get(LIST_URL, impersonate="chrome", timeout=60)
soup1 = BeautifulSoup(r1.text, "html.parser")

# Step 2: POST a control click (e.g. radio button + "Next")
r2 = session.post(
    LIST_URL,
    data={
        **_hidden_fields(soup1),
        "ctl00$Main$Category": "books",
        "ctl00$Main$Next": "Next",
    },
    impersonate="chrome", timeout=60,
)
soup2 = BeautifulSoup(r2.text, "html.parser")

# Step 3: POST a search form
r3 = session.post(
    r2.url,
    data={
        **_hidden_fields(soup2),
        "ctl00$Main$DateFrom": "01/01/2024",
        "ctl00$Main$DateTo": "31/12/2024",
        "ctl00$Main$Search": "Search",
    },
    impersonate="chrome", timeout=60, allow_redirects=True,
)
soup3 = BeautifulSoup(r3.text, "html.parser")

# Step 4: parse results from soup3, paginate from here
```

## Pagination — two flavors

WebForms apps paginate one of two ways. Look at the page source / capture a HAR to see which:

**Flavor A — URL query param:**
```
GET https://app.example.com/Results.aspx?PageNumber=3
```
You can replay this directly with GET. Easiest to scrape.

**Flavor B — Event postback:**
```python
session.post(
    results_url,
    data={
        **_hidden_fields(prev_soup),
        "__EVENTTARGET": "ctl00$Main$Page3",
        "__EVENTARGUMENT": "",
    },
)
```
You must POST and carry forward the VIEWSTATE. The `__EVENTTARGET` value is the `name` attribute of the pagination button.

**Flavor C — grid-control event:**
```python
data["__EVENTTARGET"] = "ctl00$Main$Results"
data["__EVENTARGUMENT"] = "Page$3"
```

Some grid controls use `Page$N` as event argument. Inspect a real HAR to be sure.

## Detail-page Referer requirement (frequently overlooked)

Many ASP.NET apps refuse to serve a detail page unless `Referer` matches the results page. Symptom: detail GET returns `HTTP 200` with `<title>Error</title>` and an empty form.

```python
session.get(
    f"{DETAIL_BASE}?Id=12345",
    headers={**sticky_proxy_headers, "Referer": RESULTS_URL},
    impersonate="chrome",
)
```

Always set `Referer` to the results page URL when fetching detail. Cookies alone are not enough.

## "HTTP 200 + Error" — invisible failures

ASP.NET apps return `200 OK` with a generic error page in three common situations:

1. Session expired (VIEWSTATE mismatch)
2. CSRF token / `__EVENTVALIDATION` rejected
3. You tried to fetch a stateful page (e.g. detail by internal ID) without going through the search flow

**Detection helper:**

```python
def _is_aspnet_error_page(soup: BeautifulSoup) -> bool:
    """Many ASP.NET sites return 200 + Error.aspx when the session is invalid."""
    title = (soup.title.string if soup.title else "").strip().lower()
    if title == "error":
        return True
    if soup.find("div", id=lambda x: x and "ErrorPanel" in (x or "")):
        return True
    body = str(soup)[:5000].lower()
    return "aspxerrorpath" in body
```

Call this after every navigation step. If true: re-boot the whole nav sequence from step 1 — don't try to "fix" the existing session.

## Dynamic control IDs (`ctl04`, `ctl09`, etc.)

The auto-generated control IDs change between deployments of the same template. Discover inputs from their labels or other stable DOM relationships instead of copying a control name from another site. This illustrative form associates a label with its input using `for` and `id`:

```python
soup = BeautifulSoup(r.text, "html.parser")

def input_name_for_label(soup: BeautifulSoup, label_text: str) -> str:
    label = soup.find("label", string=lambda text: text and text.strip() == label_text)
    if label is None or not label.get("for"):
        raise ValueError(f"No associated input for {label_text!r}")
    field = soup.find("input", id=label["for"])
    if field is None or not field.get("name"):
        raise ValueError(f"Input has no submitted name for {label_text!r}")
    return field["name"]

from_field = input_name_for_label(soup, "Created from")
to_field = input_name_for_label(soup, "Created to")
```

The same template deployed across many instances will use `ctl04` here and `ctl09` there. Always discover.

## Stateful internal IDs

When detail pages use a numeric `?Id=12345` param, those IDs are often **scoped to the session that generated them**. Capturing an ID from a HAR file and trying to fetch it cold in a new session will return the "Error" page.

Don't try to persist these IDs across runs. Always re-search and re-collect IDs at the start of each crawl session.

## ViewState as a data source

A non-obvious variant: some WebForms apps embed the **entire search result set inside `__VIEWSTATE`** rather than rendering it as HTML rows. After a search POST, the visible page is almost empty — the data lives base64-encoded in the hidden VIEWSTATE blob, and a small JS snippet hydrates the table client-side.

When you see this:
- The response HTML has no `<tr>` rows for the data you expected, only a small loader or "0 results" placeholder
- `__VIEWSTATE` ballooned from typical ~10 KB to hundreds of KB or megabytes
- View-source contains a giant base64 string and almost nothing else

The data IS there — just decode the VIEWSTATE:

```python
import base64, re
from bs4 import BeautifulSoup

soup = BeautifulSoup(html, "html.parser")
vs = soup.find("input", {"id": "__VIEWSTATE"})["value"]
raw = base64.b64decode(vs)
# Resulting blob is a binary-serialized .NET object graph. Easiest path: search for
# the recognizable bits with regex rather than fully parsing.
records = re.findall(rb'<div class="result">(.*?)</div>', raw, flags=re.DOTALL)
```

This turns a stateful multi-POST WebForms flow into a **single GET → single decode**. Watch for it whenever a search "works in the browser" but your scraped HTML is mysteriously empty.

## Multi-tenant SaaS recognition

Some hosted WebForms products serve multiple tenants. Keep the entry URL and tenant configuration separate from extraction logic, discover each deployment's navigation from its own DOM or HAR, and validate field labels before reusing a parser. Pair this with `templated-cms-schema-drift.md` for label-drift handling.

## Gotchas

- `__VIEWSTATE` is **massive** (often >10 KB). Don't log it or store it in payload. Echo it forward, then drop it.
- The `__VIEWSTATE` value depends on the response that generated it — you can't construct one from scratch. Always grab it from the previous response.
- Some sites add `__VIEWSTATE` validation against IP address — losing the sticky proxy session breaks the form. See `../networking/proxy-zyte.md`.
- A catalog's list page may show only item names and summaries; specifications or stock history may require detail-page requests. Check the required fields before planning N+1 fetches.
- Pages may have multiple `<table>` elements. Inspect the DOM to identify the results table instead of assuming a particular ID.

## Minimal working crawler skeleton

```python
def crawl(from_date: str, to_date: str, proxy_url: str | None = None) -> Iterator[dict]:
    session = cffi_requests.Session()
    sticky = open_proxy_session(proxy_url)  # see networking/proxy-zyte.md

    # 1. Boot
    r1 = session.get(LIST_URL, headers=sticky, **_pxy(proxy_url))
    soup1 = BeautifulSoup(r1.text, "html.parser")

    # 2. Optional radio selection
    r2 = session.post(LIST_URL, data={**_hidden_fields(soup1), ...}, headers=sticky, **_pxy(proxy_url))
    soup2 = BeautifulSoup(r2.text, "html.parser")

    # 3. Date-range search
    r3 = session.post(r2.url, data={**_hidden_fields(soup2), ...}, headers=sticky, **_pxy(proxy_url), allow_redirects=True)
    soup3 = BeautifulSoup(r3.text, "html.parser")

    # 4. Loop over pages
    page = 1
    last = _last_page(soup3)
    while page <= last:
        soup = soup3 if page == 1 else _fetch_page(session, page, sticky, proxy_url)
        for row in _parse_rows(soup):
            internal_id = _extract_internal_id(row)
            detail = _fetch_detail(session, internal_id, sticky, proxy_url, referer=RESULTS_URL)
            yield {**row, **detail}
        page += 1
```

## Related

- `../networking/proxy-zyte.md` — sticky session is essential for VIEWSTATE-based sites
- `../anti-bot/error-decoders.md` — HTTP 421 misdirected, "200 + Error" deep dive
- `../reliability/concurrency-curl-cffi.md` — per-thread sessions when parallelizing N+1 detail fetches
- `templated-cms-schema-drift.md` — same template, different field names per deployment
- `legacy-cms.md` — adjacent quirks (ColdFusion, JSP, classic ASP)
