# Modern Stealth Browsers (nodriver / patchright / camoufox)

`playwright-stealth` and `undetected-chromedriver` are the old guard. Both still work against weak defenses, but against 2026-era anti-bot (Cloudflare managed challenge, DataDome, Kasada) they're increasingly detected. The current stack is three tools with fundamentally different approaches. Pick by *what the target checks*, not by habit.

> Note: `playwright-stealth`'s old `stealth_sync(page)` / `stealth_async(page)` API was replaced by a `Stealth` class (`Stealth().apply_stealth_sync(page)`) in recent versions. If you see `stealth_sync` in old code, it's deprecated. Prefer the tools below for hard targets.

---

## Why headless gets caught: the CDP `Runtime.enable` leak

The single most important modern detection signal isn't `navigator.webdriver` (everyone patches that). It's the **automation protocol itself**.

Playwright/Puppeteer/Selenium drive Chrome over the **Chrome DevTools Protocol (CDP)**. To receive execution-context events they call `Runtime.enable`, which is observable from page JavaScript (it perturbs error stack traces / console behavior in a detectable way). Anti-bot scripts probe for exactly this. So a "stealthed" Playwright can still be flagged **because it's Playwright**, regardless of how many navigator properties you spoof.

The three modern tools each answer this differently:

| Tool | Approach to the CDP problem | Base browser |
|---|---|---|
| **nodriver** | No Playwright/Selenium shim at all — drives real Chrome directly over CDP, avoids the leaky calls | Chromium |
| **patchright** | Playwright fork that *patches* the leaks (suppresses the observable `Runtime.enable`, closes other CDP tells), `channel=chrome` for real Chrome TLS | Chromium |
| **camoufox** | Different engine entirely — a Firefox fork with spoofing compiled in at the C level | Firefox |

---

## nodriver — CDP-direct, lightest footprint

The official successor to `undetected-chromedriver` (same author, `ultrafunkamsterdam`). Launches a real Chrome and talks CDP directly — **no WebDriver, so no `navigator.webdriver`, and none of the Playwright CDP tells.**

```python
import nodriver as uc

async def main():
    browser = await uc.start(headless=False)
    page = await browser.get("https://target.com")
    await page.select("div.data", timeout=15)
    html = await page.get_content()
    await browser.stop()

uc.loop().run_until_complete(main())
```

- **Best for:** targets with basic or no active WAF where you just need real JS execution without the Playwright fingerprint. Lightest memory footprint of the three.
- **Weakness:** it does **not** simulate mouse movement, scroll, or keystroke timing. Against DataDome, Akamai Bot Manager, or PerimeterX — which score behavior — it gets blocked fast. Add human-like interaction yourself or use camoufox.
- `zendriver` is a maintained community fork if nodriver stalls.

## patchright — the practical Playwright upgrade

A drop-in Playwright fork (Python **and** Node) that patches the known CDP-leak signals at startup. If you already have Playwright code, this is the smallest diff to a real stealth gain.

```python
# pip install patchright && patchright install chromium
from patchright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=False)  # real Chrome → real TLS
    ctx = browser.new_context(locale="en-US", viewport={"width": 1280, "height": 800})
    page = ctx.new_page()
    page.goto("https://target.com", wait_until="networkidle")
    # ... same Playwright API you already know
    browser.close()
```

- **Best for:** Cloudflare-protected sites, and any team already on Playwright. Use `channel="chrome"` (real installed Chrome), not bundled Chromium, so the TLS fingerprint is genuine.
- Keep the API identical to Playwright — everything in `browser-automation/browser-techniques.md` (network listener, request injection, route interception) works unchanged.
- **Good fit when you must pull a Cloudflare-gated file download** (e.g. an XLSX behind a JS challenge) via `expect_download()`.

## camoufox — Firefox fork for the hardest targets

An anti-detect Firefox build with canvas/WebGL/navigator/screen spoofing done at the **C++ level** (not injected JS, so there's no JS shim to detect). It presents a genuinely legitimate Firefox fingerprint because it *is* Firefox with modified internals. Playwright-compatible driver.

```python
# pip install camoufox[geoip]
from camoufox.sync_api import Camoufox

with Camoufox(headless=False, humanize=True, geoip=True) as browser:
    page = browser.new_page()
    page.goto("https://hard-target.com")
    page.wait_for_selector(".data")
    html = page.content()
```

- **Best for:** the toughest fingerprinting (DataDome especially — camoufox has succeeded where patchright failed). `humanize=True` adds human-like cursor movement; `geoip=True` aligns the spoofed locale/timezone with your proxy's exit IP.
- **Weakness:** Firefox has smaller real-world share than Chrome, so a Firefox UA is slightly more "notable" on Chrome-heavy sites — but a *real* Firefox fingerprint beats a *fake* Chrome one every time.
- **Higher-level wrapper:** Scrapling's `StealthyFetcher` is Camoufox under the hood with `solve_cloudflare=True` and the adaptive parser bolted on — reach for it if you want the Camoufox stealth without managing the browser directly (`reference/scrapling.md`).

---

## Choosing — and validating

**Escalation order for a browser-required target:**
1. `patchright` with `channel=chrome` — cheapest upgrade, clears most Cloudflare.
2. `camoufox` with `humanize=True` + geo-aligned residential proxy — for DataDome / behavioral scorers.
3. Managed browser (Bright Data Scraping Browser, Browserbase) — when you don't want to run/scale browsers yourself. See `networking/`.

`nodriver` sits *below* this ladder: reach for it when the target is light and you want minimal overhead, not when you're fighting a real WAF.

**Validate your fingerprint before a big run** against public probes:
- **CreepJS** (`abrahamjuliot.github.io/creepjs`) — the reference fingerprint/entropy test.
- `bot.sannysoft.com`, `browserleaks.com/tls` (check your JA3/JA4), `arh.antoinevastel.com/bots`.

Load one through your stealth browser + proxy and read the report — it tells you exactly which signal is leaking before a real target does.

---

## Behavioral signals still matter

None of these tools fake human *behavior* unless you ask (nodriver/patchright do nothing; camoufox `humanize` does some). Behavioral scorers (DataDome, PerimeterX, Kasada) want:
- Non-linear mouse paths, realistic dwell/scroll before clicks
- Human-plausible inter-action timing (not fixed sleeps)
- A warmed session (visit a landing page, accept cookies, *then* hit the data)

Add these explicitly on hard targets. `slow_mo=` + scripted mouse moves + `page.wait_for_timeout(random.uniform(...))` is the floor.

---

## Gotchas

- **Headful beats headless** on the hardest sites — headless Chrome still has GPU/rendering tells. Run headful under `Xvfb`/`xvfb-run` on servers.
- **Proxy + fingerprint must agree.** A German residential IP with a `en-US`/`America/New_York` browser locale is a contradiction. Use camoufox `geoip=True` or set locale/timezone to match the exit IP.
- **`channel="chrome"` needs Chrome installed** on the machine; bundled Chromium has a subtly different fingerprint.
- **These are heavier and slower than HTTP.** Follow the ladder: use a browser only to *harvest tokens/cookies*, then replicate bulk fetches with `curl_cffi` (see SKILL.md Level 4). Don't drive a browser per record.

---

## Related

- `anti-bot/anti-bot-vendors.md` — which vendor scores behavior vs. TLS vs. JS, and per-vendor bypass
- `anti-bot/tls-http-clients.md` — the cheaper HTTP-only layer to try first
- `browser-automation/browser-techniques.md` — capture/inject/route patterns (work under patchright & camoufox too)
- `networking/proxy-providers.md` — residential/mobile proxies + managed browsers
