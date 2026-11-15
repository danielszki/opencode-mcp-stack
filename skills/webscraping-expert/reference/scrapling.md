# Scrapling — the all-in-one adaptive/stealth framework

Scrapling (D4Vinci, BSD-3, ~67k★, v0.4.x) is unusual: a **single library that spans the whole extraction ladder** — fast HTTP with TLS impersonation, a stealth browser that solves Cloudflare, full Playwright automation, a Scrapy-style spider, a CLI, and an MCP server — plus **adaptive selectors that survive site redesigns**. It's worth knowing well because it collapses a lot of the escalation this skill describes into one dependency with a consistent API.

**Install:**
```bash
pip install "scrapling[fetchers]"   # parser + fetchers
scrapling install                    # download the browsers (once)
pip install "scrapling[ai]"          # + MCP server
pip install "scrapling[shell]"       # + interactive CLI shell
pip install "scrapling[all]"         # everything
```

---

## The fetchers map onto the ladder

Scrapling exposes three fetcher tiers (each with a `Session` and an `Async*Session` variant). Pick by cost, exactly like SKILL.md's ladder:

| Scrapling | Ladder level | Use when |
|---|---|---|
| `Fetcher` / `FetcherSession` | L2–L3 (HTTP + TLS impersonation) | Plain/JSON APIs and static HTML; supports `impersonate=` and **`http3=True`** |
| `StealthyFetcher` / `StealthySession` | L5–L6 (stealth browser) | Cloudflare/behavioral walls — **`solve_cloudflare=True`** built in (Camoufox-based) |
| `DynamicFetcher` / `DynamicSession` | L6 (full Playwright) | JS-heavy SPAs needing clicks/render |

```python
from scrapling.fetchers import Fetcher, StealthyFetcher, DynamicFetcher

# L2–L3: fast HTTP with a real browser TLS fingerprint (+ HTTP/3)
page = Fetcher.get("https://api.example.com/items",
                   impersonate="chrome", stealthy_headers=True, http3=True)

# L5–L6: stealth browser that clears Cloudflare Turnstile/interstitial itself
page = StealthyFetcher.fetch("https://cf-protected.com",
                             headless=True, solve_cloudflare=True, network_idle=True)

# L6: full browser automation
page = DynamicFetcher.fetch("https://spa.example.com", network_idle=True, disable_resources=False)
```

Every fetch returns a parseable `Response` — same selector API regardless of tier, so escalating from HTTP to stealth doesn't change your parsing code.

---

## Adaptive selectors — the headline feature

The reason to reach for Scrapling over plain parsel: it can **relocate elements after the site's markup changes.** On the first run you save a structural fingerprint; on later runs it re-finds the element by similarity even if classes/positions moved.

```python
# First run — store the pattern
products = page.css(".product-card", auto_save=True)

# Later run, after the site redesigned its classes — relocate by stored fingerprint
products = page.css(".product-card", adaptive=True)   # still finds them

# Or expand from one known-good element to its siblings
first = page.css(".product-card")[0]
rest  = first.find_similar()                            # all structurally-similar elements
```

This is the durable answer to selector rot — pair it with the skill's bronze-first rule (persist raw HTML) and you get a scraper that both survives redesigns *and* can be replayed against old bronze.

---

## Parsing API (parsel-like, plus extras)

```python
page.css(".quote .text::text").getall()      # CSS + ::text / ::attr() pseudo-elements
page.xpath('//span[@class="text"]/text()').getall()
page.find_all("div", class_="quote")          # BeautifulSoup-style
page.find_by_text("Login", tag="button")      # text search
# Navigation: element.parent, .next_sibling, .below_elements(), .find_similar()
```

Performance: on par with Parsel/Scrapy and roughly **~800× faster than BeautifulSoup+lxml** on large trees — so there's no speed penalty for the extra features.

---

## Spider framework (when it's a crawl, not a fetch)

A Scrapy-style spider without Scrapy's ceremony, with two things Scrapy makes hard: **multi-session routing** (send hard URLs to a stealth session, easy ones to HTTP) and **pause/resume**.

```python
from scrapling.spiders import Spider, Request, Response
from scrapling.fetchers import FetcherSession, AsyncStealthySession

class MySpider(Spider):
    name = "mine"
    start_urls = ["https://example.com/"]
    concurrent_requests = 10
    robots_txt_obey = True

    def configure_sessions(self, manager):
        manager.add("fast", FetcherSession(impersonate="chrome"))
        manager.add("stealth", AsyncStealthySession(headless=True), lazy=True)

    async def parse(self, response: Response):
        for link in response.css("a::attr(href)").getall():
            sid = "stealth" if "protected" in link else "fast"
            yield Request(link, sid=sid, callback=self.parse)
        yield {"title": response.css("h1::text").get()}

result = MySpider(crawldir="./crawl_data").start()   # Ctrl+C to pause; rerun same crawldir to resume
result.items.to_jsonl("out.jsonl")
```

- `crawldir=` gives **graceful pause/resume** — aligns with `reliability/resumable-extraction.md`.
- `spider.stream()` yields items in real time.
- Built-in per-domain throttling, `robots_txt_obey`, and dev-mode disk caching.

---

## Networking niceties

- **`ProxyRotator(strategy="cyclic")`** or custom rotation; per-request proxy override on any session.
- **Ad/tracker blocking** (~3,500 known domains) and arbitrary domain blocking in browser fetchers — cuts bandwidth and noise.
- **DNS-over-HTTPS** option (routes DNS through Cloudflare DoH) to prevent DNS leaks when using proxies.

---

## CLI — zero-code extraction & curl conversion

```bash
scrapling shell        # IPython shell with Scrapling loaded; converts a pasted curl → Scrapling request
scrapling extract get           'https://example.com' out.md
scrapling extract fetch         'https://example.com' out.md --css-selector '#products' --impersonate chrome
scrapling extract stealthy-fetch 'https://cf-demo.com' out.html --css-selector 'a' --solve-cloudflare
```
Output by extension: `.txt` (text), `.md` (markdown), `.html` (raw). The `scrapling shell` curl→request conversion is a fast path for the DevTools "Copy as cURL" workflow in `discovery/`.

## MCP server — Scrapling as an AI tool

```bash
pip install "scrapling[ai]"
```
Exposes Scrapling to LLM clients (Claude, Cursor, …) as an MCP server that **pre-extracts targeted content before it reaches the model** — the page is reduced to the relevant slice first, cutting tokens and cost. This is the cleanest way to wire scraping into an agent without dumping whole pages into context. See `reference/ai-extraction.md` for the broader AI-extraction picture.

---

## When to use Scrapling vs. the à-la-carte stack

- **Reach for Scrapling** when: markup drifts (adaptive selectors), you want one lib across HTTP→stealth→crawl, you need Cloudflare solved without wiring a solver, or you're exposing scraping to an LLM agent (MCP).
- **Stay à la carte** (`curl_cffi` + `parsel`, or `patchright`/`camoufox` directly) when: the target is stable and structured (no need for adaptivity), you already have a working pipeline, or you want fine control over the exact stealth engine and fingerprint.

## Gotchas

- **`solve_cloudflare` is not magic** — it clears Turnstile/interstitial, not a hard WAF/IP block. If you're getting "Sorry, you've been blocked", that's IP-level (see `anti-bot/anti-bot-vendors.md`) — add a residential proxy, Scrapling won't fix it.
- **Browsers must be installed** (`scrapling install`) for the stealth/dynamic fetchers; the base `pip install scrapling` is parser-only.
- **Bronze-first still applies.** Adaptive selectors reduce breakage but don't replace persisting the raw response — save the HTML/JSON, then parse.
- **HTTP/3** (`http3=True`) is a genuine edge over most Python clients (see `anti-bot/tls-http-clients.md`) — useful when a site behaves differently over h3.
- Licensed for research/educational use — respect the target's ToS and local law, same as any scraper.

---

## Related

- `reference/ai-extraction.md` — Scrapling among crawl4ai / firecrawl / ScrapeGraphAI; when AI extraction fits
- `anti-bot/modern-stealth-browsers.md` — Camoufox (what `StealthyFetcher` builds on) vs patchright vs nodriver
- `anti-bot/anti-bot-vendors.md` — where `solve_cloudflare` helps and where it doesn't
- `anti-bot/tls-http-clients.md` — `Fetcher`'s impersonation + HTTP/3 in context of curl_cffi/primp/rnet
- `reliability/resumable-extraction.md` — the same pause/resume discipline `crawldir` gives you
