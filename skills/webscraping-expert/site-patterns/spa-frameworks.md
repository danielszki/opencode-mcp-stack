# SPA frameworks — React / Next / Vue / Svelte

Modern web apps render almost entirely client-side. The initial HTML response is a near-empty shell; everything you see in the browser arrives later via JS execution and JSON API calls. Scraping an SPA naively (GET the URL, parse HTML) returns nothing — the data isn't in the document yet.

The good news: SPAs are usually **easier** to scrape than server-rendered sites once you find the right entry point. There's almost always a JSON payload either embedded in the initial HTML (hydration data) or fetched from a clean internal API. The job is finding it.

## When you see this

- View-source shows a near-empty `<body>` with a single mount point: `<div id="root">` (React/CRA), `<div id="__next">` (Next.js), `<div id="app">` (Vue/Nuxt), `<div id="svelte">` (Svelte), or similar
- The HTML response contains a large `<script>` block setting one of: `__NEXT_DATA__`, `__NUXT__`, `__INITIAL_STATE__`, `__APOLLO_STATE__`, `__REDUX_STATE__`, `window.__data = ...`
- DevTools Network shows requests to `/api/...`, `/_next/data/<buildId>/...json`, `/graphql`, or similar after the initial document loads
- Bundle filenames in `<script src>` include hashes (`main.a1b2c3.chunk.js`) — typical SPA build output

## Three paths to the data, in order of cost

Try them in this order — the cheapest one that works wins.

### (a) Hydration payload embedded in the HTML — single GET

The fastest path. The initial document often carries the full state needed to render the first view, serialized as JSON inside a `<script>` tag. Recover it with a single GET and a regex/HTML parser:

```python
import re, json, httpx
from bs4 import BeautifulSoup

html = httpx.get("https://app.example.com/path", timeout=30).text
soup = BeautifulSoup(html, "html.parser")

# Next.js: id="__NEXT_DATA__" with type="application/json"
tag = soup.find("script", id="__NEXT_DATA__")
if tag:
    data = json.loads(tag.string)
    page_props = data["props"]["pageProps"]

# Generic globals: window.__INITIAL_STATE__ = {...};
m = re.search(r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\});", html, re.DOTALL)
if m:
    state = json.loads(m.group(1))

# Apollo cache hydration: window.__APOLLO_STATE__
m = re.search(r"__APOLLO_STATE__\s*=\s*(\{.*?\});?</script>", html, re.DOTALL)
```

When this works it's a single request, no API replay, no auth, no rate limiting. Always try it first.

### (b) Internal JSON API discovered via HAR — clean replay

When the initial HTML doesn't have what you need (e.g. infinite-scroll feeds, search results, anything that takes a user action to load), the SPA fetches it from a JSON endpoint after hydration. Capture a HAR of the real user flow and look for:

- `/api/v1/...`, `/api/v2/...`, `/graphql`, `/rpc/<method>` — the typical paths
- `/_next/data/<BUILD_ID>/<page-path>.json` — Next.js's SSG/SSR data endpoint; the response is `{"pageProps": {...}, "__N_SSG": true}`
- `/trpc/<procedure>` — tRPC apps
- `/api/edge/<path>` — Vercel/Cloudflare edge functions

Replay with httpx/curl_cffi using just the cookies and `Authorization` header from the HAR. If the endpoint is `GET` and the response has the shape you want, you're done. For POST + JSON body, copy the structure literally and parametrize what changes.

### (c) Headless browser — last resort

When (a) and (b) both fail — usually because the data is computed in client JS (e.g. decrypting a payload, computing client-side derived state) or because authentication is too complex to replicate without running the login JS — fall back to a real browser via Playwright/patchright. See `../browser-automation/browser-techniques.md`. This is the slow, fragile, expensive path; use it only when forced.

## Next.js specifics

Next.js apps are the most common SPA target and have one important quirk: the data-API path includes a **build ID** that changes every deploy.

- Path shape: `/_next/data/<BUILD_ID>/<route>.json?<query-params>`
- The build ID is in the initial HTML's `__NEXT_DATA__`: `data["buildId"]`
- After every deploy, your hardcoded path returns 404

```python
def extract_build_id(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("script", id="__NEXT_DATA__")
    return json.loads(tag.string)["buildId"]
```

In a long-running scraper, **re-extract the build ID** from a fresh home-page GET at the start of each run (or whenever you get a 404 from the data endpoint).

> **`__NEXT_DATA__` and `/_next/data/` are the *Pages Router* (older Next.js).** Modern Next.js defaults to the **App Router**, which streams React Server Component "flight" data via `self.__next_f.push([...])` inline scripts and a `text/x-component` RSC endpoint — a completely different extraction. If you don't see `__NEXT_DATA__` but do see `self.__next_f.push`, go to **`nextjs-app-router-rsc.md`**.

## Authentication in SPAs

SPAs almost never use cookie-based auth. Instead the token sits in `localStorage` (or `sessionStorage`) and the app's fetch interceptor attaches it as `Authorization: Bearer <token>` on every API call.

For scraping you do not need to replicate the login flow — capture the `Authorization` header out of a HAR and use it directly. The token typically lives 1–24 hours; refresh by re-running the login when scraping breaks with 401s.

```python
headers = {
    "Authorization": "Bearer eyJhbGciOi...",   # from HAR
    "Content-Type": "application/json",
    "Accept": "application/json",
}
```

Some SPAs also send a CSRF or signed-request header (`X-CSRF-Token`, `X-Requested-With: XMLHttpRequest`) — copy these from the HAR too.

## Pagination in SPA APIs

The three common shapes:

- **Cursor (most common in modern stacks):** `?cursor=<opaque>&limit=20` → response has `nextCursor` or `next_token` field
- **Offset/limit:** `?offset=20&limit=20` → response has `total` count
- **Page number:** `?page=2&per_page=20` → response has `total_pages` or `has_next`

If the API is GraphQL, see `graphql.md` — Relay-style cursor connections dominate.

## Routing in SPAs and what it means for scraping

SPA routes don't trigger full page loads — they just swap components and pull new JSON. **You cannot "crawl URLs"** the same way you would on a server-rendered site. Two options:

1. **Identify the API endpoint** behind each route and call it directly (preferred — see path (b) above)
2. **Drive a browser to each route** and read the rendered DOM (slow, see path (c))

Trying to GET an SPA's deep route URL with httpx will return the same nearly-empty shell as the home page — the route is interpreted on the client.

## Gotchas

- **Skeleton loaders fool "wait until loaded" heuristics.** A page that renders gray placeholder boxes during fetch will look "loaded" to `page.wait_for_load_state("networkidle")` but the real data isn't there yet. Wait for a specific selector that only appears once data populates, not a generic timeout.
- **Hydration mismatch warnings ≠ scraping signal.** Modern frameworks print console warnings about hydration mismatches even on healthy pages. Don't gate on console output.
- **`__NEXT_DATA__` can be huge.** The hydration payload for a complex page can be 1–5 MB of JSON. Parse it incrementally if memory matters; the actual data you want is usually a small slice of `props.pageProps.<something>`.
- **Service workers cache aggressively.** A scraper opening a real browser may hit a stale cached response served by the SPA's service worker. Disable service workers in the browser context (Playwright: `context.set_offline(False)` is not enough; use `context.add_init_script` to neutralize `navigator.serviceWorker`).
- **Don't grep view-source for a string you see in the rendered DOM.** If the string was added by JS after hydration, it's not in the HTML. Use the rendered DOM (Playwright `page.content()`) or trace it back to the API call that produced it.
- **Hash-routing (`/#/route`).** Older SPAs use hash routes; the fragment never reaches the server, so server-side logs and HAR filtering by URL look wrong. The data API still uses normal paths — focus on the XHR/fetch entries.

## Related

- `graphql.md` — modern SPAs commonly use GraphQL as their internal API
- `../discovery/har-driven-workflow.md` — capturing the actual API calls behind an SPA UI
- `../discovery/devtools-workflow.md` — finding hydration payloads and API endpoints from a live session
- `../browser-automation/browser-techniques.md` — when you genuinely need to drive a real browser
- `nextjs-app-router-rsc.md` — App Router / RSC flight-data extraction (the modern Next.js shape)
- `embedded-bi-dashboard.md` — a subspecies of SPA (embedded analytics)
