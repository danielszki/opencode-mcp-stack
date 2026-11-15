# Sticky proxy sessions (universal concept)

A "sticky session" pins all your requests through a residential proxy to a **single exit IP** for the duration of the session. Without one, the proxy rotates IPs per request — which breaks any target that ties session cookies, CSRF tokens, or auth state to the client IP.

## When you need a sticky session

- Target uses session cookies (most legacy apps — ASP.NET, ColdFusion, JSP)
- Target uses CSRF / VIEWSTATE / `_token` style anti-forgery
- Target uses Cloudflare cookie cf_clearance (tied to IP)
- Target geo-blocks: a rotating proxy whose IPs occasionally land outside the allowed region will fail intermittently
- Any time changing IP mid-session produces HTTP 421, 403, or 200+Error

If your target is a simple JSON API with no cookies, you usually don't need sticky — rotating IPs is fine.

## How providers implement it

The mechanism varies but the semantics are the same. To create a session: ask the proxy for one. To reuse it: include the session ID in subsequent requests.

| Provider | How to start session | How to pin follow-ups |
|---|---|---|
| **Zyte / Crawlera** | Send header `X-Crawlera-Session: create` on first request; capture returned SID | Send `X-Crawlera-Session: <SID>` on follow-ups |
| Bright Data | Username suffix `-session-<random_id>` (you generate the ID) | Same suffix on follow-ups |
| Oxylabs | Username suffix `-sessid-<id>` | Same suffix |
| Smartproxy | Username suffix `-session-<id>` | Same suffix |
| Webshare | No explicit sticky on basic plan; same IP if you reuse the same proxy endpoint | N/A |

For the Zyte playbook in full, see `proxy-zyte.md`.

## Session TTL

Sticky sessions have a TTL — usually 10-30 minutes of inactivity, sometimes 1-2 hours total. After expiry the session ID returns an error (per provider — see decoder in `proxy-zyte.md`).

For long-running crawls (hours), refresh the session opportunistically:
- After every page batch
- After any 5xx response
- Periodically by wall-clock time (every ~20 min)

## How many sessions

- **One global session** for stateful flows (search → paginate → detail). All requests must share the same exit IP.
- **One session per worker** if you parallelize multiple independent search flows. They can each have their own session.
- **Avoid**: one session per request. That defeats the point — you're back to rotating IPs.

Concurrent fetches **within** a single session (e.g. parallel detail fetches in a paginated crawl) are fine; they share the same session ID and exit IP. See `../reliability/concurrency-curl-cffi.md`.

## Cost considerations

Sticky sessions don't cost extra at most providers, but they reduce your effective rotation. If a target rate-limits by IP at 100 req/min, a single sticky session can never exceed that — even with 50 concurrent threads.

Solutions:
- Use multiple parallel sticky sessions (each its own session ID)
- Refresh sessions more aggressively to land on different IPs

## Related

- `proxy-zyte.md` — full Zyte sticky session playbook
- `proxy-providers.md` — cross-provider cheatsheet
- `../reliability/concurrency-curl-cffi.md` — sharing a session across threads
- `../anti-bot/error-decoders.md` — what each provider's "session expired" error looks like
