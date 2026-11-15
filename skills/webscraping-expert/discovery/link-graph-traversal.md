# Link-graph traversal — finding data within a site

When the user gives you a starting URL but **the data isn't on that page directly** (e.g. they hand you a retailer's homepage and the full product catalog is buried three clicks deep, or an event site where the schedule sits behind several menus), you have to find the data page yourself. This file is the recipe.

A useful mental model is a "binary tree" — recursive descent through links, narrowing as you go. The actual technique is graph traversal of the site's internal link structure, scored by signals that indicate "this page probably has the data".

## When to use this

- User answered Q1 with "(b) I have a URL to a site, and I think the data is somewhere inside it"
- Autonomous discovery's quick checklist (`autonomous-discovery.md`) ran clean — no obvious sitemap entry or API path — but the data still has to be in there somewhere
- Site has hundreds or thousands of pages and you need to find the one with the right table / register / list

If you already have the exact data URL, skip this file and go to `har-driven-workflow.md`.

## The four phases

```
Phase 1 — Cheap shortcuts first    (sitemap, robots.txt, search box)
Phase 2 — Seed the frontier        (collect candidate pages from the entry URL)
Phase 3 — Scored traversal         (BFS with relevance heuristics; prune aggressively)
Phase 4 — Identify data pages      (signals that a page actually contains the target data)
```

Try Phase 1 first — it solves ~60% of cases in seconds and avoids the whole traversal. Only fall through to Phase 2+ when shortcuts fail.

---

## Phase 1 — Cheap shortcuts (try these first, in order)

### Shortcut A — robots.txt + sitemap

```python
import httpx

def quick_sitemap_check(base_url: str) -> list[str]:
    """Return all URLs declared in robots.txt + sitemap.xml chain."""
    urls: list[str] = []
    # robots.txt often points to a sitemap
    r = httpx.get(f"{base_url.rstrip('/')}/robots.txt", timeout=15, follow_redirects=True)
    sitemap_urls = []
    if r.status_code == 200:
        for line in r.text.splitlines():
            if line.lower().startswith("sitemap:"):
                sitemap_urls.append(line.split(":", 1)[1].strip())
    # Fallback to /sitemap.xml directly
    sitemap_urls = sitemap_urls or [f"{base_url.rstrip('/')}/sitemap.xml"]

    from xml.etree import ElementTree as ET
    for sm_url in sitemap_urls:
        try:
            r = httpx.get(sm_url, timeout=15, follow_redirects=True)
            if r.status_code != 200:
                continue
            root = ET.fromstring(r.text)
            # Sitemap index: contains <sitemap><loc>...</loc></sitemap> entries
            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            for loc in root.findall(".//sm:loc", ns):
                urls.append(loc.text)
        except Exception:
            continue
    return urls
```

Now filter the URL list with keyword matches from the user's data description. If the user said "product catalog" you're looking for paths containing `product`, `catalog`, `shop`, `inventory`, `category`; if they said "a public register", paths like `register`, `search`, `data`, `export`. A single grep usually surfaces the right page.

### Shortcut B — Site's own search box

If the site has a search box visible on the homepage, **try using it before traversing**. Search forms usually POST to a `/search?q=...` endpoint that returns ranked results — the site does the discovery work for you.

```python
# Inspect the homepage HTML for a search form
from bs4 import BeautifulSoup
soup = BeautifulSoup(httpx.get(base_url).text, "html.parser")
search_forms = soup.find_all("form", attrs={"role": "search"}) + \
               soup.find_all("form", action=lambda a: a and "search" in a.lower())
```

If found, replicate the GET/POST with the user's keywords as `q=`. Top hits are very likely the data page.

### Shortcut C — Google `site:` query (when shortcuts A & B fail)

Falls back to the Google deep-research workflow but narrowed to the site:

```
site:example.com "product catalog export"
site:example.com inurl:inventory
site:example.com filetype:xlsx
```

See `google-deep-research.md` Phase 3 templates. With `site:` applied, you usually only need 10–30 queries to surface the data page, not 300.

---

## Phase 2 — Seed the frontier

If shortcuts didn't surface the data page, start traversing. The "frontier" is the queue of URLs to visit; seed it from the entry URL's outbound links plus a few obvious candidates.

```python
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def extract_internal_links(url: str, html: str) -> set[str]:
    """All same-host hrefs from the page, normalized."""
    soup = BeautifulSoup(html, "html.parser")
    host = urlparse(url).netloc
    links: set[str] = set()
    for a in soup.find_all("a", href=True):
        absolute = urljoin(url, a["href"])
        if urlparse(absolute).netloc == host:
            # Drop fragments and query strings for dedup
            clean = absolute.split("#")[0]
            links.add(clean)
    return links

def seed_frontier(entry_url: str) -> set[str]:
    r = httpx.get(entry_url, timeout=30, follow_redirects=True)
    return extract_internal_links(entry_url, r.text)
```

A typical homepage yields 50–200 internal links. That's the starting set for Phase 3.

**Common "obvious candidate" paths to inject into the frontier manually** if not already linked:

```
/sitemap, /sitemap.html
/site-map
/directory
/services
/data, /open-data, /datasets
/search, /find
/register, /registers
/products, /catalog, /inventory, /listings  (or whatever the data is)
/api, /api/v1, /api/v2
/feed, /rss, /atom.xml
```

---

## Phase 3 — Scored traversal

Do a breadth-first walk, but **score each link before queueing it** and only visit links above a threshold. Without scoring, a large site has 10 000+ pages and you'd walk forever.

### Scoring heuristics

For each link `<a href="X">anchor text</a>` discovered:

| Signal | Score | Detection |
|---|---|---|
| Anchor text contains a user keyword | +5 | substring match |
| URL path contains a user keyword | +3 | substring in `path` |
| URL path contains data-pattern terms (`register`, `data`, `download`, `search`, `list`, `export`) | +2 | static list |
| URL ends in `.csv` / `.xlsx` / `.json` / `.xml` | +10 | extension check |
| URL contains a year (`2024`, `2025`) | +1 | regex |
| Link is in `<nav>` or `<header>` (likely menu item, often the right path) | +1 | DOM context |
| Anchor text is generic (`click here`, `more`, `details`) | -1 | static list |
| URL contains `/contact`, `/about`, `/careers`, `/news`, `/blog`, `/login` | -3 | static list |
| URL contains a fragment that increments (`?p=1`, `?date=2024-01-15`) — calendar / pagination trap | -5 | regex on query |
| Depth > 5 from entry | -1 per extra level | track depth |

Sum the signals; queue only links with **score ≥ 3**. Adjust threshold based on result count — too few candidates → lower threshold; too many → raise it.

### The traversal loop

```python
import heapq
from collections import deque

def traverse(entry_url: str, keywords: list[str], max_pages: int = 200):
    visited: set[str] = set()
    frontier: deque = deque([(entry_url, 0)])  # (url, depth)
    candidates: list[tuple[float, str]] = []  # (score, url) for data-likely pages

    while frontier and len(visited) < max_pages:
        url, depth = frontier.popleft()
        if url in visited or depth > 5:
            continue
        visited.add(url)

        try:
            r = httpx.get(url, timeout=20, follow_redirects=True)
        except Exception:
            continue
        if r.status_code != 200 or "text/html" not in r.headers.get("content-type", ""):
            continue

        # Phase 4 — is THIS page a data page?
        page_score = score_data_page(r.text, keywords)
        if page_score >= 5:
            candidates.append((page_score, url))

        # Score and queue outbound links
        for link in extract_internal_links(url, r.text):
            if link in visited:
                continue
            link_score = score_link(link, anchor_text_for(link, r.text), keywords)
            if link_score >= 3:
                frontier.append((link, depth + 1))

    candidates.sort(reverse=True)
    return candidates[:20]
```

This is a sketch — production code should add per-host rate limiting, dedup of near-identical URLs (e.g. session IDs in query string), and respect `robots.txt`.

---

## Phase 4 — Identify data pages

While traversing, score each fetched page on signals that suggest "this page actually has the target data":

| Signal | Score | Detection |
|---|---|---|
| Page contains a `<table>` with >5 rows of consistent structure | +5 | `len(soup.find_all("tr")) > 5` + uniform `<td>` count per row |
| Page has pagination controls | +3 | links/buttons with `page=`, `next`, "Page 2", `<nav class="pagination">` |
| Page has a date column header (`Date`, `Published`, `Updated`, etc.) | +3 | text match in `<th>` |
| Page has a search/filter form | +2 | `<form>` with text inputs, date pickers, dropdowns |
| Page contains keyword-density of user keywords > 1% | +2 | count keyword hits / word count |
| Page is a list of downloadable files (`.csv`, `.xlsx`, `.pdf`) | +5 | href extensions in anchor list |
| Page is GIS / map embed (Leaflet, MapboxGL, ArcGIS) | +4 | look for `leaflet.js`, `mapboxgl`, `arcgis` in script srcs — see `site-patterns/geojson-bbox-map-portal.md` |
| Page has SPA shell signals (`__NEXT_DATA__`, `__INITIAL_STATE__`) | +3 | see `site-patterns/spa-frameworks.md` |
| Page is a generic landing / "Welcome to..." (low text, lots of nav) | -3 | text/HTML ratio < 5% |

Pages scoring ≥ 5 are likely candidates. Surface the top 5–10 to the user and let them confirm before scraping.

---

## Output to the user

After traversal:

```
Walked 137 pages from the entry URL. Found 4 candidate data pages:

1. https://example.com/catalog/products (score 12)
   - Has a table with 50 rows + pagination, columns visible
2. https://example.com/data/inventory-export.xlsx (score 10)
   - Direct XLSX download
3. https://example.com/online/search (score 8)
   - Search form with filters
4. https://example.com/api/v1/products (score 6)
   - JSON endpoint, returns paginated list

Which one matches what you described? If multiple, I can scrape all of them.
```

Let the user pick. Don't auto-start on all four.

---

## Gotchas

- **Calendar pages and infinite loops** — a `<a href="?date=2024-01-16">` link generator can produce a million URLs. Detect by URLs that differ only in a query param value pattern and either dedup or blacklist the path.
- **`robots.txt` should be respected.** Even though you're traversing for discovery (not bulk scraping), repeatedly hitting `Disallow:` paths from one IP risks an IP-level block that affects the actual data fetch later.
- **Login walls don't 404.** A page behind auth often returns HTTP 200 with a login form HTML — the page text won't contain your keywords. The scoring will deprioritize it naturally, but if all candidates score low, suspect a login wall and ask the user about auth.
- **JavaScript-rendered navigation** — for SPA sites, `<a href>` links may be empty (`href="#"`) with JS-attached click handlers. The link extractor sees nothing. Fall back to running the entry URL in a headless browser (`../browser-automation/browser-bootstrap-handoff.md`) and capturing the DOM after hydration.
- **Same-host check is fragile.** `example.gov` and `data.example.gov` are different hosts but the same organisation. Either widen the host check to "same eTLD+1" (use the `tldextract` library) or maintain an allow-list of known subdomains.
- **Anchor text != intent.** "Click here for the full list" might link to a static PDF instead of a database. Score on URL signals AND anchor text, weighted equally.
- **Crawl politeness.** 1 request per second per host is a safe default. Faster gets you rate-limited; slower wastes time. Add jitter (0.5–1.5s) to avoid looking like a bot.

---

## Related

- `google-deep-research.md` — when you don't have any URL at all, find candidate sites first
- `autonomous-discovery.md` — the 5-minute pre-traversal checklist (try this BEFORE link traversal)
- `har-driven-workflow.md` — once the data page is found, capture how the browser actually fetches it
- `../site-patterns/spa-frameworks.md` — when the candidate page is an SPA and traversal needs a browser
- `../browser-automation/browser-bootstrap-handoff.md` — when JS-rendered links require a real browser
