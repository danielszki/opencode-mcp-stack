# Python Libraries for Web Scraping

Comprehensive reference for choosing the right tool. Ordered by layer in the stack.

## HTTP clients

### requests
- **Best for:** simple GET/POST, JSON APIs, small scripts
- **Pros:** dead simple, ubiquitous, great docs, Session for cookie persistence
- **Cons:** sync only, no HTTP/2, blocked by advanced bot detection (TLS fingerprint)
- **Typical pattern:**
  ```python
  import requests
  s = requests.Session()
  s.headers.update({"User-Agent": "Mozilla/5.0 ..."})
  r = s.get("https://api.example.com/data", params={"k": "v"}, timeout=30)
  r.raise_for_status()
  data = r.json()
  ```

### httpx
- **Best for:** async code, HTTP/2, modern features
- **Pros:** sync + async APIs, HTTP/2, same interface as requests, connection pooling
- **Cons:** slightly slower warm-up than requests
- **When to prefer:** concurrent fetches, async pipelines, need HTTP/2
  ```python
  import httpx, asyncio
  async def fetch_all(urls):
      async with httpx.AsyncClient(http2=True, timeout=30) as c:
          return await asyncio.gather(*[c.get(u) for u in urls])
  ```

### aiohttp
- **Best for:** high-concurrency crawling, websockets
- **Pros:** mature async, used by Scrapy core
- **Cons:** async-only, steeper learning curve than httpx

### curl-cffi
- **Best for:** bypassing TLS fingerprint blocks (Akamai, Cloudflare JA3/JA4) — **the default impersonation client**
- **Pros:** drop-in replacement for requests, mimics real browser TLS/HTTP2, broadest profile list, sync + async
- **Cons:** larger binary
  ```python
  from curl_cffi import requests
  r = requests.get("https://blocked.example.com", impersonate="chrome")  # generic alias = newest profile
  ```
  Use generic aliases (`chrome`/`safari`/`firefox`), not a hardcoded old version. Full detail: `anti-bot/tls-http-clients.md`.

### primp (Rust-backed, fastest)
- **Best for:** high-throughput impersonation; `requests`-like API. Formerly `pyreqwest-impersonate`.
  ```python
  import primp
  r = primp.Client(impersonate="chrome_131", impersonate_os="macos").get(url)
  ```

### rnet (Rust-backed, async-native)
- **Best for:** high-concurrency async crawlers needing TLS impersonation + HTTP/2 emulation. Wraps `wreq`/reqwest-impersonate.

### tls-client (Go, low-level)
- **Best for:** hand-tuning the fingerprint (custom cipher/extension order) below what curl_cffi exposes.

### pyppeteer (deprecated — use playwright)
### urllib3 (low-level, use requests/httpx on top)

## HTML parsing

### BeautifulSoup4
- **Best for:** general-purpose HTML/XML parsing, forgiving of malformed HTML
- **Backend:** use `lxml` for speed (`BeautifulSoup(html, "lxml")`)
- **Typical:**
  ```python
  from bs4 import BeautifulSoup
  soup = BeautifulSoup(html, "lxml")
  for a in soup.select(".product > a"):
      print(a["href"], a.text.strip())
  ```

### lxml
- **Best for:** fastest parser, XPath/XSLT support
- **When to prefer:** performance-critical, structured XML, need XPath
  ```python
  from lxml import etree, html
  tree = html.fromstring(html_text)
  prices = tree.xpath("//span[@class='price']/text()")
  ```

### parsel
- **Best for:** mixing XPath + CSS selectors, used by Scrapy
- **Interface:** `selector.css(...)`, `selector.xpath(...)`, chainable

### selectolax
- **Best for:** 5-10x faster than BeautifulSoup+lxml on huge HTML
- **When to prefer:** crawling millions of pages, performance matters

## Browser automation

### Playwright (Python)
- **Best for:** SPAs, interaction, network interception, modern default
- **Pros:** async + sync, auto-wait, headless+headful, network mocking, multi-browser
- **Install:** `pip install playwright && playwright install chromium`
  ```python
  from playwright.sync_api import sync_playwright
  with sync_playwright() as p:
      browser = p.chromium.launch(headless=True)
      page = browser.new_page()
      page.goto("https://example.com")
      page.wait_for_selector(".data")
      html = page.content()
      # Intercept requests:
      # page.on("response", lambda r: ...)
      browser.close()
  ```
- **Stealth:** vanilla Playwright is detectable (leaks the CDP `Runtime.enable` signal). For protected sites use the modern stealth stack below, not `playwright-stealth` (largely superseded).

### Modern stealth browsers (the 2026 stack)
- **`patchright`** — Playwright fork that patches CDP leaks; `channel="chrome"` for real TLS. **The practical upgrade for Cloudflare** and the smallest diff from existing Playwright code.
- **`camoufox`** — Firefox fork with C-level fingerprint spoofing + real Firefox TLS. **Best against DataDome / behavioral scorers.**
- **`nodriver`** — `undetected-chromedriver` successor; drives Chrome over CDP directly (no webdriver flag). Lightest, but no behavioral sim — only for basic/no-WAF targets.
- Full guidance + when-to-use: `anti-bot/modern-stealth-browsers.md`.

### Selenium
- **Best for:** legacy codebases, when Playwright doesn't support something
- **Cons:** slower, more boilerplate; `undetected-chromedriver` is now maintained as **`nodriver`**.

### pyppeteer (DEPRECATED)
Use Playwright instead — same DevTools Protocol but maintained.

## Crawling frameworks

### Scrapy
- **Best for:** large-scale structured crawling (10k+ pages), multi-site
- **Pros:** built-in middleware (retries, throttling, robots.txt), pipelines, spiders
- **Cons:** complex for one-off scrapes, overkill for <1000 pages
- **Key concepts:** `Spider`, `Item`, `Pipeline`, `Middleware`
  ```python
  import scrapy
  class MySpider(scrapy.Spider):
      name = "products"
      start_urls = ["https://example.com/catalog"]
      def parse(self, response):
          for p in response.css(".product"):
              yield {"name": p.css("h2::text").get(), "price": p.css(".price::text").get()}
          next_page = response.css("a.next::attr(href)").get()
          if next_page:
              yield response.follow(next_page, self.parse)
  ```

### crawlee-python
- **Best for:** modern alternative to Scrapy with Playwright integration built-in
- **Pros:** async-first, mixes HTTP and browser seamlessly

### scrapling (adaptive, stealth-first) — ~67k★
- **Best for:** one lib spanning HTTP → stealth browser → crawl → parse, with **adaptive selectors** that survive redesigns, `solve_cloudflare=True`, HTTP/3, a spider with pause/resume, a CLI, and an MCP server. Three fetchers (`Fetcher`=HTTP+impersonation, `StealthyFetcher`=Camoufox, `DynamicFetcher`=Playwright). **Full playbook: `reference/scrapling.md`.**

### crawl4ai / firecrawl (LLM-ready)
- **crawl4ai** — open-source, self-hosted, page → LLM-ready markdown + LLM extraction strategies (~66k★).
- **firecrawl** — managed API (`/scrape` `/crawl` `/extract`); handles proxies/JS/anti-bot. See `reference/ai-extraction.md`.

## Anti-bot tooling

| Tool | What it does | When |
|------|--------------|------|
| `curl-cffi` / `primp` / `rnet` | Impersonate real browser TLS/HTTP2 fingerprints | requests blocked at network layer — **try first** |
| `patchright` | Playwright fork; patches CDP leaks, real-Chrome TLS | Cloudflare JS challenge; upgrade from Playwright |
| `camoufox` | Firefox fork; C-level fingerprint spoof + real FF TLS | DataDome / behavioral scorers (hardest targets) |
| `nodriver` | CDP-direct Chrome, no webdriver flag (uc successor) | Basic/no-WAF targets, lightest footprint |
| `CapSolver` / `2Captcha` | Solve reCAPTCHA / hCaptcha / **Turnstile** / **DataDome** / AWS-WAF | A CAPTCHA/token blocks you |
| Zyte API / Bright Data Web Unlocker / ZenRows | Full managed unblocking (proxy+browser+CAPTCHA) | Hard targets, production budget, no infra to run |
| `cloudscraper` / `FlareSolverr` | Old Cloudflare JS-challenge solvers | **Lagging in 2026 — don't lead with these** |

## Specialized format libs

| Format | Lib | Notes |
|--------|-----|-------|
| JSON-stat 2.0 | `pyjstat` | Eurostat, Statistics Canada, etc. |
| SDMX | `sdmx1` | OECD, ECB, IMF |
| PDF tables | `tabula-py`, `pdfplumber`, `camelot` | Best: try pdfplumber first, camelot for complex tables, tabula as fallback |
| Scanned PDFs (OCR) | `pytesseract`, `ocrmypdf` | Install tesseract system-wide first |
| XLSX | `openpyxl` (read_only for speed), `pandas.read_excel` | `read_only=True` streams — essential for 100MB+ files |
| CSV | stdlib `csv`, `pandas.read_csv` | Encoding: often `utf-8-sig` due to BOM |
| GraphQL | `gql` or plain `requests.post` | `gql` adds schema introspection |
| gRPC/Protobuf | `grpcio`, `protobuf` | Rare in public scraping |

## Data storage

- **JSON lines (.jsonl):** append-friendly, easy for pipelines
- **Parquet:** compressed, typed, for analytical datasets (`pyarrow`)
- **SQLite:** built-in, great for dedup and querying during scrape
- **DuckDB:** fast analytical queries over Parquet/CSV without loading

## Proxies

- **Residential (Bright Data, Oxylabs, IPRoyal):** real ISP IPs, hard to detect, $$$
- **Datacenter (Webshare, ProxyMesh):** cheap, fast, often detected
- **Rotating (per request):** set `proxies={"http": "http://user:pass@proxy:port"}`
- **Session sticky:** use same IP for whole session (important for cookie-based flows)

## Testing & debugging

- **`requests-mock`:** mock HTTP in tests
- **`responses`:** another HTTP mocking lib
- **`vcrpy`:** record real requests, replay in tests
- **Playwright trace viewer:** `context.tracing.start()` → visual debug of what happened

## Keep it simple

For 90% of scraping jobs: **requests + BeautifulSoup** is enough. Only escalate when you hit a real block.
