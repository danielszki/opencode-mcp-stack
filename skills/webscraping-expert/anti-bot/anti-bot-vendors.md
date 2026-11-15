# Anti-Bot Vendors — what each one checks, and how to get past it

Not all bot walls are the same. Each major vendor *weights different signals*, so the winning move differs per vendor. Identify the vendor first (fingerprints below), then apply the matching approach. Guessing wastes the cheapest attempts.

**The one rule that saves the most time:** distinguish a **WAF/IP block** from a **JS challenge**. They look similar (both often HTTP 403) but need opposite fixes — see the last section.

---

## Detection-weighting matrix (2026)

| Vendor | Primary signal it weights | TLS fingerprint alone enough? | What actually gets past it |
|---|---|---|---|
| **Cloudflare** | TLS/JA4 + global ML reputation; Turnstile for challenge | Often yes for Bot Fight Mode / basic | `curl_cffi` (latest profile) + good IP; managed challenge → real browser (patchright) or `cf_clearance` harvest; Turnstile → solver |
| **DataDome** | Per-site *behavior* + IP reputation; JS challenge issues the `datadome` cookie | **No** — needs JS execution for the `dd`/`datadome` cookie | camoufox (`humanize`) + residential proxy + warm session; or DataDome-capable solver; or managed unblocker |
| **Akamai Bot Manager** | Browser *execution* / sensor data (`_abck`, `bm_sz` cookies) | No | Real browser that generates valid sensor data; managed unblocker; sensor-data solver |
| **Kasada** | Proof-of-work + JS integrity (`x-kpsdk-ct`/`-cd`) | No | Solve/execute the PoW (specialist solvers) or managed unblocker; hardest OSS target |
| **PerimeterX / HUMAN** | Network effect + behavior (`_px*` cookies) | No | Behavioral browser (camoufox) + residential proxy; PX-capable solver |
| **F5 / Shape / Distil** | Token validity via a proprietary JS VM | No | Real browser; token generation is VM-obfuscated — usually a managed service |
| **Imperva / Incapsula** | `___utmvc`/`incap_ses` cookies, JS challenge | Sometimes | `curl_cffi` + IP; else real browser |
| **AWS WAF** | Rules + optional AWS WAF CAPTCHA | Often yes | Clean headers/IP; CAPTCHA → CapSolver `AntiAwsWafTask` |

**Reading the matrix:** where "TLS alone enough?" is **No**, `curl_cffi`/primp/rnet will get you a clean handshake and then a challenge page. That's your cue to escalate to a real browser (`anti-bot/modern-stealth-browsers.md`) or a managed unblocker (`networking/`), *not* to keep tweaking headers.

---

## Identify the vendor from the response

```python
import re

VENDOR_SIGNS = {
    "Cloudflare":      [r"cf-ray", r"cf_chl", r"__cf_bm", r"cf_clearance", r"challenges\.cloudflare\.com", r"cf-turnstile"],
    "DataDome":        [r"datadome", r"dd_cookie", r"geo\.captcha-delivery\.com", r"x-datadome"],
    "Akamai":          [r"_abck", r"bm_sz", r"ak_bmsc", r"akamai"],
    "Kasada":          [r"x-kpsdk", r"kpsdk", r"/149e9513-.*\.js"],
    "PerimeterX/HUMAN":[r"_px[0-9A-Za-z]?", r"px-captcha", r"perimeterx", r"human-challenge"],
    "F5/Shape":        [r"x-shape", r"_shape", r"distil", r"__d[a-z]{2}"],
    "Imperva":         [r"incap_ses", r"___utmvc", r"visid_incap"],
    "AWS WAF":         [r"aws-waf-token", r"awswaf"],
}

def identify_vendor(headers: dict, body: str, cookies: dict) -> list[str]:
    hay = " ".join([str(headers).lower(), body[:5000].lower(), str(cookies).lower()])
    return [v for v, pats in VENDOR_SIGNS.items() if any(re.search(p, hay) for p in pats)] or ["none/unknown"]
```

Check **response headers, the set cookies, and the challenge HTML** together — vendors leak in all three.

---

## Cloudflare, specifically (the most common wall)

Cloudflare is layered; treat each layer separately.

1. **Bot Fight Mode / basic managed rules** — mostly a TLS + reputation check. `curl_cffi` with a *current* profile (`impersonate="chrome"`) + a non-datacenter IP clears it. This is the common case; try it first.
2. **Managed Challenge ("Checking your browser…", interstitial)** — requires real JS execution to mint `cf_clearance`. Options:
   - Real browser (`patchright`, `channel=chrome`) → let it solve → harvest the `cf_clearance` cookie + matching `User-Agent`, then reuse both in `curl_cffi` for bulk. **`cf_clearance` is bound to IP + UA** — reuse the same proxy IP and exact UA or it's void.
   - Managed unblocker (Zyte API, Bright Data Web Unlocker) — pay per request, no browser to run.
3. **Turnstile** (the widget) — a CAPTCHA-class challenge. Solve via CapSolver/2Captcha (`AntiTurnstileTask`), inject the token. See `anti-bot/captcha-solvers.md`. OSS shortcut: **Scrapling's `StealthyFetcher.fetch(url, solve_cloudflare=True)`** clears Turnstile/interstitial without wiring a solver (see `reference/scrapling.md`) — but it won't beat a hard WAF/IP block.

**`cloudscraper` / FlareSolverr status:** both lag Cloudflare's current challenges and are unreliable in 2026. Don't lead with them. `curl_cffi` + IP, then a real browser, then a managed unblocker is the durable ladder.

---

## DataDome / Kasada / Akamai — why HTTP clients can't win alone

These score **client-side execution and behavior**, then bind a cookie:
- **DataDome** issues `datadome` after a JS challenge; residential IP alone is *not* enough — a residential IP with a Python TLS fingerprint and no JS still fails. Winning combo: camoufox (real Firefox fingerprint) + `humanize` + residential proxy + a warm session (land, dwell, then fetch).
- **Kasada** requires solving a proof-of-work and passing JS-integrity checks (`x-kpsdk-*`). It's the hardest common OSS target — usually a specialist solver or managed unblocker.
- **Akamai** validates sensor-data payloads baked into `_abck`. A real browser generates them; HTTP clients don't.

For all three: if you're not prepared to run a real browser with behavior, **a managed unblocker is the honest answer** (`networking/proxy-providers.md`).

---

## WAF/IP block vs. JS challenge — the diagnosis that changes everything

They both often surface as HTTP 403. The fix is opposite. Diagnose before reacting:

| Signal | WAF / IP block | JS challenge |
|---|---|---|
| Body text | "Sorry, you have been blocked", "Access denied", Ray ID | "Checking your browser", "Please enable JavaScript", spinner |
| Does a fresh cookie help? | **No** — it's IP/TLS-level | Sometimes — solving the challenge mints one |
| Does a real browser help? | Only via a **different IP** | **Yes** — it executes the JS |
| Right move | **Change IP** (residential/mobile proxy), slow down, warm up | Run a **real browser** or **solver**; harvest the clearance cookie |

**Worked example:** curl_cffi + `chrome124` + RSC headers returned "Sorry you've been blocked" on every variant — a **WAF/IP block**, not a challenge. Session-cookie carry-over failed *because cookies were never the issue*. The correct escalation was a residential proxy (or a mirror source — see `reference/common-patterns.md`), not more header tuning. Recognizing WAF-vs-challenge early would have saved a dozen dead-end attempts.

---

## Gotchas

- **A vendor can layer challenges** — Cloudflare may pass TLS then throw Turnstile only on the data endpoint. Probe the *actual* target URL, not just the homepage.
- **`cf_clearance` and `datadome` cookies are IP+UA-bound.** Harvest and reuse them on the *same* proxy IP and UA, or they're rejected.
- **Escalating too fast burns money.** Always try `curl_cffi` + a good IP before a browser, and a browser before a paid unblocker.
- **Report non-retryable blocks to the user.** If the honest answer is "this needs a $/req managed unblocker or a residential proxy," say so with the cost — don't silently loop.

---

## Related

- `anti-bot/tls-http-clients.md` — the HTTP-only layer to try first
- `anti-bot/modern-stealth-browsers.md` — patchright/camoufox/nodriver for JS-challenge targets
- `anti-bot/captcha-solvers.md` — Turnstile / DataDome / AWS-WAF solving
- `anti-bot/ban-detection.md` — rate-limit vs. ban triage
- `networking/proxy-providers.md` — residential/mobile proxies + managed unblockers (Zyte API, Web Unlocker)
