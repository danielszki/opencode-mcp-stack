# Templated CMS — schema drift across deployments

A pattern that bites everyone the first time: a vendor sells a CMS / portal product to many customers. Each customer deploys the same template, but **field names, column headers, and JSON keys drift between installations**. Mapping you wrote for customer A will silently miss data from customer B.

## When you see this

- Multiple sites use what is obviously the same template (same layout, same UI controls, same JS bundles)
- Vendor branding present (footer "Powered by X", JS namespace, URL patterns)
- You're tempted to write a single hardcoded schema mapping ("the date column is always called 'Created At'")

Common offenders:
- WordPress installs with the same plugin (custom field names vary)
- Salesforce orgs sharing a managed package (label translations vary)
- ServiceNow instances across enterprises
- Product catalogs deployed across many stores
- Banking platforms (Temenos, Finastra) deployed across many banks

## How it goes wrong

In an illustrative catalog example, deployment A labels a field `"Created At"`. Deployment B uses `"Created at"` (lowercase `a`), `"Creation Date"`, or omits it. Hardcoding one label makes the mapping brittle.

Your code:
```python
created_at = payload["Created At"]  # KeyError on deployment B
```

…silently produces null values for an unknown percentage of records, and you discover it weeks later when someone asks why a dashboard is wrong.

## Mitigation — never assume, always validate

**Rule 1:** When configuring a new deployment, validate against real data before mapping:

```sql
-- Check what keys actually appear in raw payloads
SELECT k, COUNT(*) FILTER (WHERE coalesce(payload->>k, '') <> '') AS non_empty
FROM raw_records, jsonb_object_keys(payload) k
WHERE source = :deployment_name
  AND lower(k) ~ '(created|creation|date)'
GROUP BY k ORDER BY non_empty DESC;
```

This single query, run against ~50 records, tells you which key actually holds the data.

**Rule 2:** Store the per-deployment mapping in config, not in code:

```python
# config.py — one entry per deployment
FIELD_MAPPING_PER_DEPLOYMENT: dict[str, dict[str, list[str]]] = {
    "deployment_a": {"created_at": ["Created At"]},
    "deployment_b": {"created_at": ["Created at"]},
    "deployment_c": {"created_at": ["Creation Date"]},
    "deployment_d": {"created_at": ["Date"]},  # contextually disambiguated upstream
}
```

Then the crawler is generic and the config is the only place that changes per deployment.

**Rule 3:** Normalize in the parser, not in the consumer. If deployment D uses `Date` but the canonical name is `Created At`, rename at extraction time:

```python
def _normalize_created_at(payload: dict, deployment_key: str) -> dict:
    raw_keys = FIELD_MAPPING_PER_DEPLOYMENT[deployment_key]["created_at"]
    for key in raw_keys:
        if payload.get(key):
            payload["Created At"] = payload[key]  # canonical name
            break
    return payload
```

Downstream code only knows about `Created At`. Adding a deployment with `Creation Timestamp` is a one-line config edit.

## When the field is genuinely absent

Sometimes a deployment legitimately doesn't expose the field. Make that explicit:

```python
FIELD_MAPPING_PER_DEPLOYMENT = {
    ...
    "deployment_e": {"created_at": None},  # this deployment doesn't have it
}
```

Then dashboards can distinguish "0% because the field isn't exposed" from "0% because our mapping is wrong" — a critical difference for debugging.

## Case-sensitivity is the most common bug

Among all drifts, ASCII case is by far the most common: `Order Date` vs `Order date`, `Total Cost` vs `Total cost`, `Item Number` vs `Item number`. Many DOM-to-text conversions strip exactly one space or change exactly one letter.

When debugging a "this field is empty for this one deployment" issue, **always** print the exact key including case before assuming it's a data quality issue.

## Field discovery query (run for any new deployment)

```sql
-- All payload keys observed in this deployment, sorted by occurrence
SELECT k, COUNT(*) AS n
FROM raw_records, jsonb_object_keys(payload) k
WHERE source = :deployment
GROUP BY k ORDER BY n DESC LIMIT 50;
```

Run this immediately after the first batch lands. The list is your ground truth — don't trust intuition from another deployment.

## Related

- `../discovery/devtools-workflow.md` — how to inspect a new deployment cleanly
- `../parsing/document-extraction.md` — strategies for extracting data from drifting templates
