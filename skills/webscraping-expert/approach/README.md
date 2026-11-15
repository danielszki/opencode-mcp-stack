# Approach — intake flows by experience level

**Scope:** Step 0 of the skill (intake) is gated by the user's self-reported experience level. Each file in this folder is one intake flow.

`SKILL.md` always asks the experience question first (Q1, alone), then loads the matching flow from here.

## Files

| File | When to use | Style |
|---|---|---|
| `new-to-scraping.md` | User picked "New to scraping" (first time or close to it) | One question per message; explain what / why / how; define every technical term inline |
| `some-experience.md` | User picked "Some experience" (has built a scraper before) | All six questions in one message with short context lines |
| `experienced.md` | User picked "Experienced" (knows curl, HAR, TLS impersonation, proxies) | All six questions in one terse message, no explanations |

## What the intake covers

All three flows ask the same six things (in different depths):

1. Target URL
2. Data needed
3. Volume (rough record count)
4. curl or HAR (preferred capture; or autonomous discovery)
5. Authentication
6. Output format (CSV / JSON / Excel / database)

**What the intake does NOT ask:** frequency / recurring schedule. Recurring runs require infrastructure (cron, Prefect, Airflow, GitHub Actions) you cannot set up or maintain for the user. Build a one-shot script; the user schedules it themselves.
