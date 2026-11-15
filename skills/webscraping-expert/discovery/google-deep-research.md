# Google deep-research workflow

When the user has **no starting URL** (or only a vague topic), use Google's advanced search operators as a structured discovery tool to surface candidate sources before scraping anything. This file is a workflow, not just a cheat-sheet — follow the recipe below in order.

## When to use this

- User answered Q1 with "(c) I don't have any URL — I just know what kind of data I want"
- User has a starting URL but you suspect the data also exists on other sites (e.g. open-data mirrors, regulator publications) worth surveying
- You're auditing how many sources publish a particular dataset

If the user already has the exact data URL, **skip this file** — go straight to `har-driven-workflow.md`.

## The four phases

```
Phase 1 — Keyword elicitation  (ask user for 2–10 seeds)
Phase 2 — Keyword expansion    (you generate 10+ more)
Phase 3 — Query matrix         (≥300 queries from ≥12 keywords × ≥25 templates)
Phase 4 — Execution & triage   (run, dedup, score, surface top candidates)
```

---

## Phase 1 — Keyword elicitation

Ask the user for **2–10 seed keywords** describing the data they want. Frame the request based on their experience level (see `../approach/` files for tone).

```
Tell me 2 to 10 keywords that describe the data you want.

Aim for a mix:
- The thing itself (e.g. "product catalog", "event schedule", "job listings")
- The publisher (e.g. "retailer", "marketplace", "event organizer")
- Geographic context (e.g. the city, region, or country relevant to your search)
- A field name you expect to see (e.g. "product code", "publication date", "category")
- A document type if relevant (e.g. "catalog", "CSV export", "JSON feed")

Even 2 keywords are enough to start — I'll expand the list.
```

If the user gives fewer than 2, push back gently and ask for at least one more. If they give more than 10, take the first 10 — diminishing returns past that.

---

## Phase 2 — Keyword expansion

Generate **at least 10 additional keywords** from the seeds. Aim for variety, not synonyms-only. Pull from these expansion axes:

| Axis | Example given user seed: "used car listings" |
|---|---|
| Synonyms / terminology variants | "pre-owned vehicles", "second-hand cars", "used autos", "dealer inventory" |
| Owner / publisher names | "dealer group", "marketplace", "classifieds site", "manufacturer certified" |
| Specific instances (top-N most likely sources) | name 5 specific marketplaces / large dealer chains in the target market |
| Field/column names visible in this kind of data | "make", "model", "year", "mileage", "VIN", "price" |
| Document types | "annual report", "data dictionary", "API documentation", "open data catalog" |
| Industry jargon / platform names | "VIN decode", "trim level", "odometer", "inventory feed" |
| Negative space (what to exclude) — useful later in queries | "-new", "-rental", "-finance" — narrow noise |
| Local language if non-English target | translate seeds into the local language(s) |

Aim for **12+ keywords total** after expansion. Save them as a list.

---

## Phase 3 — Query matrix

Produce **≥300 distinct Google queries** by applying a set of ~25 templates to each of the 12+ keywords. The math: 12 keywords × 25 templates = 300; more keywords → more queries automatically.

### Operator cheat-sheet (reference)

| Operator | Effect | Example |
|---|---|---|
| `"..."` | Exact phrase match | `"product code"` |
| `-term` | Exclude | `used cars -rental` |
| `OR` (uppercase) | Union | `"used car" OR "pre-owned"` |
| `( )` | Group | `(catalog OR inventory) site:example.com` |
| `site:` | Restrict to domain or TLD | `site:example.com` |
| `inurl:` | Term must appear in URL | `inurl:catalog` |
| `intitle:` | Term must appear in `<title>` | `intitle:"product catalog"` |
| `intext:` | Term must appear in body | `intext:"open data"` |
| `filetype:` | Restrict by file extension | `filetype:pdf`, `filetype:xlsx`, `filetype:csv`, `filetype:json` |
| `*` | Wildcard for one word | `"catalog * 2024"` |
| `..` | Numeric range | `used car 2018..2024` |
| `cache:` | Google's cached copy | `cache:example.com/page` |
| `related:` | Sites similar to given URL | `related:example.com` |
| `AROUND(N)` | Two terms within N words of each other | `mileage AROUND(5) price` |

`+` was retired by Google (~2011) — use `"..."` to force inclusion instead.

### The 25 standard query templates

For each of the 12+ keywords `K`, generate queries from these templates. Where two keywords appear in a template, iterate over pairs `(Ki, Kj)`.

| # | Template | What it surfaces |
|---|---|---|
| 1 | `K` | Baseline |
| 2 | `"K"` | Exact-phrase variant |
| 3 | `K site:.gov` (or country TLD: `.gov.au`, `.gov.br`, `.gov.uk`) | Government sources |
| 4 | `K site:.edu` | Academic / research |
| 5 | `K site:.org` | NGOs, civil-society |
| 6 | `K filetype:pdf` | PDF publications |
| 7 | `K filetype:xlsx OR filetype:xls` | Spreadsheet data |
| 8 | `K filetype:csv` | Tabular data dumps |
| 9 | `K filetype:json OR filetype:xml` | Machine-readable feeds |
| 10 | `K inurl:download OR inurl:data` | Data-download pages |
| 11 | `K intitle:"register" OR intitle:"directory"` | Registers and directories |
| 12 | `K intitle:"index of"` | Open file listings |
| 13 | `K "open data" OR "open access"` | Open-data portals |
| 14 | `K "API" OR "endpoint"` | Documented APIs |
| 15 | `K "data dictionary" OR "schema"` | Field definitions |
| 16 | `K "annual report" OR "statistics"` | Periodic publications |
| 17 | `K cache:K` (use after finding a stale link) | Recover dead pages |
| 18 | `Ki Kj` | Pair intersection (top pairs by relevance) |
| 19 | `Ki Kj site:.gov` | Pair intersection on government |
| 20 | `Ki Kj filetype:pdf` | Pair PDFs |
| 21 | `Ki Kj filetype:xlsx OR filetype:csv` | Pair tabular |
| 22 | `K 2020..2025` | Recent years numeric range |
| 23 | `K -K_noise` (with negative keyword from Phase 2) | Noise-filtered |
| 24 | `K archive.org OR web.archive.org` | Wayback / archived versions |
| 25 | `K "robots.txt"` or `K "sitemap.xml"` | Crawl-config leakage |

For the pair templates (`Ki Kj`), pick the top ~10 most informative pairs rather than the full C(12,2)=66 — focus on pairs that combine a "what" keyword with a "who" or "where" keyword.

**Concrete count check:** 12 single-keyword templates × 17 single-keyword templates (#1-17) = 204 single-keyword queries. Plus ~10 pairs × 4 pair-templates (#18-21) = 40 pair queries. Plus ~12 keywords × 4 remaining templates (#22-25) = 48. Total = **292** — just under 300, expand the pair count or add more keywords to clear the threshold.

---

## Phase 4 — Execution and triage

### Executing the queries

Three options for running 300+ Google searches programmatically:

1. **WebSearch tool (built-in to Claude Code)** — best when available. Rate-limited but free. Run queries in batches of ~10, dedup URLs across results, save to a structured store.
2. **Paid search API** — SerpAPI, Serper, ScraperAPI's Google endpoint, ValueSERP, Zenserp. ~$1-5 per 1000 searches. Necessary at production scale or when WebSearch quota is exhausted.
3. **Headless browser on duckduckgo.com or Bing** — when Google specifically rate-limits the IP. DDG's HTML interface (`html.duckduckgo.com/html`) is unauthenticated and forgiving. Bing's API is paid but documented.

**Never scrape google.com directly with `requests` or `httpx`** — Google fingerprints aggressively and you'll get 429s within ~10 queries. Use one of the three options above.

### Storing results

For each query, save:

```python
{
    "query": "used car inventory site:example.com filetype:csv",
    "template_id": 6,
    "keyword": "used car inventory",
    "result_rank": 1,
    "url": "https://example.com/inventory/export.csv",
    "title": "Used Vehicle Inventory — CSV Export",
    "snippet": "...",
    "ts": "2026-05-15T14:00:00Z",
}
```

JSONL is fine. Dedup by `url` across all queries — the same site usually surfaces under multiple keyword combinations.

### Triage and scoring

After execution, score each unique URL on these signals:

| Signal | Weight | How to detect |
|---|---|---|
| Domain authority for the topic | high | official publisher / well-known source for the topic; `.gov.<tld>` for public data; top result across multiple queries |
| Filetype matches expected data shape | high | `.csv` / `.xlsx` / `.json` if user wants tabular; `.pdf` if user wants documents |
| URL path semantically related | medium | contains `data`, `download`, `export`, `inventory`, `listings`, `catalog`, `api` |
| Snippet contains keywords from the user's data description | medium | substring match in `snippet` |
| Multiple queries surfaced this URL | medium | dedup count — same URL surfacing across many queries → strong candidate |
| Open-data portal hosts | high | path contains `/dataset/`, `/api/3/action/`, `/explore/`, host is data.gov.X |
| Negative signals | strong negative | filetype `.html` only, root page with no data path, news/blog domains, scraper-aggregator sites |

Rank URLs by score; present the **top 10–20 to the user** with one-line descriptions. Let them pick which to proceed with — don't auto-start scraping all of them.

---

## Output to the user

After Phase 4, summarize to the user like:

```
Ran 312 Google queries across 14 keywords. Surfaced 89 unique URLs.

Top candidates ranked by relevance:

1. https://data.example.com/dataset/vehicle-inventory — open-data / API portal, 17 datasets matching keywords
2. https://marketplace.example.com/search — search UI with table + pagination
3. https://example.com/downloads/inventory-2024.xlsx — direct XLSX file
[...]

Which of these should I start with? Or should I cast a wider net (run more queries)?
```

Always offer to widen the net — sometimes the right source is deep in the long tail.

---

## Gotchas

- **Google personalises results.** Two runs of the same query from different IPs / sessions may differ. If reproducibility matters, log raw HTML alongside parsed results, or use a paid API that returns deterministic output.
- **Rate limits hit fast on stock Google.** WebSearch tool batches help. Direct scraping = banned within tens of queries.
- **Country/region affects results enormously.** The same query from a US IP returns different sites than from an AU IP. Pin region via the API's `gl=` / `cr=` parameters when possible.
- **`site:` is not exact.** `site:example.com` includes all subdomains — `data.example.com`, `shop.example.com`, etc. Sometimes that's what you want, sometimes not; check the result domains.
- **Operators can stack but order matters cognitively, not technically.** `site:.gov filetype:csv "inventory"` and `"inventory" filetype:csv site:.gov` return the same results — Google doesn't care about order.
- **`AROUND(N)` and `..` are undocumented but still work** in most cases. Don't rely on them in production; they may quietly stop working.
- **Long-tail keywords beat short ones** for discovery. `"used car inventory export"` (4 words) usually finds the actual data page; `cars` (1 word) finds news articles and SaaS pitch pages. Bias the keyword expansion toward 2–4-word phrases.

---

## Related

- `link-graph-traversal.md` — once you pick a candidate site from the Google triage, traverse its link graph to find the actual data page
- `autonomous-discovery.md` — for a single known URL, the 5-minute checklist before involving the user
- `har-driven-workflow.md` — for capturing how the chosen site actually serves the data
