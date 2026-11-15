# Rate Limit & Ban Detection

## Auto rate limit tester

Before bulk extraction, probe the maximum safe speed:

```python
import requests, time

def probe_rate_limit(session: requests.Session, test_url: str, max_rps: int = 20) -> float:
    """
    Binary-search for the maximum safe requests-per-second.
    Returns safe RPS to use for bulk extraction.
    """
    print("Probing rate limit...")
    lo, hi = 0.1, float(max_rps)

    for _ in range(6):  # 6 iterations narrows to ±5%
        mid = (lo + hi) / 2
        delay = 1.0 / mid
        failed = 0

        for _ in range(10):
            r = session.get(test_url, timeout=10)
            if r.status_code == 429:
                failed += 1
            time.sleep(delay)

        if failed > 2:
            hi = mid      # too fast
        else:
            lo = mid      # safe

    safe_rps = lo * 0.8   # 20% safety margin
    safe_delay = 1.0 / safe_rps
    print(f"Safe rate: {safe_rps:.1f} req/s → {safe_delay:.2f}s between requests")
    return safe_rps
```

---

## Block type detection

When extraction fails, diagnose WHY before deciding the fix:

```python
from dataclasses import dataclass

@dataclass
class BlockDiagnosis:
    block_type: str       # "rate_limit" | "ip_ban" | "session_expired" | "captcha" | "geo_block" | "unknown"
    description: str
    suggested_fix: str
    is_retryable: bool

def diagnose_block(response: requests.Response) -> BlockDiagnosis:
    status = response.status_code
    content = response.text[:1000].lower()
    headers = {k.lower(): v.lower() for k, v in response.headers.items()}

    # Rate limit
    if status == 429:
        retry_after = headers.get("retry-after", "unknown")
        return BlockDiagnosis(
            block_type="rate_limit",
            description=f"Too many requests. Retry-After: {retry_after}s",
            suggested_fix="Add delay between requests or reduce concurrency",
            is_retryable=True,
        )

    # Session expired / auth
    if status == 401:
        return BlockDiagnosis(
            block_type="session_expired",
            description="Authentication required or session expired",
            suggested_fix="Clear session cache and re-login via browser harvest",
            is_retryable=True,
        )

    if status == 403:
        # Try to distinguish IP ban from auth block
        if any(kw in content for kw in ["ip", "banned", "blocked", "access denied", "your ip"]):
            return BlockDiagnosis(
                block_type="ip_ban",
                description="IP address blocked by the site",
                suggested_fix="Switch to residential proxy. Checkpoint saved — resume with new IP.",
                is_retryable=False,
            )
        if any(kw in content for kw in ["login", "sign in", "authenticate", "session"]):
            return BlockDiagnosis(
                block_type="session_expired",
                description="403 with login content — session likely expired",
                suggested_fix="Re-harvest session cookies via browser",
                is_retryable=True,
            )
        if any(kw in content for kw in ["cloudflare", "ray id", "checking your browser"]):
            return BlockDiagnosis(
                block_type="bot_detection",
                description="Cloudflare or similar bot protection triggered",
                suggested_fix="Switch to curl_cffi with chrome profile + residential proxy",
                is_retryable=False,
            )
        return BlockDiagnosis(
            block_type="ip_ban",
            description="403 — likely IP or fingerprint block",
            suggested_fix="Try curl_cffi first. If still blocked: rotating residential proxy.",
            is_retryable=False,
        )

    # CAPTCHA
    if any(kw in content for kw in ["captcha", "recaptcha", "hcaptcha", "turnstile", "are you human"]):
        return BlockDiagnosis(
            block_type="captcha",
            description="CAPTCHA challenge detected",
            suggested_fix="See captcha-solvers.md for identification and solving options",
            is_retryable=False,
        )

    # Geo block
    if status in (451, 403) and any(kw in content for kw in ["not available in your country", "geographic", "region"]):
        return BlockDiagnosis(
            block_type="geo_block",
            description="Content restricted to specific geographic regions",
            suggested_fix="Use a geo-targeted proxy from the target country",
            is_retryable=False,
        )

    # Redirect to login
    if response.history and any("login" in r.url.lower() for r in response.history):
        return BlockDiagnosis(
            block_type="session_expired",
            description="Redirected to login page — session expired",
            suggested_fix="Re-harvest session cookies",
            is_retryable=True,
        )

    return BlockDiagnosis(
        block_type="unknown",
        description=f"HTTP {status} — unrecognized block type",
        suggested_fix="Inspect the response manually. See full response headers and first 500 bytes of body.",
        is_retryable=False,
    )
```

---

## Reporting blocks to the user

When a non-retryable block is detected, always stop and report:

```python
def handle_block(diagnosis: BlockDiagnosis, checkpoint_path: str) -> None:
    print("\n" + "="*60)
    print(f"⛔ EXTRACTION BLOCKED — {diagnosis.block_type.upper()}")
    print("="*60)
    print(f"Reason:    {diagnosis.description}")
    print(f"Fix:       {diagnosis.suggested_fix}")
    print(f"Progress:  Saved to {checkpoint_path}")
    print(f"Retryable: {'Yes — fix issue and run again' if diagnosis.is_retryable else 'No — manual intervention needed'}")
    print("="*60)

    if diagnosis.block_type == "ip_ban":
        print("""
Next steps:
  1. Get a rotating residential proxy (see ../networking/proxies-overview.md)
  2. Set PROXY env var: export PROXY=http://user:pass@proxy:port
  3. Re-run the script — it will resume from checkpoint
        """)
    elif diagnosis.block_type == "session_expired":
        print("""
Next steps:
  1. Run: python extractor.py --refresh-session
  2. This will open a browser for login, save new cookies
  3. Re-run extraction — it will resume from checkpoint
        """)
    elif diagnosis.block_type == "captcha":
        print("""
Next steps:
  1. Check ./captcha-solvers.md to identify the CAPTCHA type
  2. Screenshot the CAPTCHA and share it here
  3. I'll identify the type and recommend a solver
        """)
```

---

## Retry policy per block type

```python
def should_retry(diagnosis: BlockDiagnosis, attempt: int) -> tuple[bool, float]:
    """Returns (should_retry, delay_seconds)."""
    if diagnosis.block_type == "rate_limit":
        # Exponential backoff: 5s, 10s, 20s, 40s, 80s
        return (attempt < 5, 5 * 2**attempt)

    if diagnosis.block_type == "session_expired" and attempt < 1:
        # Try once with refreshed session
        return (True, 2.0)

    # IP ban, geo block, bot detection, captcha — don't retry automatically
    return (False, 0)
```

---

## Proactive rate limit signals

Don't wait for a 429. Watch for early warning signs:

| Signal | Meaning |
|--------|---------|
| Response time increases from 200ms to 2000ms | Server is throttling you |
| `X-RateLimit-Remaining: 5` header | About to hit limit |
| `X-RateLimit-Reset: 1719000000` header | Reset timestamp |
| Response body is identical for 3+ consecutive requests | Cached/blocked response |
| Increasing % of 5xx errors | Server under load, back off |

```python
def check_proactive_signals(response: requests.Response) -> str | None:
    remaining = response.headers.get("X-RateLimit-Remaining")
    if remaining and int(remaining) < 10:
        return f"Rate limit warning: {remaining} requests remaining"

    reset = response.headers.get("X-RateLimit-Reset")
    if reset:
        wait = int(reset) - int(time.time())
        if wait > 0:
            return f"Rate limit resets in {wait}s"

    return None
```
