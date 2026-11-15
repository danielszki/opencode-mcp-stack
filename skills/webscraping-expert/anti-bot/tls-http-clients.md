# TLS / HTTP Fingerprint Clients (the 2026 landscape)

`curl_cffi` is the skill's default, but it is no longer the only serious option. Several Rust-backed clients now match or beat it on speed and fingerprint fidelity. This file is the map: what each client is, when to reach for it, and the gotchas.

**The core idea (unchanged):** Python's `requests`/`httpx`/`aiohttp` all use the system OpenSSL stack, which emits a distinctive TLS ClientHello (JA3/JA4) and HTTP/2 SETTINGS/frame order (the Akamai HTTP/2 fingerprint). Bot-detection vendors keep databases of these and flag them instantly. A fingerprint client reproduces a real browser's handshake byte-for-byte so the network layer looks like Chrome/Safari/Firefox.

---

## Decision table

| Client | Engine | Impersonation | Async | Speed | Use when |
|---|---|---|---|---|---|
| **curl_cffi** | libcurl (curl-impersonate, lexiforest fork) | JA3/JA4 + HTTP/2 + header order | ✅ `AsyncSession` | Fast | **Default.** Broadest profile list, easiest drop-in, best docs. |
| **primp** | Rust (`rquest`) | JA3/JA4 + HTTP/2 | ✅ | Fastest | You want max throughput and a `requests`-like API; formerly `pyreqwest-impersonate`. |
| **rnet** | Rust (`wreq`/reqwest-impersonate) | JA3/JA4 + HTTP/2, rich browser emulation | ✅ (native async) | Fastest | Async-heavy pipelines, fine-grained emulation, HTTP/2 tuning. |
| **tls-client** | Go (bogdanfinn) via bindings | Low-level TLS knobs, extension ordering | ⚠️ | Fast | You need to hand-tune the fingerprint (custom cipher/extension order) below what curl_cffi exposes. |
| **impit** | Rust (Apify) | Browser impersonation, "made simple" | ✅ | Fast | Apify ecosystem; simple API. |

Rule of thumb: **start with curl_cffi.** Only switch to primp/rnet when profiling shows the HTTP client is your bottleneck, or when curl_cffi's profile for your target browser is stale and primp/rnet has a fresher one.

---

## curl_cffi — profiles are the thing that goes stale

The library is actively maintained (lexiforest fork; `curl_cffi` 0.11.x line). **Do not hardcode an old Chrome number.** Fingerprints rot: as real Chrome advances, sites raise their floor and an old `chrome124` starts looking anomalous.

**Use the generic aliases** so you always ride the latest shipped profile:

```python
from curl_cffi import requests

# Preferred: generic aliases auto-select the newest profile the installed version ships
r = requests.get(url, impersonate="chrome")          # newest Chrome
r = requests.get(url, impersonate="safari")           # newest Safari
r = requests.get(url, impersonate="firefox")          # newest Firefox
r = requests.get(url, impersonate="chrome_android")   # newest Chrome on Android
r = requests.get(url, impersonate="safari_ios")       # newest Safari on iOS
```

**Profiles available in the current line** (pin a specific one only when a site fingerprints a known-good older build):

```
chrome:   chrome110, chrome116, chrome119, chrome120, chrome123, chrome124,
          chrome131, chrome133a, chrome136, chrome142, chrome145, chrome146
safari:   safari153, safari155, safari170, safari180, safari184, safari260, safari2601
safari_ios: safari172_ios, safari180_ios, safari184_ios, safari260_ios
firefox:  firefox133, firefox135, firefox144, firefox147
mobile:   chrome99_android, chrome131_android
other:    edge99, edge101, tor145
```

- The **`a` suffix** (e.g. `chrome133a`) is an *alternative* fingerprint observed in the wild from Chrome A/B testing — not an official browser build. Try it when the plain number is blocked.
- Check what your installed version actually supports:
  ```python
  from curl_cffi import requests
  print(requests.BrowserTypeLiteral.__args__)   # or read the docs' targets page for your version
  ```
- Keep `curl_cffi` itself updated (`uv pip install -U curl_cffi`) — new browser targets ship in new releases.

**Rotate profiles as a fallback ladder**, but bias toward the latest:

```python
from curl_cffi import requests

PROFILES = ["chrome", "safari", "firefox", "chrome136", "chrome131"]

def fetch(url, **kw):
    last = None
    for p in PROFILES:
        try:
            r = requests.get(url, impersonate=p, timeout=30, **kw)
            if r.status_code == 200:
                return r
            last = r
        except Exception as e:
            last = e
    raise RuntimeError(f"All impersonation profiles failed (last: {last})")
```

---

## primp — the fast drop-in

```python
import primp

client = primp.Client(impersonate="chrome_131", impersonate_os="macos")
r = client.get("https://site.com/api")
print(r.status_code, r.json())
```

- Python binding to the Rust `rquest` engine. Consistently benchmarks as the fastest impersonating client.
- API is close to `requests`. Impersonation targets use an underscore style (`chrome_131`, `safari_18`); also takes `impersonate_os`.
- Was renamed from `pyreqwest-impersonate` → **`primp`**. If you find old `pyreqwest_impersonate` imports, they're the same lineage.

## rnet — async-native, rich emulation

```python
import asyncio, rnet

async def main():
    client = rnet.Client(impersonate=rnet.Impersonate.Chrome131)
    resp = await client.get("https://site.com/api")
    print(resp.status, await resp.text())

asyncio.run(main())
```

- Rust-backed (same lineage as `reqwest-impersonate`/`wreq`). Native async, HTTP/2 control, browser emulation beyond just TLS.
- Reach for it in high-concurrency async crawlers where you'd otherwise wrap curl_cffi's `AsyncSession`.

## tls-client — when you must hand-tune

```python
import tls_client

session = tls_client.Session(
    client_identifier="chrome_133",
    random_tls_extension_order=True,   # extra entropy vs. a static fingerprint
)
r = session.get("https://site.com/api")
```

- Go port (bogdanfinn) with Python bindings. Exposes low-level TLS: custom cipher suites, explicit extension ordering, forced HTTP/2 settings.
- Use only when curl_cffi's canned profile isn't granular enough. Otherwise it's more rope than you need.

---

## HTTP/3 / QUIC is the next frontier

Fingerprinting is moving to **HTTP/3 over QUIC**. A growing number of sites negotiate h3, and the QUIC handshake has its own fingerprintable shape. Most Python impersonation clients are still HTTP/1.1 + HTTP/2 only.

- **Practical stance today:** stay on HTTP/2 — sites still serve it, and h3 is opt-in via `Alt-Svc`. If a target *forces* h3 or behaves differently over h3, you currently need a real browser (Chromium speaks h3 natively) rather than an HTTP client.
- **Exception:** **Scrapling's `Fetcher.get(url, http3=True)`** already exposes HTTP/3 from Python (see `reference/scrapling.md`) — a genuine edge when a site treats h3 clients differently.
- Watch `curl_cffi`/`rnet` releases for QUIC impersonation; it's the obvious next capability.

---

## Gotchas

- **A fingerprint client fixes the network layer only.** It sends no JavaScript execution, no canvas/WebGL, no behavioral signals. Against Cloudflare-managed-challenge/DataDome/Kasada it gets you a clean TLS handshake and then a challenge page. See `anti-bot/anti-bot-vendors.md`.
- **Match headers to the profile.** Impersonating `chrome146` while sending a `chrome/124` `User-Agent` and mismatched `sec-ch-ua` is a tell. curl_cffi sets sane defaults; if you override headers, keep them consistent with the chosen profile.
- **Proxies + impersonation compose** — pass `proxies=` exactly as with `requests`. See `networking/`.
- **Profile availability is version-locked.** `chrome146` won't exist in an old curl_cffi. Upgrade the lib, don't downgrade your target.

---

## Related

- `anti-bot/browser-impersonation.md` — curl_cffi deep dive, JA3/JA4 explainer
- `anti-bot/anti-bot-vendors.md` — what each vendor checks; where TLS alone stops working
- `anti-bot/modern-stealth-browsers.md` — when you need a real browser (nodriver/patchright/camoufox)
- `reference/libraries.md` — the full library map
