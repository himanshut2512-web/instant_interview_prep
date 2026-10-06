from ._build import P, Q, S, T, md, note

TOPIC = {
    "key": "python",
    "name": "Python",
    "keywords": ["python", "pandas", "numpy", "scripting", "flask", "django", "fastapi", "oops", "pyspark"],
    "core": ["python", "pandas"],
    "subtopics": ["Data types & mutability", "Comprehensions & generators", "Decorators & context managers",
                  "OOP & dunder methods", "Concurrency & the GIL", "pandas & NumPy performance"],
    "revision": note(
        summary="Python rounds test core language semantics (types, mutability, scope), idiomatic code "
        "(comprehensions, generators, decorators, context managers), OOP, error handling and - for data roles - "
        "fluent, vectorised pandas/NumPy.",
        concepts=[
            ("Mutable vs immutable", "list/dict/set are mutable; int/float/str/tuple/frozenset are immutable. Only "
             "immutable (hashable) objects can be dict keys or set members."),
            ("list / tuple / set / dict", "Ordered & mutable / ordered & immutable / unique, O(1) membership / "
             "key-value hash map (insertion-ordered since 3.7)."),
            ("Comprehension vs generator", "A list comprehension builds the whole list in memory; a generator "
             "(expression or `yield`) produces items lazily, one at a time."),
            ("Decorator", "A callable that takes a function and returns a wrapped function - logging, timing, "
             "caching, retries, auth. Use functools.wraps to keep metadata."),
            ("Context manager", "`with` guarantees setup/teardown via __enter__/__exit__ or "
             "contextlib.contextmanager - files, locks, DB transactions."),
            ("*args / **kwargs", "Collect extra positional arguments into a tuple and keyword arguments into a dict."),
            ("GIL", "In standard CPython only one thread runs Python bytecode at a time: threads help I/O-bound work, "
             "processes help CPU-bound work. (3.13+ offers an optional free-threaded build.)"),
            ("Shallow vs deep copy", "copy.copy duplicates the outer container only; copy.deepcopy recursively "
             "copies nested objects."),
            ("is vs ==", "`is` compares identity (same object); `==` compares value via __eq__."),
            ("Vectorisation", "pandas/NumPy push loops into optimised C code; row-wise .apply or Python loops are "
             "10-100x slower."),
        ],
        explanation=md("""
            **Data model.** Everything is an object with an identity, a type and a value. Variables are *names bound
            to objects*, so `b = a` makes both names point to the same list - mutating through `b` is visible via
            `a`. Function arguments are passed "by object reference".

            **Mutability traps.** Default arguments are evaluated once, at definition time, so
            `def f(x, acc=[])` shares one list across calls. Use `acc=None` and create the list inside.

            **Iteration.** Any object with `__iter__` is iterable; generators implement the iterator protocol for
            you. Chaining generators builds memory-flat pipelines (read -> parse -> filter -> aggregate) that can
            stream files larger than RAM.

            **OOP.** Classes bundle state and behaviour. Know `__init__`, `__repr__`, `__eq__`/`__hash__`,
            `@property`, `@classmethod` vs `@staticmethod`, inheritance and the MRO (C3 linearisation, visible via
            `Cls.__mro__`). Prefer composition over deep inheritance; `dataclasses` remove boilerplate.

            **Errors.** Catch specific exceptions, keep `try` blocks small, use `finally`/context managers for
            cleanup, and raise custom exceptions with useful messages.

            **Concurrency.**

            | Workload | Tool |
            |---|---|
            | Many network/disk waits | `asyncio` or threads |
            | CPU-heavy pure Python | `multiprocessing` / `ProcessPoolExecutor` |
            | Numeric arrays | NumPy/pandas (release the GIL in C code) |

            **pandas performance.** Use vectorised column operations, `groupby().agg()`, `merge` on proper keys,
            categorical dtypes for low-cardinality strings, `pd.to_numeric(..., downcast=...)`, and read only the
            needed columns (`usecols`) or in chunks. Watch for many-to-many merges that silently explode row counts.
        """),
        code=md("""
            import time
            from functools import wraps

            def timed(fn):
                @wraps(fn)
                def wrapper(*args, **kwargs):
                    start = time.perf_counter()
                    try:
                        return fn(*args, **kwargs)
                    finally:
                        print(f"{fn.__name__} took {time.perf_counter() - start:.3f}s")
                return wrapper

            def read_rows(path):              # generator: one line in memory at a time
                with open(path) as fh:
                    for line in fh:
                        yield line.rstrip().split(",")

            @timed
            def total_sales(path):
                return sum(float(r[2]) for r in read_rows(path) if r[1] == "IN")
        """),
        language="python",
        pitfalls=[
            "Mutable default arguments (`def f(x, items=[])`) that leak state between calls.",
            "Using `is` to compare values such as strings or numbers.",
            "Modifying a list while iterating over it - iterate over a copy or build a new list.",
            "Chained assignment in pandas (`df[df.a > 0]['b'] = 1`) - use `.loc[mask, 'b'] = 1`.",
            "Row-wise `.apply` or `iterrows` where a vectorised expression exists.",
        ],
        tips=[
            "Think aloud: state the approach and its time/space complexity before coding.",
            "Write idiomatic code - comprehensions, `enumerate`, `zip`, `collections.Counter`/`defaultdict`.",
            "For data tasks, say how you would validate the result (row counts, nulls, duplicates).",
            "Mention edge cases (empty input, ties, None/NaN) without being asked.",
        ],
        cheat_sheet=[
            "dict/set lookups are O(1) average; list membership is O(n).",
            "Strings are immutable - build with ''.join(parts), not += in a loop.",
            "sorted() returns a new list; list.sort() sorts in place and returns None.",
            "Generators can be consumed only once.",
            "Use `if __name__ == '__main__':` to make modules importable and runnable.",
            "df.loc is label-based, df.iloc is position-based.",
            "groupby + agg(named=('col', 'func')) gives clean, flat column names.",
        ],
        likely_questions=[
            "Difference between list, tuple, set and dict?",
            "What are generators and why use them?",
            "Explain decorators with an example.",
            "What is the GIL?",
            "How would you speed up a slow pandas pipeline?",
        ],
    ),
    "theory": [
        T("beginner", "What is the difference between a list, a tuple, a set and a dictionary in Python?",
          """
          | Type | Ordered | Mutable | Duplicates | Typical use |
          |---|---|---|---|---|
          | `list` | yes | yes | yes | sequences you append to / sort |
          | `tuple` | yes | no | yes | fixed records, dict keys, return multiple values |
          | `set` | no | yes | no | de-duplication, fast membership tests |
          | `dict` | insertion-ordered (3.7+) | yes | unique keys | key -> value lookups |

          Lists and tuples are indexable; sets and dicts are hash tables, so membership checks are **O(1) on
          average** versus O(n) for a list. Because tuples are immutable (and hashable when their items are), they
          can be dictionary keys - e.g. `{(store_id, sku): qty}`. In data work I use sets to de-duplicate IDs and
          dicts for lookups/mappings.
          """,
          ["Mutability and hashability", "Ordering guarantees", "O(1) vs O(n) membership", "A practical use case for each"],
          "Use the table structure verbally, then give one real example from your own code - e.g. a set used to "
          "de-duplicate customer IDs.",
          ["Why can't a list be a dictionary key?", "How is a dict implemented internally?",
           "When would you use a namedtuple or dataclass instead of a tuple?"], hot=True),
        T("beginner", "What are mutable and immutable objects, and why is a mutable default argument a bug?",
          """
          Mutable objects (`list`, `dict`, `set`, most custom objects) can change in place; immutable ones (`int`,
          `float`, `str`, `tuple`, `frozenset`) cannot - "changing" them creates a new object.

          Default argument values are evaluated **once, when the function is defined**. So:

          ```python
          def add(item, bucket=[]):
              bucket.append(item)
              return bucket

          add(1)  # [1]
          add(2)  # [1, 2]  <- same list reused!
          ```

          The fix is the `None` sentinel:

          ```python
          def add(item, bucket=None):
              bucket = [] if bucket is None else bucket
              bucket.append(item)
              return bucket
          ```

          Mutability also matters for hashing (only immutable objects can be dict keys) and for aliasing:
          `b = a` does not copy a list.
          """,
          ["Definition with examples", "Defaults evaluated at definition time", "None-sentinel fix", "Aliasing / copying"],
          "Write the 4-line buggy example on the whiteboard - interviewers love seeing you know the exact mechanism.",
          ["What is the difference between shallow and deep copy?", "Is a tuple containing a list hashable?"], hot=True),
        T("intermediate", "Explain generators and the `yield` keyword. When would you use them instead of a list?",
          """
          A generator is a function that uses `yield` to produce a sequence **lazily**: each `next()` resumes the
          function until the next `yield`, keeping its local state between calls. Generator expressions
          (`(x*x for x in data)`) are the inline form.

          Use them when:
          - the data is large or infinite (log files, streaming records) - memory stays flat;
          - you want a pipeline of stages (`read -> parse -> filter`) without materialising intermediates;
          - you might stop early (`any()`, `next()`), avoiding wasted work.

          Trade-offs: a generator can be iterated **only once**, has no `len()` or indexing, and debugging is
          slightly harder. If you need random access or multiple passes, use a list.

          ```python
          def read_large_file(path):
              with open(path) as f:
                  for line in f:
                      yield line.strip()

          errors = sum(1 for line in read_large_file("app.log") if "ERROR" in line)
          ```
          """,
          ["Lazy evaluation & state retention", "Memory efficiency", "Pipelines / early exit", "Single-pass limitation"],
          "Tie it to a real case - e.g. streaming a multi-GB file - and mention `yield from` for delegating to sub-generators.",
          ["What does `yield from` do?", "How is a generator different from an iterator?",
           "How would you process a 20 GB CSV in Python?"], hot=True),
        T("intermediate", "What is a decorator? How would you write one that retries a function on failure?",
          """
          A decorator is a callable that receives a function and returns a new function that adds behaviour around
          it - without changing the original code. `@retry` above `def f()` is shorthand for `f = retry(f)`.

          ```python
          import time, functools

          def retry(times=3, delay=1.0, exceptions=(Exception,)):
              def decorator(fn):
                  @functools.wraps(fn)
                  def wrapper(*args, **kwargs):
                      for attempt in range(1, times + 1):
                          try:
                              return fn(*args, **kwargs)
                          except exceptions:
                              if attempt == times:
                                  raise
                              time.sleep(delay * 2 ** (attempt - 1))  # exponential backoff
                  return wrapper
              return decorator

          @retry(times=4, exceptions=(ConnectionError,))
          def fetch_rates(): ...
          ```

          Note the three levels: the outer function takes the decorator's arguments, the middle one takes the
          function, the inner `wrapper` runs at call time. `functools.wraps` preserves the name and docstring.
          Common uses: logging, timing, caching (`functools.lru_cache`), authentication, rate limiting.
          """,
          ["Higher-order function concept", "@ syntax equivalence", "Decorator with arguments (3 levels)", "functools.wraps"],
          "Retry-with-backoff is a great example because it shows production thinking - mention catching only "
          "specific, transient exceptions.",
          ["What does functools.wraps do?", "How does lru_cache work?", "Can you decorate a class?"]),
        T("advanced", "What is the GIL, and how do you speed up CPU-bound versus I/O-bound Python code?",
          """
          The **Global Interpreter Lock** is a mutex in CPython that lets only one thread execute Python bytecode at
          a time. It simplifies memory management (reference counting) but means threads do not run Python code in
          parallel on multiple cores.

          - **I/O-bound** work (HTTP calls, DB queries, file reads) spends most time waiting; the GIL is released
            while waiting, so `threading` or `asyncio` give big speed-ups.
          - **CPU-bound** pure-Python work (parsing, loops, simulations) needs real parallelism: `multiprocessing` /
            `concurrent.futures.ProcessPoolExecutor`, or moving the hot loop into C-backed libraries (NumPy,
            pandas, Numba, Cython) which release the GIL.
          - At larger scale, distribute with Spark, Dask or Ray.

          Trade-offs: processes have higher start-up and serialisation (pickling) cost, so batch work into
          sizeable chunks. Newer Python versions also offer an optional free-threaded (no-GIL) build, but most
          production stacks still run the standard interpreter.
          """,
          ["What the GIL is and why it exists", "I/O-bound -> threads/asyncio", "CPU-bound -> processes/vectorisation",
           "Overheads and trade-offs"],
          "Classify the workload first ('is it CPU- or I/O-bound?') - that framing is exactly what interviewers want to hear.",
          ["When is asyncio better than threads?", "How do processes share data?",
           "How would you parallelise feature engineering over 500 files?"], hot=True),
        T("advanced", "A pandas pipeline on a 10 GB dataset is slow and memory-hungry. How do you optimise it?",
          """
          1. **Measure first** - `%timeit`, `cProfile`/`line_profiler`, `df.memory_usage(deep=True)`.
          2. **Load less** - `usecols`, explicit `dtype`s, `parse_dates` only where needed, Parquet instead of CSV
             (columnar + compressed), or `chunksize` for streaming aggregation.
          3. **Shrink dtypes** - `category` for low-cardinality strings, downcast `int64 -> int32`,
             `float64 -> float32`; often a 50-80% memory cut.
          4. **Vectorise** - replace `iterrows`/row-wise `apply` with column arithmetic, `np.where`, `np.select`,
             `.str`/`.dt` accessors, `groupby().transform()`.
          5. **Fix joins** - check key uniqueness before `merge` (many-to-many explodes rows); merge on
             categoricals/ints, not long strings.
          6. **Avoid copies** - chain operations, drop unused columns early, avoid repeated `concat` in a loop
             (collect then concat once).
          7. **Scale out when needed** - Polars or DuckDB for single-machine speed, Dask/Spark when data outgrows
             RAM.

          I'd quote the before/after: e.g. "memory 9 GB -> 2.3 GB, runtime 40 min -> 4 min".
          """,
          ["Profile before optimising", "I/O + dtype optimisation", "Vectorisation", "Join hygiene",
           "Knowing when to switch tools"],
          "Answer as a checklist, then anchor it with a real before/after number from your projects.",
          ["What is the difference between apply, map and transform?", "When would you choose Polars or Spark?",
           "How do categorical dtypes save memory?"]),
    ],
    "practical": [
        P("beginner", "Return the k most frequent words in a list, breaking ties alphabetically.",
          """
          Input: `words = ["data", "ai", "data", "ml", "ai", "data", "sql"]`, `k = 2`
          Output: `["data", "ai"]`
          """,
          ["Count occurrences with a hash map (Counter).", "Sort by (-count, word) so ties go alphabetical.",
           "Return the first k words.", "Mention the heap alternative for large n and small k."],
          "`Counter` counts in O(n). Sorting the unique words by the key `(-count, word)` gives highest frequency "
          "first and alphabetical order on ties. For a very large vocabulary and small k, `heapq.nsmallest` with "
          "the same key avoids sorting everything.",
          """
          from collections import Counter
          import heapq

          def top_k_words(words, k):
              counts = Counter(words)
              return [w for w, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:k]]

          def top_k_words_heap(words, k):          # O(n + u log k)
              counts = Counter(words)
              return heapq.nsmallest(k, counts, key=lambda w: (-counts[w], w))

          print(top_k_words(["data", "ai", "data", "ml", "ai", "data", "sql"], 2))  # ['data', 'ai']
          """, "python",
          "O(n + u log u) with sorting (u = unique words), O(n + u log k) with a heap; O(u) extra space.",
          ["k larger than the number of unique words", "Empty list", "Case sensitivity ('AI' vs 'ai')"],
          "Clarify tie-breaking and case sensitivity before coding - it shows you think about requirements.",
          ["How would you do this for a 100 GB file?", "Can you do it in a single pass with bounded memory?"], hot=True),
        P("intermediate", "Using pandas, find each customer's total spend, order count and days since last order, "
          "then return the top 5 customers by spend.",
          """
          `orders` DataFrame columns: `order_id`, `customer_id`, `order_date` (string), `amount`.
          Use `as_of = 2026-01-31` as today's date.
          """,
          ["Parse dates once with pd.to_datetime.", "Group by customer with named aggregations.",
           "Compute recency from the max order date.", "Sort and take the top 5."],
          "Named aggregation keeps the code readable and produces flat column names. Recency is computed after the "
          "aggregation on just one row per customer, which is cheap.",
          """
          import pandas as pd

          def top_customers(orders: pd.DataFrame, as_of="2026-01-31", n=5) -> pd.DataFrame:
              df = orders.assign(order_date=pd.to_datetime(orders["order_date"]))
              summary = (
                  df.groupby("customer_id")
                    .agg(total_spend=("amount", "sum"),
                         orders=("order_id", "nunique"),
                         last_order=("order_date", "max"))
              )
              summary["days_since_last"] = (pd.Timestamp(as_of) - summary["last_order"]).dt.days
              return summary.sort_values("total_spend", ascending=False).head(n).reset_index()
          """, "python",
          "O(n) for the groupby plus O(c log c) to sort c customers.",
          ["Refund rows with negative amounts", "Duplicate order rows (hence nunique)", "Missing or malformed dates"],
          "Say how you'd sanity-check the output: totals reconcile with df.amount.sum(), no null customer IDs.",
          ["How would you write the same in SQL?", "How would you compute RFM segments from this?"], hot=True),
        P("advanced", "Implement an LRU (least-recently-used) cache with O(1) get and put.",
          """
          `cache = LRUCache(2)`; `put(1, 'a')`, `put(2, 'b')`, `get(1)` -> 'a', `put(3, 'c')` evicts key 2,
          `get(2)` -> -1.
          """,
          ["Need O(1) lookup -> hash map.", "Need O(1) recency updates/eviction -> doubly linked list.",
           "OrderedDict combines both: move_to_end + popitem(last=False).",
           "Mention the manual dict + linked-list version if asked."],
          "`OrderedDict` keeps keys in order of insertion and supports moving a key to the end in O(1). Every access "
          "moves the key to the 'most recent' end; when capacity is exceeded we pop from the 'least recent' end.",
          """
          from collections import OrderedDict

          class LRUCache:
              def __init__(self, capacity: int):
                  self.capacity = capacity
                  self.data = OrderedDict()

              def get(self, key):
                  if key not in self.data:
                      return -1
                  self.data.move_to_end(key)          # mark as most recently used
                  return self.data[key]

              def put(self, key, value) -> None:
                  if key in self.data:
                      self.data.move_to_end(key)
                  self.data[key] = value
                  if len(self.data) > self.capacity:
                      self.data.popitem(last=False)   # evict least recently used
          """, "python",
          "O(1) time for get and put; O(capacity) space.",
          ["Capacity 0", "Updating an existing key", "Thread safety if shared across threads"],
          "Explain why you need two structures (hash map + linked list) before showing the OrderedDict shortcut.",
          ["How would you make it thread-safe?", "How does functools.lru_cache differ?",
           "How would you add a TTL per entry?"]),
    ],
    "scenario": [
        S("beginner", """
          Your Python script processes a sales CSV perfectly on your laptop, but in production it crashes with a
          MemoryError on the full 8 GB file. The report is due in two hours.
          """,
          "How do you fix it quickly and safely?",
          [("Reproduce & measure", "Check file size, row count and df.memory_usage(deep=True) on a sample."),
           ("Load less", "Read only needed columns (usecols) with explicit, smaller dtypes."),
           ("Stream", "Process with chunksize or a generator and aggregate incrementally."),
           ("Validate", "Compare totals from the chunked run with a known sample result."),
           ("Prevent", "Switch storage to Parquet and add a memory test to the pipeline.")],
          """
          I'd first confirm *why* it fails: on a 1% sample I'd check `memory_usage(deep=True)` - CSVs loaded with
          default `object`/`int64` dtypes often take 3-5x the file size in RAM.

          The quickest safe fix is to stop loading everything at once. I'd read only the columns the report needs
          with `usecols`, give explicit dtypes (category for region/product, `float32` for amounts), and process the
          file with `chunksize=1_000_000`, aggregating each chunk into a running `groupby` result. That keeps memory
          flat regardless of file size.

          Before sending the report I'd validate: row count processed equals the file's row count, and totals for
          one region match a manual check. After the deadline I'd propose converting the source to Parquet and
          adding a memory regression check so this does not recur.
          """,
          ["Diagnoses before changing code", "Knows chunking / dtype tricks", "Validates output under time pressure",
           "Proposes a durable prevention"],
          ["Just asking for a bigger machine without understanding the cause", "Skipping validation of chunked results",
           "Rewriting the whole pipeline under a deadline"],
          ["What if a group spans multiple chunks?", "When would you move this to Spark?"]),
        S("intermediate", """
          A nightly pandas feature-engineering job that used to take 5 minutes now takes 2 hours after the input
          data roughly doubled. Downstream model training is now missing its SLA.
          """,
          "Walk me through how you would find and fix the slowdown.",
          [("Clarify", "Did only volume change, or also code, library versions or data distribution?"),
           ("Profile", "Time each stage with cProfile/line_profiler to find the hotspot."),
           ("Check joins", "Verify merge key uniqueness - a many-to-many join can explode rows non-linearly."),
           ("Optimise", "Vectorise apply/loops, fix dtypes, filter early, reuse computed groupbys."),
           ("Scale & guard", "Move to Polars/DuckDB/Spark if needed and add runtime + row-count alerts.")],
          """
          A 2x data increase causing a 24x slowdown tells me something is **super-linear**, so I'd look for that
          rather than generic tuning.

          First I'd profile the job stage by stage. The usual suspects are (1) a `merge` where the key is no longer
          unique - duplicates on both sides create a many-to-many join and the row count explodes; (2) row-wise
          `apply`/`iterrows`; (3) repeated `concat` inside a loop, which is quadratic.

          In a similar case I found a lookup table had started containing duplicate SKUs, so a merge produced 30x
          the rows. I de-duplicated the dimension, added an assertion on key uniqueness (`validate="many_to_one"`
          in `merge`), and vectorised a row-wise apply - runtime dropped below the original 5 minutes.

          Finally I'd add guardrails: row-count and runtime alerts, and a plan to move to Spark or DuckDB if volume
          keeps growing.
          """,
          ["Spots the super-linear signal", "Uses profiling instead of guessing", "Knows merge validation",
           "Adds monitoring to prevent recurrence"],
          ["Blaming data volume without evidence", "Jumping straight to Spark", "Not validating the fix on the full data"],
          ["What does validate='one_to_one' do in merge?", "How would you test this job automatically?"], hot=True),
        S("advanced", """
          You must enrich 1 million customer records by calling a third-party REST API that allows 100 requests per
          second, and the whole job must finish within an hour. Calls occasionally fail with 429 or 5xx errors.
          """,
          "Design the Python solution.",
          [("Do the maths", "1M / 100 rps = 10,000 s (about 2.8 h) - batching or more quota is required."),
           ("Reduce calls", "Use batch endpoints, cache/deduplicate keys, skip already-enriched records."),
           ("Concurrency", "asyncio + aiohttp with a semaphore and a token-bucket rate limiter."),
           ("Resilience", "Retries with exponential backoff + jitter on 429/5xx; idempotent writes."),
           ("Operability", "Checkpoint progress, log failures to a dead-letter table, monitor throughput.")],
          """
          I'd start with arithmetic: 1,000,000 calls at 100/s is about 2.8 hours, so a naive solution cannot meet a
          1-hour SLA. I'd first try to **reduce the number of calls**: de-duplicate keys, skip records enriched
          recently (cache), and use a batch endpoint if one exists - 50 records per call makes it 20,000 calls,
          about 3.5 minutes.

          For the calls themselves I'd use `asyncio` with `aiohttp`: a token-bucket limiter keeps us under 100 rps,
          and a semaphore caps open connections. Each call is wrapped in retries with exponential backoff and
          jitter, honouring `Retry-After` on 429s; 4xx errors other than 429 go to a dead-letter table instead of
          retrying.

          Results are written in idempotent batches (upsert by customer_id) and progress is checkpointed, so a crash
          resumes rather than restarts. I'd expose metrics (rps, error rate, ETA) and alert if the ETA exceeds the
          SLA. If batching isn't available, I'd negotiate higher quota or split across approved API keys.
          """,
          ["Does capacity maths up front", "Reduces work before parallelising", "Correct async + rate limiting",
           "Idempotency, checkpointing and failure handling"],
          ["Spawning 1M threads", "Retrying non-retryable errors forever", "No checkpointing for a long job"],
          ["Threads vs asyncio here?", "How do you implement a token bucket?",
           "How would you test this without hitting the real API?"]),
    ],
    "quiz": [
        Q("beginner", "What does this print?\n\n```python\na = [1, 2, 3]\nb = a\nb.append(4)\nprint(a)\n```",
          ["[1, 2, 3]", "[1, 2, 3, 4]", "[4]", "An error"], 1,
          "`b = a` binds a second name to the same list object, so appending through `b` mutates the list `a` also "
          "refers to.",
          ["Would be true only if b were a copy, e.g. a.copy().", "Correct - a and b are the same object.",
           "append adds to the existing list; it does not replace it.", "Appending to a list is valid."],
          "Aliasing questions are a quick screen for whether you understand Python's name-binding model.", hot=True),
        Q("beginner", "Which of these built-in types is immutable?",
          ["list", "dict", "set", "tuple"], 3,
          "Tuples cannot be modified after creation (though they may contain mutable objects).",
          ["Lists support append/remove in place.", "Dicts can be updated in place.", "Sets support add/discard.",
           "Correct - tuples are immutable, which also makes them usable as dict keys when their items are hashable."],
          "Expect a follow-up on why immutability matters for dict keys."),
        Q("intermediate", "Given `def f(x, items=[]): items.append(x); return items`, what does `f(2)` return "
          "if `f(1)` was called first?",
          ["[2]", "[1, 2]", "[1]", "None"], 1,
          "Default values are evaluated once at definition time, so both calls share the same list.",
          ["Would happen with the items=None idiom.", "Correct - the default list persists across calls.",
           "The second call appends 2.", "The function returns the list."],
          "Name the fix (None sentinel) right after giving the answer.", hot=True),
        Q("intermediate", "What is the average time complexity of `x in s` when `s` is a Python set?",
          ["O(1)", "O(log n)", "O(n)", "O(n log n)"], 0,
          "Sets are hash tables, so membership is a hash lookup - O(1) on average (O(n) only in pathological "
          "collision cases).",
          ["Correct.", "That would be a balanced tree or binary search.", "That is list membership.",
           "That is sorting cost."],
          "Mention converting a list to a set before repeated membership checks - a common optimisation."),
        Q("advanced", "In standard CPython, which option best speeds up a CPU-bound pure-Python function across "
          "8 cores?",
          ["threading.Thread pool", "asyncio.gather", "multiprocessing / ProcessPoolExecutor",
           "Adding more print statements"], 2,
          "Separate processes each have their own interpreter and GIL, so they run truly in parallel on multiple "
          "cores.",
          ["Threads are serialised by the GIL for Python bytecode.", "asyncio is single-threaded concurrency for I/O.",
           "Correct.", "Not an optimisation."],
          "State the CPU-bound vs I/O-bound distinction before answering - it signals real-world experience."),
    ],
}
