# Zyte Smart Proxy Manager (Crawlera) — primary proxy reference

**This is the default proxy provider.** When a scraping task needs a proxy, reach for Zyte unless the user explicitly asks to compare alternatives.

---

## When you see this

- `PROXY_URL` env points at a Zyte endpoint (`proxy.crawlera.com:8011`, `*.zyte.com`, etc.)
- Target requires geo-routing (gov sites that geo-block non-domestic IPs are the typical case)
- Target uses anti-bot CDN (Akamai / Cloudflare / Imperva) that needs residential IPs + TLS impersonation
- Target uses stateful sessions (ASP.NET cookies, Salesforce, CSRF tokens) — all follow-up requests must exit the same IP

## How it works

Zyte is a residential proxy pool with **session pinning** and **geo-routing** controlled by HTTP request headers, not by the URL.

- **`X-Crawlera-Session: create`** → Zyte assigns a session ID, returns it in the response header. All subsequent requests sending the same ID exit through the same IP.
- **`X-Crawlera-Region: <ISO_country>`** → Zyte routes via an exit IP located in that country.
- Other proxy providers do the same thing with different syntax (username suffix). Zyte's header-based approach is more ergonomic.

## Pattern — minimum viable proxy setup

```python
import os
from curl_cffi import requests as cffi_requests

PROXY_URL = os.environ["PROXY_URL"]   # never hardcode

def _pxy_kwargs(proxy_url: str | None) -> dict:
    """Drop-in kwargs for every curl_cffi call when proxy is configured."""
    if proxy_url:
        return {"proxies": {"http": proxy_url, "https": proxy_url}, "verify": False}
    return {}

session = cffi_requests.Session()
sticky = {"X-Crawlera-Session": "create", "X-Crawlera-Region": "AU"}

# Bootstrap: open the session and capture the SID
r = session.get(
    "https://target.example.com/",
    headers=sticky,
    impersonate="chrome",
    timeout=60,
    **_pxy_kwargs(PROXY_URL),
)
r.raise_for_status()

# Pin all subsequent requests to the same exit IP
sid = r.headers.get("X-Crawlera-Session", "")
sticky = {"X-Crawlera-Region": "AU"}
if sid:
    sticky["X-Crawlera-Session"] = sid

# Every follow-up request must include `headers=sticky`
r2 = session.get("https://target.example.com/api/data", headers=sticky, impersonate="chrome", **_pxy_kwargs(PROXY_URL))
```

## Pattern — boot retry with fresh session on each attempt

When the target's anti-bot occasionally rejects (different exit IP on each retry helps):

```python
import random, time
import logfire

_MAX_BOOT_ATTEMPTS = 4

last_exc: Exception | None = None
for attempt in range(_MAX_BOOT_ATTEMPTS):
    sticky = {"X-Crawlera-Session": "create", "X-Crawlera-Region": "AU"}
    try:
        session.cookies.clear()
        r = session.get(url, headers=sticky, impersonate="chrome", timeout=60, **_pxy_kwargs(PROXY_URL))
        r.raise_for_status()
        sid = r.headers.get("X-Crawlera-Session", "")
        sticky = {"X-Crawlera-Region": "AU"}
        if sid:
            sticky["X-Crawlera-Session"] = sid
        break  # success
    except Exception as exc:
        last_exc = exc
        wait = 3 * (2 ** attempt) + random.uniform(0, 2)
        logfire.warn("boot attempt {n} failed: {err}; retry in {w:.0f}s", n=attempt+1, err=str(exc), w=wait)
        time.sleep(wait)
else:
    raise RuntimeError(f"failed after {_MAX_BOOT_ATTEMPTS} attempts: {last_exc}")
```

## Concurrency: same SID across threads, separate `curl_cffi.Session` per thread

When parallelizing detail fetches (or any follow-up request batch), all threads share the same Zyte session header — so they exit through the same IP — but each thread needs its own `curl_cffi.Session` because libcurl serializes per-session.

See `../reliability/concurrency-curl-cffi.md` for the pattern.

```python
import threading
from concurrent.futures import ThreadPoolExecutor

tls = threading.local()

def _get_thread_session(boot_session: cffi_requests.Session) -> cffi_requests.Session:
    s = getattr(tls, "session", None)
    if s is None:
        s = cffi_requests.Session()
        # Inherit auth cookies from the boot session
        for c in boot_session.cookies.jar:
            s.cookies.set(c.name, c.value, domain=c.domain, path=c.path)
        tls.session = s
    return s

def _fetch_one(item, sticky_header):
    s = _get_thread_session(boot_session)
    return s.get(item.url, headers=sticky_header, impersonate="chrome", **_pxy_kwargs(PROXY_URL))

with ThreadPoolExecutor(max_workers=10) as ex:
    for result in ex.map(lambda i: _fetch_one(i, sticky), items):
        ...
```

All ten threads exit through the **same residential IP** because they share `sticky["X-Crawlera-Session"]`. This is essential when the target uses ASP.NET session cookies or any other stateful auth.

## Error decoder

Memorize these. Every diagnosis starts here.

| HTTP | Response header `x-crawlera-error` | Meaning | Fix |
|---|---|---|---|
| 503 | `internal_server_error` | Zyte has no exit IP available in the requested region | Verify `X-Crawlera-Region` value (use ISO 3166 alpha-2 uppercase); check Zyte plan covers this geo; retry — pool may fill in seconds |
| 503 | `bad_session_id` | The sticky session ID is unknown/expired | Drop the SID, re-send `X-Crawlera-Session: create`, reboot full nav |
| 503 | `nxdomain` | DNS resolution failed for target | Check target URL spelling; some targets block DNS in certain regions |
| 407 | (none) | Bad credentials in `PROXY_URL` | Verify `.env` |
| 421 | (none — target's response, not Zyte's) | Target's CDN rejected the request because the SNI/cert doesn't match. Common cause: proxy rotated IP mid-session and the new IP is in a different POP. | Pin sticky session BEFORE the first TLS handshake; force `X-Crawlera-Region` to match cert geo |
| 200 + "Error" page in HTML | (none) | Target's application rejected — usually expired CSRF / VIEWSTATE / cookie | Re-boot the full navigation sequence; don't try to reuse stale tokens. See `../site-patterns/aspnet-webforms.md` and `../site-patterns/legacy-cms.md` |
| 429 | (none) | Target's own rate limit hit despite the proxy | Respect `Retry-After`; rotate sticky session (force a new exit IP); reduce concurrency |

## Why `X-Crawlera-Region` is non-negotiable for geo-restricted targets

Without an explicit region:
- Zyte's pool spans many countries; mid-session your exit IP can switch to a different geography
- Geo-blocked targets return 421 (TLS routing mismatch) or timeout
- TLS cert + SNI must consistently match the target's expected geo

A request to an Australian gov portal without `X-Crawlera-Region: AU` will fail intermittently and unpredictably. Always set the region.

## When to suggest a non-Zyte alternative

Only when:
- The user explicitly asks for a cost comparison
- Zyte's residential pool doesn't cover the target region (rare, but check the dashboard)
- The use case needs mobile/4G IPs specifically (Zyte residential ≠ mobile)
- The user already has another provider's credentials handy for a one-off

In those cases, lead with: *"Default is Zyte; switching to X because [specific reason]. Quer prosseguir?"* — then see `proxy-providers.md`.

## Related

- `proxies-overview.md` — when proxies are needed at all
- `proxy-providers.md` — cheatsheet of other providers
- `sticky-sessions.md` — the universal concept (cross-provider)
- `geo-targeting.md` — recognizing geo-blocks
- `../reliability/concurrency-curl-cffi.md` — per-thread session pattern
- `../anti-bot/error-decoders.md` — 421 Misdirected and "200 + Error" details
