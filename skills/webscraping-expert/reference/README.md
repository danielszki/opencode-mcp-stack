# Reference

**Scope:** Quick lookup material — libraries, copy-paste patterns, glossary, skill-wide contracts (medallion architecture), anti-patterns, the self-critique discipline, and the final HTML report spec. Not narrative; just look up what you need.

## Files

| File | Contents |
|---|---|
| `libraries.md` | Full library catalogue — install, when to use, examples. `curl_cffi`/`primp`/`rnet`, `playwright`/`patchright`/`camoufox`/`nodriver`, `scrapling`/`crawl4ai`/`firecrawl`, `beautifulsoup4`, `lxml`, `pdfplumber`, etc. |
| `ai-extraction.md` | LLM-driven & adaptive scraping: `crawl4ai`, `firecrawl`, `scrapling`, `ScrapeGraphAI`, `browser-use`; the roll-your-own markdown→LLM→schema pattern; when NOT to use AI. |
| `scrapling.md` | Deep dive on Scrapling (~67k★): fetcher-tiers→ladder mapping, adaptive selectors, `solve_cloudflare`, HTTP/3, spider (pause/resume, multi-session), CLI, MCP server. |
| `common-patterns.md` | Copy-paste working snippets for the most common needs (session setup, JSON paginated fetch, table parsing, fallback/mirror sources, fixture-fallback). |
| `medallion-architecture.md` | Bronze-first delivery contract. Defines bronze / silver / gold, when silver/gold are opt-in by user level, and minimum bronze schema. |
| `anti-patterns.md` | "What NOT to do" — bad/good code pairs covering process, stack choice, site-pattern gotchas, validation, hygiene. |
| `self-critique.md` | Five-category checklist (Gaps / Unvalidated / Assumptions / Staleness / Recommendations) to run before declaring done. Calibrated per user level. |
| `recon-report.md` | Final HTML deliverable spec — neutral monochrome report Claude generates at end of every scrape. Section structure, style rules, full boilerplate. |
