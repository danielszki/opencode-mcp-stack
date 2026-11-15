# Recon report — final deliverable

At the end of every scrape, generate a **single self-contained HTML report** styled in a clean, neutral brand and hand it to the user alongside the bronze data file(s). This is the closing deliverable — what the user actually shows to teammates or archives for the project.

The report is generated **fresh per scrape, in code, not from a template file.** Use the style spec and the boilerplate skeleton below as the rendering contract; fill the sections with the run's actual content.

## When to generate

After self-critique is complete (see `self-critique.md`), and bronze has been validated end-to-end. The HTML report is the last artifact you produce in a run. Filename pattern: `recon-report-<sanitized-domain>-<YYYY-MM-DD>.html`, saved in the user's working directory. Share the absolute file path with the user along with the bronze data path(s).

## What the report must contain

Eight sections, in this order:

1. **Site Architecture** — what stack, what rendering model, where the data lives
2. **Requested Data Points** — table of every field the user asked for, whether it was captured, with which method, and validation status
3. **Discovered Endpoints** — every URL/API the scraper touched, with auth, format, pagination, and validation status
4. **Protection Assessment** — what anti-bot / rate-limit / auth protections were observed, what bypass worked, what to expect at scale
5. **Extraction Strategy** — the chosen approach ranked against alternatives, with cost/speed/validation columns
6. **Bronze Output** — file paths, schema, row counts, content hashes; this section is what the user uses to verify the data exists
7. **Recommendations** — punch list of specific follow-ups that close gaps / validate assumptions / unlock larger runs
8. **Self-Critique** — the five categories from `self-critique.md` (Gaps / Unvalidated / Assumptions / Staleness / Recommendations)

Do not omit sections. If a section has nothing in it, write a single line stating that explicitly ("No protections detected" / "All requested fields captured").

## Branding rules

Clean, neutral, monochrome visual identity — no logo, no brand marks, no decorative color:

- **Background:** pure white `#FFFFFF`
- **Headlines:** large bold sans-serif, near-black `#0A0A0A`, tight letter-spacing
- **Body:** 16px regular, dark gray `#2A2A2A`
- **Accents:** thin `#EEEEEE` rules only; no colored block fills in chrome
- **Status indicators:** subdued color text only:
  - Validated → `#1F7A1F` (forest green)
  - Partial → `#B8860B` (amber)
  - Unvalidated / Failed → `#B91C1C` (dark red)
- **Whitespace:** generous; content max-width 880px, 48–64px section gaps
- **Wordmark:** top-left, plain text `Recon Report` in the headline font — no logo image, no external asset.
- **Font stack:** `'Inter', -apple-system, 'Helvetica Neue', Helvetica, Arial, sans-serif`
- **No bright colors anywhere in chrome.** No blue buttons, no green badges, no decorative gradients.

## Generation rules

- **Single self-contained `.html` file.** All CSS inline in a single `<style>` block.
- **No JavaScript.** No client logic, no charts library, no analytics.
- **No external CSS or fonts loaded.** System font stack only — the report must render identically offline.
- **No logo image.** The header is a plain text wordmark; the report must render identically offline with zero external assets.
- **Responsive via max-width + padding.** Use the media query in the skeleton.
- **No sensitive data in the report.** Do not include raw cookies, `Authorization` headers, session tokens, credentials, or full HAR content. Reference them as "captured" / "stored in bronze" — never inline.
- **No data dump.** Don't paste the bronze CSV/JSON content into the report; reference its filepath and row count.

## Boilerplate skeleton

Use this exact CSS. Substitute the placeholder content (`{{ ... }}`) with the run's actual data.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Recon Report — {{ domain }}</title>
<style>
  body {
    margin: 0;
    background: #FFFFFF;
    color: #1A1A1A;
    font-family: 'Inter', -apple-system, 'Helvetica Neue', Helvetica, Arial, sans-serif;
    font-size: 16px;
    line-height: 1.55;
    -webkit-font-smoothing: antialiased;
  }
  .header {
    padding: 32px 48px;
    border-bottom: 1px solid #EEE;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .header .wordmark { font-weight: 700; font-size: 15px; letter-spacing: -0.01em; color: #0A0A0A; }
  .header .nav-stub { font-size: 13px; color: #888; }
  main {
    max-width: 880px;
    margin: 0 auto;
    padding: 80px 48px 96px;
  }
  h1 {
    font-size: 56px;
    font-weight: 700;
    letter-spacing: -0.02em;
    line-height: 1.05;
    color: #0A0A0A;
    margin: 0 0 16px;
  }
  h2 {
    font-size: 28px;
    font-weight: 700;
    letter-spacing: -0.01em;
    color: #0A0A0A;
    margin: 72px 0 24px;
  }
  h3 {
    font-size: 18px;
    font-weight: 600;
    margin: 32px 0 12px;
    color: #1A1A1A;
  }
  .lede {
    font-size: 18px;
    color: #4A4A4A;
    max-width: 640px;
    margin: 0 0 32px;
  }
  .meta {
    color: #888;
    font-size: 13px;
    margin-top: 0;
  }
  .meta strong { color: #1A1A1A; font-weight: 600; }
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0 32px;
    font-size: 14px;
  }
  th, td {
    text-align: left;
    padding: 12px 16px;
    border-bottom: 1px solid #EEE;
    vertical-align: top;
  }
  th {
    font-weight: 600;
    color: #1A1A1A;
    background: #FAFAFA;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.02em;
  }
  code {
    font-family: 'JetBrains Mono', 'SF Mono', Menlo, Consolas, monospace;
    font-size: 13px;
    background: #F5F5F5;
    padding: 2px 6px;
    border-radius: 3px;
    color: #1A1A1A;
  }
  pre {
    background: #FAFAFA;
    border: 1px solid #EEE;
    padding: 20px;
    border-radius: 6px;
    overflow-x: auto;
    font-family: 'JetBrains Mono', 'SF Mono', Menlo, Consolas, monospace;
    font-size: 13px;
    line-height: 1.6;
    color: #1A1A1A;
  }
  .status-ok { color: #1F7A1F; font-weight: 600; }
  .status-partial { color: #B8860B; font-weight: 600; }
  .status-fail { color: #B91C1C; font-weight: 600; }
  ul { padding-left: 24px; margin: 12px 0 24px; }
  li { margin: 6px 0; }
  .punch-list li { margin: 12px 0; }
  .punch-list .scope { color: #888; font-size: 13px; margin-left: 8px; }
  .selfcrit h3 { margin-top: 24px; }
  hr { border: 0; border-top: 1px solid #EEE; margin: 64px 0; }
  footer {
    padding: 32px 48px;
    border-top: 1px solid #EEE;
    color: #888;
    font-size: 13px;
    text-align: center;
  }
  @media (max-width: 640px) {
    .header { padding: 24px; }
    main { padding: 48px 24px 72px; }
    h1 { font-size: 40px; }
    h2 { font-size: 24px; margin-top: 56px; }
    table { font-size: 13px; }
    th, td { padding: 10px 12px; }
  }
</style>
</head>
<body>

<div class="header">
  <span class="wordmark">Recon Report</span>
  <span class="nav-stub">{{ YYYY-MM-DD }}</span>
</div>

<main>
  <h1>{{ domain }}</h1>
  <p class="lede">{{ One-to-two sentence summary: what was scraped, how, and the headline outcome. }}</p>
  <p class="meta">Generated <strong>{{ YYYY-MM-DD }}</strong> · <code>{{ N }} records</code> · {{ M }} endpoints discovered · bronze at <code>{{ path/to/bronze.csv }}</code></p>

  <h2>1. Site Architecture</h2>
  <table>
    <tr><th>Field</th><th>Value</th></tr>
    <tr><td>Framework</td><td>{{ Next.js / Custom SSR / ASP.NET WebForms / GraphQL / ... }}</td></tr>
    <tr><td>Rendering</td><td>{{ SSR / CSR / hybrid / static }}</td></tr>
    <tr><td>Detection method</td><td>{{ how identified — header, HTML signature, known-site lookup }}</td></tr>
  </table>

  <h2>2. Requested Data Points</h2>
  <table>
    <tr><th>Field</th><th>Source</th><th>Method</th><th>Status</th></tr>
    <tr>
      <td>{{ field_name }}</td>
      <td>{{ raw HTML / rendered DOM / API / etc. }}</td>
      <td><code>{{ selector / JSON path / endpoint }}</code></td>
      <td class="status-ok">Validated</td>
    </tr>
    {{ ... rows per field ... }}
  </table>

  <h2>3. Discovered Endpoints</h2>
  <table>
    <tr><th>Endpoint</th><th>Method</th><th>Auth</th><th>Format</th><th>Pagination</th><th>Status</th></tr>
    <tr>
      <td><code>{{ /api/v1/foo }}</code></td>
      <td>{{ GET }}</td>
      <td>{{ none / cookie / Bearer }}</td>
      <td>{{ JSON / HTML / GeoJSON }}</td>
      <td>{{ cursor / offset / none }}</td>
      <td class="status-ok">Validated</td>
    </tr>
    {{ ... }}
  </table>

  <h2>4. Protection Assessment</h2>
  <table>
    <tr><th>Mechanism</th><th>Status</th><th>Evidence</th><th>Impact at scale</th></tr>
    <tr><td>{{ Cloudflare }}</td><td>{{ Active / Not detected }}</td><td>{{ cf-ray header, challenge HTML }}</td><td>{{ requires curl_cffi impersonate or stealth browser }}</td></tr>
    {{ ... }}
  </table>

  <h2>5. Extraction Strategy</h2>
  <table>
    <tr><th>Rank</th><th>Approach</th><th>Coverage</th><th>Cost</th><th>Validation</th></tr>
    <tr><td>1</td><td>{{ direct JSON API replay }}</td><td>{{ all fields }}</td><td>Low</td><td class="status-ok">Validated</td></tr>
    {{ ... }}
  </table>

  <h2>6. Bronze Output</h2>
  <table>
    <tr><th>File</th><th>Records</th><th>Schema</th><th>Content hash (first 12)</th></tr>
    <tr>
      <td><code>{{ listings-bronze.csv }}</code></td>
      <td>{{ 1,247 }}</td>
      <td>{{ source, source_record_id, fetched_at, content_hash, payload }}</td>
      <td><code>{{ a1b2c3d4e5f6 }}</code></td>
    </tr>
  </table>

  <h2>7. Recommendations</h2>
  <ul class="punch-list">
    <li>{{ specific follow-up }} <span class="scope">{{ closes which gap; estimated cost }}</span></li>
    {{ ... }}
  </ul>

  <h2>8. Self-Critique</h2>
  <div class="selfcrit">
    <h3>Gaps</h3>
    <p>{{ specifics, or "None — all requested fields captured." }}</p>

    <h3>Unvalidated claims</h3>
    <p>{{ anything reported as working but not tested end-to-end }}</p>

    <h3>Assumptions</h3>
    <p>{{ load-bearing assumptions not verified }}</p>

    <h3>Staleness risk</h3>
    <p>{{ time- or context-dependent factors that may invalidate the scraper later }}</p>

    <h3>Recommendations (drill-down)</h3>
    <p>{{ punch list specifics, with effort estimates }}</p>
  </div>
</main>

<footer>
  webscraping-expert
</footer>

</body>
</html>
```

## Status indicator usage

In tables and inline text:

- `<span class="status-ok">Validated</span>` — extraction method tested end-to-end, confirmed working
- `<span class="status-partial">Partial</span>` — method identified but not fully verified (e.g. tested page 1 only, not full pagination)
- `<span class="status-fail">Unvalidated</span>` — theoretical / assumed, never tested

Pair status with the **Why** in the cell next to it where space allows. Don't use the colors anywhere else — they're load-bearing for the validation story.

## Anti-patterns

- **Pasting raw payloads into the report** — bronze data goes in the bronze file, not in the HTML. The HTML references the file path; it doesn't duplicate.
- **Including cookies / tokens / credentials** — even if "needed for reproducibility", do not embed. Reference as `[redacted]` or describe the auth shape ("session cookie via login flow") without printing values.
- **Adding charts / graphs / JavaScript visualizations** — the report is static and printable. If a chart is genuinely useful, generate it as an inline SVG, otherwise skip.
- **Decorative colors** — the only colors in the report are black, grays, and the three status indicators. No blue links, no green success banners, no orange callouts. Keep the report strictly monochrome.
- **Padding self-critique with platitudes** — if there are no gaps, say "None — all requested fields captured." Don't invent risks just to fill the section.

## Related

- `self-critique.md` — feeds Section 8 of the report; run the critique before generating the HTML
- `medallion-architecture.md` — bronze paths/schemas reported in Section 6 follow the medallion contract
- `anti-patterns.md` — the recommendations in Section 7 often point at one of these
