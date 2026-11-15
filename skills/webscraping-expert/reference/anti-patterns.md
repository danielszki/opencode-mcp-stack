# Anti-patterns — what NOT to do

A grab-bag of mistakes that recur in scraping work, paired with what to do instead. Skim this before declaring a scraper done.

Each entry follows the same shape: **Bad** → **Good** → one-line **Why**.

---

## Skipping the intake

```
User: "scrape that store's product listings"
You:  *immediately starts writing code*
```

```
User: "scrape that store's product listings"
You:  *runs the experience-level intake first, then the matching approach flow*
```

**Why:** 90% of "wrong-path" scraping work comes from missing a constraint that intake would have surfaced — volume, auth, output format, recurring vs one-shot. Two minutes of questions saves hours of rework. See `../approach/`.

---

## Opening a browser when HTTP works

```python
# BAD: launching Playwright when the page is server-rendered HTML
async with async_playwright() as p:
    browser = await p.chromium.launch()
    page = await browser.new_page()
    await page.goto(url)
    html = await page.content()
```

```python
# GOOD: try HTTP first; only escalate if it actually fails
from curl_cffi import requests as cffi_requests
r = cffi_requests.get(url, impersonate="chrome", timeout=30)
if r.status_code == 200 and "<table" in r.text:
    return r.text
# only now consider the browser
```

**Why:** browsers are ~100x slower, ~10x more RAM, easier to detect, and harder to parallelize. Always test the cheaper path first. See the extraction ladder in `SKILL.md`.

---

## Using plain `requests` on TLS-protected sites

```python
# BAD: requests.get() — Python's TLS fingerprint is on every WAF blocklist
import requests
r = requests.get("https://protected-site.example", timeout=30)
# → 403 / Cloudflare challenge HTML
```

```python
# GOOD: curl_cffi with Chrome impersonation matches a real browser's JA3/JA4
from curl_cffi import requests as cffi_requests
r = cffi_requests.get("https://protected-site.example", impersonate="chrome", timeout=30)
```

**Why:** modern anti-bot stacks (Cloudflare, Akamai, PerimeterX, Datadome) fingerprint the TLS handshake. Plain `requests` is identifiable as Python before any HTTP request is sent. See `../anti-bot/browser-impersonation.md`.

---

## Fetching detail pages without the right `Referer`

```python
# BAD: cold-fetching detail by ID, no Referer
session.get(f"{DETAIL_BASE}?Id=12345")
# → 200 OK + <title>Error</title> + empty page
```

```python
# GOOD: echo the results page as Referer; same session
session.get(f"{DETAIL_BASE}?Id=12345", headers={"Referer": RESULTS_URL})
```

**Why:** many enterprise apps (ASP.NET WebForms, Java/Struts, some PHP CMSes) refuse a detail request whose `Referer` doesn't match the listing page. Symptom is HTTP 200 with an error template — easy to miss. See `../site-patterns/aspnet-webforms.md`.

---

## Trusting `length: -1` on DataTables (or any "give me everything" param)

```python
# BAD: hoping for the full dataset in one POST
session.post(endpoint, data={"draw": 1, "start": 0, "length": -1})
# → server quietly caps at its configured max (often 100), returns 100 rows
```

```python
# GOOD: paginate against recordsFiltered
total = first_page["recordsFiltered"]
for start in range(0, total, page_size):
    ...
```

**Why:** undocumented server caps are everywhere. Asking for "all" silently returns "as many as we feel like". Always paginate. See `../site-patterns/datatables-server-side.md`.

---

## Pinning hardcoded persisted-query IDs

```python
# BAD: hardcoded doc_id from a HAR captured last month
DOC_ID = "27242482582022127"
session.post(GRAPHQL_URL, data={"doc_id": DOC_ID, "variables": "..."})
# → site deployed a new build last week; doc_id now returns PersistedQueryNotFound
```

```python
# GOOD: extract the current doc_id from the live frontend bundle at start of run
def get_doc_id_for(op_name: str) -> str:
    bundle = httpx.get(MAIN_JS_URL).text
    m = re.search(rf'"{op_name}"\s*,\s*doc_id:\s*"(\d+)"', bundle)
    return m.group(1)
```

**Why:** strict-persisted-query servers tie query IDs to a specific frontend build. Deploys invalidate them. Pinning = guaranteed silent breakage. See `../site-patterns/graphql.md`.

---

## Scraping `google.com` directly with `requests` or `httpx`

```python
# BAD: 10 queries in, you're banned
for q in queries:
    httpx.get(f"https://www.google.com/search?q={q}")
```

```python
# GOOD: use the WebSearch tool, a paid SERP API (SerpAPI, Serper), or DDG HTML
# For high-volume research see ../discovery/google-deep-research.md
```

**Why:** Google fingerprints aggressively. Direct scraping gets banned within tens of queries from the same IP and triggers CAPTCHA challenges that don't auto-resolve. Always use an intermediary.

---

## Silently transforming bronze into "cleaned" output

```python
# BAD: user asked for CSV; you delivered typed columns, parsed dates, dropped "empty" rows
df["listed_date"] = pd.to_datetime(df["Date Listed"])
df = df.dropna(subset=["listed_date"])
df.to_csv("listings.csv")
```

```python
# GOOD: bronze CSV — every column the source returned, dates as strings, no row drops
write_bronze(records, "listings.csv")
# Then, only if the user asks: silver = typed, deduped, validated
```

**Why:** silent transforms = silent data loss. Bronze is the contract; silver is opt-in (and gated by the user's experience level). See `medallion-architecture.md`.

---

## Trusting `HTTP 200` to mean "it worked"

```python
# BAD: status check only
r = session.get(detail_url)
if r.status_code == 200:
    yield parse(r.text)  # might be parsing an error page
```

```python
# GOOD: also check for app-level success markers
r = session.get(detail_url)
if r.status_code == 200 and not _is_error_page(r.text):
    yield parse(r.text)

def _is_error_page(html: str) -> bool:
    soup = BeautifulSoup(html, "html.parser")
    title = (soup.title.string or "").strip().lower() if soup.title else ""
    return title in ("error", "page not found") or "aspxerrorpath" in html.lower()
```

**Why:** many enterprise apps return 200 + a generic error page when sessions expire, CSRF tokens fail, or the requested resource is gone. Looks fine to a status-code check; obviously empty when you actually look. See `../anti-bot/error-decoders.md`.

---

## Hardcoding control IDs from one deployment

```python
# BAD: works on this deployment, breaks on every other site using the same template
data = {"ctl00$Main$DateFrom": "01/01/2024"}  # illustrative control name
```

```python
# GOOD: discover the control name from the live DOM
label = soup.find("label", string="Created from")  # inspect the target's label
from_field = soup.find("input", id=label["for"])["name"]
data = {from_field: "01/01/2024"}
```

**Why:** same template, different `ctlNN` numbering per deployment. See `../site-patterns/aspnet-webforms.md` and `../site-patterns/templated-cms-schema-drift.md`.

---

## Capturing one record without checking the others

```python
# BAD: parsed one detail page correctly, declared the parser done
detail = parse_detail(html_of_first_record)
assert detail["created_at"]  # passes
# ... 10 000 records later, half are missing created_at because the field
# uses a different label on some categories
```

```python
# GOOD: sample 5–10 records spanning categories / dates / statuses, validate each
sample = random.sample(records, k=10)
for rec in sample:
    detail = parse_detail(fetch(rec["id"]))
    assert all_required_fields(detail), f"missing field in {rec['id']}"
```

**Why:** the same source frequently emits slightly different shapes across categories. One-record validation hides the schema-drift problem. See `../site-patterns/templated-cms-schema-drift.md`.

---

## Persisting internal IDs across runs

```python
# BAD: scraping IDs once, replaying them next week
ids = json.load(open("ids-from-last-week.json"))
for id_ in ids:
    fetch_detail(id_)  # → 200 + "Error" page because IDs are session-scoped
```

```python
# GOOD: re-discover IDs every run
ids = list(list_search_results())  # fresh session, fresh IDs
for id_ in ids:
    fetch_detail(id_)
```

**Why:** many apps generate per-session internal IDs (`?Id=12345`) that don't survive across sessions. Cold-fetching a cached ID returns an error page. See `../site-patterns/aspnet-webforms.md`.

---

## Logging the full HAR / response body to disk

```python
# BAD: every request and its response written to a debug log
log.info(f"response: {r.text}")
log.info(f"har_entry: {json.dumps(har_entry)}")
```

```python
# GOOD: log the URL, status, content_hash, response size. Persist the full body to bronze, not logs.
log.info(f"GET {url} → {r.status_code} ({len(r.content)} bytes, sha256={sha[:12]})")
```

**Why:** debug logs filled with response payloads explode disk usage, leak cookies/tokens, and become unreadable. Bronze tables already store the full payload — don't duplicate.

---

## Running unbounded parallel requests against one host

```python
# BAD: 200 simultaneous workers hammering one server
with ThreadPoolExecutor(max_workers=200) as pool:
    pool.map(fetch, urls)
# → 429s, IP ban, or worse — the site falls over and you DOS'd them
```

```python
# GOOD: bound by host, throttle, jitter
sem_per_host = {"example.com": asyncio.Semaphore(5)}
async with sem_per_host[host]:
    await asyncio.sleep(random.uniform(0.5, 1.5))
    await fetch(url)
```

**Why:** the goal is to extract data, not to crash a server or get IP-banned. 2–5 concurrent per host is the safe default; profile up from there only if the server clearly handles it.

---

## Treating errors as the end state

```python
# BAD: first 5xx kills the run; partial bronze discarded
for url in urls:
    r = session.get(url)
    r.raise_for_status()  # crash on first failure
    save(r)
```

```python
# GOOD: bronze is append-only and resumable; log failures, keep going
for url in urls:
    try:
        r = session.get(url)
        r.raise_for_status()
        save_bronze(r)
    except Exception as e:
        record_failure(url, e)
        continue
# Later: replay failures with backoff
```

**Why:** a 12-hour bronze run that dies on hour 11 should resume from where it stopped, not start over. Plan for failures from line 1. See `../reliability/`.

---

## Related

- `../site-patterns/` — each pattern's gotchas section lists more pattern-specific anti-patterns
- `medallion-architecture.md` — bronze-first contract; "silent silver" is the canonical anti-pattern this skill is designed against
- `../anti-bot/error-decoders.md` — recognizing 4xx/5xx that mean things other than what they appear to mean
