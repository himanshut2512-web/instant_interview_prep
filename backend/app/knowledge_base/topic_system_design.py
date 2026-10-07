from ._build import P, Q, S, T, md, note

TOPIC = {
    "key": "system_design",
    "name": "System Design",
    "keywords": ["system design", "distributed", "scalable", "scalability", "microservices", "architecture",
                 "high availability", "low latency", "backend", "api", "apis", "rest", "caching", "redis",
                 "load balancing", "senior", "lead", "principal", "architect"],
    "core": ["system design", "distributed systems", "microservices", "scalability"],
    "subtopics": ["Scaling & load balancing", "Caching", "Databases: SQL vs NoSQL, replication, sharding",
                  "CAP & consistency", "Queues & async processing", "API design & rate limiting",
                  "Back-of-envelope estimation"],
    "revision": note(
        summary="System design interviews assess how you structure an ambiguous problem: requirements, estimates, "
        "a sensible high-level architecture, and deep dives into data, scaling, reliability and trade-offs.",
        concepts=[
            ("Vertical vs horizontal scaling", "Bigger machine vs more machines behind a load balancer; horizontal "
             "needs stateless services."),
            ("Load balancer", "Distributes requests (round robin, least connections, consistent hashing); health "
             "checks remove bad nodes."),
            ("Caching", "Cache-aside, write-through, write-back; TTLs and eviction (LRU); CDN for static content."),
            ("Replication", "Copies of data for availability and read scaling (leader-follower, multi-leader)."),
            ("Sharding", "Split data across nodes by key (hash/range) to scale writes and storage."),
            ("CAP theorem", "During a network partition you trade consistency against availability."),
            ("Message queue", "Kafka/SQS/RabbitMQ decouple producers and consumers, absorb spikes, enable retries."),
            ("Idempotency", "Retrying a request has the same effect as doing it once - idempotency keys for payments."),
            ("Rate limiting", "Token bucket / sliding window to protect services and enforce quotas."),
            ("Observability", "Metrics, logs, traces; SLIs/SLOs and alerting."),
        ],
        explanation=md("""
            **Interview framework (about 45 minutes).**
            1. **Requirements** (5 min): functional (what it does) and non-functional (scale, latency,
               availability, consistency, cost). Confirm what's out of scope.
            2. **Estimates** (5 min): users, QPS (peak ~2-3x average), storage per year, bandwidth.
            3. **API & data model** (5-10 min): key endpoints and entities.
            4. **High-level design** (10 min): clients -> CDN/load balancer -> stateless services -> cache ->
               databases -> queues/workers -> analytics.
            5. **Deep dives** (10-15 min): the hardest parts - hot keys, consistency, failure handling, scaling the
               database.
            6. **Trade-offs & wrap-up**: bottlenecks, monitoring, what you'd do with more time.

            **Choosing storage.**

            | Need | Typical choice |
            |---|---|
            | Transactions, joins, strong consistency | PostgreSQL/MySQL (+ read replicas) |
            | Massive key-value access, flexible schema | DynamoDB/Cassandra/MongoDB |
            | Caching, counters, leaderboards | Redis |
            | Search / full-text | Elasticsearch/OpenSearch |
            | Analytics | Columnar warehouse (BigQuery/Snowflake) |
            | Files, images | Object storage (S3) + CDN |

            **Numbers to remember.** ~86,400 seconds/day (use 10^5 for estimates); 1M requests/day is about 12 QPS;
            memory access ~100 ns, SSD read ~100 us, cross-region round trip ~100 ms.
        """),
        code=md("""
            import time
            import threading

            class TokenBucket:
                # allow `rate` requests/second with bursts up to `capacity`
                def __init__(self, rate: float, capacity: int):
                    self.rate, self.capacity = rate, capacity
                    self.tokens = capacity
                    self.updated = time.monotonic()
                    self.lock = threading.Lock()

                def allow(self) -> bool:
                    with self.lock:
                        now = time.monotonic()
                        self.tokens = min(self.capacity, self.tokens + (now - self.updated) * self.rate)
                        self.updated = now
                        if self.tokens >= 1:
                            self.tokens -= 1
                            return True
                        return False
        """),
        language="python",
        pitfalls=[
            "Jumping to components before clarifying requirements and scale.",
            "Designing for 1 billion users when the requirement is 10,000.",
            "Single points of failure (one database, one region) without acknowledging them.",
            "Ignoring cache invalidation and data consistency.",
            "Not discussing monitoring, failure modes and trade-offs.",
        ],
        tips=[
            "Drive the conversation with the framework; check in with the interviewer at each step.",
            "State assumptions and numbers explicitly.",
            "Explain trade-offs for every major choice (why this DB, why async).",
            "Go deep on one or two components rather than shallow on everything.",
        ],
        cheat_sheet=[
            "Read-heavy -> caching + read replicas; write-heavy -> sharding + queues.",
            "Stateless services scale horizontally; keep session state in Redis or tokens.",
            "Use idempotency keys for payments and retries.",
            "Cache-aside: read cache -> miss -> read DB -> populate cache with TTL.",
            "Consistent hashing minimises data movement when nodes change.",
            "Availability 99.9% is about 8.8 h downtime/year; 99.99% is about 53 min/year.",
        ],
        likely_questions=[
            "Design a URL shortener.", "Design a rate limiter.", "Design a notification system.",
            "SQL vs NoSQL?", "Explain the CAP theorem.", "How would you scale a read-heavy service?",
        ],
    ),
    "theory": [
        T("beginner", "What is the difference between vertical and horizontal scaling, and what does a load "
          "balancer do?",
          """
          - **Vertical scaling (scale up)**: give one machine more CPU/RAM. Simple, no code changes, but limited by
            the largest machine, expensive at the top end, and still a single point of failure.
          - **Horizontal scaling (scale out)**: add more machines and spread the load. Nearly unlimited and
            resilient, but services must be **stateless** (session state in Redis/tokens) and data layers need
            replication/sharding.

          A **load balancer** sits in front of the servers and distributes requests using algorithms such as round
          robin, least connections or hashing. It runs **health checks** to stop routing to unhealthy instances,
          can terminate TLS, and enables zero-downtime deployments. L4 balancers route on IP/port; L7 balancers
          route on HTTP details (paths, headers).
          """,
          ["Both scaling types with trade-offs", "Statelessness requirement", "LB algorithms & health checks", "L4 vs L7"],
          "Mention autoscaling groups/Kubernetes HPA as the practical form of horizontal scaling.",
          ["How do you handle user sessions with many servers?", "What happens if the load balancer fails?"],
          hot=True),
        T("beginner", "SQL vs NoSQL databases - how do you choose?",
          """
          **Relational (SQL)** databases (PostgreSQL, MySQL) store structured data in tables with a fixed schema,
          support joins and ACID transactions, and are the default when data is relational and consistency matters
          (orders, payments, inventory). They scale reads with replicas; scaling writes requires sharding.

          **NoSQL** families trade some of that for scale and flexibility:
          - **Key-value** (Redis, DynamoDB): very fast lookups by key - sessions, caches, carts.
          - **Document** (MongoDB): flexible JSON documents - product catalogues, user profiles.
          - **Wide-column** (Cassandra): huge write throughput - time-series, event logs.
          - **Graph** (Neo4j): relationship-heavy queries - social graphs, fraud rings.

          Decide by access patterns, consistency needs, scale and team expertise. Many systems use both
          (polyglot persistence).
          """,
          ["SQL strengths (ACID, joins)", "NoSQL families with use cases", "Access-pattern-driven choice",
           "Polyglot persistence"],
          "Use one system you built as the example and justify its database choice.",
          ["What is eventual consistency?", "How does DynamoDB partition data?"]),
        T("intermediate", "Explain caching strategies and how you handle cache invalidation.",
          """
          **Where**: browser/CDN (static assets), application cache (Redis/Memcached), database buffer cache.

          **Patterns**
          - **Cache-aside (lazy loading)**: app reads cache; on a miss reads the DB and populates the cache. Most
            common; the cache only holds requested data.
          - **Write-through**: write to cache and DB together - cache always fresh, writes slower.
          - **Write-back (write-behind)**: write to cache, persist asynchronously - fast writes, risk of data loss.
          - **Read-through**: the cache itself loads from the DB on misses.

          **Invalidation** ("one of the two hard problems"): TTLs for bounded staleness; explicit delete/update on
          writes (delete-on-write is safer than update-on-write under races); versioned keys; event-driven
          invalidation via change data capture.

          **Pitfalls**: cache stampede when a hot key expires (use locks/request coalescing or staggered TTLs),
          hot keys (replicate or local caches), and caching errors or personalised data incorrectly. Eviction
          policies such as LRU/LFU bound memory.
          """,
          ["Cache layers", "Patterns with trade-offs", "Invalidation strategies", "Stampede & hot keys"],
          "Discuss the consistency you can tolerate (seconds? minutes?) - it drives the TTL choice.",
          ["What is a cache stampede and how do you prevent it?", "When should you NOT cache?"], hot=True),
        T("intermediate", "Explain the CAP theorem and how it affects real system design.",
          """
          In a distributed data store, when a **network partition** occurs, you must choose between:
          - **Consistency (C)**: every read sees the latest write (or an error), and
          - **Availability (A)**: every request gets a non-error response, possibly with stale data.
          Partition tolerance (P) isn't optional in real networks, so the practical choice is **CP vs AP during
          partitions**.

          - **CP** systems (e.g. HBase, ZooKeeper, a strongly consistent SQL primary) refuse some requests rather
            than return stale data - suitable for payments, inventory reservation, account balances.
          - **AP** systems (e.g. Cassandra, DynamoDB with eventual consistency) stay available and reconcile later -
            suitable for feeds, likes, carts, analytics counters.

          PACELC extends this: even without partitions there's a trade-off between **latency and consistency**.
          Many databases let you tune it per operation (quorum reads/writes, strongly consistent reads).
          """,
          ["Correct definitions", "Partition makes P mandatory", "CP vs AP examples", "PACELC / tunable consistency"],
          "Pick a feature and say whether it needs CP or AP and why - shows applied understanding.",
          ["What is eventual consistency?", "How do quorum reads and writes work (R + W > N)?"], hot=True),
        T("advanced", "Walk me through how you approach a system design interview question.",
          """
          1. **Clarify requirements**: core use cases, users, read/write ratio, latency/availability targets,
             consistency needs, what's out of scope. Write them down.
          2. **Estimate scale**: daily active users -> requests per second (peak), storage growth, bandwidth -
             numbers drive later choices.
          3. **Define APIs and data model**: main endpoints and entities, keys and access patterns.
          4. **High-level architecture**: clients, CDN, load balancer, stateless services, cache, database(s),
             queues, workers, analytics. Walk one request end to end.
          5. **Deep dives**: the bottleneck or trickiest part - database scaling (replicas, sharding key), caching
             strategy, consistency, hot spots, idempotency, failure handling.
          6. **Reliability & operations**: redundancy across zones, backups, rate limiting, monitoring/alerting,
             deployment strategy.
          7. **Trade-offs & evolution**: what I'd change at 10x scale, what I simplified.

          Throughout, I state assumptions, think aloud and check in with the interviewer.
          """,
          ["Requirements first", "Back-of-envelope numbers", "API/data model", "Architecture + deep dives",
           "Reliability and trade-offs"],
          "Literally use this skeleton in the interview - interviewers reward structure.",
          ["How do you estimate QPS from DAU?", "Which deep dive would you choose for a chat app?"], hot=True),
        T("advanced", "Replication vs sharding - and why is consistent hashing useful?",
          """
          **Replication** keeps copies of the same data on several nodes:
          - leader-follower: writes go to the leader, reads can go to followers (read scaling, failover); async
            replication risks replica lag and data loss on failover.
          - multi-leader / leaderless (quorums) for multi-region writes, with conflict resolution.

          **Sharding (partitioning)** splits data across nodes so each holds a subset - scaling writes and storage.
          Key choice is crucial: range-based keys allow range scans but risk hot spots; hash-based keys spread load
          evenly but make range queries harder. Cross-shard joins and transactions become expensive; resharding is
          painful.

          **Consistent hashing** places nodes and keys on a hash ring; each key belongs to the next node clockwise.
          Adding/removing a node moves only about 1/N of the keys (instead of nearly all with `hash % N`). **Virtual
          nodes** (many points per physical node) smooth the distribution. Used by Cassandra, DynamoDB, distributed
          caches and load balancers.
          """,
          ["Replication purposes & lag", "Sharding & shard-key trade-offs", "Consistent hashing mechanics",
           "Virtual nodes"],
          "Explain why hash % N is bad when N changes - it sets up consistent hashing nicely.",
          ["How do you choose a shard key?", "How do you handle a celebrity hot key?"]),
    ],
    "practical": [
        P("beginner", "Design (and sketch in FastAPI) a REST API for a task-management service.",
          """
          Users create, list, update and delete tasks; tasks have title, status (todo/doing/done), due date.
          Listing must support filtering by status and pagination.
          """,
          ["Resource-oriented URLs and HTTP verbs.", "Correct status codes.", "Cursor/limit pagination & filtering.",
           "Validation and idempotency."],
          "Use nouns for resources, verbs via HTTP methods, 201 on create, 404 for missing tasks, 422 for invalid "
          "input. Cursor-based pagination stays stable as data changes.",
          """
          from datetime import date
          from typing import Literal
          from fastapi import FastAPI, HTTPException, Query
          from pydantic import BaseModel

          app = FastAPI()
          Status = Literal["todo", "doing", "done"]

          class TaskIn(BaseModel):
              title: str
              status: Status = "todo"
              due: date | None = None

          class Task(TaskIn):
              id: int

          TASKS: dict[int, Task] = {}

          @app.post("/tasks", status_code=201, response_model=Task)
          def create_task(body: TaskIn):
              task = Task(id=len(TASKS) + 1, **body.model_dump())
              TASKS[task.id] = task
              return task

          @app.get("/tasks", response_model=list[Task])
          def list_tasks(status: Status | None = None, after_id: int = 0, limit: int = Query(20, le=100)):
              items = [t for t in TASKS.values() if t.id > after_id and (status is None or t.status == status)]
              return sorted(items, key=lambda t: t.id)[:limit]

          @app.patch("/tasks/{task_id}", response_model=Task)
          def update_task(task_id: int, body: TaskIn):
              if task_id not in TASKS:
                  raise HTTPException(404, "Task not found")
              TASKS[task_id] = Task(id=task_id, **body.model_dump())
              return TASKS[task_id]

          @app.delete("/tasks/{task_id}", status_code=204)
          def delete_task(task_id: int):
              TASKS.pop(task_id, None)       # idempotent delete
          """, "python",
          "In-memory demo; a real service would use a database with an index on (user_id, status, id).",
          ["Concurrent updates (use ETags/versions)", "Deleting a missing task", "Very large page sizes"],
          "Discuss authentication, versioning (/v1) and rate limiting as next steps.",
          ["Offset vs cursor pagination?", "PUT vs PATCH?", "How do you version an API?"]),
        P("intermediate", "Implement a token-bucket rate limiter allowing N requests per second per user with bursts.",
          """
          `limiter.allow(user_id) -> bool`. Rate: 5 requests/second, burst capacity 10. Must be thread-safe.
          """,
          ["Each user has a bucket with tokens up to capacity.", "Refill tokens based on elapsed time.",
           "Consume one token per allowed request.", "Lock for thread safety; discuss distributed version."],
          "Lazily refilling on each call avoids background timers. For multiple servers, keep buckets in Redis and "
          "update atomically with a Lua script.",
          """
          import threading
          import time
          from collections import defaultdict

          class RateLimiter:
              def __init__(self, rate=5.0, capacity=10):
                  self.rate, self.capacity = rate, capacity
                  self.buckets = defaultdict(lambda: [capacity, time.monotonic()])  # tokens, last refill
                  self.lock = threading.Lock()

              def allow(self, user_id: str) -> bool:
                  with self.lock:
                      tokens, last = self.buckets[user_id]
                      now = time.monotonic()
                      tokens = min(self.capacity, tokens + (now - last) * self.rate)
                      allowed = tokens >= 1
                      self.buckets[user_id] = [tokens - 1 if allowed else tokens, now]
                      return allowed

          limiter = RateLimiter()
          print(sum(limiter.allow("u1") for _ in range(15)))   # 10 allowed in a burst
          """, "python",
          "O(1) per request; memory O(number of active users).",
          ["Clock adjustments (use monotonic time)", "Memory growth (evict idle users)", "Multiple servers"],
          "Compare with fixed-window and sliding-window-log approaches briefly.",
          ["How would you implement this in Redis?", "Token bucket vs leaky bucket?"], hot=True),
        P("advanced", "Implement a consistent-hashing ring with virtual nodes.",
          """
          `ring.add_node(name)`, `ring.remove_node(name)`, `ring.get_node(key)`. Use 100 virtual nodes per server.
          Show that adding a node moves only a fraction of keys.
          """,
          ["Hash each virtual node (name#i) onto a sorted ring.", "For a key, binary-search the first node hash >= "
           "key hash (wrap around).", "Virtual nodes smooth the load.", "Measure key movement when adding a node."],
          "bisect keeps lookups O(log V) for V virtual nodes. Only keys between the new node's points and their "
          "predecessors move, roughly 1/N of all keys.",
          """
          import bisect
          import hashlib

          def _hash(value: str) -> int:
              return int(hashlib.md5(value.encode()).hexdigest(), 16)

          class ConsistentHashRing:
              def __init__(self, vnodes=100):
                  self.vnodes = vnodes
                  self.ring = []          # sorted hashes
                  self.owner = {}         # hash -> node

              def add_node(self, node):
                  for i in range(self.vnodes):
                      h = _hash(f"{node}#{i}")
                      bisect.insort(self.ring, h)
                      self.owner[h] = node

              def remove_node(self, node):
                  for i in range(self.vnodes):
                      h = _hash(f"{node}#{i}")
                      self.ring.remove(h)
                      del self.owner[h]

              def get_node(self, key):
                  idx = bisect.bisect(self.ring, _hash(key)) % len(self.ring)
                  return self.owner[self.ring[idx]]

          ring = ConsistentHashRing()
          for n in ("cache-a", "cache-b", "cache-c"):
              ring.add_node(n)
          keys = [f"user:{i}" for i in range(10_000)]
          before = {k: ring.get_node(k) for k in keys}
          ring.add_node("cache-d")
          moved = sum(before[k] != ring.get_node(k) for k in keys)
          print(f"moved {moved / len(keys):.1%} of keys")     # about 25%, not ~75% as with hash % N
          """, "python",
          "Lookup O(log V); add/remove O(v log V) with insort (fine for small rings).",
          ["Empty ring", "Hash collisions between virtual nodes", "Weighted nodes (more vnodes for bigger servers)"],
          "Contrast with hash % N to show why remapping matters for caches.",
          ["How do you handle replication on the ring?", "How would you weight bigger servers?"]),
    ],
    "scenario": [
        S("beginner", """
          During a festive sale, your e-commerce site's product pages slow to 8 seconds and the database CPU sits at
          100%. Traffic is 10x normal, mostly people browsing products.
          """,
          "What do you do now, and what do you change for the next sale?",
          [("Stabilise", "Enable/extend caching of product pages and API responses; rate-limit abusive clients."),
           ("Offload reads", "Route reads to replicas; serve static assets via CDN."),
           ("Find hotspots", "Slow-query log, missing indexes, N+1 queries."),
           ("Degrade gracefully", "Turn off non-essential features (recommendations widgets) temporarily."),
           ("Prepare", "Load tests, autoscaling, pre-warmed caches, queue-based checkout for the next sale.")],
          """
          Browsing traffic is **read-heavy**, so the quickest relief is to stop hitting the database for every page
          view. Immediately: cache product detail responses in Redis/CDN with a short TTL (even 60 seconds removes
          most DB load), serve images and static assets via the CDN, and route remaining reads to read replicas.
          I'd check the slow-query log for a missing index or N+1 queries and temporarily disable expensive
          non-essential widgets.

          For the next sale: load-test at 15x expected traffic, autoscale the stateless app tier, pre-warm caches for
          top products, add read replicas, and protect checkout with a queue and rate limiting so browsing spikes
          can't starve payments. A runbook and dashboards (p95 latency, DB CPU, cache hit rate) let the team react
          in minutes.
          """,
          ["Correctly identifies read-heavy load", "Caching/CDN/replicas first", "Graceful degradation",
           "Preparation with load testing"],
          ["Only scaling the DB vertically", "Restarting servers repeatedly", "No plan for next time"],
          ["How would you keep prices/stock fresh with caching?", "What is graceful degradation?"]),
        S("intermediate", """
          Design a URL-shortening service like bit.ly: 100 million new links per month, 10:1 read-to-write ratio,
          redirects should take under 50 ms, and links never expire unless the user deletes them.
          """,
          "Walk through your design.",
          [("Requirements & estimates", "~40 writes/s avg, ~400 reads/s (peaks higher); ~6 billion links in 5 years."),
           ("Key generation", "7-char base62 codes (3.5 trillion combinations) from a counter/ID service or hashing."),
           ("Storage", "Key-value store (code -> long URL, owner, created_at), partitioned by code."),
           ("Read path", "Load balancer -> stateless redirect service -> Redis cache -> DB; 301/302 redirect."),
           ("Extras", "Analytics via async events to a queue, rate limiting, abuse detection.")],
          """
          **Estimates**: 100M links/month is about 40 writes/s on average; with 10:1 reads, about 400 redirects/s
          average and maybe 2-4k/s at peak. Over 5 years, 6 billion links x ~500 bytes is about 3 TB.

          **Short codes**: 7 base62 characters give 62^7, about 3.5 trillion codes. I'd generate unique IDs from a
          distributed counter (e.g. ranges handed out to each app server) and base62-encode them - no collisions and
          no lookups needed. (Hashing the URL plus collision checks is the alternative.)

          **Storage**: a key-value/NoSQL store (DynamoDB/Cassandra) keyed by code, which shards naturally; a
          relational DB with the code as primary key also works at this scale.

          **Read path**: load balancer -> stateless redirect service -> Redis cache (popular links are highly
          skewed, so hit rates are high) -> DB on miss -> HTTP 302 (or 301 if we don't need analytics on every hit).
          Click analytics are published asynchronously to Kafka so redirects stay fast.

          **Extras**: rate limiting and malware/phishing checks on creation, custom aliases with uniqueness checks,
          multi-AZ replication for availability.
          """,
          ["Quantified estimates", "Sound key-generation scheme", "Read-optimised path with caching",
           "Async analytics", "Abuse & availability considerations"],
          ["Random codes without collision handling", "Synchronous analytics writes on redirect",
           "No capacity estimates"],
          ["301 vs 302 redirect?", "How do you support custom aliases?", "How do you prevent enumeration?"],
          hot=True),
        S("advanced", """
          Design the service that powers "Recommended for you" on an e-commerce home page: 50 million users,
          5,000 requests/second at peak, a 100 ms latency budget, and the catalogue changes daily.
          """,
          "Design the architecture end to end.",
          [("Two-stage approach", "Candidate generation (hundreds of items) then ranking (top 20)."),
           ("Offline", "Batch training of embedding/CF models; precompute candidates per user nightly."),
           ("Online", "Feature store lookups + lightweight ranker within the latency budget."),
           ("Serving", "Cache per-user results, fallbacks to popular items, A/B framework."),
           ("Feedback loop", "Log impressions/clicks to retrain; monitor CTR, latency, coverage.")],
          """
          I'd use the standard **two-stage** design.

          **Candidate generation (offline + nearline)**: nightly jobs train collaborative-filtering/embedding models
          (two-tower) on interaction logs. For each active user we precompute ~500 candidates (similar items to
          recent views, co-purchases, trending in their segment) and store them in a key-value store. An ANN index
          (FAISS/ScaNN) over item embeddings supports fresh candidates from the current session.

          **Ranking (online)**: on request, fetch candidates and real-time features (session clicks, price, stock)
          from an online feature store, score them with a gradient-boosted or small neural ranker (~10-20 ms), apply
          business rules (in stock, diversity, no recently purchased items), and return the top 20.

          **Latency budget**: cache (5 ms) -> candidate fetch (10 ms) -> features (15 ms) -> ranking (20 ms) ->
          rules (5 ms), leaving headroom. Results are cached per user for a few minutes; on timeout, fall back to
          precomputed or popular items.

          **Feedback & quality**: log impressions and clicks to Kafka for training data and dashboards; evaluate
          with offline metrics (recall@k, NDCG) and online A/B tests on CTR and revenue per session; handle cold-start
          users with popularity/segment-based recommendations.
          """,
          ["Candidate generation + ranking split", "Offline/online separation", "Latency budget reasoning",
           "Fallbacks and caching", "Feedback loop and evaluation"],
          ["One heavy model scoring the full catalogue per request", "No cold-start strategy", "No fallback path"],
          ["How do you handle new items (item cold start)?", "How would you A/B test the ranker?"], hot=True),
    ],
    "quiz": [
        Q("beginner", "What is the main job of a load balancer?",
          ["Store user sessions", "Distribute incoming requests across multiple servers", "Compress images",
           "Run database migrations"], 1,
          "It spreads traffic across healthy instances and removes unhealthy ones via health checks.",
          ["Session state belongs in a cache/store.", "Correct.", "That's a CDN/app concern.", "Unrelated."],
          "Mention health checks and L4 vs L7.", hot=True),
        Q("beginner", "Horizontal scaling means:",
          ["Buying a bigger server", "Adding more servers to share the load", "Adding more database indexes",
           "Increasing cache TTLs"], 1,
          "Scale-out adds machines; it requires stateless services and data partitioning.",
          ["That's vertical scaling.", "Correct.", "An optimisation, not scaling.", "Unrelated."],
          "Contrast with vertical scaling limits."),
        Q("intermediate", "According to the CAP theorem, during a network partition a distributed system must choose "
          "between:",
          ["Latency and throughput", "Consistency and availability", "Sharding and replication", "Cost and security"], 1,
          "Partitions are unavoidable, so the trade-off is serving possibly stale data (A) or refusing requests (C).",
          ["That's PACELC's else-branch, roughly.", "Correct.", "Design techniques, not CAP properties.", "Unrelated."],
          "Give an example of a CP and an AP use case.", hot=True),
        Q("intermediate", "In the cache-aside pattern, what happens on a cache miss?",
          ["The request fails", "The application reads from the database and populates the cache",
           "The cache writes to the database", "The database pushes all data to the cache"], 1,
          "The app owns the logic: read DB, store in cache with a TTL, return the value.",
          ["No.", "Correct.", "That's write-through/write-back.", "No."],
          "Mention TTLs and invalidation on writes."),
        Q("advanced", "What is the main benefit of consistent hashing?",
          ["It encrypts keys", "Adding or removing a node remaps only a small fraction of keys",
           "It guarantees strong consistency", "It removes the need for replication"], 1,
          "Only keys adjacent to the changed node move (about 1/N), unlike hash % N which remaps almost everything.",
          ["Hashing isn't encryption.", "Correct.", "Unrelated to consistency models.", "Replication is still needed."],
          "Mention virtual nodes for balance.", hot=True),
    ],
}
