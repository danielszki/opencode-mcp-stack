# Autonomous Discovery Checklist

Before asking the user for help, try these in order. Each should take <30 seconds.

## 1. Robots & sitemap (30s)

```bash
curl https://site.com/robots.txt
curl https://site.com/sitemap.xml
```

Look for:
- `Sitemap:` lines → find the data URLs
- `Disallow:` lines → often leak API paths the site doesn't want indexed but still uses
- API paths like `/api/v1/`, `/graphql`, `/data/`

## 2. Common API conventions

Try these URLs (via GET with `Accept: application/json`):

```
/api
/api/v1
/api/v2
/api/health
/api/docs
/openapi.json
/swagger.json
/swagger/ui
/graphql
/_next/data/
/wp-json/wp/v2/
/wp-json/         # WordPress
/.well-known/     # OIDC, etc.
```

If any return JSON, inspect the shape.

## 3. Platform fingerprint

Detect the backend via response headers, meta tags, or cookie names:

| Signal | Likely platform | API pattern |
|--------|-----------------|-------------|
| `X-Powered-By: Next.js` | Next.js | `/_next/data/{buildId}/...json` |
| `__NEXT_DATA__` script tag | Next.js | same |
| `wp-content/` in HTML | WordPress | `/wp-json/wp/v2/` |
| `Shopify.theme` | Shopify | `/products.json`, `/collections.json` |
| `window.__NUXT__` | Nuxt.js | API in network tab |
| Drupal.settings | Drupal | `/jsonapi/` |
| `ckan` in meta | CKAN data portal | `/api/3/action/package_search` |
| Socrata | Open data | `/resource/{id}.json` |

## 4. View source + search for JSON

```
view-source:https://site.com/page
```

Ctrl+F for:
- `__NEXT_DATA__` — initial Next.js payload
- `__INITIAL_STATE__` — Redux state
- `window.__preloadedData` — Ember/Angular
- `<script type="application/ld+json">` — structured data
- `<script type="application/json">` — generic embedded JSON

These usually contain the whole initial page data already — no API call needed.

## 5. Check if data is in a static file

Inspect `<a href="">` and `<link>` for:
- `.csv`, `.xlsx`, `.json`, `.zip`, `.xml`, `.pdf`
- CDN URLs (`cdn.site.com`, `s3.amazonaws.com`)

Many "interactive" sites download a full dataset once and render it client-side.

## 6. GitHub / public repos

If the site is open data or government:
- Search GitHub for the org name
- Data is often on GitHub or GitLab, not the website
- Data.world, Kaggle also mirror public datasets

## 7. Google dorks

```
site:site.com filetype:csv
site:site.com filetype:xlsx
site:site.com filetype:json
"api.site.com" OR "site.com/api"
```

## 8. Wayback Machine

If current site blocks scraping or has removed data:
- `https://web.archive.org/web/*/site.com/*`
- Sometimes old HTML is easier to parse than current rendered SPA

## Time budget

Spend at most 5 minutes on autonomous discovery. If nothing works, switch to the user-guided DevTools workflow — don't waste time guessing.

## When to stop and ask

Ask the user for help when:
- You've tried 3+ common API patterns with no success
- The response is a login wall
- The data is clearly dynamic (interactive filters, hover tooltips) and the API isn't obvious from URL patterns
- You need session-specific cookies you can't generate
