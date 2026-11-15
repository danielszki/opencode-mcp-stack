# Concurrency with `curl_cffi` — the per-thread session pattern

A non-obvious gotcha: a naïve `ThreadPoolExecutor` with `curl_cffi` looks parallel but is essentially **serial**. Each thread submits work, but the underlying libcurl handle serializes requests on the shared `Session` object.

## Symptom

```python
# Looks concurrent, but isn't
session = curl_cffi.Session()
with ThreadPoolExecutor(max_workers=10) as ex:
    futures = [ex.submit(fetch, url, session) for url in urls]
    for f in as_completed(futures):
        ...
```

You set `max_workers=10`, expect a 10× speedup, and get maybe 1.1×. Each request still feels like 1 second because libcurl serializes them on the shared handle.

## The cause

`curl_cffi.Session()` wraps a single libcurl `CurlMulti` handle. Concurrent `.get()` / `.post()` calls on the same session serialize through that handle.

This is **different** from `requests.Session()`, which is also not thread-safe but for different reasons (cookie jar contention, connection pool).

## The fix — one session per thread, via `threading.local()`

Each worker thread gets its own `curl_cffi.Session()`. Auth cookies established during a "boot" sequence are copied from the boot session into each thread-local session on first use.

```python
import threading
from concurrent.futures import ThreadPoolExecutor
from curl_cffi import requests as cffi_requests

# Boot session — does the initial auth/nav, holds the cookies
boot_session = cffi_requests.Session()
sticky_header = ...  # established during boot, shared across threads

# Per-thread session storage
tls = threading.local()

def _get_thread_session() -> cffi_requests.Session:
    s = getattr(tls, "session", None)
    if s is None:
        s = cffi_requests.Session()
        # Inherit auth cookies from boot session
        for c in boot_session.cookies.jar:
            s.cookies.set(c.name, c.value, domain=c.domain, path=c.path)
        tls.session = s
    return s

def fetch_one(item):
    s = _get_thread_session()
    return s.get(
        item.url,
        impersonate="chrome",
        headers=sticky_header,
        timeout=60,
        **proxy_kwargs,
    )

with ThreadPoolExecutor(max_workers=10) as ex:
    futures = [ex.submit(fetch_one, item) for item in items]
    for f in futures:
        result = f.result()
        ...
```

The key points:
- `threading.local()` gives each thread its own `session` attribute
- Threads only create a new `Session` on their first call (cached after that)
- Cookies from the boot are copied so each thread inherits authentication
- All threads share the same `sticky_header` (Zyte session ID) so they exit through the same IP — see `../networking/proxy-zyte.md`

## Benchmark — real numbers

Tested on a target with ~100 records per page, behind Zyte residential AU proxy:

| Concurrency | Time / record | Speedup |
|---|---|---|
| 1 (serial) | 2.48 s | 1.0× |
| 5 | 0.83 s | 3.0× |
| 10 | 0.70 s | **3.5×** |
| 20 | 0.65 s | 3.8× (diminishing) |

Speedup plateaus around 10-15 workers. Beyond that, proxy provider rate limits and target server response time dominate.

## When NOT to use this pattern

- **Stateful navigation between requests** — if request N depends on the response of request N-1 (cookies set, VIEWSTATE updated), you cannot parallelize. Most ASP.NET WebForms search-page interactions are serial by nature; only the detail-page batch is parallelizable.
- **Strict per-IP rate limits** — if the target rate-limits per-IP at, say, 5 req/min, more than ~5 concurrent threads will all hit 429 simultaneously.
- **Small batches** — overhead of thread creation isn't worth it for fewer than ~20 items.

## Pagination is still serial

Pagination is almost always serial — page N+1 needs state from page N (cookies, hidden form fields, pagination tokens). Parallelize the **detail fetches per page**, not the pagination loop:

```python
for page in range(1, last_page + 1):
    page_soup = fetch_page(page)         # serial
    records_on_page = parse(page_soup)
    # Now parallelize the N detail fetches for this page
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = [ex.submit(fetch_one, r) for r in records_on_page]
        for f in futures:
            yield f.result()
```

## Concurrency knob — exposed to operator

Always expose `detail_concurrency` (or similar) as a parameter, defaulting to 10:

```python
def crawl(detail_concurrency: int = 10, ...) -> Iterator[Record]:
    ...
```

If proxy provider starts rate-limiting or target gets sensitive, the operator drops it without code changes.

## Always ask the user before turning on concurrency

For unfamiliar targets, ask before enabling parallel fetches:

> Multi-threading will run X parallel requests through the proxy.
> Risks: provider rate limit, target detecting burst pattern, IP ban.
> Expected speedup at concurrency=10: ~3-4× based on the per-thread session pattern.
>
> Want me to enable it? Default off is also fine.

## Related

- `../networking/proxy-zyte.md` — sticky session must be shared across threads (same exit IP)
- `../anti-bot/error-decoders.md` — what to do when concurrency triggers 429 or 503
