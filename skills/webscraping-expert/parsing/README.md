# Parsing

**Scope:** Turning raw responses into structured records. HTML, JSON, PDF, XLSX, HAR. Schema drift handling. Pagination limits.

## Files

| File | Contents |
|---|---|
| `structured-data.md` | **Check first.** JSON-LD / microdata / RDFa / OpenGraph embedded in the page markup — the cheapest, most redesign-proof extraction after a direct API. `extruct` one-shot, schema.org type map, `ItemList` as a free crawl frontier. |
| `document-extraction.md` | PDF (pdfplumber → camelot → OCR fallback), XLSX (openpyxl streaming), CSV, HTML tables. Download ladder when programmatic fetch fails. |

**Note:** API pagination caps and slicing strategies live in `../site-patterns/paginated-facet-search-api.md` — that pattern's "Bypassing the offset cap by facet-slicing" section covers the territory.
