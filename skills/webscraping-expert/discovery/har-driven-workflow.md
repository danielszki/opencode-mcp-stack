# HAR-driven workflow

The fastest path from "user has a target site" to "working scraper" is almost always: ask for a `.har` file, then mechanically reverse-engineer it. This workflow consistently saves hours vs. probing blind.

## When to use this workflow

- Target requires login, multi-step navigation, or has hidden auth
- Plain `requests` returns 403 / Cloudflare / "Error" page
- Site is an SPA where API calls aren't visible in the URL
- Target uses any kind of stateful session (cookies, CSRF tokens, VIEWSTATE)
- You can't predict the API URL ahead of time

For simple GET-the-page sites, you don't need a HAR — just `requests` + BeautifulSoup.

## Step 1 — Ask the user to produce a HAR

Be specific about what to capture:

```
Please record a HAR file of the data you want to scrape:

1. Open the target in Chrome (or Firefox)
2. DevTools → Network tab → ☑ Preserve log → ☐ Disable cache
3. Refresh the page once with DevTools open
4. Perform the exact interaction you want to scrape (apply filters, click into a record, etc.)
5. Click the **download icon** (↓) in the Network toolbar → **"Export HAR (sanitized)..."**
   - If you need raw cookies / `Authorization` headers preserved, right-click in the request list → **"Save all as HAR with content"** instead
6. Send me the .har file
```

A good HAR captures everything: every request, every response body, all cookies, all headers, full TLS info. Strictly more useful than a single curl.

## Step 2 — Initial inventory

Open the HAR in Python and list the unique server-side requests (filter out assets):

```python
import json
from urllib.parse import urlparse

with open("site.har") as f:
    har = json.load(f)

seen = []
for entry in har["log"]["entries"]:
    url = entry["request"]["url"]
    host = urlparse(url).hostname or ""
    method = entry["request"]["method"]
    status = entry["response"]["status"]
    # Filter to target site, exclude assets
    if "target.example.com" not in host:
        continue
    if any(url.endswith(ext) for ext in (".css", ".js", ".png", ".jpg", ".gif", ".svg", ".woff", ".woff2", ".ico")):
        continue
    path = urlparse(url).path
    qs = urlparse(url).query.split("&")[0] if urlparse(url).query else ""
    key = (method, path, qs)
    if key not in seen:
        seen.append(key)
        print(f"  {method:5s} {status:3d}  {path}  ?{qs[:60]}")
```

You'll get a clean list of 3-15 endpoints. The data you want is usually behind one or two of them.

## Step 3 — Locate the data endpoint

For each candidate endpoint, check the response body:

```python
def find_data(har, contains: str):
    for entry in har["log"]["entries"]:
        body = entry["response"]["content"].get("text", "") or ""
        if contains in body:
            return entry
    return None

entry = find_data(har, "<some unique value visible on the page>")  # e.g. an app number, product SKU
print(entry["request"]["url"])
print(entry["request"]["method"])
```

Anchor to a unique value you can see on the page — this is faster than guessing endpoint names.

## Step 4 — Extract the POST payload (when relevant)

If the data endpoint is a POST, extract the form / JSON body:

```python
def extract_post(entry):
    post = entry["request"].get("postData", {})
    print("--- params ---")
    for p in post.get("params", []):
        n, v = p.get("name", ""), p.get("value", "")
        if len(v) > 80:
            v = v[:60] + f"... ({len(v)}b)"
        print(f"  {n} = {v}")
    print()
    print("--- raw ---")
    print(post.get("text", "")[:1000])

extract_post(entry)
```

For form-encoded payloads (`application/x-www-form-urlencoded`), the `params` list is your friend. Pay attention to:
- Hidden fields (`__VIEWSTATE`, CSRF tokens) — see `../site-patterns/aspnet-webforms.md`
- Auth-bearing fields (`aura.token`, `authToken`) — see `../site-patterns/salesforce-experience-cloud.md`
- Dynamic field names (control IDs that may differ per deployment)

For JSON payloads, just inspect the structure and find the parameters you control.

## Step 5 — Extract required headers

Many endpoints rejection-test specific headers. Capture them:

```python
def headers_of(entry):
    return {h["name"]: h["value"] for h in entry["request"]["headers"]}

h = headers_of(entry)
for k, v in h.items():
    if k.lower() not in ("user-agent", "accept", "accept-language", "accept-encoding"):
        # Show only the interesting ones (auth, csrf, custom)
        if len(v) > 100:
            v = v[:80] + "..."
        print(f"  {k}: {v}")
```

Headers that often matter and need to be replicated:
- `Referer` — many legacy sites enforce this
- `Origin` — common in CORS-protected APIs
- `X-CSRF-Token`, `X-Requested-With`, `X-Auth-Token`
- `Cookie` (parse separately, see step 6)
- Site-specific: `x-sfdc-lds-endpoints` (Salesforce), `X-Crawlera-Session` (Zyte proxy)

## Step 6 — Extract cookies and auth state

```python
# Initial cookies (set before the first request)
cookies = {c["name"]: c["value"] for c in har["log"]["entries"][0]["request"]["cookies"]}

# Or: cookies set during the session
for entry in har["log"]["entries"]:
    for c in entry["response"]["cookies"]:
        print(f"  {c['name']} = {c['value'][:40]}...  ({c.get('domain', '')})")
```

If the data endpoint depends on a specific cookie set during login, your scraper will need to either:
- Mimic the login flow with `requests`
- Or harvest cookies via Playwright once and reuse them (see `../browser-automation/session-cache.md`)

## Step 7 — Reconstruct in Python and smoke-test

Build the minimal request, then test:

```python
from curl_cffi import requests as cffi_requests

r = cffi_requests.post(
    "https://target.example.com/api/search",
    data={...},  # from step 4
    headers={...},  # from step 5
    cookies={...},  # from step 6, if needed
    impersonate="chrome",
    timeout=30,
)
r.raise_for_status()
data = r.json()
print(f"Got {len(data.get('records', []))} records")
```

If the smoke test returns the same data shape as the HAR's recorded response, you've successfully replicated the request. From here, the rest is pagination and parsing.

## Step 8 — Diff if it fails

If your reconstructed request doesn't return the expected data, diff against the HAR:

1. **Headers** — print yours vs. theirs side-by-side; one missing header is usually the culprit
2. **Body** — make sure URL encoding matches (quote characters, encoded vs literal)
3. **Cookies** — verify all cookies in the HAR's request are present in yours
4. **TLS profile** — if 403 / blocked: try other `impersonate` profiles (`chrome120`, `safari17_0`)
5. **Order of operations** — some endpoints require a prior page load to set server-side state; replay the previous N requests first

## Anti-patterns

- ❌ **Sharing a HAR over a chat channel without redacting auth tokens** — HARs often contain `Authorization: Bearer ...` headers. Treat them as secrets.
- ❌ **Hardcoding session-bound IDs from the HAR** — internal numeric IDs in the HAR (e.g. `?Id=12345`) frequently expire with the session. Re-search from the HAR's search step instead.
- ❌ **Skipping a "boring" earlier request** — sometimes a noop-looking GET to `/page/init` sets a critical session cookie. When in doubt, replay everything.

## Output checklist

When you finish reverse-engineering a HAR, you should have:

1. The minimal sequence of HTTP requests needed to reach the data
2. For each request: URL, method, headers, body, expected response shape
3. A list of fields that must be discovered dynamically per session (VIEWSTATE, CSRF, fwuid, etc.)
4. A list of fields that vary by deployment (control IDs, list IDs) but are stable within a deployment
5. The pagination mechanism (URL param? POST event? cursor?)

That output translates directly to a crawler module.

## Related

- `../discovery/devtools-workflow.md` — interactive variant when HAR isn't possible
- `har-parser.md` — reference for the HAR JSON schema
- `../site-patterns/aspnet-webforms.md` — common patterns to recognize while parsing
- `../site-patterns/salesforce-experience-cloud.md` — Aura-specific HAR signatures
