# Intake flow — Some experience

Run this flow when the user picked **"Some experience"** at Q1.

## How to run this flow

This level has two acceptable modes, in order of preference:

**Mode A — Mixed `AskUserQuestion` + text** *(preferred when the client supports it)*: send the discrete-choice questions (Q1 starting point, Q4 input type, Q5 auth, Q6 output format) as `AskUserQuestion` boxes; send the free-text ones (Q2 data needed, Q3 volume) as one short text message. Order: ask Q1 alone (the answer changes whether to run discovery first), then send Q2+Q3 as a single text message, then Q4, Q5, Q6 as separate `AskUserQuestion` boxes (or batch 2–3 of them via the multi-question form of `AskUserQuestion`).

**Mode B — Single bundled text message** *(fallback when `AskUserQuestion` is unavailable)*: send all six questions as one numbered list with short context lines.

In both modes:
- **Define niche terms inline, in one sentence each**, the first time they appear: `curl`, `HAR`, anything proxy/TLS-related, anything cookie/auth-related, "persisted query", "viewstate". Don't assume the user knows them.
- Tone: collegial peer. Short explanations for niche terms, no explanations for day-1 HTTP vocabulary.
- If the user responds with only partial answers, gently ask for what's missing — don't restart the intake.

---

## Mode A — `AskUserQuestion` boxes

### Q1 — Starting point

```
question: "What kind of starting point do you have?"
header:   "Starting point"
options:
  - label: "Exact URL of the data page"
    description: "You can open it and the data is right there."
  - label: "Site root / entry URL, data is inside somewhere"
    description: "I'll traverse the site (sitemap → search → link-graph BFS) to find the data page."
  - label: "No URL — just a topic"
    description: "I'll run a Google-operator sweep (≥300 queries) to find candidates first."
```

Follow up with one text message asking for the actual URL / topic value.

### Q2 + Q3 — Data + volume (one text message)

```
While I think about Q1, two quick freeform questions:

- **What to extract** — concretely (e.g. "table X with columns A, B, C", "all product cards on the listing page").
- **Rough volume** — record count estimate. Helps me plan pagination strategy.
```

### Q4 — Input type

```
question: "I need to see how your browser talks to the site. What can you give me?"
header:   "Input"
options:
  - label: "I'll paste a curl command"
    description: "curl = one specific request copied from DevTools → right-click → Copy as cURL. Good for single-endpoint scrapes."
  - label: "I'll drop a HAR file"
    description: "HAR = recording of every request on a page (cookies, headers, the lot). Best for multi-step flows. DevTools F12 → Network → ☑ Preserve log → reload + interact → ↓ Export HAR (sanitized)."
  - label: "Try discovery first — no input from me"
    description: "I attempt to find the API on my own. ~60% success; if I get stuck I'll come back asking for the HAR."
```

Follow up based on choice:
- "Paste curl" → "Paste it here when you're ready."
- "Drop HAR" → "Drag the .har file into the chat when you're ready. Tip: if `Export HAR (sanitized)` strips Cookie/Authorization headers I'll need, right-click in the request list → 'Save all as HAR with content' for the raw version."
- "Discovery first" → proceed without waiting.

### Q5 — Auth

```
question: "Is the page behind a login?"
header:   "Auth"
options:
  - label: "No — public"
    description: "Anyone can view the data without logging in."
  - label: "Yes — login required"
    description: "Capture the HAR *after* logging in (session token travels inside) or share credentials."
  - label: "Not sure"
    description: "Open the URL in private/incognito; if the data is visible, it's public."
```

### Q6 — Output format

```
question: "Where should the extracted data go?"
header:   "Output"
options:
  - label: "CSV (Recommended)"
    description: "Spreadsheet file, opens in Excel / Google Sheets. Safest default."
  - label: "JSON"
    description: "Structured text. Useful if another program reads it."
  - label: "Excel (.xlsx)"
    description: "Native Excel format."
  - label: "Database"
    description: "Only if you have one set up — Postgres, SQLite, etc."
```

---

## Mode B — Single bundled text message (fallback)

```
Quick intake — answer what applies:

1. **Starting point** — pick one and share it:
   - **(a) Exact URL** of the data page → paste it.
   - **(b) Site root / entry URL, data is inside somewhere** → paste the entry URL and tell me roughly what to look for. I'll traverse the site (sitemap → site search → scored link-graph BFS) to find the data page.
   - **(c) No URL — just a topic** → describe the data and target domain. I'll run a Google-operator sweep (≥300 queries) to find candidates first.

2. **Data needed** — what to extract, concretely (e.g. "table X with columns A, B, C", "all product cards on the listing page").

3. **Volume** — rough record count. Helps me plan pagination strategy.

4. **curl or HAR** — the gold input. With either, I can replicate the exact request your browser made instead of guessing selectors or reverse-engineering the JS.

   Quick definitions if these are new:
   - **curl** = a single request copied as a command-line string from DevTools (right-click any request in the Network panel → Copy → "Copy as cURL"). Good for one-endpoint scrapes.
   - **HAR file** = a recording of *all* requests, responses, cookies and headers from a session (a `.har` file you export from DevTools). Better for multi-step flows (login → search → detail) or when you're not sure which request has the data.

   If you have either, paste/drag it. If not, capture a HAR:
   DevTools (F12) → **Network** tab → ☑ Preserve log → reload page + do the actions that load your data → toolbar **download icon (↓)** → **"Export HAR (sanitized)..."** → drag the `.har` file into this chat.

   If sanitization strips `Cookie` / `Authorization` headers I'll need, right-click in the request list → **"Save all as HAR with content"** for the unsanitized version.

   Or say **"discover"** and I'll try to find the API on my own first (works ~60% of the time; if not I'll come back asking for the HAR).

5. **Authentication** — is the page behind a login? If yes, share credentials or (preferred) a HAR captured *after* logging in — the session token travels inside.

6. **Output format** — CSV / JSON / Excel / database?
```

When the user replies, summarize back what you understood in 2–3 lines before starting code — short confirmation, not a recap of every answer.

If they picked **(b)** at Q1, work from `../discovery/link-graph-traversal.md` to find the data page within the site.
If they picked **(c)**, work from `../discovery/google-deep-research.md` to surface candidate sites before continuing the rest of the intake.

---

## Final delivery — bronze first, offer silver once

Deliver the raw extracted data (bronze) in the format they picked at Q6 and confirm it works end-to-end. **Then, in one short message**, offer silver as an option:

```
Bronze is in — [N] records extracted to [their format]. Want me to clean & type it? I can parse dates, dedupe records, drop empty rows, normalize the column names.
```

If they say no or don't engage with it, stop — don't push. If they say yes, propose a silver schema before building it and confirm before writing code.

Do not propose gold (aggregations / analytics) unless they ask. The user at this level has enough vocabulary that you can use the term "bronze" naturally if you want — but don't lecture; one mention is enough.

See `../reference/medallion-architecture.md` for the contract details.
