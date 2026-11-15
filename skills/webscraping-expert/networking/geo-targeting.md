# Geo-targeting

Some targets only serve content to specific countries. Your home IP gets timeouts, 403s, or a CDN error page. The fix is a proxy with an exit IP in the right country.

## How to recognize a geo-block

| Symptom | Probably geo-block |
|---|---|
| Browser works from country X, all clients timeout from country Y | ✅ Very likely |
| `curl --max-time 10 https://target.com` stalls indefinitely (no TCP connect) | ✅ Likely (could also be hard IP-ban) |
| HTTP 451 Unavailable For Legal Reasons | ✅ Confirmed |
| HTTP 421 Misdirected Request through a non-target proxy | ✅ Likely — TLS routing rejects non-domestic |
| Response body says "this content is not available in your region" | ✅ Confirmed |
| 503 from your proxy with `x-crawlera-error: internal_server_error` | ❓ Your proxy can't allocate exit IP in target region |

How to confirm: try the same request through a proxy located in the target country. If it works, geo-block confirmed.

## Set the exit country

The mechanism differs per provider:

| Provider | How |
|---|---|
| **Zyte** | Header `X-Crawlera-Region: <ISO_alpha-2_uppercase>` (e.g. `AU`, `DE`, `US`) |
| Bright Data | Username suffix `-country-<code>` (lowercase, e.g. `-country-au`) |
| Oxylabs | Username suffix `_country-<code>` (uppercase) |
| Smartproxy | Username suffix `-country-<code>` (lowercase) |
| Webshare | Endpoint hostname per country (`us.p.webshare.io`, `de.p.webshare.io`, …) |

For Zyte specifically (the default), see `proxy-zyte.md`.

## Combine with sticky session

Geo-pinning and sticky-session are usually combined. Without a sticky session, your proxy may rotate to a different country mid-session, even if you set the country at session start.

```python
# Zyte: both at once
sticky = {
    "X-Crawlera-Session": "create",
    "X-Crawlera-Region": "AU",
}
```

After the first request, capture the session ID and continue sending **both** headers on follow-ups.

## Multiple countries

If you need to scrape data restricted to different countries (e.g. regional pricing pages), open a separate sticky session per country:

```python
sessions = {}
for country in ["AU", "NZ", "GB"]:
    s = curl_cffi.Session()
    r = s.get(BASE, headers={"X-Crawlera-Session": "create", "X-Crawlera-Region": country}, ...)
    sid = r.headers.get("X-Crawlera-Session", "")
    sessions[country] = {"session": s, "headers": {"X-Crawlera-Session": sid, "X-Crawlera-Region": country}}
```

Each session has its own exit IP in its own country. Use the right one per request.

## Cost note

Residential proxies in less common geos (some African or Pacific countries) cost more than US/EU/AU/UK pools. Check your provider's pricing per geo before committing to country-specific scraping at volume.

## Related

- `proxy-zyte.md` — full Zyte playbook (default provider)
- `sticky-sessions.md` — pair geo-pin with sticky for stable routing
- `../anti-bot/error-decoders.md` — distinguishing geo-block from IP-ban from rate-limit
