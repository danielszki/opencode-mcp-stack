# Legacy CMS quirks

A grab-bag of quirks shared by legacy enterprise web platforms (ASP.NET WebForms, classic ASP, ColdFusion, JSP/Struts, older PHP enterprise CMSes). When you encounter any of these, recognize them quickly — they share patterns that confuse tools designed for modern APIs.

For ASP.NET WebForms specifically, see `aspnet-webforms.md` — this file covers cross-platform behaviors.

## "HTTP 200 + Error" — silent failures

Legacy CMSes very often return `HTTP 200 OK` with an error page in the body instead of using a proper status code. Symptoms:

- `<title>Error</title>` or `<title>Application Error</title>`
- A `<div id="ErrorPanel">`, `<div class="error-page">`, or similar
- URL changed to `/Error.aspx`, `/error.cfm`, `/exception.jsp`
- Body contains stack traces, "An error occurred", or "Object reference not set"

**Detection helper (works across most legacy stacks):**

```python
from bs4 import BeautifulSoup

def is_silent_error(response_text: str) -> bool:
    soup = BeautifulSoup(response_text, "html.parser")
    title = (soup.title.string if soup.title else "").strip().lower()
    if title in ("error", "application error", "exception"):
        return True
    for selector in ["#ErrorPanel", ".error-page", ".exception-page", "#cf_error"]:
        if soup.select_one(selector):
            return True
    body = response_text[:5000].lower()
    return any(s in body for s in ["aspxerrorpath", "cfdiagnostics", "applicationexception"])
```

Call this after every navigation step. Never trust 200 alone.

## Session-bound numeric IDs

When a detail page is reached via `?Id=12345` or `?recordKey=98765`, those numeric IDs are often **scoped to the session that generated them**. Symptoms when an ID is reused cold:

- 200 OK + Error page (the most common)
- 302 redirect to the home page
- 404, but with the same generic error template

**Implication for scraping:** don't persist these IDs across runs. Always re-search from the entry point and harvest fresh IDs.

Affected platforms include:
- Salesforce (`Id` like `a0FMp000003MGFhMAO` — globally unique but ACL-checked)
- ASP.NET WebForms apps with VIEWSTATE-bound state
- Java/Struts apps using `formToken`
- ColdFusion apps with CFID/CFTOKEN session pinning

## CSRF / anti-forgery tokens

Legacy stacks scatter CSRF tokens under different names. Some you'll see:

- ASP.NET: `__EVENTVALIDATION`, `__VIEWSTATEGENERATOR`, sometimes `ctl00$CSRFToken`
- Spring MVC: `_csrf` or `CSRF-TOKEN` cookie + `X-CSRF-TOKEN` header
- ColdFusion: `csrfToken` hidden field, sometimes URL param
- Struts: `struts.token` hidden field, name matches a constant
- Plain custom: `__RequestVerificationToken`, `authenticity_token`

Always echo back **all** hidden inputs from the previous response — don't filter to fields you think you understand. Token validation often combines multiple fields.

## Referer-checked endpoints

Many legacy detail pages require the `Referer` header to match an expected page. Detail GETs return the Error page if `Referer` is absent, even when cookies are valid.

```python
headers = {
    "Referer": "https://app.example.com/Results.aspx",
    ...
}
```

This is independent of CSRF tokens — it's an additional check.

## Stateful navigation: you can't skip steps

Some pages are only reachable through a specific sequence:

```
Login → Choose Tenant → Pick Module → Search → Results → Detail
```

Skipping to "Detail" with a known URL fails silently because step 2 sets server-side session state that step 5 expects. Always replay the full sequence.

**HAR-driven recipe:**
1. Capture a full HAR of the user navigating from login to the target page
2. Identify every non-asset request (`.aspx`, `.cfm`, `.jsp`, JSON endpoints)
3. Replay them in order, carrying cookies + hidden form fields forward
4. Diff your responses against the HAR responses at each step

## Cookie-bound exit IP

When the app issues a session cookie tied to the client's IP address, switching IPs mid-session invalidates the cookie. The app responds with the Error page or redirects to login.

**Implication for proxies:** you MUST use a sticky proxy session (see `../networking/proxy-zyte.md`). Rotating IPs per request breaks legacy apps.

## Encoded payloads everywhere

Legacy stacks tend to URL-encode aggressively, sometimes double. When you see `%2520` (which is `%20` re-encoded), you have a double-encoded value. When constructing forms:

```python
from urllib.parse import quote

# Safe single-encoding
form_data = {"field": "value with spaces"}  # requests will encode once
```

If you're building the URL manually, encode each component once and let the HTTP library do the rest. Avoid `quote(quote(value))`.

## Dynamic control IDs

Server-rendered platforms generate IDs like `ctl04`, `ctl09`, `dnn_ctr1234_Main`, `_ngcontent_c0` (Angular SSR mimicking this pattern). These can change between deployments of the same template, sometimes between page loads.

**Rule:** find inputs by partial-name match, never exact:

```python
# Bad: brittle to template changes
session.post(url, data={"ctl00$ctl04$DateBox": "01/01/2024"})

# Good: discover the actual name from the DOM
from_field = next(
    inp["name"] for inp in soup.find_all("input")
    if "DateBox" in (inp.get("name") or "")
)
session.post(url, data={from_field: "01/01/2024"})
```

## Backwards-style date formats

Many legacy systems use `dd/mm/yyyy` (UK/AU/NZ-style) regardless of locale settings. When you POST `2024-01-15` (ISO) and get the Error page, try `15/01/2024`. The wire format almost never matches what JSON APIs would use.

## Related

- `aspnet-webforms.md` — specifics of the ASP.NET flavor (VIEWSTATE, `__doPostBack`)
- `../networking/proxy-zyte.md` — sticky session is mandatory for these sites
- `../anti-bot/error-decoders.md` — the response-symptom decoder table
