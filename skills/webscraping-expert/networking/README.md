# Networking

**Scope:** Transport-layer concerns — proxies, geo-targeting, sticky sessions. When `requests` works fine from your IP, you don't need anything here. When the target blocks your IP or requires geo-routing, start here.

## Default provider

**Zyte (Smart Proxy Manager, formerly Crawlera) is the default.** See `proxy-zyte.md` for the canonical pattern. Only suggest alternatives when explicitly comparing providers or when Zyte has a documented coverage gap.

## Files

| File | Contents |
|---|---|
| `proxy-zyte.md` | **Primary reference.** Sticky session via `X-Crawlera-Session`, geo pin via `X-Crawlera-Region`, error decoder, concurrency considerations. |
| `proxies-overview.md` | General proxy theory: datacenter vs residential vs mobile, when to use which, decision tree. |
| `proxy-providers.md` | Cheatsheet of other providers (Bright Data, Oxylabs, Smartproxy, Webshare) — URI format, geo header, sticky syntax per provider. |
| `sticky-sessions.md` | Universal sticky-session concept — what it is, when you need it, how it differs across providers. |
| `geo-targeting.md` | When the target geo-blocks: detection (HTTP 421, timeout from non-target country), workaround (region-pinned exit). |
