# Idempotent / incremental runs

Pattern for production scrapers: the **first** run is full-history, every **subsequent** run only fetches new records. This is essential when:

- A monthly cron triggers the crawler
- Crashes are recoverable without re-fetching everything
- The target has cap-per-day limits (proxy budget, target rate limit)
- Detail fetches are expensive (one per record)

## The pattern

On startup, the crawler loads the set of record IDs already present in the destination. It passes that set to the extractor. The extractor skips records whose ID is in the set — before any expensive fetch.

```python
# At flow start
known: frozenset[str] = frozenset()
if params.skip_known:
    with Session(engine) as session:
        known = get_known_record_ids(session, source=SOURCE, ...)
    logger.info(f"Loaded {len(known)} known IDs — will skip")

records = crawl(
    from_year=2015,
    to_year=2026,
    proxy_url=settings.proxy_url,
    known_record_ids=known,
)
```

Inside the crawler:

```python
def crawl(
    *, from_year: int, to_year: int, proxy_url: str | None,
    known_record_ids: frozenset[str] = frozenset(),
) -> Iterator[Record]:
    for page in iter_pages(...):
        for source_record_id, internal_id, row in parse_page(page):
            if source_record_id in known_record_ids:
                continue  # skip BEFORE the expensive detail fetch
            detail = fetch_detail(internal_id)  # only paid for new records
            yield Record(source_record_id=source_record_id, ..., **detail)
```

## Where to check the known set

**Skip as early as possible** to maximize savings:

1. **Before detail fetch** (most common, biggest savings)
2. **Before pagination** (when list is sorted newest-first and you've seen the latest known ID, you can stop)
3. **Before upsert** (last-resort dedup — DB upsert will be a no-op, but you wasted the fetch)

Most savings come from #1. A typical N+1 crawler costs 1 list request per page + N detail requests per page. Skipping known records skips all the detail requests.

## Getting the known set

The implementation depends on your destination:

```python
# Postgres / SQLAlchemy
def get_known_record_ids(session: Session, *, source: str) -> frozenset[str]:
    stmt = select(BronzeRecord.source_record_id).where(BronzeRecord.source == source)
    return frozenset(session.execute(stmt).scalars().all())

# SQLite
def get_known_record_ids(conn: sqlite3.Connection, *, source: str) -> frozenset[str]:
    cur = conn.execute("SELECT id FROM records WHERE source = ?", (source,))
    return frozenset(row[0] for row in cur)

# JSON file
def get_known_record_ids(path: Path) -> frozenset[str]:
    if not path.exists():
        return frozenset()
    return frozenset(json.loads(path.read_text()))

# MongoDB
def get_known_record_ids(coll, *, source: str) -> frozenset[str]:
    return frozenset(doc["record_id"] for doc in coll.find({"source": source}, {"record_id": 1}))
```

The crawler shouldn't know about the storage — it just receives a `frozenset[str]`.

## Trade-offs

**First run cost:** Higher than necessary. The first run fetches everything because `known_record_ids` is empty. Subsequent runs are cheap.

**Memory:** A frozenset of 100k 30-char strings is ~6 MB. For 10M records, ~600 MB — at that scale, switch to a Bloom filter or a "since timestamp" query instead.

**Re-fetching when records change:** This pattern assumes a record's contents don't change after first ingestion. If they do (e.g. a listing's price or status gets updated later), you need an additional update path — typically a periodic "refresh window" that re-fetches the last N days of records regardless of `known_record_ids`.

## The "refresh window" addition

For cases where records can be updated upstream after first ingestion:

```python
def crawl(*, known_record_ids: frozenset[str], refresh_days: int = 30, ...):
    today = date.today()
    cutoff = today - timedelta(days=refresh_days)

    for source_record_id, internal_id, row in iter_records():
        created_at = parse_date(row.get("created_at"))
        # Always re-fetch recent records — they may have new info
        if created_at and created_at >= cutoff:
            yield fetch_full(internal_id)
            continue
        # Older records: only fetch if unknown
        if source_record_id in known_record_ids:
            continue
        yield fetch_full(internal_id)
```

This gives you:
- New records: fetched (always)
- Recent records (last 30 days): re-fetched on every run (captures updates)
- Old records: fetched once, then skipped forever

## Don't dedup with `seen` set when `known_record_ids` covers it

If you already have `known_record_ids`, adding a separate `seen` set inside the crawler is redundant unless the source genuinely emits the same record twice within a single run.

```python
# Redundant when known_record_ids is used
seen: set[str] = set()
for rec in source:
    if rec.id in seen:  # ← redundant
        continue
    seen.add(rec.id)
    if rec.id in known_record_ids:
        continue
    yield rec
```

Drop `seen` unless you have evidence of intra-run duplicates.

## Combined with resumable checkpoints

`known_record_ids` covers "what's done historically". `checkpoint.json` covers "where we are in this run". Use both for production crawlers:

- Crash mid-run → checkpoint resumes the page/record cursor
- Restart cleanly → `known_record_ids` skips already-finished records
- See `resumable-extraction.md`

## Related

- `resumable-extraction.md` — checkpoint pattern for mid-run resume
- `concurrency-curl-cffi.md` — when skipping known records lets you parallelize the remainder
