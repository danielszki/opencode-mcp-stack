# Browser Fingerprint Impersonation (curl_cffi)

## Why plain requests gets blocked

Python's `requests` library uses the system's SSL stack (OpenSSL) which produces a distinctive TLS ClientHello — a fingerprint called **JA3** (or the newer **JA4**). Bot detection services (Cloudflare, Akamai, PerimeterX, DataDome) maintain databases of known JA3 signatures and immediately flag `requests` and `httpx` as bots.

The fix: use `curl_cffi`, which compiles against a patched version of libcurl that reproduces the exact TLS ClientHello of real browsers.

## What the fingerprint includes

- **Cipher suites** — which encryption algorithms are proposed, in what order
- **TLS extensions** — what extensions the client supports (ALPN, SNI, etc.)
- **GREASE values** — random-looking bytes that real Chrome inserts for forward-compatibility
- **HTTP/2 settings frames** — real browsers use specific initial window sizes and HPACK table settings
- **Header order** — browsers send headers in a consistent order that differs from requests

All of these together create a fingerprint that's almost impossible to fake without using libcurl.

## Installation

```bash
pip install curl-cffi
```

No system dependencies needed — ships as a wheel with libcurl built in.

## Basic usage

```python
from curl_cffi import requests

# Drop-in replacement for requests
r = requests.get("https://site.com/api", impersonate="chrome")
r = requests.post("https://site.com/api", json={"key": "val"}, impersonate="chrome")

# With a Session (recommended — maintains cookies)
session = requests.Session()
session.impersonate = "chrome"
r = session.get("https://site.com/data")
```

## Available impersonation profiles

**Don't hardcode an old Chrome number** — fingerprints go stale as real browsers advance, and an old `chrome124` starts looking anomalous. Prefer the **generic aliases**, which auto-select the newest profile your installed version ships:

```python
requests.get(url, impersonate="chrome")          # newest Chrome
requests.get(url, impersonate="safari")           # newest Safari
requests.get(url, impersonate="firefox")          # newest Firefox
requests.get(url, impersonate="chrome_android")   # newest Chrome / Android
requests.get(url, impersonate="safari_ios")       # newest Safari / iOS
```

Profiles in the current (0.11.x) line — pin a specific one only when a site fingerprints a known-good older build:
```
chrome:   chrome110 … chrome124, chrome131, chrome133a, chrome136, chrome142, chrome145, chrome146
safari:   safari153, safari155, safari170, safari180, safari184, safari260, safari2601
safari_ios: safari172_ios, safari180_ios, safari184_ios, safari260_ios
firefox:  firefox133, firefox135, firefox144, firefox147
mobile:   chrome99_android, chrome131_android
other:    edge99, edge101, tor145
```
The **`a` suffix** (e.g. `chrome133a`) is an *alternative* fingerprint observed from Chrome A/B testing — try it when the plain number is blocked. Keep `curl_cffi` itself updated (`uv pip install -U curl_cffi`) — new browser targets ship in new releases.

**Recommendation order:**
1. `impersonate="chrome"` — newest Chrome, matches the majority of users
2. `impersonate="safari"` — good for Apple-targeted sites or Apple-specific detection
3. `impersonate="firefox"` — some sites allowlist Firefox but not unknown clients
4. Pin an older specific build only if a site bans the newest (rare)

**Faster alternatives:** for high-throughput or async-native work, `primp` and `rnet` (Rust-backed) match curl_cffi's fingerprinting and benchmark faster. See `anti-bot/tls-http-clients.md`.

## Advanced: Session with proxy + impersonation

```python
from curl_cffi import requests

session = requests.Session()
session.impersonate = "chrome"

# Add proxy
session.proxies = {
    "http": "http://user:pass@proxy.provider.com:8080",
    "https": "http://user:pass@proxy.provider.com:8080",
}

# Add realistic headers
session.headers.update({
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://site.com/",
    "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
})

r = session.get("https://blocked-site.com/api")
```

## Async usage

```python
import asyncio
from curl_cffi.requests import AsyncSession

async def fetch_all(urls: list[str]) -> list[dict]:
    async with AsyncSession(impersonate="chrome") as session:
        tasks = [session.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]

results = asyncio.run(fetch_all(["https://api.site.com/1", "https://api.site.com/2"]))
```

## Detecting what's blocking you

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `requests` → 403, `curl_cffi` → 200 | JA3/JA4 fingerprint block | Use curl_cffi, you're done |
| Both → 403 | IP block or cookie required | Add proxy + get cookie from browser |
| `curl_cffi` → 200 but wrong data | Geo block | Add geo-targeted proxy |
| All → 403 after N requests | Rate limit + IP ban | Proxy rotation + backoff |
| JS challenge page | Cloudflare JS verification | Real browser (`patchright`) → harvest `cf_clearance`, or managed unblocker (Zyte API) |
| CAPTCHA | Active bot protection | 2captcha / CapSolver API |

## When curl_cffi is not enough

1. **Site checks behavioral signals** — The site loads JS and checks for mouse movement, scroll events, interaction timing. `curl_cffi` sends no such signals.
   → Real stealth browser: `patchright` (Cloudflare) or `camoufox` (DataDome/behavioral). See `anti-bot/modern-stealth-browsers.md`. (`playwright-stealth` is largely superseded.)

2. **Login-gated content** — The session cookie can only be obtained after a real browser login.
   → Use browser injection (Level 4 in SKILL.md)

3. **Cloudflare managed challenge / Turnstile** — Needs actual JS execution, not just a JA3 match.
   → Managed challenge: real browser (`patchright`) → harvest `cf_clearance`, or a managed unblocker (Zyte API / Web Unlocker). Turnstile widget: solver (CapSolver/2Captcha). See `anti-bot/anti-bot-vendors.md`. (`cloudscraper`/FlareSolverr lag current Cloudflare — don't lead with them.)

## Alternatives to curl_cffi

The impersonation-client field has grown. Full comparison in `anti-bot/tls-http-clients.md`; the short version:

- **`primp`** (Rust `rquest`) — fastest; `requests`-like API; `impersonate="chrome_131"`. Formerly `pyreqwest-impersonate`.
- **`rnet`** (Rust `wreq`/reqwest-impersonate) — async-native, rich HTTP/2 emulation; best for high-concurrency async crawlers.
- **`tls-client`** (Go, bogdanfinn) — low-level knobs when you must hand-tune:
  ```python
  import tls_client
  session = tls_client.Session(client_identifier="chrome_133", random_tls_extension_order=True)
  r = session.get("https://site.com/api")
  ```
  Use only when curl_cffi's canned profile isn't granular enough.

Prefer `curl_cffi` by default (broadest profiles, easiest). Switch to primp/rnet when the HTTP client is your measured bottleneck.
