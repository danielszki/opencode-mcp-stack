# Protection gaps — surfaces the anti-bot does not cover

## When you see this

The main pages of a site are behind an anti-bot wall (JS challenge, DataDome/Akamai/PerimeterX block, managed challenge) and the standard escalation (`curl_cffi` → stealth browser → residential) keeps failing. Before paying for a managed unblocker or declaring the target blocked, probe the surfaces that are usually **not** under the same rule.

Typical shape: a large, older site with many surfaces built over the years (feeds, widgets, exports, mobile API, legacy hosts). The HTML route is protected; a sibling route that serves the same records is not.

## How it works

Anti-bot products are configured per **path pattern, host, and content type**, not per dataset:

- **Static-asset exclusions are vendor integration defaults.** DataDome's default URI exclusion skips requests that look like JavaScript, CSS, images and fonts; Cloudflare does not score static resources unless static-resource protection is switched on. Some routers ignore the suffix (or read it as a format hint) and still render the dynamic page, so the edge sees an asset while the app returns data. That makes `.js` the strongest suffix candidate; `.css` and image suffixes rarely reach a data handler.
- **Feeds and sitemaps are open for syndication reasons.** RSS/Atom, sitemaps, oEmbed and embeddable widgets stay reachable so search engines, aggregators and partners keep working. `.rss`, `.xml` and `.json` work when the site already publishes that format, not because a vendor exempts the extension.
- **Rules are scoped per path and host.** DataDome, Akamai and Cloudflare all protect XHR/API traffic when configured to. A sibling XHR or host differs from the HTML page because the rule set does: Akamai protects a listed set of endpoints, Cloudflare rules match specific hostnames and paths, and a server-side module may be installed on some backends and not others.
- **APIs serving mobile apps, partner integrations or old frontends** are frequently on another host or version, outside the rule set written for the main site.
- **Export and report endpoints** ("download results", CSV/XLSX/PDF) are often added later and wired outside the protected path list.

The wall is a property of the route, not of the data. Find a route that carries the same records with a weaker rule, then decide whether you may use it (see the sign-off rule below).

## Pattern / code

Probe a matrix of variants from the **same client and egress that was blocked**, so the comparison isolates the route:

| Family | Variants to try against a blocked URL `P` |
|---|---|
| Suffix / format | `P.js`, `P.json`, `P.rss`, `P.atom`, `P.xml`, `P.csv` (suffix on the path, query kept), `P?format=json`, `P/feed`, header `Accept: application/json` |
| Sibling endpoints | the page's XHRs (DevTools Network → Fetch/XHR, or a HAR), `…/partial`, `…/fragment`, "load more" / infinite-scroll endpoints |
| API versions and hosts | `/api/v1` vs `/api/v2`, `api.`, `m.`, `mobile.`, `legacy.`, `old.`, `beta.`, regional or country hosts |
| Syndication | `/rss`, `/feed`, `sitemap*.xml`, oEmbed, AMP (`/amp`, `?amp=1`), print views (`?print=1`, `/print`) |
| Exports | "download"/"export" buttons, `Export*.ashx`, `/export?format=csv`, report endpoints (BI tools, `/reports/`) |
| App surfaces | the mobile app's API (from app traffic, if the project allows), partner/embed widget endpoints |

The probe below builds the suffix/format family for one URL, records every request as a JSONL line (the evidence for the exhaustion checklist), and classifies each response.

```python
import json
import random
import re
import time
import uuid
from urllib import robotparser
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

from curl_cffi import requests

CLIENT = "curl_cffi chrome"
FEED_SUFFIXES = (".json", ".rss", ".atom", ".xml")
# Variants that ask for a data format: a 200 text/html answer there is a catch-all or soft 404.
SUSPECT_LABELS = {".json", ".rss", ".atom", ".xml", ".csv", "/feed", "?format=json", "accept_json"}


def with_path_suffix(url: str, suffix: str) -> str:
    """Append to the path only; the query string is kept as is."""
    p = urlsplit(url)
    return urlunsplit(p._replace(path=p.path.rstrip("/") + suffix))


def with_query(url: str, **params: str) -> str:
    """Set params on the existing query, replacing any key already there."""
    p = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if k not in params]
    return urlunsplit(p._replace(query=urlencode(query + list(params.items()), quote_via=quote)))


def variants(url: str) -> list[dict]:
    v = [{"label": "base", "url": url, "headers": {}}]
    v.append({"label": "accept_json", "url": url, "headers": {"Accept": "application/json"}})
    if urlsplit(url).path not in ("", "/"):  # "/.json" on a root URL is not a format variant
        for s in (".js", *FEED_SUFFIXES, ".csv"):
            v.append({"label": s, "url": with_path_suffix(url, s), "headers": {}})
    v.append({"label": "/feed", "url": with_path_suffix(url, "/feed"), "headers": {}})
    for k, val in (("format", "json"), ("amp", "1"), ("print", "1")):
        v.append({"label": f"?{k}={val}", "url": with_query(url, **{k: val}), "headers": {}})
    return v


def detect_challenge(status: int, headers: dict, body: str) -> str | None:
    """Return the vendor whose challenge/block this response looks like, or None."""
    h = {k.lower(): str(v) for k, v in headers.items()}
    if h.get("cf-mitigated") == "challenge" or "Just a moment..." in body or "Attention Required!" in body:
        return "cloudflare"
    if status == 403 and h.get("server", "").lower() == "cloudflare" and "cf-ray" in h:
        return "cloudflare"  # WAF block page: no challenge marker, only the edge headers
    # x-datadome also appears on allowed responses; only a 4xx with it is a block.
    if "captcha-delivery" in body or ("x-datadome" in h and status >= 400):
        return "datadome"
    if "Reference #" in body and "You don't have permission" in body:
        return "akamai"
    if "x-amzn-waf-action" in h or (status == 202 and "challenge.js" in body):
        return "aws_waf"
    if status == 429 and any(k.startswith("x-kpsdk") for k in h):
        return "kasada"
    if "_Incapsula_" in body:
        return "imperva"
    if "px-captcha" in body:
        return "perimeterx"
    return None


def is_suspect(label: str, status: int | None, content_type: str) -> bool:
    """A 200 text/html on a data-format variant is usually a catch-all route or soft 404."""
    return label in SUSPECT_LABELS and status == 200 and content_type.startswith("text/html")


def visible_text(body: str) -> str:
    """Page text with volatile parts removed, so two renders of one page compare equal."""
    text = re.sub(r"(?is)<(script|style)\b.*?</\1\s*>", " ", body)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = re.sub(r"\b[0-9a-fA-F]{16,}\b|\d{6,}", "#", text)  # tokens, nonces, timestamps
    return " ".join(text.split())


def robots_allowed(robots_txt: str | None, url: str, user_agent: str = "*") -> bool | None:
    if robots_txt is None:
        return None  # robots.txt could not be fetched: unknown, not allowed
    rp = robotparser.RobotFileParser()
    rp.parse(robots_txt.splitlines())
    return rp.can_fetch(user_agent, url)


def fetch_robots(session: requests.Session, url: str) -> str | None:
    p = urlsplit(url)
    try:
        r = session.get(urlunsplit((p.scheme, p.netloc, "/robots.txt", "", "")), impersonate="chrome", timeout=30)
    except Exception:
        return None
    if detect_challenge(r.status_code, dict(r.headers), r.text[:50000]):
        return None  # a challenge page is not a robots.txt
    if r.status_code == 404:
        return ""  # no robots.txt: everything allowed
    if r.status_code != 200 or not r.headers.get("content-type", "").startswith("text/plain"):
        return None
    return r.text


def probe(session: requests.Session, v: dict, egress: str) -> dict:
    p = urlsplit(v["url"])
    rec = {"attempt": f"GET {p.path or '/'}{'?' + p.query if p.query else ''} [{v['label']}]",
           "url": v["url"], "client": CLIENT, "egress": egress,
           "evidence": uuid.uuid4().hex[:12],  # probe id: the JSONL line is the evidence
           "outcome": None,  # filled after you review the body
           "ts": time.time(), "label": v["label"], "headers_sent": v["headers"]}
    try:
        r = session.get(v["url"], headers=v["headers"], impersonate="chrome", timeout=30, allow_redirects=True)
    except Exception as e:
        return rec | {"status": None, "challenged": None, "error": repr(e)}
    body = r.text[:50000]
    ctype = r.headers.get("content-type", "")
    return rec | {
        "status": r.status_code,
        "final_url": r.url,
        "bytes": len(r.content),
        "content_type": ctype,
        "challenged": detect_challenge(r.status_code, dict(r.headers), body),
        "suspect": is_suspect(v["label"], r.status_code, ctype),
        "text": visible_text(body),
    }


def run(url: str, egress: str, evidence_path: str = "probes.jsonl", user_agent: str = "*") -> list[dict]:
    """egress names the network path, e.g. "local", "dc-US", "res-US" (exhaustion-checklist schema)."""
    session = requests.Session()
    robots = fetch_robots(session, url)
    results = []
    with open(evidence_path, "a") as fh:
        for v in variants(url):
            rec = probe(session, v, egress)
            rec["robots_allowed"] = robots_allowed(robots, v["url"], user_agent)
            base = results[0] if results else None
            comparable = base is not None and all(
                r["status"] is not None and r["challenged"] is None for r in (base, rec))
            rec["same_as_base"] = rec.get("text") == base.get("text") if comparable else None
            results.append(rec)
            fh.write(json.dumps({k: x for k, x in rec.items() if k != "text"}) + "\n")
            fh.flush()  # a crash or Ctrl-C keeps every probe already sent
            time.sleep(random.uniform(1, 3))
    return results


# results = run("https://example.com/items/123/history?page=2", egress="dc-US")
# A hit: status 200, challenged None, not suspect, same_as_base not True, and a body
# that carries records.
```

Every probe line stays in the JSONL file, hits and misses alike. A negative result is evidence for the exhaustion checklist, not waste. Each line is an attempt object in the exhaustion-checklist shape: `evidence` is the probe id, and `outcome` stays `null` until you have read the body and filled it in.

`same_as_base` is set only when both the base and the variant came back unchallenged (otherwise `null`), and compares visible text (scripts and styles stripped, whitespace collapsed, long hex/digit runs masked) so nonces and timestamps do not break equality. `true` means the router ignored the variant and served the same page. `false` is not evidence that the router read the suffix: the page may simply differ between two renders.

If a `.js` variant with a query is challenged, retry page 1 without the query before ruling the suffix out.

Once a gap returns records, check: does it paginate? does it accept the same filters/sort? what is the per-query cap? Then plan coverage by slicing (filters × sort orders × date windows) around the cap.

### Sign-off rule

A route that returns records is not automatically usable. Classify it:

| Class | Examples | Rule |
|---|---|---|
| **Intended-public** | feeds linked from the page, documented exports and APIs, sitemaps, open-data copies | Fine to use at a courteous pace |
| **Unintended** | a suffix trick on a protected route, an unlinked sibling endpoint, a path disallowed in `robots.txt` | `needs_signoff`: record it and get the project owner's explicit approval before production use |
| **Hard limit** | reaching the origin around the CDN (origin IP, unlisted origin host), anything behind a login | Stop. Not a sign-off item: do not use it, even with approval to "try anything" |

## Gotchas

- Gaps close without notice. Keep a fallback route, and alert on a sudden drop in records or a challenge marker in the response.
- A `200` can still be a challenge page. Always check headers and body for markers, never the status alone.
- A `200 text/html` on `.json` or `.rss` is usually the site's catch-all route or a soft 404, not data. The `suspect` flag catches it; open the body before counting it as a hit.
- Never probe a protected site from a personal/home IP; a ban there costs more than a proxy request.
- Unprotected routes are often unscaled: they were never sized for crawler traffic. Keep the pace well below what the main site tolerates, and never run a burst against a gap.
- `robots.txt` that could not be fetched is unknown, not permission. Record `robots_allowed: null` and treat the route as unintended until checked.
- Before Python 3.14, `urllib.robotparser` does not expand `*` or `$` (it matches path prefixes only). When the rules use them, read them by eye before trusting `robots_allowed: true`.

## Related

- `anti-bot-vendors.md` — identify the vendor first; its rules are scoped per path and host, which is why some sibling routes and suffixes sit outside them
- `ban-detection.md` — distinguish a WAF/IP block from a JS challenge before probing gaps
- `../discovery/autonomous-discovery.md` — sitemaps, embedded JSON and common API paths
- `../discovery/exhaustion-checklist.md` — this file is family D of the checklist
