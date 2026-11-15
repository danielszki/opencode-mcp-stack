# Browser Automation Techniques

Advanced Playwright patterns for data extraction when plain HTTP fails.

---

## Technique 1 — Network listener (capture + replicate)

The most powerful technique: let the browser make the real API calls, capture them, then replicate with `requests`. You run the browser once, extract calls for bulk work.

```python
from playwright.sync_api import sync_playwright, Response
import json, time

class NetworkListener:
    """Captures API responses during browser navigation."""

    def __init__(self, url_patterns: list[str]):
        self.patterns = url_patterns
        self.captured: list[dict] = []

    def _matches(self, url: str) -> bool:
        return any(p in url for p in self.patterns)

    def on_response(self, response: Response) -> None:
        if not self._matches(response.url):
            return
        if not response.ok:
            return
        ct = response.headers.get("content-type", "")
        if "json" not in ct:
            return
        try:
            self.captured.append({
                "url": response.url,
                "status": response.status,
                "headers": dict(response.headers),
                "body": response.json(),
            })
        except Exception:
            pass

    def run(self, target_url: str, wait_for: str | None = None) -> list[dict]:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                viewport={"width": 1280, "height": 720},
                locale="en-US",
            )
            page = ctx.new_page()
            page.on("response", self.on_response)

            page.goto(target_url, wait_until="domcontentloaded")

            if wait_for:
                page.wait_for_selector(wait_for, timeout=15_000)
            else:
                page.wait_for_load_state("networkidle")

            # Scroll to trigger lazy loading
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1.5)

            browser.close()

        return self.captured


# Usage: find what API calls are made
listener = NetworkListener(url_patterns=["/api/", "/graphql", "/data"])
calls = listener.run("https://site.com/dashboard")

for call in calls:
    print(call["url"])
    print(json.dumps(call["body"], indent=2)[:200])
```

---

## Technique 2 — Request listener (capture headers for replication)

When you need to replicate auth headers or see the full request, not just the response:

```python
from playwright.sync_api import sync_playwright, Request

def capture_request_details(target_url: str, api_pattern: str) -> list[dict]:
    captured = []

    def on_request(request: Request) -> None:
        if api_pattern not in request.url:
            return
        captured.append({
            "url": request.url,
            "method": request.method,
            "headers": dict(request.headers),
            "post_data": request.post_data,
        })

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.on("request", on_request)
        page.goto(target_url, wait_until="networkidle")
        browser.close()

    return captured

# Now you have everything needed to replicate with requests:
# - headers (incl. Authorization, Cookie, x-api-key)
# - POST body
# - exact URL with query params
details = capture_request_details("https://site.com", "/api/secure-data")
print(details[0]["headers"])
```

---

## Technique 3 — Browser request injection

Use the browser's fetch context to make API calls that require the browser's session state (cookies, tokens embedded in JS runtime):

```python
from playwright.sync_api import sync_playwright

def inject_fetch_in_browser(target_url: str, api_url: str) -> dict:
    """
    Navigate to target_url to establish session, then inject a fetch call
    to api_url from within the browser context (uses browser's cookies/tokens).
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Establish session
        page.goto(target_url, wait_until="networkidle")

        # Inject fetch call using browser's own session state
        result = page.evaluate(f"""
            async () => {{
                const r = await fetch('{api_url}', {{
                    headers: {{
                        'Accept': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest',
                    }},
                    credentials: 'include',  // sends session cookies automatically
                }});
                return await r.json();
            }}
        """)

        browser.close()
        return result

data = inject_fetch_in_browser(
    "https://site.com/dashboard",
    "https://site.com/api/restricted-data?country=DE"
)
```

**When to use injection vs. listening:**
- **Listen** → you want to see what the site calls naturally
- **Inject** → you know the API URL but need the session cookies from a live browser

---

## Technique 4 — Iterating API calls inside browser session

When you need to paginate or call many URLs but must stay within the browser session (tokens embedded in JS that can't be extracted):

```python
from playwright.sync_api import sync_playwright

COUNTRIES = ["DE", "FR", "NL", "BE", "AT"]

def batch_inject_fetches(base_url: str, api_template: str, params: list[str]) -> list[dict]:
    """
    Make multiple API calls from within one browser session.
    Use when the auth token lives only in JS memory (not in cookies).
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(base_url, wait_until="networkidle")

        results = []
        for param in params:
            url = api_template.format(param=param)
            result = page.evaluate(f"""
                async () => {{
                    const r = await fetch('{url}', {{credentials: 'include'}});
                    if (!r.ok) return null;
                    return r.json();
                }}
            """)
            if result:
                results.append({"param": param, "data": result})

        browser.close()
        return results

data = batch_inject_fetches(
    base_url="https://site.com/app",
    api_template="https://site.com/api/country/{param}/stats",
    params=COUNTRIES,
)
```

---

## Technique 5 — Route interception (modify requests in flight)

Playwright can intercept outgoing requests and modify them — useful for adding headers the site normally adds via JS:

```python
from playwright.sync_api import sync_playwright

def fetch_with_modified_headers(url: str, extra_headers: dict) -> list[dict]:
    captured = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Intercept all API calls and add extra headers
        def handle_route(route, request):
            if "/api/" in request.url:
                route.continue_(headers={**dict(request.headers), **extra_headers})
            else:
                route.continue_()

        page.route("**/*", handle_route)

        def capture(response):
            if "/api/" in response.url and response.ok:
                try:
                    captured.append(response.json())
                except Exception:
                    pass

        page.on("response", capture)
        page.goto(url, wait_until="networkidle")
        browser.close()

    return captured
```

---

## Technique 6 — Stealth mode (avoid detection)

Headless Chromium has detectable signals (`navigator.webdriver`, missing plugins, etc.), **but the bigger tell in 2026 is the automation protocol itself** — vanilla Playwright leaks the CDP `Runtime.enable` signal, so a "stealthed" Playwright can still be flagged *because it's Playwright*. Patching navigator properties (the old `playwright-stealth` approach) no longer clears serious anti-bot.

**Use a stealth-native driver instead of patching vanilla Playwright:**

```python
# Preferred for Cloudflare: patchright (Playwright fork, patches CDP leaks)
from patchright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=False)  # real Chrome → real TLS
    page = browser.new_context(locale="en-US").new_page()
    page.goto("https://heavily-protected-site.com")
```

```python
# Preferred for DataDome / behavioral: camoufox (Firefox fork, C-level fingerprint spoof)
from camoufox.sync_api import Camoufox
with Camoufox(headless=False, humanize=True, geoip=True) as browser:
    page = browser.new_page()
    page.goto("https://datadome-protected-site.com")
```

Every technique above (network listener, request/route interception, injection) works unchanged under `patchright` and `camoufox` — they're Playwright-API-compatible. Full decision guide (nodriver vs patchright vs camoufox, CDP `Runtime.enable` leak, CreepJS validation): **`../anti-bot/modern-stealth-browsers.md`**.

> Legacy note: `playwright-stealth`'s `stealth_sync(page)` API was replaced by a `Stealth` class in recent versions and is largely superseded for hard targets. `undetected-chromedriver` is now maintained as **`nodriver`**.

---

## When to use each technique

| Situation | Technique |
|-----------|-----------|
| Don't know what APIs the site calls | Listener (Technique 1) |
| Know the API URL, need auth headers | Request listener (Technique 2) |
| Know the API URL, need browser session | Browser injection (Technique 3) |
| Need to call many URLs in same session | Batch injection (Technique 4) |
| Need to add headers to browser requests | Route interception (Technique 5) |
| Site detects headless | Stealth mode (Technique 6) |
| All above fail | Proxies + headful (non-headless) mode |

---

## Headful mode (last resort against detection)

Some sites detect `headless=True` directly by checking screen resolution, GPU, or Chrome's headless-specific behavior. Run in headful mode (real visible browser) as a last resort:

```python
browser = p.chromium.launch(
    headless=False,  # opens a real browser window
    slow_mo=100,     # adds 100ms delay between actions (more human-like)
)
```

Note: headful requires a display. On a server: use `Xvfb` (virtual framebuffer) or `xvfb-run python script.py`.
