# expert: full example

Input:

```text
I want to add a cache to my web app's product search endpoint because it feels slow. /expert
```

Output (the rewritten prompt):

````
I want to add a cache to my web app's product search endpoint because it feels slow. I want a deeper version of this job, not a bigger one: same goal, same endpoint, but the cache only goes in if measurement shows it is the right fix.

Field: web backend performance engineering.

1. Done when: on the same replayed request log, the endpoint's p95 latency (and p50) drops by a stated amount against a baseline I recorded before changing anything. Cached results are never staler than the freshness I accept, and the cache-hit ratio is reported.

2. Expert moves:
   - Measure before building. "Feels slow" is not a number. Record p50/p95/p99 per request and break the time down into app code, DB query, network and serialization. Most of the time a cache is not the first fix. An unindexed query, an N+1 or a oversized payload is often the real cause (not checked: general experience, no base rate known; I don't know a reliable percentage and won't invent one).
   - Decide the freshness contract first, before choosing a cache. How stale may a price, stock level or availability be, and which of those fields change often? That decides the TTL and the invalidation, and whether to cache the whole response or only the expensive query.
   - Estimate the hit ratio from real queries before building. If most searches are one-off strings, a cache will rarely hit. Check the distribution of query strings, which is typically heavily skewed toward a few popular terms (not checked: general knowledge, to be confirmed on my logs).

3. Raw material: the endpoint's code and its query path; the slow-query log or `EXPLAIN ANALYZE` output for the real query (I don't know which database I use, so this is the first thing to name); production access logs or APM traces with real search strings, latencies and status codes, not a synthetic benchmark; and the current cache or CDN headers on the endpoint.

4. Methods:
   - Measure first, in the spirit of Brendan Gregg's "Systems Performance" method: define the problem, take a baseline, find the bottleneck, change one thing, measure again. The steps are: (a) baseline with percentiles; (b) a time breakdown per layer; (c) fix the query or index if that is the cause; (d) only then add the cache.
   - Cache-aside: read the cache, on a miss query and then populate it. Key = normalized query (lowercase, trimmed, sorted filters, page, sort, locale, plus anything that changes the result such as currency or user segment). Give it a TTL and an upper bound on memory.
   - Stampede protection when a popular key expires. Use request coalescing (singleflight), or probabilistic early refresh as in Vattani, Chierichetti and Lowenkamp's "Optimal Probabilistic Cache Stampede Prevention" (2015) (not checked: cited from memory).
   - Tools I can choose from, depending on my stack: `EXPLAIN ANALYZE` (Postgres/MySQL 8), `k6`, `wrk` or `hey` for load, and Redis or an in-process LRU for the store. Name the one that fits my stack; don't pick one from habit.

5. External check: a load test replaying a sample of real production search strings, run before and after, against the baseline from step 4(a). Pass = p95 improves by the target we agree on, hit ratio is above the level where the cache pays for itself, and a test that changes a product's price returns the new price within the TTL. Fail = the improvement is within run-to-run noise, or any response is staler than the contract.

6. Likely failure: the cache goes in, the hit ratio is low because queries are long-tail or the key includes noisy parameters (session ID, timestamp, unsorted filters), and the endpoint still feels slow. Early signal: the hit ratio on replayed real traffic is low before I build anything, or the time breakdown shows the time is not in the data fetch. Stop and re-plan at that point.

7. Off the table:
   - Do not change the response shape or search relevance, because clients depend on them.
   - Do not cache anything user-specific, or personalized pricing, in a shared key, because that leaks data between users.
   - Do not add new infrastructure (e.g. a new Redis server) if an in-process or already-deployed cache is enough, to avoid extra operating cost.
   - Do not touch the database schema without showing me the change first.

8. Not checked: my stack, my database, current latency, whether results include personalized or fast-changing data, and the hit ratio (all not checked: said by me or unknown). The one observation that would overturn the premise is that the time is spent outside the query, for example in rendering, serialization, or a downstream call, so a cache would not help.

9. First step: record the baseline. Pull p50/p95/p99 for the search endpoint from logs or APM, then run `EXPLAIN ANALYZE` on its main query. Tell me where the time goes before writing any cache code.
````

Produced by Claude Sonnet with this skill, in an empty folder with no access to the app.

