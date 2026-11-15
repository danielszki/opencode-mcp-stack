# Browser bootstrap → HTTP handoff

A cost-optimization pattern: spin up a real browser **once** to clear an initial challenge (JS-rendered cookies, anti-bot probe, Cloudflare Turnstile, opaque session token), capture the resulting cookies/headers, then close the browser and do all subsequent requests with a cheap HTTP client (`curl_cffi`, `httpx`, `requests`).

Browsers are expensive — RAM, startup time, parallelism caps, detection surface. HTTP clients are cheap. When the site's protection only fires on the initial page load (or on a specific "Accept terms" page) and the actual data endpoints are plain JSON, this pattern gets you the best of both worlds.

## When this applies

Look for one of these signals — when the site exhibits *any* of them, this pattern is likely to work:

- The first GET returns a JS-only challenge page (rotating script, encrypted cookie, "Checking your browser" interstitial); subsequent requests with the cookie set behave normally
- Initial entry sets an opaque session token cookie (`__cf_bm`, `incap_ses_*`, `_abck`, `XSRF-TOKEN`, custom session ID) that the API endpoint requires; once you have it, the API doesn't re-challenge
- Terms-of-service / age-gate page must be POST-accepted (`__doPostBack` style or a button click) before data endpoints are reachable
- A custom session header or CSRF token written to the DOM by JS must be captured live, but doesn't expire for the session's lifetime
- TLS / fingerprinting passes via the real Chrome — useful when `curl_cffi` impersonation alone isn't enough but a manual cookie copy is

If the protection re-challenges on every request, or if data is computed client-side after a JS pipeline, this pattern won't work — use full browser automation instead (`browser-techniques.md`).

## Pattern

Three stages: **bootstrap** in a real browser, **handoff** the cookies/headers to an HTTP client, **bulk** all data requests via HTTP.

```python
from playwright.sync_api import sync_playwright
from curl_cffi import requests as cffi_requests

def bootstrap_session(entry_url: str) -> dict:
    """Drive a real browser through the initial challenge and return the
    cookies + extra headers needed to replay as cheap HTTP."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        page = context.new_page()

        # Capture any custom session header the server emits in a response
        captured_headers: dict[str, str] = {}
        def on_response(resp):
            for h_name in ("x-example-session", "x-example-csrf"):
                if v := resp.headers.get(h_name):
                    captured_headers[h_name] = v
        page.on("response", on_response)

        page.goto(entry_url, wait_until="networkidle", timeout=60_000)
        # Optional: dismiss a terms-accept modal, click into the data section, etc.
        # page.click("button:has-text('Accept')")
        # page.wait_for_selector(".search-form", timeout=30_000)

        cookies = context.cookies()
        ua = page.evaluate("navigator.userAgent")
        browser.close()

    return {
        "cookies": {c["name"]: c["value"] for c in cookies},
        "user_agent": ua,
        "extra_headers": captured_headers,
    }

def bulk_fetch(api_url: str, session_state: dict, params: dict | None = None):
    """Use the cheap HTTP path with the captured state."""
    return cffi_requests.get(
        api_url,
        cookies=session_state["cookies"],
        headers={
            "User-Agent": session_state["user_agent"],
            **session_state["extra_headers"],
        },
        params=params,
        impersonate="chrome",
        timeout=60,
    )
```

## Choosing what to capture

Three things travel from browser → HTTP client:

1. **Cookies.** Always. Both first-party and third-party (some challenges set cookies on a CDN domain).
2. **User-Agent.** Read from `navigator.userAgent` rather than hardcoding — some challenges check it.
3. **Custom headers.** Anything the server returned that the JS subsequently reads and echoes back. Discover via `page.on("response")` or by inspecting the post-challenge XHR calls in a HAR.

Do NOT carry over: the full Playwright `localStorage` (the HTTP client can't replicate runtime JS state), service workers, or browser fingerprint state. If the API ends up needing those, the pattern doesn't apply and you need full browser automation.

## When session lifetime matters

Captured sessions expire. Strategies depending on how long:

- **Long-lived (hours+):** bootstrap once at the start of a run, scrape everything in one session, dispose. This is the common case.
- **Medium (~30 min, e.g. Cloudflare `__cf_bm`):** bootstrap, scrape until 4xx, re-bootstrap. Wrap the HTTP fetch in retry logic that re-runs `bootstrap_session()` on 403/401.
- **Short or per-page:** if every page requires a fresh challenge, the pattern saves no money — go full browser.

To detect mid-run expiry, watch for the HTTP client suddenly getting the original challenge HTML back (instead of JSON), or 403/401 responses that succeed after a fresh bootstrap.

## Parallelization

A captured session can usually be reused across **threads** (the cookies + headers are stateless from the server's perspective). But:

- Most sites bind the session to the **IP** that ran the bootstrap. Run all HTTP requests through the same proxy/IP that ran the browser, not a rotating pool.
- A few sites bind the session to a specific server-side **session ID** that allows N concurrent requests max (often 1 or 5). When you hit the cap, you get serialized 5xx errors. Test parallelism with a small batch before scaling.
- If you need true horizontal scale, run **multiple browser bootstraps** in parallel (each on a distinct sticky IP) and pool their captured sessions.

## Gotchas

- **Cookies have an `expires` field — respect it.** A session captured at noon with cookies expiring at 1pm will silently start failing at 1pm. Read `c["expires"]` and refresh before then.
- **Some cookies are `httpOnly` and won't appear in `document.cookie`** — but Playwright's `context.cookies()` returns them. If you're tempted to read cookies via JS evaluation, you'll miss the important ones. Use the context API.
- **Headless detection happens during bootstrap.** Stock Playwright Chromium is detectable (`navigator.webdriver === true`). Use `patchright`, `playwright-stealth`, or `playwright.chromium.launch_persistent_context(channel="chrome")` to defeat the common probes. See `browser-techniques.md`.
- **The browser may add headers your HTTP client doesn't.** `Sec-Fetch-Site`, `Sec-Ch-Ua`, `Accept-Language` — these are set automatically by Chrome and a server can require them. `curl_cffi`'s `impersonate="chrome"` reproduces the common set; if the API still 403s, capture the real headers from the post-challenge XHR call in the HAR and copy them verbatim.
- **TLS fingerprint mismatch is the silent killer.** The bootstrap browser presents Chrome's JA3/JA4 fingerprint; `requests` or `httpx` present Python's. Some anti-bot stacks (notably Akamai) record the JA3 of the request that set the cookie and reject subsequent requests with a different JA3 carrying the same cookie. Always use `curl_cffi.requests` with `impersonate="chrome<version>"` matching the browser version, not plain `httpx`.
- **JavaScript challenge re-fires after navigation.** Cookies set on `/login` may not be valid for `/api/v1/data` if the challenge runs per-path. Bootstrap by visiting the *deepest* URL you can without auth, not just the home page.
- **Re-bootstrap cost adds up.** If the session expires every 5 minutes and you re-bootstrap each time, the savings vanish. Profile end-to-end before committing to this pattern.

## Related

- `browser-techniques.md` — full browser automation; use when this handoff doesn't work
- `session-cache.md` — caching the captured session between runs to avoid re-bootstrapping when the cookies are still valid
- `../anti-bot/error-decoders.md` — recognizing when a 4xx means "your session expired" vs "the API really rejected you"
- `../networking/sticky-sessions.md` — pinning HTTP requests to the same IP that ran the bootstrap
