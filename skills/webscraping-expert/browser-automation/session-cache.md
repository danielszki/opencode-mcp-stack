# Session & Cookie Cache

## Why cache sessions

- Cookies from a browser login expire. Re-logging in for every run is slow and detectable.
- Saved sessions allow resuming without a browser login for hours/days.
- Never hardcode credentials in code — store the session artifact (cookies), not the password.

---

## Standard session cache (JSON file, no SQLite)

```
data/{source}/
└── raw/
    └── source/
        └── .session_cache.json   ← hidden file, not committed to git
```

```python
import json, time
from pathlib import Path
import requests

SESSION_CACHE_VERSION = 1

class SessionCache:
    def __init__(self, cache_path: Path):
        self.path = cache_path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict | None:
        if not self.path.exists():
            return None
        try:
            data = json.loads(self.path.read_text())
            if data.get("version") != SESSION_CACHE_VERSION:
                return None
            if data.get("expires_at") and time.time() > data["expires_at"]:
                print("Session cache expired.")
                return None
            return data
        except Exception:
            return None

    def save(self, cookies: dict, headers: dict = {}, ttl_seconds: int = 3600 * 8) -> None:
        self.path.write_text(json.dumps({
            "version": SESSION_CACHE_VERSION,
            "saved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "expires_at": time.time() + ttl_seconds,
            "cookies": cookies,
            "headers": headers,
        }, indent=2))
        print(f"Session cached (valid for {ttl_seconds//3600}h).")

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()
            print("Session cache cleared.")

    def apply_to_session(self, session: requests.Session) -> None:
        data = self.load()
        if not data:
            return
        session.cookies.update(data.get("cookies", {}))
        session.headers.update(data.get("headers", {}))
        print("Session restored from cache.")
```

---

## Cookie harvester via browser

Captures cookies from a real browser login and saves to cache:

```python
from playwright.sync_api import sync_playwright

def harvest_session(
    login_url: str,
    username: str,
    password: str,
    cache: SessionCache,
    *,
    username_selector: str = "input[name='username']",
    password_selector: str = "input[name='password']",
    submit_selector: str = "button[type='submit']",
    wait_for_selector: str | None = None,
    ttl_seconds: int = 3600 * 8,
    extra_headers: dict = {},
) -> None:
    """
    Open browser, log in, extract cookies + auth headers, save to cache.
    Close browser immediately after — no further browser use needed.
    """
    captured_headers: dict = {}

    def intercept(response):
        # Grab any Bearer token or API key from JSON auth responses
        if response.ok and "json" in response.headers.get("content-type", ""):
            try:
                body = response.json()
                token = body.get("access_token") or body.get("token") or body.get("jwt")
                if token:
                    captured_headers["Authorization"] = f"Bearer {token}"
            except Exception:
                pass

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # headful avoids bot detection
        ctx = browser.new_context()
        page = ctx.new_page()
        page.on("response", intercept)

        page.goto(login_url, wait_until="domcontentloaded")
        page.fill(username_selector, username)
        page.fill(password_selector, password)
        page.click(submit_selector)

        if wait_for_selector:
            page.wait_for_selector(wait_for_selector, timeout=15_000)
        else:
            page.wait_for_load_state("networkidle")

        cookies = {c["name"]: c["value"] for c in ctx.cookies()}
        browser.close()

    cache.save(
        cookies=cookies,
        headers={**captured_headers, **extra_headers},
        ttl_seconds=ttl_seconds,
    )


def get_authenticated_session(
    cache: SessionCache,
    login_url: str,
    username: str,
    password: str,
    **login_kwargs,
) -> requests.Session:
    """Return a session, using cache if valid or harvesting fresh cookies."""
    session = requests.Session()

    cached = cache.load()
    if cached:
        session.cookies.update(cached.get("cookies", {}))
        session.headers.update(cached.get("headers", {}))
        print("Using cached session.")
    else:
        print("No valid session cache. Harvesting via browser...")
        harvest_session(login_url, username, password, cache, **login_kwargs)
        cache.apply_to_session(session)

    return session
```

---

## Detecting session expiry during extraction

When a session expires mid-extraction, the site usually returns a redirect to `/login` or a 401/403. Detect and refresh:

```python
class SessionAwareExtractor:
    def __init__(self, cache: SessionCache, login_url: str, username: str, password: str):
        self.cache = cache
        self.login_url = login_url
        self.username = username
        self.password = password
        self.session = get_authenticated_session(cache, login_url, username, password)

    def _is_session_expired(self, response: requests.Response) -> bool:
        # Common signals of expired session
        if response.status_code in (401, 403):
            return True
        if response.url and "login" in response.url.lower():
            return True
        if "text/html" in response.headers.get("content-type", "") and response.status_code == 200:
            # Got HTML instead of JSON — likely redirected to login page
            return b"login" in response.content[:500].lower()
        return False

    def get(self, url: str, **kwargs) -> requests.Response:
        response = self.session.get(url, timeout=30, **kwargs)

        if self._is_session_expired(response):
            print("Session expired. Refreshing...")
            self.cache.clear()
            self.session = get_authenticated_session(
                self.cache, self.login_url, self.username, self.password
            )
            response = self.session.get(url, timeout=30, **kwargs)

        response.raise_for_status()
        return response
```

---

## .gitignore for session files

Always add to `.gitignore`:
```
.session_cache.json
**/source/.session_cache.json
*.session.json
```

---

## File organization

```
data/{source}/
└── raw/
    └── source/
        ├── .session_cache.json    ← cookies + headers (gitignored)
        └── checkpoint.json        ← extraction progress
```

The session cache is co-located with the source data so it's clear which session belongs to which source.
