# CAPTCHA Identification & Solving

## Step 1 — Always identify the CAPTCHA type first

**Never recommend or use a solver without knowing the exact CAPTCHA type.** Different CAPTCHAs require different solvers, and not all services support all types.

When a CAPTCHA is encountered:

1. Ask the user for a screenshot of it
2. Identify the type from the visual + page source
3. Verify the solver supports it (check the compatibility table below)
4. Only then recommend and implement

---

## CAPTCHA identification guide

### By visual appearance

| What you see | CAPTCHA type | Notes |
|---|---|---|
| "I'm not a robot" checkbox + image grid | **reCAPTCHA v2** | Most common. Checkbox triggers image challenge |
| No visible element, invisible challenge | **reCAPTCHA v3** | Score-based, no user interaction |
| Image + audio challenge, hCaptcha logo | **hCaptcha** | Used by Cloudflare, Discord, many EU sites |
| Spinning/floating challenge with Cloudflare branding | **Cloudflare Turnstile** | Newer, JS-based behavioral check |
| Click the images matching the description | **Arkose Labs (FunCaptcha)** | Used by Facebook, Xbox, Roblox |
| Drag the slider to complete the puzzle | **GeeTest v3/v4** | Common on Chinese sites, some EU portals |
| Enter text from distorted image | **Text CAPTCHA (classic)** | Legacy, easily solvable with OCR |
| "Prove you're human" with behavior analysis | **AWS WAF CAPTCHA** | Uses audio/visual challenge |
| Kasada "K" logo in corner | **Kasada** | Behavioral, no standard solver |

### From page source

```python
import re, requests

def identify_captcha_from_html(html: str) -> str:
    checks = {
        "reCAPTCHA v2": [r"recaptcha", r"google\.com/recaptcha", r"grecaptcha\.render"],
        "reCAPTCHA v3": [r"grecaptcha\.execute", r"recaptcha.*v3"],
        "hCaptcha": [r"hcaptcha\.com", r"hcaptcha-widget", r"h-captcha"],
        "Cloudflare Turnstile": [r"turnstile\.cloudflare\.com", r"cf-turnstile"],
        "Arkose Labs": [r"arkoselabs\.com", r"funcaptcha", r"enforcement\.arkoselabs"],
        "GeeTest": [r"geetest", r"gt\.js", r"initGeetest"],
        "AWS WAF CAPTCHA": [r"aws-waf-captcha", r"AwsWafCaptcha"],
        "Kasada": [r"kasada", r"2ZqA\.js"],
    }
    lower = html.lower()
    for name, patterns in checks.items():
        if any(re.search(p, lower) for p in patterns):
            return name
    return "Unknown CAPTCHA"

html = requests.get("https://target.com").text
print(identify_captcha_from_html(html))
```

---

## Solver platform compatibility

Always verify support before recommending. This table reflects known support as of 2026:

| CAPTCHA Type | 2captcha | CapSolver | Anti-Captcha | DeathByCaptcha | Notes |
|---|:---:|:---:|:---:|:---:|---|
| reCAPTCHA v2 | ✅ | ✅ | ✅ | ✅ | Universal support |
| reCAPTCHA v3 | ✅ | ✅ | ✅ | ✅ | Needs `action` + `min_score` param |
| hCaptcha | ✅ | ✅ | ✅ | ✅ | Needs `sitekey` + page URL |
| Cloudflare Turnstile | ✅ | ✅ | ✅ | ❌ | Newer, not all services support |
| Arkose Labs | ✅ | ✅ | ✅ | ❌ | Expensive, low success rate |
| GeeTest v3 | ✅ | ✅ | ✅ | ✅ | Needs `gt` + `challenge` params |
| GeeTest v4 | ✅ | ✅ | ❌ | ❌ | Much harder, higher failure rate |
| AWS WAF CAPTCHA | ❌ | ✅ | ❌ | ❌ | CapSolver `AntiAwsWafTask` |
| DataDome | ❌ | ✅ | ❌ | ❌ | CapSolver has a DataDome task; still needs matching proxy + UA |
| Kasada | ❌ | ⚠️ | ❌ | ❌ | Proof-of-work; specialist/managed only, unreliable via generic solvers |
| Text/Image CAPTCHA | ✅ | ✅ | ✅ | ✅ | Human workers or OCR |

**CapSolver is AI/ML-based** (not human-worker like classic 2Captcha/Anti-Captcha), so it's fast on token-type challenges — Turnstile and reCAPTCHA v3 typically resolve in **under 3s**. Its API is **2Captcha-compatible**, so migration between the two is mostly a base-URL swap.

**When none support it (Kasada, F5/Shape, hard DataDome):** use a managed unblocker that handles the challenge internally — Zyte API, Bright Data Web Unlocker, ZenRows. See `networking/proxy-providers.md`.

---

## Extracting CAPTCHA parameters from the page

Before calling a solver, you need `sitekey` and page URL:

```python
import re
from bs4 import BeautifulSoup

def extract_captcha_params(html: str, page_url: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    params = {"page_url": page_url}

    # reCAPTCHA v2
    tag = soup.find("div", class_="g-recaptcha")
    if tag:
        params["type"] = "recaptcha_v2"
        params["sitekey"] = tag.get("data-sitekey", "")
        return params

    # reCAPTCHA v3
    m = re.search(r'grecaptcha\.execute\(["\']([^"\']+)["\']', html)
    if m:
        params["type"] = "recaptcha_v3"
        params["sitekey"] = m.group(1)
        m2 = re.search(r'action["\']?\s*:\s*["\']([^"\']+)["\']', html)
        params["action"] = m2.group(1) if m2 else "submit"
        return params

    # hCaptcha
    tag = soup.find(attrs={"data-hcaptcha-sitekey": True}) or soup.find(class_="h-captcha")
    if tag:
        params["type"] = "hcaptcha"
        params["sitekey"] = tag.get("data-sitekey") or tag.get("data-hcaptcha-sitekey", "")
        return params

    # Cloudflare Turnstile
    tag = soup.find(class_="cf-turnstile") or soup.find(attrs={"data-sitekey": True})
    if tag and "turnstile" in html.lower():
        params["type"] = "turnstile"
        params["sitekey"] = tag.get("data-sitekey", "")
        return params

    return {"type": "unknown"}
```

---

## 2captcha integration

Docs: https://2captcha.com/api-docs

```python
import requests, time

class TwoCaptchaSolver:
    BASE = "https://2captcha.com"

    def __init__(self, api_key: str):
        self.key = api_key

    def solve_recaptcha_v2(self, sitekey: str, page_url: str) -> str:
        r = requests.post(f"{self.BASE}/in.php", data={
            "key": self.key, "method": "userrecaptcha",
            "googlekey": sitekey, "pageurl": page_url, "json": 1,
        })
        task_id = r.json()["request"]
        return self._wait(task_id)

    def solve_recaptcha_v3(self, sitekey: str, page_url: str, action: str = "submit", min_score: float = 0.5) -> str:
        r = requests.post(f"{self.BASE}/in.php", data={
            "key": self.key, "method": "userrecaptcha", "version": "v3",
            "googlekey": sitekey, "pageurl": page_url,
            "action": action, "min_score": min_score, "json": 1,
        })
        task_id = r.json()["request"]
        return self._wait(task_id)

    def solve_hcaptcha(self, sitekey: str, page_url: str) -> str:
        r = requests.post(f"{self.BASE}/in.php", data={
            "key": self.key, "method": "hcaptcha",
            "sitekey": sitekey, "pageurl": page_url, "json": 1,
        })
        task_id = r.json()["request"]
        return self._wait(task_id)

    def solve_turnstile(self, sitekey: str, page_url: str) -> str:
        r = requests.post(f"{self.BASE}/in.php", data={
            "key": self.key, "method": "turnstile",
            "sitekey": sitekey, "pageurl": page_url, "json": 1,
        })
        task_id = r.json()["request"]
        return self._wait(task_id)

    def _wait(self, task_id: str, max_wait: int = 120) -> str:
        for _ in range(max_wait // 5):
            time.sleep(5)
            r = requests.get(f"{self.BASE}/res.php", params={
                "key": self.key, "action": "get", "id": task_id, "json": 1,
            })
            data = r.json()
            if data["status"] == 1:
                return data["request"]
            if data["request"] not in ("CAPCHA_NOT_READY", "CAPTCHA_NOT_READY"):
                raise RuntimeError(f"Solver error: {data['request']}")
        raise TimeoutError(f"CAPTCHA not solved in {max_wait}s")
```

---

## CapSolver integration

Docs: https://docs.capsolver.com

```python
import requests, time

class CapSolver:
    BASE = "https://api.capsolver.com"

    def __init__(self, api_key: str):
        self.key = api_key

    def _create_task(self, task: dict) -> str:
        r = requests.post(f"{self.BASE}/createTask", json={"clientKey": self.key, "task": task})
        data = r.json()
        if data.get("errorId"):
            raise RuntimeError(f"CapSolver error: {data.get('errorDescription')}")
        return data["taskId"]

    def _get_result(self, task_id: str, max_wait: int = 120) -> dict:
        for _ in range(max_wait // 5):
            time.sleep(5)
            r = requests.post(f"{self.BASE}/getTaskResult", json={"clientKey": self.key, "taskId": task_id})
            data = r.json()
            if data["status"] == "ready":
                return data["solution"]
        raise TimeoutError("CapSolver timeout")

    def solve_recaptcha_v2(self, sitekey: str, page_url: str) -> str:
        tid = self._create_task({"type": "ReCaptchaV2Task", "websiteURL": page_url, "websiteKey": sitekey})
        return self._get_result(tid)["gRecaptchaResponse"]

    def solve_hcaptcha(self, sitekey: str, page_url: str) -> str:
        tid = self._create_task({"type": "HCaptchaTask", "websiteURL": page_url, "websiteKey": sitekey})
        return self._get_result(tid)["gRecaptchaResponse"]

    def solve_turnstile(self, sitekey: str, page_url: str) -> str:
        tid = self._create_task({"type": "AntiTurnstileTask", "websiteURL": page_url, "websiteKey": sitekey})
        return self._get_result(tid)["token"]

    def solve_aws_waf(self, sitekey: str, page_url: str) -> str:
        tid = self._create_task({"type": "AntiAwsWafTask", "websiteURL": page_url, "websiteKey": sitekey})
        return self._get_result(tid)["cookie"]
```

---

## Submitting CAPTCHA token to the site

After solving, inject the token into the form or API call:

```python
# reCAPTCHA / hCaptcha — inject into form POST
token = solver.solve_recaptcha_v2(sitekey, page_url)
r = session.post("https://site.com/submit", data={
    "username": "user",
    "password": "pass",
    "g-recaptcha-response": token,   # reCAPTCHA
    # "h-captcha-response": token,   # hCaptcha
})

# Via Playwright (fill hidden field, then submit)
page.evaluate(f'document.getElementById("g-recaptcha-response").value = "{token}"')
page.click("button[type='submit']")
```

---

## Cost reference (approximate, 2026)

| CAPTCHA Type | 2captcha | CapSolver | Notes |
|---|---|---|---|
| reCAPTCHA v2 | ~$1.00/1000 | ~$0.80/1000 (→$0.65 at volume) | Most common |
| reCAPTCHA v3 | ~$2.00/1000 | ~$1.50/1000 | Higher cost |
| hCaptcha | ~$2.00/1000 | ~$1.50/1000 | |
| Turnstile | ~$1.00/1000 | ~$1.20/1000 | Solves in <3s (CapSolver) |
| GeeTest v4 | ~$4.00/1000 | ~$1.20/1000 | |
| Arkose Labs | ~$4.00/1000 | ~$3.00/1000 | Low success rate |
| DataDome | — | quote per volume | Token task; pair with matching proxy/UA |

**Always tell the user the cost before implementing.** Example: "This site uses hCaptcha. Solving 10,000 CAPTCHAs = ~$15–20 with 2captcha."
