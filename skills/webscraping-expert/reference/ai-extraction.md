# AI / LLM-driven extraction & adaptive scraping

The biggest shift since 2024: a wave of tools that either (a) turn pages into **LLM-ready markdown** for downstream models, (b) use an **LLM inside the extraction step** to pull typed data from messy HTML, or (c) **self-heal** when a site's markup changes. These don't replace the extraction ladder — you still want the cheapest path to structured data — but they change what "last resort" looks like, and they're excellent when markup is chaotic, one-off, or constantly drifting.

**When to reach for AI extraction:**
- Markup is inconsistent across pages or **drifts frequently** (selectors keep breaking).
- You need data from *many differently-structured* sites and can't hand-write a parser per site.
- One-off / low-volume where engineering a precise parser costs more than an LLM pass.
- You're feeding a **RAG / LLM pipeline** and want clean markdown, not raw HTML.

**When NOT to:** high-volume, stable, structured sources (a documented API or a clean JSON endpoint). An LLM pass there just adds cost, latency, and a hallucination surface. Bronze-first still applies — **persist the raw HTML/markdown before the LLM touches it**, so extraction is re-runnable and auditable.

---

## The tools (2026)

### crawl4ai — open-source, LLM-ready crawler
- **What:** self-hosted Python library. Renders (Playwright under the hood), emits clean **markdown** tuned for LLMs, supports CSS/XPath *and* LLM-based extraction strategies, chunking, and schema output. One of the fastest-growing scraping repos (~66k★).
- **Use when:** you want full control + no per-request vendor cost, and you're OK running/scaling browsers yourself.
```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://example.com/article")
        print(result.markdown)        # LLM-ready markdown
        # result.extracted_content when an extraction_strategy is set
asyncio.run(main())
```

### firecrawl — managed API, zero infra
- **What:** hosted API (also self-hostable). Endpoints: **`/scrape`** (one page → markdown/JSON), **`/crawl`** (whole site), **`/extract`** (schema-driven, LLM-backed). Handles proxies, JS, and anti-bot for you.
- **Use when:** you want reliability without running browsers/proxies; low-to-mid volume where managed credits beat owning infra. Past high volume, self-hosted crawl4ai is usually cheaper.
```python
from firecrawl import FirecrawlApp
app = FirecrawlApp(api_key="...")
doc = app.scrape_url("https://example.com", params={"formats": ["markdown", "json"]})
```

### scrapling — adaptive, stealth-first, all-in-one (Python)
- **What (v0.4.x, ~67k★):** a single framework spanning one request → full crawl. Three fetcher tiers (`Fetcher` = HTTP+TLS impersonation, `StealthyFetcher` = Camoufox stealth with `solve_cloudflare=True`, `DynamicFetcher` = full Playwright), **adaptive selectors** that relocate elements after a redesign (`auto_save=True` → `adaptive=True`), a Scrapy-style spider with pause/resume + multi-session routing, a CLI, and a built-in **MCP server** that pre-extracts content before the LLM (fewer tokens).
- **Use when:** you want stealth + adaptivity + parsing in one dependency, and selectors keep breaking — reach for it via `scrapling.fetchers.Fetcher`.
- **Full playbook: `reference/scrapling.md`** — fetcher-to-ladder mapping, adaptive API, spider, CLI, MCP, gotchas.
```python
from scrapling.fetchers import Fetcher, StealthyFetcher
page = Fetcher.get("https://example.com", stealthy_headers=True)
rows = page.css(".product")                     # parsel-like, but adaptive-capable
hard = StealthyFetcher.fetch("https://cf-protected.com")   # Camoufox stealth path
```

### ScrapeGraphAI — LLM *during* extraction
- **What:** you give a natural-language prompt + a URL (or HTML); it uses an LLM (via a graph pipeline) to return **typed, schema-validated JSON** directly. No selectors.
- **Use when:** structure varies wildly and you'd rather describe the target ("get the product name, price, and rating") than write a parser.

### browser-use / stagehand / skyvern — LLM agent drives the browser
- **What:** an LLM plans and executes browser actions (click, type, navigate) to reach and read data. `browser-use` (Python) is the popular open one; `stagehand` (Browserbase) and `skyvern` are siblings.
- **Use when:** the path to data needs *reasoning over the UI* (multi-step flows, unpredictable layouts). Slowest and most expensive — genuine last resort, above headful automation.

---

## Choosing between them

| Need | Reach for |
|---|---|
| Clean markdown for a RAG/LLM pipeline, self-hosted | **crawl4ai** |
| Same, but zero infra / managed anti-bot | **firecrawl** |
| Stealth + adaptive parsing + crawl in one lib | **scrapling** |
| Describe the data in English, get typed JSON | **ScrapeGraphAI** (or firecrawl `/extract`) |
| Multi-step UI navigation that needs reasoning | **browser-use / stagehand / skyvern** |
| High-volume, stable, structured source | **none of the above** — use the API / hidden endpoint (SKILL.md ladder) |

---

## The generic LLM-extraction pattern (roll-your-own)

You don't always need a framework. The durable pattern: **fetch cheaply → reduce to markdown → LLM with a strict schema → validate.**

```python
import curl_cffi.requests as cffi
from markdownify import markdownify           # or trafilatura for main-content extraction

html = cffi.get(url, impersonate="chrome").text
persist_bronze(url, html)                     # BRONZE FIRST — raw HTML to disk/S3

md = markdownify(html)                         # shrink tokens; keep structure
# Send `md` to the LLM with a JSON schema (structured output). Validate the result
# against the schema; on mismatch, retry. Store the LLM output as SILVER, never as bronze.
```

- **Cut tokens before the model:** `trafilatura`/`markdownify`/`selectolax` to strip nav/boilerplate. scrapling's MCP does this for you.
- **Force structured output** (JSON schema / tool-call), then **validate** — never trust free-form LLM text as data.
- **Cost & hallucination are real.** Log token spend; spot-check LLM extractions against the raw bronze.

---

## Gotchas

- **Bronze-first is non-negotiable here.** The LLM/markdown output is *silver*. Persist the raw response first so a prompt change or model swap doesn't force a re-crawl.
- **LLMs hallucinate fields.** Schema-validate; sample-audit against source; prefer deterministic parsing when the structure is stable.
- **Anti-bot still applies.** crawl4ai/scrapling render real browsers (so they inherit the stealth story in `anti-bot/modern-stealth-browsers.md`); firecrawl handles it server-side; ScrapeGraphAI needs *you* to fetch past the wall unless you feed it HTML.
- **Managed vs self-host cost crossover:** managed (firecrawl) wins at low/mid volume; self-host (crawl4ai/scrapling) wins at scale but you own proxies + uptime.

---

## Related

- `reference/libraries.md` — where these sit among HTTP/parse/browser libs
- `anti-bot/modern-stealth-browsers.md` — the browser engines crawl4ai/scrapling drive
- `reference/medallion-architecture.md` — raw HTML = bronze, LLM output = silver
- `parsing/document-extraction.md` — non-HTML sources (PDF/XLSX) into LLM pipelines
