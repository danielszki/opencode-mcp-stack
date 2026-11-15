# HAR File Parser & Analysis

## What is a HAR file

HAR (HTTP Archive) is a JSON format that records **every network request and response** made by the browser during a session. It is the most complete way to share browser network activity.

A HAR file contains, for each request:
- Full request URL, method, query parameters
- All request headers (User-Agent, Cookie, Authorization, sec-ch-ua, sec-fetch-*, etc.)
- Request body (POST data, JSON payload)
- All response headers (Set-Cookie, Content-Type, Cache-Control, etc.)
- Full response body (HTML, JSON, CSS, etc.)
- Timing data (blocked, DNS, SSL, connect, wait, receive)
- Cookies sent and received

**When to ask for a HAR instead of a curl:**
- The site makes multiple requests to work (login → token → data)
- You need to see all requests including static assets (reveals API structure)
- The user isn't technical enough to find a specific request in DevTools
- You want to verify what auth tokens the site uses

---

## How to export a HAR

Ask the user:
```
To capture all network requests, please:
1. Open Chrome → DevTools (F12) → Network tab
2. ☑ Check "Preserve log"
3. Navigate to the target page and interact with it (load data, apply filters, etc.)
4. Click the **download icon** (↓) in the Network toolbar → **"Export HAR (sanitized)..."**
   - If sanitization strips something I need (e.g. `Cookie` / `Authorization` headers), right-click anywhere in the request list → **"Save all as HAR with content"** for the unsanitized version
5. Save the .har file and share it with me

The HAR will contain every request + response, including authentication tokens and cookies (when using the unsanitized export).
```

---

## HAR analyzer — extract all useful requests

```python
import json
from pathlib import Path
from dataclasses import dataclass

@dataclass
class HarEntry:
    url: str
    method: str
    status: int
    content_type: str
    request_headers: dict
    request_cookies: dict
    query_params: dict
    post_data: str | None
    response_headers: dict
    response_body: str | None
    response_size: int
    time_ms: float

    def to_curl(self) -> str:
        """Reconstruct curl command from this entry."""
        parts = [f"curl -X {self.method} '{self.url}'"]
        skip = {"host", "content-length", "accept-encoding"}
        for name, value in self.request_headers.items():
            if name.lower() not in skip:
                parts.append(f"  -H '{name}: {value}'")
        if self.post_data:
            parts.append(f"  --data-raw '{self.post_data}'")
        return " \\\n".join(parts)

    def is_api(self) -> bool:
        return "json" in self.content_type or "xml" in self.content_type

    def is_html(self) -> bool:
        return "html" in self.content_type

    def has_auth(self) -> bool:
        headers_lower = {k.lower(): v for k, v in self.request_headers.items()}
        return bool(
            self.request_cookies
            or "authorization" in headers_lower
            or "x-api-key" in headers_lower
            or "x-auth-token" in headers_lower
        )


class HarParser:
    def __init__(self, har_path: Path):
        data = json.loads(har_path.read_text(encoding="utf-8"))
        self.entries = [self._parse_entry(e) for e in data["log"]["entries"]]
        self.creator = data["log"].get("creator", {})
        self.har_path = har_path

    def _parse_entry(self, e: dict) -> HarEntry:
        req = e["request"]
        resp = e["response"]
        return HarEntry(
            url=req["url"],
            method=req["method"],
            status=resp["status"],
            content_type=resp["content"].get("mimeType", ""),
            request_headers={h["name"]: h["value"] for h in req.get("headers", [])},
            request_cookies={c["name"]: c["value"] for c in req.get("cookies", [])},
            query_params={q["name"]: q["value"] for q in req.get("queryString", [])},
            post_data=req.get("postData", {}).get("text"),
            response_headers={h["name"]: h["value"] for h in resp.get("headers", [])},
            response_body=resp["content"].get("text"),
            response_size=resp["content"].get("size", 0),
            time_ms=e.get("time", 0),
        )

    def api_calls(self) -> list[HarEntry]:
        return [e for e in self.entries if e.is_api() and e.status < 400]

    def html_pages(self) -> list[HarEntry]:
        return [e for e in self.entries if e.is_html() and e.status < 400]

    def auth_requests(self) -> list[HarEntry]:
        return [e for e in self.entries if e.has_auth()]

    def find_data(self, search_text: str) -> list[HarEntry]:
        """Find entries whose response body contains a specific string."""
        results = []
        for e in self.entries:
            if e.response_body and search_text.lower() in e.response_body.lower():
                results.append(e)
        return results

    def get_cookies(self) -> dict:
        """Collect all cookies from all Set-Cookie headers."""
        cookies = {}
        for e in self.entries:
            for name, value in e.response_headers.items():
                if name.lower() == "set-cookie":
                    # Parse cookie: "name=value; Path=...; ..."
                    parts = value.split(";")[0].split("=", 1)
                    if len(parts) == 2:
                        cookies[parts[0].strip()] = parts[1].strip()
        return cookies

    def get_auth_headers(self) -> dict:
        """Extract Authorization headers found across all requests."""
        auth = {}
        for e in self.entries:
            for name, value in e.request_headers.items():
                if name.lower() in ("authorization", "x-api-key", "x-auth-token", "bearer"):
                    auth[name] = value
        return auth

    def summary(self) -> None:
        print(f"HAR: {self.har_path.name}")
        print(f"  Total entries: {len(self.entries)}")
        print(f"  API calls (JSON/XML): {len(self.api_calls())}")
        print(f"  HTML pages: {len(self.html_pages())}")
        print(f"  Auth-carrying requests: {len(self.auth_requests())}")
        print(f"  Cookies found: {list(self.get_cookies().keys())}")
        print(f"  Auth headers found: {list(self.get_auth_headers().keys())}")
        print()
        print("API calls:")
        for e in self.api_calls():
            print(f"  [{e.status}] {e.method} {e.url[:100]}")
            print(f"         {e.response_size:,} bytes | {e.time_ms:.0f}ms")
```

---

## Usage workflow

```python
from pathlib import Path

# 1. Parse the HAR
har = HarParser(Path("data/acer/raw/aegis.acer.europa.eu.har"))
har.summary()

# 2. Find requests containing specific data
results = har.find_data("Netherlands")
for r in results:
    print(r.url)
    print(r.to_curl())

# 3. Extract cookies and auth headers to replicate
cookies = har.get_cookies()
auth_headers = har.get_auth_headers()

# 4. Build a requests session from HAR data
import requests
session = requests.Session()
session.cookies.update(cookies)
session.headers.update(auth_headers)

# 5. Replicate the API call
api_entry = har.api_calls()[0]
r = session.request(
    method=api_entry.method,
    url=api_entry.url,
    headers={k: v for k, v in api_entry.request_headers.items()
             if k.lower() not in ("host", "content-length", "accept-encoding")},
    data=api_entry.post_data,
    timeout=30,
)
```

---

## What a HAR captures vs. a single curl

| Information | HAR | curl |
|---|---|---|
| All requests in session | ✅ | ❌ (one request only) |
| Response body | ✅ | ❌ |
| All cookies (request + Set-Cookie) | ✅ | Partial |
| Auth token extraction | ✅ | ❌ |
| Request timing | ✅ | ❌ |
| All headers | ✅ | ✅ |
| Session flow (login → data) | ✅ | ❌ |
| Easy to share | ✅ | ✅ |

**Conclusion:** HAR is strictly more informative than a curl. Always prefer it when:
- The site requires a multi-step session (login → token → data)
- You're not sure which of many requests has the data
- You want to extract cookies and replicate the session

---

## Privacy note

HAR files contain **all cookies and tokens from the session**, including auth credentials. Remind the user:

> "HAR files contain your session cookies. Don't share them publicly or commit to git. I'll use them locally to build the extractor and then discard them from the conversation."
