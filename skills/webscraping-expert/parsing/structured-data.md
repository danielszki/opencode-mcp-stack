# Structured Data — JSON-LD, microdata, RDFa, OpenGraph

## Core principle

Many sites publish the exact data you want **inside the page markup, already structured**, so search engines can read it. This is the cheapest, most stable extraction path after a direct API — more stable than CSS selectors, because sites rarely refactor their SEO markup, and it survives visual redesigns that break scrapers.

**Check for structured data before writing a single CSS/XPath selector.** It is free data the site hands you on purpose.

Priority order (most useful first):

1. **JSON-LD** (`<script type="application/ld+json">`) — a clean JSON object, no DOM walking. By far the best case.
2. **Microdata** (`itemscope` / `itemprop` attributes) — structured, but you walk the DOM.
3. **RDFa** (`vocab` / `typeof` / `property` attributes) — same idea, rarer.
4. **OpenGraph / Twitter Cards** (`<meta property="og:*">`) — title, image, description, sometimes price/availability.
5. **Plain `<meta>` / `<link rel>`** — canonical URL, pagination (`rel="next"`), author, published date.

All of these ride the Level 1–2 HTTP response. No browser needed unless the markup is injected client-side (check: does it appear in `view-source:`? if yes, plain `requests` gets it).

---

## Step 1 — Is there any?

One grep tells you if it is worth parsing:

```python
import requests, re

r = requests.get(url, headers=HEADERS, timeout=30)
html = r.text

print("json-ld blocks:", len(re.findall(r'application/ld\+json', html)))
print("microdata:",      "itemscope" in html)
print("rdfa:",           "typeof=" in html or "vocab=" in html)
print("opengraph:",      len(re.findall(r'property=["\']og:', html)))
```

If `json-ld blocks > 0`, go straight to Step 2 and you are probably done.

---

## Step 2 — JSON-LD (the good case)

`extruct` handles every flavor at once and is the right default:

```python
# pip install extruct w3lib
import extruct
from w3lib.html import get_base_url

data = extruct.extract(
    html,
    base_url=get_base_url(html, url),
    syntaxes=["json-ld", "microdata", "rdfa", "opengraph"],
    uniform=True,   # normalize microdata/rdfa into the same shape as json-ld
)
# data["json-ld"] -> list of dicts, each with "@type"
```

Or parse JSON-LD by hand when you want zero dependencies:

```python
import json
from bs4 import BeautifulSoup

soup = BeautifulSoup(html, "html.parser")
blocks = []
for tag in soup.find_all("script", type="application/ld+json"):
    try:
        obj = json.loads(tag.string or "")
    except (json.JSONDecodeError, TypeError):
        continue
    # A block can be a dict, a list, or a {"@graph": [...]} wrapper
    if isinstance(obj, dict) and "@graph" in obj:
        blocks.extend(obj["@graph"])
    elif isinstance(obj, list):
        blocks.extend(obj)
    else:
        blocks.append(obj)

products = [b for b in blocks if b.get("@type") == "Product"]
```

### Schema.org types you will actually hit

| `@type` | Carries | Typical site |
|---|---|---|
| `Product` + `Offer` | name, SKU, price, currency, availability, brand, rating | e-commerce |
| `ItemList` / `BreadcrumbList` | ordered list of URLs → **free pagination / sitemap of a category** | listings, catalogs |
| `Article` / `NewsArticle` / `BlogPosting` | headline, author, datePublished, body, section | news, blogs |
| `JobPosting` | title, salary, location, employmentType, datePosted, validThrough | job boards |
| `Event` | name, startDate, location, offers | tickets, venues |
| `LocalBusiness` / `Organization` | address, geo, phone, openingHours | directories, maps |
| `Recipe`, `Review`, `AggregateRating`, `Person`, `RealEstateListing` | as named | niche verticals |

`ItemList` is the quiet hero: a category page's JSON-LD often lists every item URL on the page, giving you a crawl frontier without parsing any cards.

---

## Step 3 — Microdata / RDFa (walk the DOM)

Only if there is no JSON-LD. Let `extruct` with `uniform=True` flatten it into JSON-LD shape (above) so your downstream code does not care which syntax the site used. Hand-parsing microdata means walking `itemscope` subtrees and reading `itemprop` — tedious; prefer `extruct`.

---

## Step 4 — OpenGraph / meta fallback

When there is no schema.org markup, OG tags still give you the headline fields cheaply:

```python
def meta_map(soup):
    out = {}
    for m in soup.find_all("meta"):
        key = m.get("property") or m.get("name")
        if key and m.get("content"):
            out[key] = m["content"]
    return out

m = meta_map(soup)
title = m.get("og:title") or m.get("twitter:title")
price = m.get("product:price:amount") or m.get("og:price:amount")
canon = (soup.find("link", rel="canonical") or {}).get("href")
nxt   = (soup.find("link", rel="next") or {}).get("href")   # pagination for free
```

`<link rel="next">` / `rel="prev"` and `<link rel="canonical">` are the cheapest pagination and dedup signals on the page — use them before inventing page-number loops.

---

## Gotchas

- **Lies and staleness.** SEO markup can be wrong, rounded, or stale (price in JSON-LD lagging the cart price). When the number matters, cross-check one record against the rendered DOM or the API before trusting the whole field. Note it in self-critique.
- **Client-injected JSON-LD.** Some SPAs add JSON-LD after hydration. If `view-source:` has none but the rendered DOM does, you need a browser (Level 5) — or, better, find the API that fed it.
- **Multiple blocks, partial data.** Sites split data across several `ld+json` blocks (one `Product`, one `BreadcrumbList`, one `Organization`). Collect all blocks, then filter by `@type`; never assume the first block is the one you want.
- **`@graph` wrapper and `@id` references.** Nodes reference each other by `@id` (e.g. an `Offer` pointing to a `Product`). Resolve `@id` within the graph when a field you need lives on a referenced node.
- **HTML entities / trailing commas.** Hand-rolled JSON-LD is sometimes invalid JSON. `extruct` is more forgiving than `json.loads`; wrap manual parsing in try/except and move on rather than crashing the run.

---

## Related

- `../discovery/autonomous-discovery.md` — structured-data check belongs in the same first pass as `robots.txt` / `sitemap.xml`.
- `document-extraction.md` — once you have the record URLs from an `ItemList`, documents behind them are extracted here.
- `../reference/medallion-architecture.md` — store the raw JSON-LD object in bronze; promote parsed fields to silver.
