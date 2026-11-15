# Medallion architecture — bronze first, silver opt-in

The skill's default output contract. Every scrape lands in a **bronze** (raw) layer first. Cleaning, typing, deduplication, and analytics views (silver / gold) are explicit follow-ups, never silent steps.

## What the three layers mean

| Layer | Contents | Schema | Mutability |
|---|---|---|---|
| **Bronze** (a.k.a. raw) | Whatever the source returned, persisted as-is — full JSON payload, full HTML response, full CSV row, PDF blob. Plus minimal capture metadata. | One row per source record (or one file per page). Wide JSON column / blob column for the payload. | Append-only; never edited in-place. |
| **Silver** (a.k.a. cleaned / typed) | The bronze data, normalized: dates parsed, strings trimmed, types coerced, duplicates merged, optional rejects table for malformed rows. | Tight typed schema designed for the data, one row per logical record. | Recomputed from bronze; can be rebuilt from scratch. |
| **Gold** (a.k.a. analytics / serving) | Aggregations, joins across sources, derived metrics, time-series rollups, reports. | Whatever the consumer needs — fact/dim tables, materialized views, denormalized features. | Recomputed from silver. |

The layers form a one-way pipeline: **bronze → silver → gold**. Each downstream layer can be rebuilt from the layer above without re-scraping.

## Why bronze-first matters

1. **Source-of-truth durability.** The site you're scraping today may change tomorrow — fields renamed, layout reflowed, vendor swapped. Bronze preserves the original payload so you can recompute new silver schemas later without re-scraping.
2. **Change history.** Hashing each bronze row by content lets you detect when a record changed (price updated, availability changed) — impossible if you only kept the cleaned version.
3. **Honest failures.** A parser bug in silver doesn't destroy data; you fix the parser and re-run silver from bronze. Without bronze, parser bugs are silent data loss.
4. **Cheap incrementality.** Bronze upserts by natural key + content hash. Silver gets rebuilt from the deltas, not the full set.

## Minimum bronze schema

For any new scrape, the bronze table should have at least:

```
source            text       -- which scraper/source produced this row
source_record_id  text       -- the source's own ID for this record
fetched_at        timestamptz -- when we captured it
content_hash      text       -- sha256 of the canonical-JSON payload
payload           jsonb      -- the full raw response
```

Natural key: `(source, source_record_id, content_hash)` — same record fetched twice with no changes deduplicates; changes produce a new row (change history).

For HTML-page scrapes, persist the original HTML in `payload` as well — re-parsing the same HTML with a fixed extractor is cheaper than re-fetching the page.

## When to propose silver to the user

**Default: don't.** Bronze is the contract. Silver is extra work the user must opt into.

| User level | Silver-prompting policy |
|---|---|
| New to scraping | **Never ask.** Deliver bronze in their chosen format (CSV / JSON / Excel / DB) and stop. They will tell you if they want more. |
| Some experience | **Offer once, in one line**, after bronze is delivered and confirmed: *"Want me to clean & type this — parse dates, dedupe, drop empty rows?"* If they say no, stop. |
| Experienced | **Ask explicitly** after bronze is confirmed: *"Bronze is in. Want silver (typed/cleaned) on top? Or gold (aggregations, joins, derived metrics)?"* Walk through proposed silver schema before building. |

**Never silently transform.** If the user says "give me the product listings as CSV", the CSV is bronze: every column the source exposed, dates as strings, status as the raw value, no derived fields. Silver is opt-in.

**Never propose silver during initial intake.** Get bronze working end-to-end first. Only after the user has confirmed bronze meets their need does silver become a topic.

## Why we don't ask the simple user about silver

A first-time scraping user thinks of one output: the spreadsheet at the end. Asking them about "would you like a normalized silver layer" forces them to weigh a concept they don't have. The right behavior is: build bronze, hand them the spreadsheet, let them see it works, and let them ask for the next step. If they never ask, bronze was the right scope.

## What "bronze format" looks like by output choice

| Output the user asked for | Bronze form |
|---|---|
| CSV | One row per source record, columns = whatever the source exposes (no renaming), dates as strings. Add `fetched_at` and `source_url` columns. |
| Excel (.xlsx) | Same as CSV. One sheet per source or per page-type. |
| JSON | Array of objects; one object per source record, keys = source's own keys. Add a top-level `meta: {fetched_at, source_url, source}` envelope. |
| Database | Table per source. Schema = the minimum bronze schema above. Index on `(source_record_id, content_hash)` for upsert. |

## Blob-bronze: raw bytes on object storage + manifest sidecar

The minimum bronze schema above suits **row-shaped** sources (records into Postgres). For **file/document/API-dump** sources — XLSX/ZIP/PDF/NetCDF downloads, or an API response you want byte-exact — the durable pattern is **raw bytes on object storage (S3/GCS) with a JSON manifest sidecar**, not a database row. Persist the response *exactly as received* (no decode, no reshape) so silver can be rebuilt against the original bytes forever.

**Layout — dated snapshot + `latest` pointer, each with a `.meta.json` sidecar:**

```
s3://<bucket>/<domain>/<slug>/raw/2026-07-02T14-03-01Z.xlsx        # immutable dated snapshot
s3://<bucket>/<domain>/<slug>/raw/2026-07-02T14-03-01Z.meta.json   # its manifest
s3://<bucket>/<domain>/<slug>/raw/latest.xlsx                      # pointer to newest
s3://<bucket>/<domain>/<slug>/raw/latest.meta.json
```

For multi-file runs (e.g. one response per area × year), write a **run folder** with a run-level manifest listing every file + its size + hash:

```
raw/2026-07-02T14-03-01Z/<area>-<year>.json   (many)
raw/2026-07-02T14-03-01Z.meta.json            # {files:[{name, bytes, sha256}], stats:{...}}
```

**Manifest sidecar** — the audit trail that makes bronze trustworthy:

```json
{
  "source": "entsoe_spot", "upstream_url": "https://...",
  "fetched_at": "2026-07-02T14:03:01Z", "sha256": "…", "bytes": 184320,
  "content_type": "application/vnd.ms-excel",
  "run_id": "<orchestrator-run-id>",           // ties the artifact back to the flow run
  "schema": "entso_tyndp_v2024", "coverage": {"countries": ["DE","FR"], "years": [2024]},
  "stats": {"rows": null, "note": "parsing deferred to silver"}
}
```

**Content-addressed idempotency.** Hash the raw bytes; if the hash matches the last snapshot, the source hasn't changed — skip the write (or write a pointer, not a duplicate). Content-addressed keys (`…/<stem>.<sha256[:16]>.<ext>`) are never overwritten, so re-runs are safe and history is preserved for free.

**Also emit a bronze meta row** (a lightweight DB register, one row per extract run) alongside the S3 write — it makes runs queryable ("what did we fetch, when, how big, did it change?") without listing the bucket. This mirrors the medallion contract: the *bytes* are bronze; parsing them into typed rows is silver.

## Related

- `../site-patterns/templated-cms-schema-drift.md` — the silent renaming problem that bronze protects against
- `../site-patterns/odata.md`, `../site-patterns/pxweb.md`, `../site-patterns/sdmx-jsonstat.md` — statistics APIs whose code→label joins belong in silver, not the raw pull
- `../reliability/` — incremental sync, watermarks, restartable extraction; all assume bronze as the persistence layer
- `../reliability/idempotent-runs.md` — content-hash skip-before-fetch mechanics
- `common-patterns.md` — broader skill conventions (fixture-fallback, mirror sources)
