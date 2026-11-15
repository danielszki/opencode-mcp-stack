# DevTools Inspection Workflow

How to find the right API request when a website's data loads via XHR/fetch.

## Core principle

**Start from a visible value, not from the request list.** Trying to guess which of the 80 XHRs has your data is a waste of time. Instead, search for a text you can see on the page — it will point you to the exact response.

## Step by step

### 1. Pick a unique anchor text

Something visible on the page that is:
- **Unique** (won't match other requests by accident)
- **Specific to the data you want** (if you want country scores, pick a country + score; not a UI label)
- **Unlikely to be rendered client-side** (raw numbers are better than formatted text, because formatting may happen in JS)

Good anchors:
- A country name + a specific value: `Netherlands 2.05`
- A timestamp that appears on screen: `2024-11-15 14:30`
- A specific price or count: `131.87 EUR/MWh`
- A unique article ID

Bad anchors:
- "Download" (button label, appears everywhere)
- "Results" (page section title)
- Currency symbol alone (`€`)

### 2. Open DevTools Network with persistence

1. F12 (or Cmd+Opt+I on Mac)
2. Go to **Network** tab
3. Check ☑ **Preserve log** (so it survives page reload/navigation)
4. Click 🚫 to clear existing requests
5. Reload the page (Cmd+R / Ctrl+R)

### 3. Filter to XHR/Fetch

In the Network tab toolbar:
- Click **Fetch/XHR** filter chip (hides static assets)
- Or type `is:xhr` in the filter box

### 4. Search by anchor text

- Click the 🔍 **Search** icon in the top-left of DevTools (NOT the filter box)
- Or press Ctrl+F / Cmd+F inside the Network panel
- Paste your anchor text
- Press Enter

DevTools will search **response bodies** and highlight matches. Each match takes you to the exact request and the response line.

### 5. Choose the best request

If multiple requests match, prefer in this order:
1. **Clean JSON API** — `application/json` response, small, structured
2. **GraphQL** — usually POST to `/graphql`, JSON body with `query` field
3. **HTML fragment with your data** — workable if structured
4. **Rendered HTML page** — parse with BeautifulSoup (last resort)

Avoid requests that:
- Have a massive response that's mostly analytics or tracking data
- Are WebSocket upgrades
- Return the same data in multiple formats (pick the JSON one)

### 6. Copy as cURL

Right-click the request → **Copy** → **Copy as cURL (bash)** (on Windows use "cmd" variant only if needed)

### 7. Clean up the curl

Before running:
- Remove auth headers you don't need (trackers, A/B test cookies)
- Keep required: `Authorization`, `Cookie` (auth), `Referer`, `Origin`, `X-Requested-With`
- Convert to Python:
  ```python
  # curl --data-raw '{"a":1}' -H 'Content-Type: application/json' ...
  import requests
  r = requests.post(URL, json={"a": 1}, headers=HEADERS, cookies=COOKIES)
  ```

## Special cases

### Single-page app (Next.js, React, Vue)

Check:
- `/api/v1/*` — common internal API pattern
- `/_next/data/{buildId}/{path}.json` — Next.js SSG/SSR data
- `__NEXT_DATA__` in page HTML (`view-source:`) — initial payload embedded

### Requires login

The curl from DevTools includes your session cookie. Two options:
1. **Short-lived:** use the curl directly (valid while session is active)
2. **Long-lived:** replicate the login flow programmatically (login endpoint → store cookies → use session)

```python
s = requests.Session()
s.post(LOGIN_URL, data={"user": U, "pass": P})
# s.cookies now has session — use for subsequent requests
r = s.get(API_URL)
```

### Pagination

Look for query params on the matching request:
- `?page=2&limit=50`
- `?offset=100&limit=50`
- `?cursor=eyJ...` (opaque cursor, usually in a response field like `next_cursor`)
- `Link` header with `rel="next"` (GitHub-style)

Implement:
```python
page = 1
while True:
    r = s.get(URL, params={"page": page})
    data = r.json()
    if not data["items"]: break
    yield from data["items"]
    page += 1
```

### GraphQL

Response shows the `query` and `variables`:
```python
r = requests.post(
    "https://site.com/graphql",
    json={"query": "query($id:ID!){ user(id:$id){ name } }", "variables": {"id": 42}},
    headers={"x-api-key": "..."}
)
```

### Download buttons

The file download usually triggers a GET that returns binary (often `application/octet-stream` or `application/pdf`). DevTools shows it the same way — copy as cURL, use:
```python
r = requests.get(URL, stream=True)
with open("file.pdf", "wb") as f:
    for chunk in r.iter_content(8192):
        f.write(chunk)
```

## What to send back

When asking the user for help, be specific:

> "On the page you can see `2.05` next to Germany for water stress.
> Please:
> 1. Open DevTools → Network tab → ☑ Preserve log
> 2. Reload the page
> 3. Filter to Fetch/XHR
> 4. Click 🔍 Search → paste `2.05`
> 5. It will highlight the matching requests
> 6. Right-click the JSON response with that value → Copy → Copy as cURL
> 7. Paste it here"
