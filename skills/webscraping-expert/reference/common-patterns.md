# Common Scraping Patterns

Complete working examples. Copy and adapt.

## 1. Simple JSON API

```python
import requests

HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
r = requests.get("https://api.example.com/v1/items", headers=HEADERS, timeout=30)
r.raise_for_status()
for item in r.json()["data"]:
    print(item["name"])
```

## 2. Concurrent fetches (requests + ThreadPoolExecutor)

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

def fetch(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return url, r.json()

urls = [f"https://api.example.com/item/{i}" for i in range(1000)]

with ThreadPoolExecutor(max_workers=15) as ex:
    futures = [ex.submit(fetch, u) for u in urls]
    for f in as_completed(futures):
        url, data = f.result()
        # process
```

## 3. Async fetches (httpx)

```python
import asyncio, httpx

async def fetch(client, url):
    r = await client.get(url)
    return r.json()

async def main(urls):
    limits = httpx.Limits(max_connections=20)
    async with httpx.AsyncClient(http2=True, timeout=30, limits=limits) as c:
        return await asyncio.gather(*[fetch(c, u) for u in urls])

data = asyncio.run(main(urls))
```

## 4. Retry with backoff

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def resilient_session():
    s = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1.5,  # 1.5s, 3s, 4.5s, 6s, 7.5s
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST", "HEAD"],
    )
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.mount("http://", HTTPAdapter(max_retries=retry))
    s.headers.update({"User-Agent": "Mozilla/5.0 ..."})
    return s
```

## 5. HTML scraping with BeautifulSoup

```python
import requests
from bs4 import BeautifulSoup

r = requests.get("https://example.com/catalog", timeout=30)
soup = BeautifulSoup(r.text, "lxml")
for card in soup.select(".product-card"):
    yield {
        "name": card.select_one("h2").get_text(strip=True),
        "price": card.select_one(".price").get_text(strip=True),
        "url": card.select_one("a")["href"],
    }
```

## 6. Parse embedded JSON (Next.js, SPAs)

```python
import requests, json, re
from bs4 import BeautifulSoup

r = requests.get(URL, timeout=30)
# Next.js pattern
m = re.search(r'<script id="__NEXT_DATA__".*?>(.*?)</script>', r.text, re.DOTALL)
if m:
    data = json.loads(m.group(1))
    # Navigate the structure: data["props"]["pageProps"]["..."]
```

## 7. Playwright — wait for SPA content

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(user_agent="Mozilla/5.0 ...")
    page = ctx.new_page()
    page.goto("https://spa.example.com", wait_until="networkidle")
    page.wait_for_selector(".results-loaded")
    html = page.content()
    browser.close()
```

## 8. Playwright — intercept XHR responses

```python
from playwright.sync_api import sync_playwright

responses = []
def on_response(r):
    if "/api/data" in r.url and r.ok:
        responses.append(r.json())

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.on("response", on_response)
    page.goto("https://site.com")
    page.wait_for_load_state("networkidle")
    browser.close()
```

## 9. Convert curl to Python

```python
# Starting from:
# curl 'https://api.example.com/search' \
#   -H 'content-type: application/json' \
#   -H 'x-api-key: abc123' \
#   --data-raw '{"q":"datacenter","limit":50}'

import requests
r = requests.post(
    "https://api.example.com/search",
    headers={"content-type": "application/json", "x-api-key": "abc123"},
    json={"q": "datacenter", "limit": 50},
    timeout=30,
)
```

## 10. Parse JSON-stat 2.0 (Eurostat)

```python
import requests

def parse_jsonstat(data):
    """Flatten JSON-stat 2.0 into list of records."""
    dims = data["id"]
    sizes = data["size"]
    values = data.get("value", {})

    dim_cats = {}
    for d in dims:
        cats = data["dimension"][d]["category"]["index"]
        dim_cats[d] = [c for c, _ in sorted(cats.items(), key=lambda x: x[1])]

    for flat_str, val in values.items():
        idx = int(flat_str); indices = []; rem = idx
        for i in range(len(sizes) - 1, -1, -1):
            indices.insert(0, rem % sizes[i]); rem //= sizes[i]
        yield {dims[i]: dim_cats[dims[i]][indices[i]] for i in range(len(dims))} | {"value": val}
```

## 11. Rate-limited scraping

```python
import time, requests

class RateLimiter:
    def __init__(self, rps=2):
        self.min_interval = 1.0 / rps
        self.last = 0
    def wait(self):
        elapsed = time.monotonic() - self.last
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last = time.monotonic()

rl = RateLimiter(rps=2)
for url in urls:
    rl.wait()
    r = requests.get(url)
```

## 12. curl-cffi (TLS fingerprint bypass)

```python
from curl_cffi import requests

r = requests.get(
    "https://site-blocking-requests.com/api",
    impersonate="chrome",  # or safari16
    timeout=30,
)
```

## 13. Resumable download (large files)

```python
import requests, os

def download(url, path):
    headers = {}
    mode = "wb"
    if os.path.exists(path):
        existing = os.path.getsize(path)
        headers["Range"] = f"bytes={existing}-"
        mode = "ab"

    with requests.get(url, headers=headers, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(path, mode) as f:
            for chunk in r.iter_content(1024 * 1024):
                f.write(chunk)
```

## 14. PDF table extraction

```python
import pdfplumber

with pdfplumber.open("report.pdf") as pdf:
    for page in pdf.pages:
        for table in page.extract_tables():
            for row in table:
                print(row)

# Fallback for complex layouts: camelot-py (reads text positions)
# import camelot
# tables = camelot.read_pdf("report.pdf", pages="all", flavor="lattice")
```

## 15. XLSX streaming (large files)

```python
import openpyxl

wb = openpyxl.load_workbook("big.xlsx", data_only=True, read_only=True)
ws = wb["Sheet1"]
rows = ws.iter_rows(values_only=True)
header = next(rows)
for row in rows:
    rec = dict(zip(header, row))
    # process one row at a time — doesn't load whole file
```

For `.xlsb` (binary) or very wide sheets, `polars` with the calamine engine is dramatically faster and handles schema drift better than openpyxl:

```python
import polars as pl
df = pl.read_excel("big.xlsb", engine="calamine", sheet_id=0)   # Rust-backed, fast
```

## 16. Fallback / mirror source (when the primary is walled)

When the primary source sits behind a hard WAF/IP block you can't economically beat, a **sibling source often carries the same data on a softer domain.** Data syndicated across a network (review platforms, gov data mirrored to an aggregator, a vendor's `.com` vs its API) frequently shares IDs.

```python
SOURCES = [
    {"name": "primary",  "base": "https://primary.com",       "id_prefix": ""},
    {"name": "mirror",   "base": "https://sibling-network.com", "id_prefix": "Primary___"},  # same data, open domain
]

def fetch_with_fallback(path: str):
    for src in SOURCES:
        try:
            r = fetch(src["base"] + path)      # your curl_cffi/proxy fetch
            if r.status_code == 200 and looks_valid(r):
                return src, r
        except Blocked:
            continue
    raise RuntimeError("All sources blocked")
```

Key points: **map IDs across sources** (a mirror may prefix or reshape the primary's IDs — e.g. `Primary___12345`), and **validate the mirror matches** the primary (total counts, overlapping records, date ranges) before trusting it. Typical example: a review aggregator sits behind a hard WAF block, while a sister site on the same corporate network exposes the *same* reviews openly — often with the primary's ID embedded as a prefix (`Primary___12345`).

## 17. Fixture-fallback (source blocks automation entirely)

Some sources block *all* automated HTTP (browser-cookie-gated portals, aggressive WAF, or ToS-driven) yet publish a file a human can download. The robust pattern: **try programmatic fetch, fall back to a pre-downloaded fixture, and allow an env override** — so the pipeline is reproducible and CI-testable without hitting the site.

```python
import os
from pathlib import Path

def load_source(url: str, fixture: Path) -> bytes:
    # 1. explicit override (tests / manual refresh)
    if override := os.getenv("SOURCE_FIXTURE_PATH"):
        return Path(override).read_bytes()
    # 2. try the live fetch
    try:
        r = fetch(url)                       # curl_cffi / httpx
        if r.status_code == 200:
            return r.content
    except Exception:
        pass
    # 3. fall back to the committed fixture, and SURFACE that we did
    if fixture.exists():
        log.warning("live fetch failed — using fixture %s (data may be stale)", fixture)
        return fixture.read_bytes()
    raise RuntimeError(f"No live data and no fixture for {url}")
```

Always **log loudly** when serving a fixture (staleness is a silent-failure risk), and record the fixture's vintage in bronze metadata. This is how several US-indicator crawlers handle sources that "block automated HTTP access" (Tax Foundation, FCC BDC) — they ship a dated snapshot and re-fetch when the block lifts.
