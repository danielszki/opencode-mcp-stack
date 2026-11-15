# Salesforce Experience Cloud (Aura / Lightning Community)

Public-facing Salesforce portals — used by enterprises, governments, NGOs, and SaaS vendors worldwide for customer/community sites. Common URL form: `<tenant>.my.site.com` or `<tenant>.force.com`.

The interesting thing: most of these portals expose **Apex methods reachable without authentication** via the Aura framework. If you find the right method, you get clean JSON.

## When you see this

- URL contains `.my.site.com`, `.force.com`, `.lightning.force.com`, or a Salesforce-branded sign-in
- DevTools Network shows requests to `/s/sfsites/aura?...&aura.ApexAction.execute=1`
- Request body contains `aura.context` and `aura.token` form fields
- Response headers include `X-SFDC-*` (e.g. `X-SFDC-Request-Id`)
- Page source mentions `Aura.initApplication` or `forceCommunity`

## How it works

Aura is Salesforce's Lightning Component framework. The browser POSTs serialized "actions" to a single endpoint:

```
POST https://<tenant>.my.site.com/s/sfsites/aura?r=5&aura.ApexAction.execute=1
Content-Type: application/x-www-form-urlencoded

message=<urlencoded JSON describing the action>
&aura.context=<urlencoded JSON: { mode, fwuid, app, loaded, ... }>
&aura.pageURI=<urlencoded current page path>
&aura.token=<auth token, or "null" for public actions>
```

Each `action` references:
- `descriptor`: usually `aura://ApexActionController/ACTION$execute`
- `params.classname`: an Apex class name (e.g. `MyAppController`)
- `params.method`: a method on that class (e.g. `searchRecords`)
- `params.params`: a JSON object passed as the method's arguments

The response wraps the return value in two layers:
```json
{
  "actions": [{
    "state": "SUCCESS",
    "returnValue": {
      "returnValue": { "records": [...], "totalRecords": 400 },
      "cacheable": false
    }
  }]
}
```

## Pattern — minimal request

```python
import json
from urllib.parse import quote
import curl_cffi.requests as cffi_requests

BASE = "https://tenant.my.site.com"
AURA_URL = f"{BASE}/s/sfsites/aura?r=5&aura.ApexAction.execute=1"
PAGE_URI = "/s/some-page/inner-route"

# Aura context — `fwuid` and `loaded` come from the live site (see "fwuid" section below)
FWUID = "<copy from a live DevTools request>"
APP_LOADED = "<also from DevTools>"

AURA_CONTEXT = quote(json.dumps({
    "mode": "PROD",
    "fwuid": FWUID,
    "app": "siteforce:communityApp",
    "loaded": {"APPLICATION@markup://siteforce:communityApp": APP_LOADED},
    "dn": [], "globals": {}, "uad": True,
}, separators=(",", ":")), safe="")


def build_message(classname: str, method: str, params: dict) -> str:
    payload = {"actions": [{
        "id": "77;a",
        "descriptor": "aura://ApexActionController/ACTION$execute",
        "callingDescriptor": "UNKNOWN",
        "params": {
            "namespace": "",
            "classname": classname,
            "method": method,
            "params": params,
            "cacheable": False,
            "isContinuation": False,
        },
    }]}
    return quote(json.dumps(payload, separators=(",", ":")), safe="")


def call_apex(classname: str, method: str, params: dict) -> dict:
    body = (
        f"message={build_message(classname, method, params)}"
        f"&aura.context={AURA_CONTEXT}"
        f"&aura.pageURI={quote(PAGE_URI, safe='')}"
        f"&aura.token=null"
    )
    r = cffi_requests.post(
        AURA_URL,
        data=body,
        headers={
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": BASE,
            "referer": f"{BASE}{PAGE_URI}",
            "x-sfdc-lds-endpoints": f"ApexActionController.execute:{classname}.{method}",
        },
        impersonate="chrome",
        timeout=30,
    )
    r.raise_for_status()
    action = r.json()["actions"][0]
    if action.get("state") != "SUCCESS":
        raise RuntimeError(f"Aura {action.get('state')}: {action.get('error')}")
    return action["returnValue"]["returnValue"]


# Usage
result = call_apex(
    classname="MyAppController",
    method="searchRecords",
    params={"pageNumber": 1, "pageSize": 250, "from": "2024-01-01", "to": "2024-12-31"},
)
records = result["records"]
total = result["totalRecords"]
```

## Discovering the Apex class + method

The `classname` and `method` come from the live site. Three reliable ways:

1. **DevTools Network tab** → click any action POST → request body. The `classname` and `method` are visible (URL-decoded) in the form data.
2. **Request header `x-sfdc-lds-endpoints`** is the cleanest source. It contains `ApexActionController.execute:MyController.myMethod`.
3. **HAR file** → grep for `descriptor.*ApexAction` or `x-sfdc-lds-endpoints`.

## `fwuid` — framework UID, rotates on org upgrade

`fwuid` is a hash identifying the Aura framework version deployed in this Salesforce org. **It rotates when Salesforce upgrades the customer's org** (every few weeks/months).

**Symptoms of stale `fwuid`:** the response is:
```json
{"actions": [{"state": "INCOMPLETE", "error": [{"exceptionType": "aura:ClientOutOfSync"}]}]}
```
or contains the string `aura:fwuidNotFound`.

**Recovery:** Re-fetch a fresh `fwuid` from a live page. Simplest: GET the page URL, parse the HTML response, find the inline JS that sets `Aura.initApplication({...})` or similar, extract `fwuid`. Or just have a fallback re-fetch helper that triggers when you see the error and retries.

**Mitigation in production:** Don't hardcode `fwuid` in source. Read it from env or a refreshable cache, with auto-refresh on the `ClientOutOfSync` error.

## `pageSize` silent caps

Salesforce Apex methods very often have a hardcoded server-side cap on `pageSize`. You can ask for 1000 and get 250. **Always test the actual cap before designing the pagination loop:**

```python
result = call_apex(..., params={"pageNumber": 1, "pageSize": 1000})
actual_cap = len(result["records"])  # likely much less than 1000
```

Common caps observed in the wild: 200, 250, 500. Plan accordingly.

## Pagination patterns

Aura APIs are usually `pageNumber` + `pageSize`. Two styles:

**Style 1 — known total:**
```python
total = first_page["totalRecords"]
pages = math.ceil(total / page_size)
for p in range(1, pages + 1):
    yield from call_apex(..., params={"pageNumber": p, "pageSize": page_size})["records"]
```

**Style 2 — fetch until short page:**
```python
page = 1
while True:
    records = call_apex(..., params={"pageNumber": page, "pageSize": page_size})["records"]
    if not records:
        break
    yield from records
    if len(records) < page_size:
        break  # last page
    page += 1
```

Style 2 is safer when `totalRecords` is buggy or absent.

## Year-slicing when results exceed query limits

Salesforce SOQL is hard-capped at 50,000 rows per query (and Apex methods often impose their own lower caps). If your full result set exceeds the cap, slice by a date field and concatenate:

```python
seen = set()
for year in range(2015, today.year + 1):
    params = {"from": f"{year}-01-01", "to": f"{year}-12-31", ...}
    for rec in iter_paginated(params):
        if rec["Id"] in seen:
            continue  # cross-slice dedup
        seen.add(rec["Id"])
        yield rec
```

The `seen` set is essential because adjacent slices can return the same record if a date boundary straddles your filter logic.

## Authentication — when you need it

Most public-facing Salesforce community portals expose at least one anonymous Apex method (typically a "search" or "list" method). Send `aura.token=null` and it works.

If the method requires login, you'll get `"state": "ERROR"` with `"exceptionType": "AuraHandledException"` and a redirect-to-login hint. Then:

1. Drive a Playwright login flow once
2. Capture the `sid` cookie + the `aura.token` from a network response
3. Reuse both in `requests` for bulk fetches (see `../browser-automation/`)

## Gotchas

- The endpoint URL must include `?r=<small_int>` and `aura.ApexAction.execute=1`. The `r` value is a counter; reuse `5` and you're fine.
- `message`, `aura.context`, `aura.pageURI`, `aura.token` all need URL-encoding. Use `urllib.parse.quote(..., safe='')` to be safe.
- The response is JSON, but the outer shape is `{"actions": [...]}` — even single-action calls. Always navigate to `["actions"][0]["returnValue"]["returnValue"]`.
- `state` can be `SUCCESS`, `ERROR`, or `INCOMPLETE`. Only `SUCCESS` is usable.
- `cacheable: false` should usually stay false for scraping — caching is for browser UX, irrelevant here.
- The `Referer` header should match the page where the action would naturally originate. Sites occasionally validate this.

## Related

- `../discovery/har-driven-workflow.md` — extract `classname`, `method`, `fwuid`, and full request shape from a HAR file
- `../browser-automation/session-cache.md` — capturing `sid` cookie + `aura.token` via Playwright login
