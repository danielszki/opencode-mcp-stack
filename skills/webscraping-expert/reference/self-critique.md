# Self-critique — before declaring done

A discipline to run **at the end of every scrape**, before telling the user "bronze is in" / "done" / "extraction complete". The point is to flag what you might have missed — explicitly — instead of letting the user discover it later.

This is not optional. Even on a trivial scrape, do the 5-minute walkthrough below.

## When to run it

- After bronze has been written and validated end-to-end (sample row inspected, counts make sense)
- Before sending the final delivery message to the user
- Before generating the recon report (see `recon-report.md` — self-critique becomes Section 8 of the report)

If you're in the middle of an iterative loop ("fix this selector, re-run") the self-critique only fires when you're about to declare the loop complete. No need to run it every iteration.

## The five categories (always cover all five, in this order)

### 1. Gaps

Data points the user asked for that you **did not** capture, or captured partially. For each one:
- Which field is missing / incomplete
- Why you couldn't capture it (behind auth? not in any response? would need a different extraction technique?)
- What it would take to recover (different endpoint, browser, paid proxy, second pass)

Example:
> **Gap:** `published_date` is missing for ~12% of records. Cause: those records are in the "Archived" category, where the source omits the field entirely. To recover: cross-reference with the site's PDF annual summary (separate scrape).

If there are no gaps, write "**Gaps:** none — all requested fields captured." Don't skip the section.

### 2. Unvalidated claims

Anything you reported as "working" but didn't actually test end-to-end. Common offenders:
- Selectors found in HTML but never extracted with a parser
- API endpoints found in HAR but never replayed with a fresh request
- JSON paths identified but not parsed against a real response
- Pagination "should work" because the URL pattern is consistent — but you only fetched pages 1 and 2

For each one: name it, say what level of validation was done, say what full validation would require.

Example:
> **Unvalidated:** pagination beyond page 5 not tested. Page 1 and page 2 confirmed; pages 3–5 inferred from response metadata. Full validation = walk all pages and confirm `len(results) == reported_total`.

### 3. Assumptions

Things you took for granted but didn't verify. The big recurring ones:
- "Pagination follows the same pattern for all queries" — only tested one query
- "Schema is consistent across categories" — only tested one category
- "Field labels are stable" — same source family ([[templated-cms-schema-drift]]) frequently varies labels per tenant
- "Public access" — only tested without login, didn't try logged-in (which might expose more / different data)
- "Stable across time" — only ran today; pre-deploy frontends may emit different shapes

List the load-bearing assumptions. If one fails in production, what breaks?

Example:
> **Assumption:** parser tested on 5 records in the "Books" category. Other categories (Electronics, Clothing, Furniture) assumed consistent — not verified. Risk: a different category may emit different field names.

### 4. Staleness risk

What about the data / extraction is **time- or context-sensitive** and may invalidate the scraper later:
- Geo-locked content (prices in $USD when run from US IP, different from EU)
- Session-dependent state (logged-in vs anonymous viewing)
- A/B test layouts (different DOM for different user buckets)
- Frontend build IDs ([[graphql]] persisted queries change on deploy; [[spa-frameworks]] `_next/data/<buildId>` paths invalidate)
- Date-based content (today's "latest" is not tomorrow's)
- Counts/totals captured snapshot-in-time

Example:
> **Staleness:** prices are geo-locked. This run used a US sticky proxy; same scrape from EU IP returns EUR values via a different `currency` cookie. If user needs multi-region, parametrize the proxy region.

### 5. Recommendations

**Specific** next steps that would resolve gaps / unvalidated claims / assumptions. Not "re-run everything" — pinpoint the smallest action that closes the biggest unknown.

Format as a punch list:
- One bullet per recommendation
- Each scoped (which gap/assumption it addresses)
- Each estimated cost (1 line of code, 1 hour, 1 day)

Example:
> **Recommendations:**
> - To close "schema consistency" assumption: re-run parser against a sample of 10 records from Electronics + Furniture categories. ~5 minutes.
> - To close "pagination beyond page 5" gap: run the existing scraper to completion (all 47 pages) once and compare row count to reported total. ~30 minutes.
> - To handle frontend-deploy invalidation of doc_id: add a startup hook that extracts the current doc_id from the live JS bundle. ~1 hour. See `../site-patterns/graphql.md`.

## How to output

Self-critique is a **section in the final delivery message** — not a separate artifact. For the three approach levels:

**New to scraping** — Plain-language version, no jargon. Frame it as "things to double-check on your side":
> Before you use this, a few things to know:
> - I captured 87 records out of an expected ~90. Three were in a category I couldn't read because the source hid the date field. You might want to spot-check those by hand.
> - I tested the parser on one product category specifically. If you run this on other categories, check a few rows to make sure the columns look right.
> - The prices on this site vary by country. I scraped from a US connection — if you need other regions, let me know.

**Some experience** — Use the 5-category structure with plain headers. Skip jargon like "load-bearing assumption":
> ## Self-critique
> **Gaps:** ...
> **Unvalidated:** ...
> **Assumptions:** ...
> **Staleness:** ...
> **Recommendations:** ...

**Experienced** — Tight technical version with full vocabulary:
> ## Self-critique
> - **Gaps:** created_at missing in 12% (Discontinued category)
> - **Unvalidated:** pagination beyond page 5; `len(results) == total` not asserted
> - **Assumptions:** parser tested on Books cat only; schema drift untested across Electronics/Clothing/Furniture
> - **Staleness:** geo-locked prices (US IP); doc_id pinned for current frontend build
> - **Recommendations:** sample-test other categories (~5min); add doc_id refresh hook (~1h)

## Anti-patterns specific to self-critique

- **Don't pad it.** Five empty sections looks worse than three honest sections + two "none". Be specific or skip.
- **Don't list trivial gotchas as gaps.** "I didn't extract the page footer" is not a gap unless the user asked for the page footer.
- **Don't refuse to ship over self-critique.** The critique exists to surface risk, not to gate delivery. Ship bronze + critique together; let the user prioritize.
- **Don't apologize.** "I unfortunately couldn't..." reads as a status report on you. The user cares about the data and what to do next, not how hard you tried.

## Related

- `medallion-architecture.md` — self-critique is part of the bronze handoff; silver/gold proposals come after
- `anti-patterns.md` — most "gaps" map to one of the listed anti-patterns (e.g. "one-record validation" → schema drift gap)
