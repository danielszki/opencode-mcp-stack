# GraphQL

A single transport protocol used by apps of every size — from small SaaS dashboards to social networks at planetary scale. Once you recognize it, scraping a GraphQL backend is usually *easier* than a REST one: the query shape is explicit, pagination is standardized, and one endpoint covers everything. The catch is that "GraphQL" in the wild spans three very different security models, and the wire format isn't as uniform as the spec implies.

## When you see this

Recognize GraphQL by any of these signals:

- A POST to a path like `/graphql`, `/api/graphql`, `/query`, `/v1/graphql`, or `/gql`
- Request body contains the keys `query`, `variables`, `operationName`, or `extensions.persistedQuery`
- Response is always HTTP **200** with shape `{"data": ..., "errors": [...]}` — errors do NOT come back as 4xx/5xx
- Frontend bundle references `apollo-client`, `relay-runtime`, `urql`, `graphql-request`, or `@apollo/client`
- Request header `apollo-require-preflight: true` (Apollo CSRF prevention) or `x-apollo-operation-name`
- Connection edges in responses with `pageInfo.{hasNextPage, endCursor}` (Relay spec)

## How it works (the protocol)

A GraphQL request is just **a POST carrying a string of GraphQL syntax plus a variables dict**. The server parses, validates against its schema, executes resolvers, and returns JSON.

The three things you need to send a valid query:

1. **`query`** — the GraphQL document as a string. Either sent literally, or replaced by an identifier (see "Three modes" below).
2. **`variables`** — a JSON object with the typed values referenced in the query (`$id`, `$first`, `$after`, etc.).
3. **`operationName`** *(optional)* — the named operation to execute when the document defines multiple.

Standard wire format is **`Content-Type: application/json`**. Some servers also accept GET (`?query=...&variables=...`) for cacheable read-only queries — useful because GET responses can hit a CDN. A few large players send the body as `application/x-www-form-urlencoded` instead; see "Wire format variants" below.

## Three modes of operation

Which mode the server runs determines what you can send.

### 1. Ad-hoc queries (open API)

The server accepts arbitrary GraphQL documents. You write the query yourself and POST it. This is the easiest mode and is common in B2B SaaS APIs, developer-facing GraphQL endpoints, and smaller apps.

```python
import httpx

resp = httpx.post(
    "https://api.example.com/graphql",
    json={
        "query": """
            query GetUser($login: String!) {
              user(login: $login) { id name avatarUrl }
            }
        """,
        "variables": {"login": "octocat"},
        "operationName": "GetUser",
    },
    headers={"Authorization": "Bearer <token>"},
)
data = resp.json()["data"]
```

### 2. Automatic Persisted Queries (APQ)

Apollo's optimization: the client first sends only a **SHA-256 hash** of the query. If the server has it cached, it executes and returns the data. If not, it returns `{"errors":[{"extensions":{"code":"PERSISTED_QUERY_NOT_FOUND"}}]}`. The client retries once with both the hash AND the full query; the server caches the mapping for future calls.

Recognize APQ by the `extensions.persistedQuery` envelope:

```python
import hashlib, json, httpx

query = "query GetUser($login: String!) { user(login: $login) { id name } }"
sha = hashlib.sha256(query.encode()).hexdigest()

def call(send_query: bool):
    body = {
        "operationName": "GetUser",
        "variables": {"login": "octocat"},
        "extensions": {"persistedQuery": {"version": 1, "sha256Hash": sha}},
    }
    if send_query:
        body["query"] = query
    return httpx.post("https://api.example.com/graphql", json=body)

r = call(send_query=False)
if r.json().get("errors", [{}])[0].get("extensions", {}).get("code") == "PERSISTED_QUERY_NOT_FOUND":
    r = call(send_query=True)
print(r.json()["data"])
```

For scraping you usually skip the first hop and just send the full query — APQ is a cache optimization, not a security mechanism.

### 3. Strict persisted queries (registered-only)

Server only executes queries that were **pre-registered at build time**. Ad-hoc queries are rejected. The client sends just an identifier — sometimes a SHA-256 hash, sometimes an opaque integer or string (`doc_id`, `query_id`, `id`).

This is the hardest mode: you must **extract the registered query ID** from the frontend.

Where to find it:
- Search the JS bundle for the operation name (`grep -ro "GetUserProfile" dist/`) — usually adjacent to the ID
- Look in the HAR/devtools at the actual request body — the client sends the ID directly
- Some frameworks embed the full registered-query manifest in a `__APOLLO_QUERY_MANIFEST__` or similar global

**Operational gotcha:** these IDs are tied to a specific frontend build. When the site deploys, the IDs change. Production scrapers need to **re-extract IDs at the start of each run** (or pin to a captured manifest and accept breakage on deploy).

## Pattern — minimal scraper with cursor pagination

GraphQL pagination is dominated by the **Relay Cursor Connections spec**. A connection field exposes `edges[].node` plus a `pageInfo { hasNextPage endCursor }`. Pagination is `first: N, after: <cursor>` (forward) or `last: N, before: <cursor>` (backward).

```python
import httpx

QUERY = """
query Posts($username: String!, $first: Int!, $after: String) {
  user(username: $username) {
    posts(first: $first, after: $after) {
      edges { node { id title createdAt } }
      pageInfo { hasNextPage endCursor }
    }
  }
}
"""

def iter_posts(username: str, page_size: int = 50):
    after = None
    with httpx.Client(timeout=30) as client:
        while True:
            r = client.post(
                "https://api.example.com/graphql",
                json={
                    "query": QUERY,
                    "variables": {"username": username, "first": page_size, "after": after},
                },
                headers={"Authorization": "Bearer <token>"},
            )
            payload = r.json()
            if payload.get("errors"):
                raise RuntimeError(f"GraphQL errors: {payload['errors']}")
            conn = payload["data"]["user"]["posts"]
            for edge in conn["edges"]:
                yield edge["node"]
            if not conn["pageInfo"]["hasNextPage"]:
                return
            after = conn["pageInfo"]["endCursor"]
```

Less common but you'll also see:
- **Offset pagination**: `query Posts($limit: Int, $offset: Int)` — older or non-Relay APIs
- **`pageInfo.hasMore` / `nextToken`** — non-spec but functionally equivalent
- **No connection wrapper**: query returns a plain list and a separate "next page token" field

## Schema discovery via introspection

GraphQL servers can describe their own schema via the special `__schema` query:

```graphql
query { __schema { types { name fields { name type { name kind } } } } }
```

In dev / B2B APIs this is usually enabled and gives you the full type graph — invaluable for crafting queries without reading frontend code. In production consumer apps it's almost always **disabled** (returns "GraphQL introspection is not allowed"), but it's a free 30-second check worth doing first. If disabled, fall back to reading the JS bundle or the HAR.

## Wire format variants

Most servers want `Content-Type: application/json` with the body `{"query": "...", "variables": {...}}`. Two variants worth knowing:

**GET with query string.** Some servers (especially Apollo CDN-fronted ones) accept GET requests with `?query=...&variables=<urlencoded-json>&operationName=...`. Useful because the response can be CDN-cached. Often used in combination with APQ to keep URLs short — only the hash and variables travel in the URL.

**Form-urlencoded body.** Some large social platforms send GraphQL as **`application/x-www-form-urlencoded`** with the query identifier (e.g. `doc_id` or `query_hash`), a JSON-stringified `variables`, and an operation-name field — all embedded as form fields. It's still GraphQL, just an unusual wire format paired with strict persisted queries identified by an integer or opaque ID. Recognize by `doc_id=<integer>` (or equivalent) and `variables=<urlencoded-JSON>` in a form body where you'd expect JSON. Any auth/anti-bot headers riding alongside (CSRF tokens, anti-spam IDs, signed claim tokens) are **site-specific concerns**, not part of the GraphQL contract — treat them like any other anti-bot challenge for that site, not as GraphQL requirements.

**`variables` wrapped in base64.** Some implementations (commonly e-commerce storefronts that ship a shared frontend SDK) encode `variables` as a **base64-of-JSON blob** instead of a JSON object literal. The body looks like `variables=eyJjb3VudCI6MTAsImFmdGVyIjpudWxsfQ%3D%3D` — opaque single string where you'd expect a structured object. Decode by `json.loads(base64.b64decode(unquote(blob)))`. The query/persisted-hash side is unchanged; only `variables` carries the wrapper. When parametrizing for pagination, re-encode the modified dict back to base64 before sending.

## Hybrid GraphQL + REST

**Do not assume that a site using GraphQL uses only GraphQL.** Large products routinely run a hybrid backend where GraphQL serves list/grid/feed queries and REST endpoints (often `/api/v1/...`) handle detail views, write actions, and per-resource pagination. When inventorying a target, search the HAR for **both** `/graphql` and `/api/`, `/v1/`, `/rest/` paths — the data you want may live on either side, and the cursors / IDs / auth headers used by REST may be entirely different from the GraphQL flow even on the same host.

## Gotchas

- **HTTP 200 + errors.** The status code only reflects transport health. `data` can be `null` while `errors` is populated, or partial `data` can coexist with partial `errors`. Always check both: `payload.get("errors")` first, then `payload["data"]`.
- **Complexity / cost limits, not request limits.** Many GraphQL servers rate-limit by **query cost** (depth, breadth, number of resolved nodes) rather than request count. You can be blocked after a single oversized request, or run unlimited cheap ones. If you hit `MAX_QUERY_COMPLEXITY` / `COST_EXCEEDED`, narrow the selection set or split into multiple smaller queries — proxies and retries won't help.
- **Batching.** Some servers accept an **array of operations** in a single request: `[{query, variables}, {query, variables}]` and return `[{data, errors}, ...]` in order. When supported, this is a free 5–10x throughput multiplier with no extra rate-limit cost. Test by sending a 2-op batch and seeing if you get a 2-element array back.
- **Persisted query manifests change on deploy.** If you're scraping a strict-persisted-queries server, the IDs you extracted today may be invalid tomorrow. Either re-extract on every run or detect `PersistedQueryNotFound` / equivalent and refresh.
- **Auth lives outside the query.** GraphQL itself defines no auth scheme — tokens travel in HTTP headers (`Authorization: Bearer ...`) or cookies, exactly like REST. SPAs commonly stash the token in `localStorage` and attach it in an interceptor; replicate by grabbing the header out of a HAR rather than trying to reverse the login flow.
- **`@defer` / `@stream` directives** return **multipart responses** (`multipart/mixed`), not a single JSON object. The client receives the initial payload immediately and additional chunks streamed in. Rare in scraping targets but you'll see it on modern Apollo/Relay servers. If `r.json()` fails with a parse error and the response is `multipart/mixed`, that's why — you need a streaming parser.
- **Subscriptions over WebSocket (`graphql-ws`, `graphql-transport-ws`).** Almost never the scraping target — these are real-time push channels. If you see WebSocket upgrades to `/graphql`, it's subscriptions; the data is also reachable via the regular query endpoint in nearly every case.
- **Don't trust `operationName` to identify the query.** It's a label for logging/routing. Two requests with the same operation name can carry different queries. Identify by the `query` string itself (or by hash / doc_id when persisted).

## Related

- `discovery/har-driven-workflow.md` — capturing GraphQL operations from a real session
- `discovery/devtools-workflow.md` — locating the `/graphql` endpoint and extracting query bodies
- `spa-frameworks.md` — SPA hosts are the most common GraphQL clients; auth tokens usually come from the SPA's localStorage
- `templated-cms-schema-drift.md` — schema drift across deployments applies to GraphQL too: the same operation name can return slightly different shapes across tenants or environments
