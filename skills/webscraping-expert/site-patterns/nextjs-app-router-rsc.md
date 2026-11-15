# Next.js — App Router & React Server Components (RSC)

Next.js is not one scraping problem. There are **three distinct data-delivery shapes** depending on which router the site uses, and the popular `__NEXT_DATA__` trick only covers the oldest one. Modern Next.js (App Router, default since Next 13) streams **React Server Component "flight" data** — a format the classic playbooks miss entirely.

## When you see this

- Page source contains `self.__next_f.push([...])` script calls → **App Router (flight data)**.
- Requests with header `RSC: 1` and `Accept: text/x-component` → **App Router RSC endpoint**.
- A `<script id="__NEXT_DATA__" type="application/json">` blob → **Pages Router** (older).
- `/_next/data/<buildId>/<path>.json` requests → **Pages Router** JSON endpoint.
- `_next/static/...` chunks, `next/dist` in bundles → it's Next.js of some flavor.

---

## The three shapes

### 1. Pages Router — `__NEXT_DATA__` (the well-known one)

The initial props are a single JSON blob in the HTML:

```python
import re, json
from curl_cffi import requests

html = requests.get(url, impersonate="chrome").text
m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
data = json.loads(m.group(1))
props = data["props"]["pageProps"]           # your data usually lives here
build_id = data["buildId"]                    # reuse for the JSON endpoint
```

**Subsequent pages** (client navigations) fetch a stable JSON endpoint — often the cleanest bulk path:

```python
# GET https://site.com/_next/data/<buildId>/<locale>/<path>.json?<routeParams>
r = requests.get(f"https://site.com/_next/data/{build_id}/en/products/{slug}.json", impersonate="chrome")
page_props = r.json()["pageProps"]
```

Gotcha: `buildId` **rotates on every deploy**. Re-scrape it from a fresh HTML page when the endpoint 404s.

### 2. App Router — inline flight data (`self.__next_f.push`)

App Router serializes server-component output as a **flight stream**, chunked across many inline scripts:

```html
<script>self.__next_f.push([1,"a:[\"$\",\"div\",null,{...escaped JSON...}]"])</script>
<script>self.__next_f.push([1,"b:{\"reviews\":[...]}"])</script>
```

Reassemble the chunks, then dig out the payload:

```python
import re, json

def extract_next_flight(html: str) -> str:
    """Concatenate all self.__next_f.push string chunks into one flight buffer."""
    chunks = re.findall(r'self\.__next_f\.push\(\[\d+,\s*"((?:[^"\\]|\\.)*)"\]\)', html)
    # Each chunk is a JS string literal — unescape it back to raw text
    return "".join(json.loads(f'"{c}"') for c in chunks)   # json.loads handles \" \\ \n \uXXXX

flight = extract_next_flight(html)
# The flight buffer is line-oriented: "<id>:<json-or-ref>". Find the object you need.
```

The flight buffer isn't a single JSON document — it's a stream of `id:value` rows where values reference each other. Two robust ways to get your data out:

**(a) Targeted regex** for a known key when you just need one object:
```python
m = re.search(r'"reviews":(\[.*?\])(?=,"[a-zA-Z_]+":)', flight)
```

**(b) Balanced-brace scan** — the reliable way to lift a complete nested object/array out of a noisy stream (see snippet below).

### 3. App Router — the RSC endpoint (`text/x-component`)

Client navigations in App Router re-request the *same URL* with RSC headers and get back a raw flight stream (no HTML wrapper). You can call it directly:

```python
from curl_cffi import requests

headers = {
    "Accept": "text/x-component",
    "RSC": "1",
    # Router state tells the server which segment to render; grab it from a real
    # navigation via DevTools/HAR. It's URL-encoded JSON of the route tree.
    "Next-Router-State-Tree": "%5B%22%22%2C%7B...%7D%5D",
    "User-Agent": "Mozilla/5.0 ...",   # match your impersonate profile
}
r = requests.get("https://site.com/products?page=2", headers=headers, impersonate="chrome")
flight = r.text                          # same flight format as the inline chunks
```

- Header casing matters to some deployments (`RSC`, `Next-Router-State-Tree`, `Next-Url`).
- **This is often the pagination unlock**: the App Router page may ignore `?page=2` on a plain HTML GET but honor it on the RSC request with the right router-state tree.

---

## Balanced-brace extraction (essential for flight streams)

Regex can't reliably match nested braces. When you know a key but the value is a deep object, scan for the matching close:

```python
def extract_json_after_key(text: str, key: str):
    """Return the JSON value that follows `"key":` in a noisy stream, brace-balanced."""
    i = text.find(f'"{key}"')
    if i == -1:
        return None
    j = text.find(":", i) + 1
    while text[j] in " \t\n":
        j += 1
    if text[j] not in "{[":
        return None
    open_ch, close_ch = text[j], "}" if text[j] == "{" else "]"
    depth, in_str, esc = 0, False, False
    for k in range(j, len(text)):
        c = text[k]
        if in_str:
            if esc:            esc = False
            elif c == "\\":    esc = True
            elif c == '"':     in_str = False
        else:
            if c == '"':       in_str = True
            elif c == open_ch:  depth += 1
            elif c == close_ch: depth -= 1
            if depth == 0:
                import json
                return json.loads(text[j:k+1])
    return None
```

---

## Escalation order for a Next.js target

1. **Pages Router?** Use `_next/data/<buildId>/...json` — cleanest, most stable.
2. **App Router?** Try the **RSC endpoint** (`Accept: text/x-component` + `RSC:1` + router-state) — you get JSON-ish flight directly, no HTML parsing.
3. Else parse **inline `self.__next_f.push`** flight from the HTML.
4. Only if all fail (data truly renders client-side from opaque state) → headless browser + network listener (`browser-automation/`).

---

## Gotchas

- **`buildId` rotates on deploy** — re-harvest from fresh HTML on 404.
- **Router-state tree is required and finicky** for RSC requests — capture a real one from DevTools/HAR (Copy as cURL on a client navigation), don't hand-build it.
- **Flight chunks are JS string literals**, doubly-escaped. Unescape with `json.loads('"' + chunk + '"')`, not naive `replace('\\"', '"')`.
- **Client-side vs server-side filtering:** many Next.js sites return the *same* payload regardless of `?sort=`/`?filter=` query params and re-order in the browser. Confirm a param actually changes the server response before building pagination around it — on some review sites the rating/sort params are purely client-side, returning the same 25 records every time.
- **Cloudflare/DataDome often sit in front** — get past the wall first (see `anti-bot/anti-bot-vendors.md`), then parse.

---

## Related

- `site-patterns/spa-frameworks.md` — general SPA embedded-state extraction
- `discovery/har-driven-workflow.md` — capture the real RSC request + router-state
- `anti-bot/anti-bot-vendors.md` — Cloudflare/DataDome usually guard these sites
- `parsing/README.md` — turning extracted JSON into bronze rows
