# Error decoders

Symptom → cause → fix table for non-obvious responses. When a scrape fails in a way that doesn't match the textbook 403/429/500, find the symptom here before guessing.

## HTTP 421 Misdirected Request

**Symptom:** Target returns `HTTP 421 Misdirected Request` with no clear error message.

**Cause:** TLS / SNI / certificate mismatch. The target's CDN received a request for a hostname it doesn't serve on the connection used. Two typical scenarios:

1. **HTTP/2 connection coalescing** — your HTTP client reused a connection that the CDN considers stale or for a different hostname.
2. **Proxy rotated IPs mid-session** — your previous request went through Tokyo, this one through Frankfurt, and the target's CDN won't serve content cross-region for security/contractual reasons.

**Fix:**
- If proxied: pin a sticky proxy session BEFORE the first TLS handshake. See `../networking/proxy-zyte.md`.
- If using HTTP/2: force HTTP/1.1 for the affected host (in `curl_cffi`, set `default_headers={"Connection": "close"}`).
- If hitting consistently: ensure your proxy region matches the target's expected geo.

## HTTP 200 + "Error" page in HTML

**Symptom:** Status `200 OK`, but the response body is an error page (often titled "Error" or "Application Error").

**Cause:** Server-side rejection without proper HTTP status. The handler caught an exception (invalid session, expired CSRF token, missing referer, stateful nav skipped) and returned a generic error template instead of a 4xx/5xx.

**Detection:**
```python
from bs4 import BeautifulSoup

def is_silent_error(html: str) -> bool:
    soup = BeautifulSoup(html, "html.parser")
    title = (soup.title.string if soup.title else "").strip().lower()
    if title in ("error", "application error", "exception"):
        return True
    if soup.find("div", id=lambda x: x and "ErrorPanel" in (x or "")):
        return True
    return "aspxerrorpath" in html.lower()[:5000]
```

**Fix:** Re-boot the full navigation sequence. Common root causes:
- Session cookie expired
- Stale VIEWSTATE / EVENTVALIDATION
- Missing `Referer` header
- Tried to fetch a stateful detail page (numeric ID) without going through the search flow
- Stateful internal ID belongs to a previous session — re-search and re-collect

See `../site-patterns/legacy-cms.md` and `../site-patterns/aspnet-webforms.md` for stack-specific context.

## HTTP 503 with `x-crawlera-error: internal_server_error`

**Symptom:** Through Zyte proxy, target responds 503 with header `x-crawlera-error: internal_server_error`. Response body is empty.

**Cause:** Zyte couldn't allocate an exit IP in the requested region. Either the pool is exhausted momentarily, your plan doesn't cover the geo, or `X-Crawlera-Region` has an invalid value.

**Fix:**
- Verify `X-Crawlera-Region` is a valid ISO 3166 alpha-2 country code, uppercase (e.g. `AU`, `US`, `DE`).
- Check Zyte plan covers the geo (dashboard).
- Retry — the pool may refill in seconds.

See `../networking/proxy-zyte.md` for the full decoder.

## HTTP 503 with `x-crawlera-error: bad_session_id`

**Symptom:** 503 from Zyte, header `x-crawlera-error: bad_session_id`.

**Cause:** Your sticky session ID expired or never existed (sessions are TTL-limited, ~30 min default).

**Fix:** Drop the stale SID, send `X-Crawlera-Session: create` again to get a fresh one, then re-boot the navigation. Old session cookies on the target may also be invalid — clear them.

## HTTP 407 Proxy Authentication Required

**Symptom:** Proxy returns 407.

**Cause:** Bad credentials in your proxy URL.

**Fix:** Verify the username/password format for your provider. Common gotchas:
- Username might need a suffix (`user-session-12345`, `user-country-AU`, etc.) depending on provider
- Password might contain URL-special characters (`/`, `@`, `:`) and need encoding
- Check the literal `PROXY_URL` env var is loaded correctly (not empty, not pointing at the wrong endpoint)

## HTTP 429 with empty `Retry-After`

**Symptom:** 429 Too Many Requests, no `Retry-After` header.

**Cause:** Target rate-limit triggered but doesn't expose the backoff.

**Fix:** Treat as an exponential-backoff retry: 5s, 15s, 30s, 60s, then give up. If you hit it repeatedly:
- Reduce concurrency
- Add `random.uniform(0.3, 0.8)` sleep between sequential requests
- Rotate sticky session to force a different exit IP

## Connection timeout (no response at all)

**Symptom:** `curl: (28) Operation timed out` or Python `requests.Timeout`.

**Causes (in order of likelihood):**
1. **Geo-block:** Your IP is not in a country the target accepts. Often correlates with "site works fine in browser when you're in country X, fails everywhere else."
2. **IP ban:** Your IP was blocked by the target's WAF. Different from rate limit — typically connection-refused or silent timeout rather than 403.
3. **Network issue:** Your egress is broken (rare in normal infra).

**Differentiating:**
```bash
# Test 1: can you reach the host at all?
curl -v --max-time 10 https://target.example.com/  # if "Connecting to ..." stalls, network issue

# Test 2: does it work from a different IP?
curl -v --max-time 10 https://target.example.com/ --proxy <known-good-proxy>
```

If the proxy works but direct fails: geo-block or IP ban. Use a proxy.
If proxy ALSO times out: target is down, or your proxy egress is bad too.

## HTTP 403 with Cloudflare HTML body

**Symptom:** 403, response body contains "Cloudflare" / "checking your browser" / `cf-ray:` header.

**Cause:** Cloudflare's bot detection rejected your client. Most common at the TLS-fingerprint layer (JA3/JA4).

**Fix:**
1. Switch from `requests` to `curl_cffi` with `impersonate="chrome"` (see `browser-impersonation.md`)
2. If still 403: try `safari17_0` or `firefox121` impersonation profile
3. If still 403: residential proxy required
4. If still 403: Cloudflare has a JS challenge → need a headful browser (see `../browser-automation/`)

## HTTP 403 with response body mentioning "your IP"

**Symptom:** 403, body text references the user's IP or "your network".

**Cause:** IP-level ban — datacenter IP range blocked, or specific IP burnt from prior bursts.

**Fix:** Switch to residential proxy. Datacenter proxies usually share the same fate. See `../networking/proxy-zyte.md`.

## Aura `aura:fwuidNotFound` / `ClientOutOfSync`

**Symptom:** Salesforce Aura endpoint returns `{"actions": [{"state": "INCOMPLETE", "error": [{"exceptionType": "aura:ClientOutOfSync"}]}]}`.

**Cause:** Hardcoded `fwuid` no longer matches the deployed Salesforce framework version (Salesforce auto-upgrades orgs every few weeks).

**Fix:** Re-fetch `fwuid` from a live page. See `../site-patterns/salesforce-experience-cloud.md`.

## Response body is HTML when JSON expected

**Symptom:** You posted to a JSON endpoint, got HTML back.

**Cause:** One of:
- Session expired — server redirected to login (often with 302 swallowed by your client)
- Wrong endpoint URL (typo)
- Auth header missing
- Target deployed a maintenance page

**Fix:** Inspect the first 1000 chars of the body:
- `<html...><head><title>Login...` → re-authenticate
- `<html...><head><title>Maintenance...` → wait
- HTML with same structure as the home page → wrong endpoint
- Empty body or garbage → check headers/encoding

## Response contains data but `len(records) == 0`

**Symptom:** API returned 200 with valid JSON, but `records` is empty. Same request in browser returns data.

**Causes:**
- Missing required header (very often `Referer` or `Origin`)
- Missing required cookie set by an earlier page load
- Different filter defaults applied — your request implicitly filters to "today only" instead of the user's view
- Server bug where empty result is returned for unauthenticated requests with no error

**Fix:** Diff your request headers/cookies against the real browser request (HAR file). The smallest missing piece is usually the cause.

## Related

- `ban-detection.md` — broader diagnosis flowchart
- `../networking/proxy-zyte.md` — Zyte-specific error semantics
- `../site-patterns/legacy-cms.md` — "200 + Error" deep dive
- `../site-patterns/aspnet-webforms.md` — VIEWSTATE / EVENTVALIDATION rejections
