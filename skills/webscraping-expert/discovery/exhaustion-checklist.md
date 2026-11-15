# Exhaustion checklist — before anyone says "blocked"

## When you see this

You are about to report that a target is impossible, blocked, or has no route. Stop and run this checklist first.

"Impossible" is the most expensive wrong answer an extraction agent can give: it ends the search, and in practice a route often exists one family further down (a feed the site publishes, an open-data copy, a sibling host, an archive, or simply asking for access). Agents tend to stop after the obvious routes fail. This checklist makes "I tried everything" a claim backed by evidence.

## How it works

Three rules:

1. **An agent never declares a target `blocked`.** It may declare `stuck`, and only when every row below has evidence or an explicit N/A reason. `blocked` is a decision for whoever owns the project, taken after reviewing the stuck report (and, in multi-agent setups, after fresh agents have challenged it).
2. **Evidence means a request id, a HAR entry, or a timestamp + URL in a log**, not a sentence. A row with no evidence is a row not tried.
3. **The families are a coverage map, not an order.** Work in the order of the extraction ladder (cheapest first: discovery and public copies, then HTTP clients, then proxies, then browsers, then paid unblockers). The checklist only asks, at the end, whether every family has been covered.

Every attempt is recorded as one object, the same shape in every family:

```json
{"attempt": "GET /items/123/history.rss", "url": "https://example.com/items/123/history.rss", "client": "curl_cffi chrome", "egress": "dc-US", "status": 403, "challenged": "datadome", "evidence": "req_0088", "outcome": "challenge page, no records"}
```

- `client`: the tool and profile (`requests`, `curl_cffi chrome`, `patchright`, `unblocker`, `manual`).
- `egress`: the network path, e.g. `none` (no request sent, such as a drafted email), `local`, `dc-US`, `res-US`, `unblocker`.
- `status`: HTTP status, or `null` when the request failed before a response.
- `challenged`: the vendor whose marker was found, or `null`.

## Pattern / code

Each family points to the file in this skill that holds the technique. Try at least one attempt in every family; the project may set a higher minimum (attempts, distinct endpoints, budget spent).

| # | Family | Done when you have evidence for… | Technique |
|---|---|---|---|
| A | **Discovery** | robots.txt and the ToS read (record them as constraints: disallowed paths, automated-access clauses), sitemaps, embedded JSON (`__NEXT_DATA__`, `application/ld+json`, inline state), common API paths, the search box, link-graph from the entry page | `autonomous-discovery.md`, `link-graph-traversal.md` |
| B | **Data elsewhere** | open-data portals (CKAN/Socrata/ArcGIS/OData), bulk downloads, the parent or sibling organization's portal, official aggregators/registries, a search for the dataset name off-site, archived copies (Wayback Machine CDX, Common Crawl index) | `google-deep-research.md`, `../site-patterns/README.md` |
| C | **Hidden API** | the XHRs the page **actually makes**, found and replayed: every Fetch/XHR in DevTools or a HAR, GraphQL, RSC/flight payloads, pagination and facet APIs, form postbacks | `devtools-workflow.md`, `har-driven-workflow.md`, `../site-patterns/` |
| D | **Protection gaps** | variants of a blocked route that the page **does not call**: the suffix/format, sibling, host/version, syndication, export and app-surface matrix, with each hit classified under the sign-off rule | `../anti-bot/protection-gaps.md` |
| E | **Client fingerprint** | plain requests with realistic headers, `curl_cffi` with `chrome`/`safari`/`firefox` aliases, an alternative client (`primp`/`rnet`) | `../anti-bot/tls-http-clients.md`, `../anti-bot/browser-impersonation.md` |
| F | **Network path** | datacenter proxy, geo-targeted to the site's country, residential, sticky session, slower pacing, a different time of day | `../networking/` |
| G | **Real browser** | stealth browser (`patchright`/`camoufox`), managed-unblocker render with response capture, token/cookie harvest replayed in HTTP | `../anti-bot/modern-stealth-browsers.md`, `../browser-automation/` |
| H | **Challenge handling** | anti-bot vendor identified; CAPTCHA type identified; solver or human takeover tried where the project allows it | `../anti-bot/anti-bot-vendors.md`, `../anti-bot/captcha-solvers.md` |
| I | **Hard limits** | Login, payment, a signed agreement, and origin bypass (origin IP or unlisted origin host around the CDN) are hard stops: record the exact page and requirement, do not cross. A click-through disclaimer: record its text; if it forbids automated access, mark the route `needs_signoff` | stop here — never get past a login |
| J | **Asking for access** | an official API key or data request, a public-records/FOIA request where the owner is a public body, contacting the site owner, licensing from an aggregator or data vendor. Evidence: the request drafted (for the project owner to send) or sent, with date and recipient | — |

C and D differ by where the URL comes from: C replays requests the page itself issues; D constructs requests the page never issues. A hit in D falls under the sign-off rule in `../anti-bot/protection-gaps.md`; a hit in C usually does not.

### The stuck report

When every row is covered, report `stuck` in this shape. It is the input for whoever reviews or challenges the result:

```json
{
  "target": "https://example.com/items/123/history",
  "status": "stuck",
  "families": {
    "A": [{"attempt": "GET /sitemap.xml", "url": "https://example.com/sitemap.xml", "client": "curl_cffi chrome", "egress": "dc-US", "status": 200, "challenged": null, "evidence": "req_0012", "outcome": "no data URLs"}],
    "B": [{"attempt": "Wayback CDX query", "url": "https://web.archive.org/cdx/search/cdx?url=example.com/items/*", "client": "requests", "egress": "local", "status": 200, "challenged": null, "evidence": "cdx_q_03", "outcome": "snapshots stop two years back"}],
    "D": [{"attempt": "GET /items/123/history.rss", "url": "https://example.com/items/123/history.rss", "client": "curl_cffi chrome", "egress": "dc-US", "status": 403, "challenged": "datadome", "evidence": "req_0088", "outcome": "challenge page"}],
    "J": [{"attempt": "data request to the site's data team", "url": "mailto:data@example.com", "client": "manual", "egress": "none", "status": null, "challenged": null, "evidence": "draft_01", "outcome": "drafted, awaiting project owner to send"}]
  },
  "best_partial": "list endpoint works for 10 pages; detail blocked",
  "blocking": {"layer": "JS challenge", "vendor": "DataDome", "marker": "captcha-delivery", "where": "/items/*/history"},
  "not_tried": [{"idea": "mobile app API", "why": "no app traffic available"}],
  "spent": {"requests": 412, "proxy_requests": 180, "proxy_usd": 0.62, "minutes": 95}
}
```

## Gotchas

- **One 403 is not a block.** Neither is a block from one IP or one country — a target "blocked" from abroad is often open from an IP in its own country.
- A `200` with a challenge page in the body is a failure, and a `403` on the HTML page says nothing about its XHRs. Record the header and body markers.
- Login-only *pages* do not make the whole *site* login-only. Check whether the same records appear on a public surface.
- A partial route (list works, detail blocked; recent pages work, history capped) is progress — report it as `best_partial`, never as "blocked".
- A challenger reviewing a stuck report must not repeat recorded attempts; its job is the families and ideas the first agent did not cover.
- Write down why a row is N/A. "Not applicable" without a reason reads as "skipped".
- An agent drafts access requests (family J); the project owner decides whether and from whom they are sent.

## Related

- `../anti-bot/protection-gaps.md` — family D in depth, and the sign-off rule
- `../anti-bot/ban-detection.md` — reading a block correctly before escalating
- `../reference/README.md` — self-critique checklist and recon report spec for the end of a run
