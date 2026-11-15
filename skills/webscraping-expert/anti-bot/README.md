# Anti-bot

**Scope:** Bypassing protections at the HTTP / TLS layer. CAPTCHAs, fingerprinting, rate limits, ban diagnosis.

When `requests` works fine, skip this folder. When it returns 403, Cloudflare challenge, or anything looking like detection, start here.

## Escalation order

1. Realistic headers (Referer, sec-ch-ua, User-Agent) — see `error-decoders.md`
2. TLS/HTTP fingerprint impersonation (`curl_cffi`, or faster `primp`/`rnet`) — see `browser-impersonation.md`, `tls-http-clients.md`
3. **Identify the vendor and whether it's a WAF/IP block or a JS challenge** — see `anti-bot-vendors.md`, `ban-detection.md`
4. Real stealth browser for JS challenges (`patchright` / `camoufox` / `nodriver`) — see `modern-stealth-browsers.md`
5. CAPTCHA/token solver if it's a CAPTCHA (Turnstile/DataDome/reCAPTCHA) — see `captcha-solvers.md`
6. Probe protection gaps before paid escalation (suffix/format variants, sibling routes, other hosts, feeds, exports) — see `protection-gaps.md`
7. Managed unblocker for the hardest walls (Zyte API / Web Unlocker) — see `../networking/proxy-providers.md`

## Files

| File | Contents |
|---|---|
| `tls-http-clients.md` | The 2026 impersonation-client landscape: `curl_cffi` (profiles + generic aliases), `primp`, `rnet`, `tls-client`, HTTP/3 note. When to use which. |
| `browser-impersonation.md` | `curl_cffi` deep dive: TLS fingerprinting (JA3/JA4), `impersonate` profiles (use `chrome`/`safari`/`firefox` aliases, not old pins), alternatives. |
| `modern-stealth-browsers.md` | `nodriver` vs `patchright` vs `camoufox` vs `botasaurus`; the CDP `Runtime.enable` leak; CreepJS validation; behavioral signals. |
| `anti-bot-vendors.md` | Per-vendor detection matrix (Cloudflare/DataDome/Akamai/Kasada/PerimeterX/F5) + bypass per vendor; the WAF-block-vs-JS-challenge diagnosis. |
| `ban-detection.md` | Diagnose WHY you got blocked before trying to bypass. 403/429/Cloudflare/CAPTCHA/IP-ban decision tree. |
| `error-decoders.md` | Symptom → cause → fix table for non-obvious responses: HTTP 421 Misdirected, `200 OK + Error page`, provider-specific error headers. |
| `protection-gaps.md` | Surfaces the anti-bot rules do not cover: suffix/format variants (`.js` first; `.rss`/`.json` where the site publishes them), sibling XHRs, other hosts and API versions, feeds, exports. A runnable probe (JSONL evidence, per-vendor challenge detection, robots.txt check) to run before paid escalation, plus the sign-off rule: intended-public routes are fine, unintended ones need sign-off, origin bypass is a hard limit. |
| `captcha-solvers.md` | Identifying CAPTCHA type, compatibility tables for CapSolver / 2Captcha (incl. Turnstile / DataDome / AWS-WAF), integration code, 2026 pricing. |
