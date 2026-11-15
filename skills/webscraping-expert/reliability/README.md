# Reliability

**Scope:** Making extractions survive at scale. Concurrency, resume after crash, idempotent re-runs, retry policies, progress monitoring.

If you're scraping >100 records or the job will be scheduled, read this folder.

## Files

| File | Contents |
|---|---|
| `concurrency-curl-cffi.md` | When to parallelize, how to ask the user before doing it, ThreadPool patterns, rate limiting. Plus specific gotcha: `curl_cffi.Session` serializes — need per-thread sessions with `threading.local()` for true parallelism. |
| `resumable-extraction.md` | Checkpoint system, incremental `.jsonl` writes, restart-without-data-loss patterns. |
| `idempotent-runs.md` | Load known IDs from destination on startup, skip fetches for records already present. First-run vs subsequent-run trade-offs. |
| `live-monitor.md` | Real-time progress dashboard via stdlib HTTP server + browser polling. |
