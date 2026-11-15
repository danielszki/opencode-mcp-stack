# Intake flow — Experienced

Run this flow when the user picked **"Experienced"** at Q1.

## How to run this flow

**Default: send all six questions in one terse text message.** A power user types `1: url=..., 2: prices+ratings, 3: ~5k, 4: HAR attached, 5: no, 6: parquet` faster than clicking through six dialog boxes. Don't slow them down.

No explanations, no jargon definitions. The user knows curl, HAR, TLS impersonation, persisted queries, proxies, sticky sessions — assume vocabulary parity. Skip the politeness padding. Skip the "let me know if you need help" footer.

If they hand you a HAR or curl directly without waiting for the intake, just go — don't insist on filling in every blank.

**Alternative: `AskUserQuestion` mode.** If the user has previously asked you to use clickable option boxes (or you're in a client where typing is awkward), batch Q1, Q4, Q5, Q6 as a single multi-question `AskUserQuestion` call (max 4 per batch), with Q2 and Q3 sent as a single short text message alongside. Compact labels — no descriptions longer than 10 words at this level.

---

## Default — terse text one-shot

```
Intake:
1. Starting point — (a) exact URL, (b) site root → I traverse to find the data page, or (c) just a topic → I run Google dorks (≥300 queries) for candidates
2. Data needed
3. Volume (rough)
4. curl/HAR (or "discover")
5. Auth (login? post-login HAR available?)
6. Output format
```

## Alternative — `AskUserQuestion` batch

Send Q1, Q4, Q5, Q6 in one `AskUserQuestion` call (4 questions max per batch):

```
questions:
  - question: "Starting point?"
    header: "Start"
    options:
      - label: "Exact URL"
      - label: "Site root → I traverse"
      - label: "Topic only → I run Google dorks"
  - question: "Input?"
    header: "Input"
    options:
      - label: "curl"
      - label: "HAR"
      - label: "Discover"
  - question: "Auth?"
    header: "Auth"
    options:
      - label: "None"
      - label: "Login required (post-login HAR available)"
      - label: "Login required (no HAR)"
  - question: "Output?"
    header: "Output"
    options:
      - label: "CSV"
      - label: "JSON"
      - label: "Parquet"
      - label: "Database"
```

Then send a separate short message for Q2 (data needed) and Q3 (volume).

After they reply, go straight to work. No recap.

If they picked (b) → `../discovery/link-graph-traversal.md`.
If they picked (c) → `../discovery/google-deep-research.md`.

---

## Final delivery — bronze first, then explicit silver/gold ask

Ship bronze in their requested format and confirm it works end-to-end. **Then ask explicitly:**

```
Bronze is in — [N] records, [content_hash dedup status], [resumable from <watermark> if applicable]. Next:
- silver (typed/cleaned, parsed dates, dedup by natural key + content hash, rejects to a separate table) — propose schema before building?
- gold (aggregations / time-series rollups / joins across sources) — what's the consumer?
- nothing — bronze is enough.
```

Use the full medallion vocabulary. Walk through proposed silver/gold schemas before writing code. Default to recomputable layers — silver and gold should rebuild from bronze without re-scraping.

See `../reference/medallion-architecture.md` for the canonical contract.
