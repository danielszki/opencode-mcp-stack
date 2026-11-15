# Browser Automation

**Scope:** When HTTP requests alone are not enough. Use a real browser to: solve a JS challenge, harvest authenticated cookies, capture XHR requests you couldn't otherwise predict, or click through a flow that has no API equivalent.

**Always prefer HTTP first** (see `../discovery/` and `../site-patterns/`). Browsers are slow, fragile, expensive, and easier to detect than a well-impersonated HTTP client.

## When you genuinely need a browser

| Need | File |
|---|---|
| Capture an auth token / session cookie, then continue with cheap HTTP | `browser-bootstrap-handoff.md` |
| Capture XHR requests to reverse-engineer an API | `browser-techniques.md` (network listener, route interception) |
| Persist cookies across runs (avoid re-logging in) | `session-cache.md` |
| Site needs JS execution + behavioral signals (mouse, timing) | `browser-techniques.md` (stealth mode section: `playwright-stealth`, `patchright`) |

## Files

| File | Contents |
|---|---|
| `browser-techniques.md` | Request injection, network listener, route interception, stealth mode tricks. |
| `browser-bootstrap-handoff.md` | Use a real browser once to clear a challenge / capture a session token, then hand cookies + headers off to a cheap HTTP client for bulk work. |
| `session-cache.md` | Cookie/session JSON cache with TTL; auto-harvest fresh cookies via headless browser when expired. |
