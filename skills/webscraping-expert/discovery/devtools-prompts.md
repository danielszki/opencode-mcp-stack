# DevTools Prompt Templates

Copy-paste templates for asking the user to inspect DevTools. Fill in the anchor text.

## Template: single value on page

```
I can see `<ANCHOR>` on the page.

Please:
1. Open DevTools (F12) → Network tab → ☑ Preserve log
2. Reload the page (Cmd+R / Ctrl+R)
3. Click the 🔍 Search icon (top-left of Network panel, NOT the filter box)
4. Paste `<ANCHOR>` and press Enter
5. DevTools will show which response contains that value
6. Right-click that request → Copy → Copy as cURL
7. Paste it here

If multiple requests match, prefer the one returning JSON (not HTML).
```

## Template: map / chart / visualization

```
The data is rendered in a chart/map. To find where it comes from:

1. Open DevTools → Network → ☑ Preserve log + filter by Fetch/XHR
2. Reload the page
3. Wait for the chart to fully load
4. Interact with it: hover over the specific data point I need, e.g. `<point>`
5. If a new network request fires on hover, copy that
6. Otherwise, search (🔍) for a value visible on the chart, like `<value>`
7. Copy the matching request as cURL and send it to me

Bonus: right-click the chart → Inspect → look at the DOM. Sometimes the values are in `data-*` attributes we can scrape from HTML directly.
```

## Template: download button

```
This triggers a file download. To replicate:

1. Open DevTools → Network → ☑ Preserve log
2. Click the Download button
3. A new request appears at the bottom of Network — typically with Content-Type `application/octet-stream`, `application/pdf`, or `text/csv`
4. Right-click → Copy → Copy as cURL
5. Paste here

The URL often contains a token or signed URL — if so, it expires and we'll need the login flow instead.
```

## Template: GraphQL

```
The site uses GraphQL. To find the right query:

1. DevTools → Network → filter by `graphql` (usually one endpoint at /graphql)
2. Reload or trigger the action that loads the data
3. Click each POST to /graphql → look at the Request Payload tab
4. Find the one whose `query` field matches the data you want
5. Right-click → Copy → Copy as cURL

Send me the full curl — I need both the query string and any `x-api-key` headers.
```

## Template: login required

```
This page needs authentication. To capture the right headers:

1. Log in normally in the browser
2. Open DevTools → Network → ☑ Preserve log
3. Navigate to the data page while logged in
4. Search (🔍) for `<ANCHOR>`
5. Copy the matching request as cURL

IMPORTANT: the curl will contain your session cookie — don't share it publicly. It'll work for this scraping run but will expire eventually.
```

## Template: pagination

```
I got the first page but need to paginate. Please:

1. Navigate to page 2 in the UI
2. DevTools → Network → find the new request that loaded (filter by XHR)
3. Look at the URL / payload — compare with page 1 curl
4. Tell me what changed: query param (`?page=2`, `?offset=50`), body field (`{"cursor": "xyz"}`), or header

That tells me the pagination pattern so I can loop.
```

## Template: form submit / interactive filter

```
I need the data after applying a filter. Please:

1. DevTools → Network → ☑ Preserve log + Fetch/XHR filter
2. Clear the log (🚫)
3. Apply the filter in the UI (click the button, select the option)
4. A new request fires — that's the one
5. Copy as cURL → send to me

If it's a POST, I also need the request body (visible in the Payload tab).
```
