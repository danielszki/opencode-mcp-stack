# Proxy Networks — Setup, Geo-targeting, Rotation

## When you need proxies

- **IP rate limit:** Site returns 429 after N requests from your IP
- **IP ban:** Site blocks your IP (datacenter IP ranges are well-known)
- **Geo-restriction:** Content differs by country, or site blocks non-local IPs
- **High concurrency:** Multiple workers all hitting from the same IP → instant detection

## Proxy types compared

| Type | How it works | Detection risk | Speed | Cost | Best for |
|------|-------------|---------------|-------|------|----------|
| **Datacenter** | Hosted server IPs | High — IP ranges known to sites | Fast | $2–5/GB | Low-security sites, bulk downloads |
| **Residential** | Real consumer ISP IPs | Low — looks like a real user | Medium | $7–15/GB | High-security sites |
| **ISP (static residential)** | Fixed residential IP | Low | Fast | $2–5/IP/mo | Sessions needing stable IP |
| **Mobile (4G/5G)** | Carrier IPs | Very low | Varies | $15–25/GB | Maximum stealth |
| **Rotating (per-request)** | New IP each request | Depends on type | Medium | Per GB | Bulk extraction |
| **Session sticky** | Same IP for N minutes | Depends on type | Medium | Per GB | Cookie-based flows |

## Provider comparison

| Provider | Type | Price | Geo | Notes |
|----------|------|-------|-----|-------|
| **Webshare** | Datacenter rotating | $2/GB or $15/mo (2GB) | Limited | Good starting point, easy setup |
| **Bright Data** | Residential / mobile | $8–15/GB | 195 countries, city-level | Best coverage, complex dashboard |
| **Oxylabs** | Residential | $8–15/GB | 195 countries | Reliable, good support |
| **IPRoyal** | Residential | $7/GB | 190 countries | Mid-tier, good uptime |
| **PacketStream** | Residential | $1/GB | Limited | Budget, lower quality |
| **Smartproxy** | Residential | $7/GB | 195 countries | Good price/quality ratio |
| **ScrapingBee** | Managed (browser) | $0.0025/req | Yes | No proxy config — just an API |
| **ZenRows** | Managed (browser) | $0.004/req | Yes | Cloudflare-heavy sites |

**For most use cases:** Start with Webshare datacenter. If blocked → upgrade to IPRoyal residential. If geo needed → Bright Data or Oxylabs.

## Basic setup in requests

```python
import requests

# Single proxy
PROXY = "http://user:pass@proxy.webshare.io:80"
r = requests.get("https://target.com/api", proxies={"http": PROXY, "https": PROXY})

# Session with proxy
session = requests.Session()
session.proxies = {"http": PROXY, "https": PROXY}
r = session.get("https://target.com/api")
```

## Geo-targeted proxy (country-specific exit IP)

Each provider uses a slightly different format for selecting the exit country:

```python
# Bright Data — embed country in username
def bright_data_proxy(country: str, session_id: str | None = None) -> str:
    user = f"brd-customer-CUSTOMER_ID-zone-ZONE_NAME-country-{country.lower()}"
    if session_id:
        user += f"-session-{session_id}"
    return f"http://{user}:PROXY_PASS@zproxy.lum-superproxy.io:22225"

# Oxylabs
def oxylabs_proxy(country: str) -> str:
    return f"http://user_country-{country.upper()}:PASS@pr.oxylabs.io:7777"

# Smartproxy
def smartproxy_proxy(country: str) -> str:
    return f"http://user-country-{country.lower()}:PASS@gate.smartproxy.com:7000"

# IPRoyal
def iproyal_proxy(country: str) -> str:
    return f"http://user:PASS@geo.iproyal.com:12321?country={country.lower()}"

# Usage
for country in ["DE", "FR", "NL", "PL"]:
    proxy = bright_data_proxy(country)
    r = requests.get(
        "https://target.com/api",
        proxies={"https": proxy},
        timeout=30,
    )
```

## Sticky sessions (same IP for full flow)

For cookie-based flows (login → browse → extract), you need the same IP throughout:

```python
import random, string

def sticky_session_proxy(country: str, duration_minutes: int = 10) -> str:
    """Bright Data sticky session — same IP for N minutes."""
    session_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    user = f"brd-customer-ID-zone-ZONE-country-{country.lower()}-session-{session_id}-sessionduration-{duration_minutes}"
    return f"http://{user}:PASS@zproxy.lum-superproxy.io:22225"

# Usage: login with sticky proxy, then use same proxy for all requests in session
proxy = sticky_session_proxy("DE", duration_minutes=10)
session = requests.Session()
session.proxies = {"https": proxy}
session.post("https://site.com/login", data={"user": "u", "pass": "p"})
data = session.get("https://site.com/api/protected").json()
```

## Rotating proxy pool (manual)

When using free or paid proxy lists:

```python
import random, time, requests
from typing import Optional

class RotatingProxyPool:
    def __init__(self, proxies: list[str], max_failures: int = 3):
        self.proxies = proxies
        self.failure_count: dict[str, int] = {p: 0 for p in proxies}
        self.max_failures = max_failures

    def get_proxy(self) -> Optional[dict]:
        available = [p for p, f in self.failure_count.items() if f < self.max_failures]
        if not available:
            raise RuntimeError("All proxies exhausted")
        proxy = random.choice(available)
        return {"http": proxy, "https": proxy}

    def mark_success(self, proxy: str) -> None:
        self.failure_count[proxy] = max(0, self.failure_count[proxy] - 1)

    def mark_failure(self, proxy: str) -> None:
        self.failure_count[proxy] += 1

    def fetch(self, url: str, **kwargs) -> requests.Response:
        for _ in range(5):
            proxies = self.get_proxy()
            proxy_url = proxies["https"]
            try:
                r = requests.get(url, proxies=proxies, timeout=30, **kwargs)
                if r.status_code == 429:
                    self.mark_failure(proxy_url)
                    time.sleep(2)
                    continue
                r.raise_for_status()
                self.mark_success(proxy_url)
                return r
            except (requests.ConnectionError, requests.Timeout):
                self.mark_failure(proxy_url)
        raise RuntimeError(f"Failed to fetch {url} after all retries")

pool = RotatingProxyPool([
    "http://user:pass@proxy1:8080",
    "http://user:pass@proxy2:8080",
    "http://user:pass@proxy3:8080",
])
r = pool.fetch("https://target.com/api")
```

## curl_cffi + proxy

```python
from curl_cffi import requests

session = requests.Session()
session.impersonate = "chrome"
session.proxies = {
    "http": "http://user:pass@proxy.provider.com:8080",
    "https": "http://user:pass@proxy.provider.com:8080",
}
r = session.get("https://blocked-site.com/api")
```

## Playwright + proxy

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        proxy={
            "server": "http://proxy.provider.com:8080",
            "username": "user",
            "password": "pass",
        }
    )
    page = browser.new_page()
    page.goto("https://target.com")
```

## Cost estimation guide

Give this to the user when discussing multi-threading + proxies:

```
Estimate your proxy cost:
  - Pages to scrape: N
  - Average response size: ~50KB (typical API JSON)
  - Total data: N × 50KB = X MB = X/1000 GB

Datacenter proxy (Webshare): X/1000 × $2 = ~$Y
Residential proxy (IPRoyal): X/1000 × $7 = ~$Y

Example: 10,000 pages × 50KB = 500MB = 0.5GB
  → Datacenter: ~$1
  → Residential: ~$3.50
```

## Detecting if you need proxies

| Signal | Means |
|--------|-------|
| 429 after N requests | Rate limit — try backoff first, then proxy rotation |
| 403 from first request | IP block (likely datacenter range) → residential proxy |
| 200 but wrong data (different country) | Geo-restriction → geo-targeted proxy |
| Connection timeout | Firewall blocking your IP range → proxy |
| `curl_cffi` still 403 | Not a TLS issue — IP block → proxy |
