# Proxy providers (cross-reference)

The default is **Zyte (Smart Proxy Manager)** — see `proxy-zyte.md` for the full playbook. This file is a quick reference for *other* providers, used when comparing costs, when Zyte has a coverage gap, or when the user already has another provider's credentials.

## Quick comparison

| Provider | Type | Indicative price | Sticky session syntax | Geo syntax |
|---|---|---|---|---|
| **Zyte / Crawlera** | Residential, managed | $$ | Header `X-Crawlera-Session: create`/`<SID>` | Header `X-Crawlera-Region: AU` |
| Bright Data | Residential / mobile / datacenter | $$$ | Username suffix `-session-<id>` | Username suffix `-country-<cc>` |
| Oxylabs | Residential / mobile | $$$ | Username suffix `-sessid-<id>` | Username suffix `_country-<CC>` |
| Decodo (ex-Smartproxy) | Residential | $$ | Username suffix `-session-<id>` | Username suffix `-country-<cc>` |
| Webshare | Datacenter / residential basic | $ | None on basic plan | Endpoint hostname per country |
| IPRoyal | Residential | $$ | Username suffix `-session-<id>` | URL param `?country=<cc>` |
| ScrapingBee | Managed (browser) | per-request | N/A (per-call) | Param `country_code=us` |
| ZenRows | Managed (browser) | per-request | N/A | Param `proxy_country=US` |

> **Note:** Smartproxy rebranded to **Decodo**; the gateway host/suffix syntax is unchanged. Old `gate.smartproxy.com` credentials still work during the transition.

## Provider-specific URI formats

```python
# Zyte (header-based, recommended default)
PROXY_URL = "http://USER:PASS@proxy.crawlera.com:8011"
# Then send headers: X-Crawlera-Session, X-Crawlera-Region

# Bright Data
def brightdata_proxy(session_id: str, country: str = "") -> str:
    user = "brd-customer-XXXXX-zone-ZONE"
    if country: user += f"-country-{country.lower()}"
    if session_id: user += f"-session-{session_id}"
    return f"http://{user}:PASS@zproxy.lum-superproxy.io:22225"

# Oxylabs
def oxylabs_proxy(session_id: str, country: str = "") -> str:
    user = "USER"
    if country: user += f"_country-{country.upper()}"
    if session_id: user += f"-sessid-{session_id}"
    return f"http://{user}:PASS@pr.oxylabs.io:7777"

# Smartproxy
def smartproxy_proxy(session_id: str, country: str = "") -> str:
    user = "USER"
    if country: user += f"-country-{country.lower()}"
    if session_id: user += f"-session-{session_id}"
    return f"http://{user}:PASS@gate.smartproxy.com:7000"

# Webshare (no sticky/geo on basic plan)
PROXY_URL = "http://USER:PASS@p.webshare.io:80"

# IPRoyal (URL param + username suffix)
PROXY_URL = "http://USER:PASS@geo.iproyal.com:12321"
# Append per request: ?country=us&session=12345
```

## Generating a session ID

For providers using username-suffix sticky (Bright Data, Oxylabs, Smartproxy), you pick the session ID yourself. Use a random string:

```python
import secrets
session_id = secrets.token_hex(8)  # 16 hex chars — collision-proof and fits URL
```

Keep the same `session_id` across all requests in a session. Drop it (and pick a new one) when starting a fresh session.

## Managed unblockers (proxy + browser + CAPTCHA in one call)

When you don't want to run browsers or solve challenges yourself, a **managed unblocker** takes a URL and returns the unblocked HTML/JSON — it picks the proxy, renders JS, solves the challenge, and retries internally. This is the honest answer for DataDome/Kasada/F5 and hard Cloudflare (see `anti-bot/anti-bot-vendors.md`).

| Service | Model | Indicative 2026 price | Notes |
|---|---|---|---|
| **Zyte API** | Unified API (replaces Smart Proxy Manager/Crawlera) | ~$0.13/1k simple PAYG → ~$0.06/1k at commit; difficulty-tiered | Cheapest on easy sites, scales cost with difficulty |
| **Bright Data Web Unlocker** | Per successful request | ~$3/1k successful | Also **Scraping Browser** (remote CDP browser) + SERP API |
| **Oxylabs Web Unblocker** | Per GB | ~$9.40/GB | Good for few large pages, pricey for many small ones |
| **ZenRows / ScrapingBee** | Per request | per-call | Simple params, JS render + CAPTCHA included |
| **Apify** | Per compute + proxy | usage-based | Actor marketplace, full pipelines |

Zyte's Smart Proxy Manager / Crawlera is now folded into the **Zyte API** — new integrations should target the unified API, though the header-based Crawlera proxy in `proxy-zyte.md` still works.

## When to choose what

- **General purpose, AU/EU/US targets, sites with anti-bot:** Zyte (default)
- **High volume + cost-sensitive:** Decodo or IPRoyal
- **Cloudflare-heavy / hostile targets:** managed unblocker (Zyte API, Bright Data Web Unlocker, ZenRows) — they handle the bypass for you
- **DataDome / Kasada / F5-Shape:** managed unblocker or a real stealth browser (`camoufox`) + residential proxy — HTTP clients alone won't clear these
- **Geo-targeted scraping with rare countries:** check Bright Data or Oxylabs coverage
- **Pure datacenter, low-stakes scraping:** Webshare or any cheap datacenter provider

## Cost notes

- Residential proxies bill per GB of bandwidth. Watch out for large response bodies (images, PDFs).
- Managed services bill per request. Cheaper for low volume, expensive at scale.
- Geo-pinning is often free; mobile (4G/LTE) pools are 2-3× more expensive than residential.

## Related

- `proxy-zyte.md` — default provider, full playbook
- `sticky-sessions.md` — universal sticky session concept
- `geo-targeting.md` — when geo-pin matters
