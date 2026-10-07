from ._build import P, Q, S, T, md, note

TOPIC = {
    "key": "data_engineering",
    "name": "Big Data & Data Engineering",
    "keywords": ["spark", "pyspark", "databricks", "hadoop", "hive", "kafka", "airflow", "etl", "elt",
                 "data pipeline", "data pipelines", "data engineering", "data engineer", "big data", "delta lake",
                 "lakehouse", "data lake", "data warehouse", "snowflake", "dbt", "streaming", "adf", "glue"],
    "core": ["spark", "pyspark", "databricks", "etl", "data pipeline", "data pipelines", "data engineering"],
    "subtopics": ["ETL vs ELT", "Spark internals", "Partitioning & file formats", "Joins, shuffles & skew",
                  "Orchestration & idempotency", "Streaming & Kafka", "Data modelling & SCD", "Data quality"],
    "revision": note(
        summary="Data-engineering rounds test how you move and transform data reliably at scale: Spark internals, "
        "file formats and partitioning, performance tuning (shuffles, skew, broadcast joins), orchestration, "
        "streaming, data modelling and data quality.",
        concepts=[
            ("ETL vs ELT", "Transform before loading (classic) vs load raw then transform inside a scalable warehouse "
             "or lakehouse (modern)."),
            ("Driver & executors", "The driver builds the DAG and schedules tasks; executors run tasks on partitions "
             "in parallel."),
            ("Lazy evaluation", "Transformations build a plan; nothing runs until an action (count, write, collect)."),
            ("Narrow vs wide", "map/filter work within a partition; groupBy/join/distinct need a shuffle across "
             "the network - the expensive part."),
            ("Partitions", "The unit of parallelism; aim for ~100-200 MB per partition and enough tasks for all "
             "cores."),
            ("Data skew", "A few keys hold most rows, so one task runs forever - fix with salting, broadcast joins "
             "or AQE skew handling."),
            ("Broadcast join", "Ship a small table to every executor to avoid shuffling the large table."),
            ("Parquet / Delta", "Columnar, compressed, predicate pushdown; Delta/Iceberg add ACID transactions, "
             "MERGE, time travel and schema evolution."),
            ("Idempotency", "Re-running a pipeline for the same period produces the same result (overwrite "
             "partitions or MERGE, never blind append)."),
            ("SCD Type 2", "Keep history of changing dimension attributes with valid_from/valid_to/is_current rows."),
        ],
        explanation=md("""
            **Spark execution.** Code -> logical plan -> Catalyst optimiser -> physical plan -> DAG split into
            **stages** at shuffle boundaries -> **tasks** (one per partition). Read the Spark UI: long stages, task
            time skew (max >> median), spill to disk and shuffle read size tell you where time goes.

            **Performance checklist.**
            1. Read less: columnar formats, partition pruning (filter on partition columns), select needed columns.
            2. Avoid unnecessary shuffles: broadcast small tables, pre-aggregate before joins, avoid `groupByKey`
               on RDDs (use `reduceByKey`/DataFrame aggregations).
            3. Right-size partitions: `spark.sql.shuffle.partitions`, enable Adaptive Query Execution (AQE) to
               coalesce partitions and split skewed ones.
            4. Handle skew: salting hot keys, isolating them, or AQE skew join.
            5. Cache only data reused multiple times, and unpersist after.
            6. Prefer built-in functions over Python UDFs (or use vectorised pandas UDFs).

            **Storage layout.** Partition by low-cardinality columns used in filters (e.g. `event_date`), avoid
            thousands of tiny files (compact/OPTIMIZE), and Z-order/cluster by frequent filter columns.

            **Reliable pipelines.** Idempotent writes (overwrite partition or MERGE), parameterised runs by date so
            backfills are trivial, retries with alerting, data-quality checks (row counts, null %, uniqueness,
            freshness, referential integrity) that fail fast, and lineage/documentation.

            **Batch vs streaming.** Streaming (Kafka -> Spark Structured Streaming/Flink) when freshness matters
            in seconds/minutes; handle late data with watermarks, exactly-once with checkpoints + idempotent sinks.
        """),
        code=md("""
            from pyspark.sql import SparkSession, functions as F

            spark = (SparkSession.builder.appName("daily_sales")
                     .config("spark.sql.adaptive.enabled", "true").getOrCreate())

            orders = spark.read.parquet("s3://lake/orders/")              # partitioned by order_date
            stores = spark.read.parquet("s3://lake/dim_store/")            # small dimension

            daily = (orders
                     .filter(F.col("order_date") == "2026-01-31")          # partition pruning
                     .join(F.broadcast(stores), "store_id")                # avoid shuffling orders
                     .groupBy("order_date", "region")
                     .agg(F.sum("amount").alias("revenue"),
                          F.countDistinct("customer_id").alias("customers")))

            (daily.write.mode("overwrite")                                  # idempotent per partition
                  .option("partitionOverwriteMode", "dynamic")
                  .partitionBy("order_date")
                  .parquet("s3://lake/marts/daily_sales/"))
        """),
        language="python",
        pitfalls=[
            "Calling collect() on a large DataFrame and crashing the driver.",
            "Appending in a pipeline that may be re-run - duplicates on every retry.",
            "Partitioning by a high-cardinality column (millions of tiny files).",
            "Python UDFs on hot paths instead of built-in functions.",
            "Ignoring skew: one task processing 80% of the data.",
        ],
        tips=[
            "Describe a pipeline you built: sources, volume, tools, SLAs, and how you ensured data quality.",
            "Quote numbers: data volume, runtime before/after tuning, cost.",
            "Use Spark UI vocabulary (stages, tasks, shuffle, spill) when discussing tuning.",
            "Always mention idempotency and backfills for batch pipelines.",
        ],
        cheat_sheet=[
            "Actions: count, collect, show, write, take. Transformations: select, filter, join, groupBy.",
            "repartition(n) = full shuffle (can increase or decrease); coalesce(n) = merge partitions, no full shuffle.",
            "Default broadcast threshold: spark.sql.autoBroadcastJoinThreshold (10 MB by default).",
            "Parquet: columnar + predicate pushdown; Avro: row-based, good for streaming/schema evolution.",
            "Watermark = how late data may arrive before a window is finalised.",
            "cache() keeps data in memory; use when reusing a DataFrame several times.",
        ],
        likely_questions=[
            "Explain Spark architecture.",
            "Transformations vs actions, narrow vs wide?",
            "How do you handle data skew?",
            "repartition vs coalesce?",
            "How do you make a pipeline idempotent?",
            "Implement SCD Type 2.",
        ],
    ),
    "theory": [
        T("beginner", "ETL vs ELT, and batch vs streaming - when would you choose each?",
          """
          **ETL** transforms data on a separate engine before loading it into the target; **ELT** loads raw data
          first and transforms it inside a scalable warehouse/lakehouse (Snowflake, BigQuery, Databricks) with SQL
          tools like dbt. ELT is the modern default because storage is cheap, compute is elastic and raw data
          stays available for reprocessing. ETL still makes sense when data must be cleaned/masked before landing
          (PII) or the target can't transform at scale.

          **Batch** processes data in scheduled chunks (hourly/daily) - simpler, cheaper, ideal for reporting and
          model training. **Streaming** processes events continuously with seconds-to-minutes latency - needed
          for fraud detection, real-time personalisation or operational monitoring, at the cost of more complexity
          (state, late data, exactly-once).

          My rule: choose the simplest freshness that meets the business need - many "real-time" requests are
          satisfied by 15-minute micro-batches.
          """,
          ["Definitions", "Why ELT is common now", "Batch vs streaming trade-offs", "Freshness-driven decision"],
          "Ask 'how fresh does the data really need to be?' - it shows pragmatic engineering judgement.",
          ["What is micro-batching?", "How does dbt fit into ELT?"], hot=True),
        T("beginner", "Why are columnar formats like Parquet preferred over CSV for analytics?",
          """
          Parquet stores data **column by column** with a schema, compression and statistics:
          - **Read only needed columns** - analytics queries touch a few columns of wide tables.
          - **Compression & encoding** per column (dictionary, run-length) - often 5-10x smaller than CSV.
          - **Predicate pushdown** - row-group min/max statistics let engines skip data that can't match filters.
          - **Types & schema** are preserved (no re-parsing strings into dates and numbers).

          CSV is row-based, untyped, uncompressed and must be fully parsed. Avro is row-based but schema-rich -
          good for streaming and write-heavy workloads. Table formats like Delta Lake/Iceberg sit on top of Parquet
          to add ACID transactions, MERGE/upserts, schema evolution and time travel.
          """,
          ["Column pruning", "Compression", "Predicate pushdown", "Schema/types", "Where Avro/Delta fit"],
          "Mention a real size/runtime reduction from switching CSV to Parquet if you have one.",
          ["What does Delta Lake add on top of Parquet?", "What are row groups?"]),
        T("intermediate", "Explain Spark's architecture: driver, executors, lazy evaluation, transformations and actions.",
          """
          - The **driver** runs your program, builds the logical plan, optimises it (Catalyst) and schedules work.
          - **Executors** are JVM processes on worker nodes that run **tasks** - one task per data partition - and
            cache data.
          - A cluster manager (YARN, Kubernetes, Databricks) allocates resources.

          **Transformations** (`select`, `filter`, `join`, `groupBy`) are **lazy** - they only add to the plan.
          **Actions** (`count`, `collect`, `write`, `show`) trigger execution. Laziness lets Spark optimise the
          whole plan: pushing filters down, pruning columns, choosing join strategies.

          Transformations are **narrow** (each output partition depends on one input partition - `map`, `filter`)
          or **wide** (need data from many partitions - `groupBy`, `join`, `distinct`), which trigger a
          **shuffle**. Spark splits the DAG into **stages** at shuffle boundaries. Shuffles are the main cost
          driver - network, disk and serialisation - so tuning focuses on reducing them.
          """,
          ["Driver vs executor roles", "Lazy evaluation and why", "Narrow vs wide", "Stages & shuffles"],
          "Sketch driver -> executors -> tasks; then explain one job's stages from a real pipeline.",
          ["What is the Catalyst optimiser?", "What happens when you call collect() on 100 GB?"], hot=True),
        T("intermediate", "What is the difference between repartition and coalesce, and how do you choose the "
          "number of partitions?",
          """
          - `repartition(n)` (or by columns) does a **full shuffle** and produces evenly sized partitions; it can
            increase or decrease the count, and partitioning by a key co-locates rows for later joins/writes.
          - `coalesce(n)` **merges existing partitions without a full shuffle** - cheap, but only decreases the
            count and can produce uneven partitions.

          Typical use: `coalesce` before writing a small result to avoid many tiny files; `repartition("date")`
          before a partitioned write, or to fix skewed/uneven partitions before heavy processing.

          Sizing: aim for roughly 100-200 MB per partition and at least 2-3x as many partitions as total cores.
          `spark.sql.shuffle.partitions` (default 200) controls shuffle output; with **AQE** enabled, Spark
          coalesces small shuffle partitions automatically at runtime.
          """,
          ["Shuffle vs no shuffle", "When to use each", "Partition sizing rule of thumb", "AQE"],
          "Tie it to the small-files problem - a very common real-world issue.",
          ["What is the small-files problem?", "What does AQE do?"], hot=True),
        T("advanced", "How do you detect and fix data skew in Spark joins and aggregations?",
          """
          **Detect**: in the Spark UI, one or a few tasks in a stage take far longer than the median, with much
          larger shuffle read sizes; often a key like `NULL`, `"unknown"` or one huge customer dominates.
          `df.groupBy(key).count().orderBy(desc("count"))` confirms it.

          **Fix**, depending on the case:
          1. **Broadcast join** if one side is small - no shuffle of the big side at all.
          2. **AQE skew join** (`spark.sql.adaptive.skewJoin.enabled`) automatically splits oversized partitions.
          3. **Salting**: add a random salt (0..N-1) to the hot key on the large side and explode the small side
             N times, join on (key, salt), then aggregate.
          4. **Isolate hot keys**: process the few heavy keys separately (e.g. broadcast) and union with the rest.
          5. **Clean null keys**: filter or handle NULL join keys separately - they often cause skew.
          6. For aggregations, **two-stage aggregation**: aggregate on (key, salt), then on key.
          """,
          ["How to detect in Spark UI", "Broadcast & AQE", "Salting mechanics", "Hot-key isolation & nulls"],
          "Walk through salting concretely with numbers - interviewers often ask you to code it.",
          ["Write the salting code.", "Why do NULL keys cause skew?"], hot=True),
        T("advanced", "How do you design an idempotent, backfillable pipeline, and implement SCD Type 2?",
          """
          **Idempotency**: running the same job twice for the same input produces the same output.
          - Parameterise every run by a logical date/window, never "now".
          - Write with **overwrite-by-partition** or **MERGE (upsert)** on business keys, never blind appends.
          - Make side effects (emails, API calls) conditional and tracked.
          - Deduplicate inputs (e.g. by event id) to handle at-least-once delivery.

          **Backfills** are then just re-running the DAG for historical dates (Airflow `catchup`/`backfill`), in
          parallel if partitions are independent.

          **SCD Type 2** keeps history for changing attributes (e.g. a customer's city):
          1. Compare incoming records to current dimension rows by business key and hash of tracked attributes.
          2. For changed keys: close the current row (`valid_to = change_date`, `is_current = false`).
          3. Insert a new row with `valid_from = change_date`, `valid_to = '9999-12-31'`, `is_current = true`.
          4. Insert brand-new keys as current rows.
          With Delta Lake this is a MERGE plus an insert of the new versions in one transaction.
          """,
          ["Logical-date parameterisation", "Overwrite/MERGE not append", "Dedup for at-least-once", "SCD2 steps"],
          "Mention a backfill you ran and how idempotency made it safe.",
          ["How would you handle late-arriving data?", "SCD Type 1 vs 2 vs 3?"]),
    ],
    "practical": [
        P("beginner", "In PySpark, compute daily revenue and order count per region from Parquet data and write the "
          "result partitioned by date.",
          """
          `orders` Parquet with columns: `order_id`, `order_ts` (timestamp), `region`, `amount`, `status`.
          Only `status = 'completed'` counts.
          """,
          ["Read Parquet; filter early.", "Derive order_date from the timestamp.",
           "groupBy date and region; aggregate.", "Write partitioned by date with overwrite mode."],
          "Filtering before grouping reduces shuffle volume. Dynamic partition overwrite makes re-runs idempotent "
          "for the dates processed.",
          """
          from pyspark.sql import functions as F

          orders = spark.read.parquet("/lake/orders")
          daily = (orders
                   .filter(F.col("status") == "completed")
                   .withColumn("order_date", F.to_date("order_ts"))
                   .groupBy("order_date", "region")
                   .agg(F.sum("amount").alias("revenue"),
                        F.countDistinct("order_id").alias("orders")))

          (daily.write
                .mode("overwrite")
                .option("partitionOverwriteMode", "dynamic")
                .partitionBy("order_date")
                .parquet("/lake/marts/daily_region_revenue"))
          """, "python",
          "One shuffle for the aggregation; scan cost proportional to the columns read.",
          ["Time zones when deriving dates", "Duplicate order rows", "Late-arriving orders for past dates"],
          "Mention why you filter before the groupBy and why the write is idempotent.",
          ["How would you process only new data each day?", "How would you test this job?"]),
        P("intermediate", "Deduplicate a customer table in PySpark, keeping only the latest record per customer.",
          """
          `customers_raw(customer_id, email, city, updated_at, ingestion_ts)` contains multiple versions per
          customer. Keep the row with the latest `updated_at`; break ties with the latest `ingestion_ts`.
          """,
          ["Window partitioned by customer_id.", "Order by updated_at desc, ingestion_ts desc.",
           "row_number() and keep rn = 1.", "Drop the helper column."],
          "row_number guarantees exactly one row per customer even when timestamps tie, thanks to the secondary "
          "ordering column.",
          """
          from pyspark.sql import Window, functions as F

          w = Window.partitionBy("customer_id").orderBy(F.col("updated_at").desc(), F.col("ingestion_ts").desc())

          latest = (spark.table("customers_raw")
                    .withColumn("rn", F.row_number().over(w))
                    .filter("rn = 1")
                    .drop("rn"))
          """, "python",
          "One shuffle by customer_id plus a sort within each partition.",
          ["NULL updated_at values (decide ordering with nulls_last)", "Exact duplicate rows", "Skewed customer ids"],
          "Explain why row_number (not rank) is the right choice here.",
          ["How would you do this incrementally with Delta MERGE?", "How would you detect skew here?"], hot=True),
        P("advanced", "Implement an SCD Type 2 update for a customer dimension using Delta Lake MERGE (SQL).",
          """
          `dim_customer(customer_sk, customer_id, city, segment, valid_from, valid_to, is_current)` and a daily
          `stg_customer(customer_id, city, segment, change_date)`. Track history of `city` and `segment`.
          """,
          ["Find staged rows that are new or changed vs the current dimension row.",
           "MERGE: close current rows whose attributes changed.",
           "Insert new versions (changed keys) and brand-new keys.", "Wrap in one transaction / job run."],
          "The classic trick is to MERGE a union of (a) changed rows keyed normally - to expire the old version - "
          "and (b) the same changed rows with a NULL merge key - forcing an INSERT of the new version.",
          """
          MERGE INTO dim_customer AS d
          USING (
              -- rows to insert as new versions (merge_key NULL never matches)
              SELECT NULL AS merge_key, s.* FROM stg_customer s
              JOIN dim_customer d ON s.customer_id = d.customer_id AND d.is_current = true
              WHERE s.city <> d.city OR s.segment <> d.segment
              UNION ALL
              -- all staged rows keyed by business key (to expire old versions / insert new keys)
              SELECT s.customer_id AS merge_key, s.* FROM stg_customer s
          ) AS u
          ON d.customer_id = u.merge_key AND d.is_current = true
          WHEN MATCHED AND (d.city <> u.city OR d.segment <> u.segment) THEN
              UPDATE SET d.is_current = false, d.valid_to = u.change_date
          WHEN NOT MATCHED THEN
              INSERT (customer_id, city, segment, valid_from, valid_to, is_current)
              VALUES (u.customer_id, u.city, u.segment, u.change_date, DATE '9999-12-31', true);
          """, "sql",
          "One MERGE pass over the staged rows joined with current dimension rows.",
          ["NULL attribute values (use null-safe comparison <=>)", "Multiple changes for one key in one batch",
           "Late-arriving changes with an older change_date"],
          "Explain the NULL merge-key trick before writing - it's the non-obvious part.",
          ["How would you handle multiple updates per key in one batch?", "How do fact tables join to SCD2 dims?"]),
    ],
    "scenario": [
        S("beginner", """
          You arrive at 9 a.m. to find the overnight pipeline failed. Leadership dashboards still show the day
          before yesterday's numbers, and a sales review starts at 11 a.m.
          """,
          "What do you do?",
          [("Communicate", "Tell dashboard users immediately that data is stale and give an ETA."),
           ("Diagnose", "Read logs to find the failing task and root cause."),
           ("Recover", "Fix or work around it and re-run idempotently from the failed step."),
           ("Validate", "Check row counts and key totals before announcing recovery."),
           ("Prevent", "Write a short RCA; add alerts, retries or data-quality checks.")],
          """
          First, **communicate**: a quick message to the dashboard owners and the sales review organiser - "data is
          stale since Tuesday, investigating, update by 9:45". A stale banner on the dashboard prevents wrong
          decisions.

          Then diagnose from the orchestrator logs: which task failed and why - a source file arriving late, a
          schema change, a credentials expiry, or a resource issue. I'd fix the immediate cause (e.g. adjust the
          schema mapping) and re-run from the failed task; because our tasks overwrite their date partition, the
          re-run is safe and won't duplicate data.

          Before announcing recovery I'd validate row counts and revenue totals against the source. Afterwards I'd
          write a short RCA and add prevention: an alert at failure time (not at 9 a.m.), automatic retries for
          transient errors, and a schema-change check at ingestion.
          """,
          ["Communicates before fixing", "Structured diagnosis", "Idempotent re-run", "Validation + prevention"],
          ["Silently fixing without telling users", "Re-running blindly and duplicating data", "No follow-up RCA"],
          ["How would you design alerting for this pipeline?", "What makes a re-run safe?"]),
        S("intermediate", """
          A Spark job joining 3 billion click events with a 200-million-row user table now takes 3 hours. In the
          Spark UI, 199 of 200 tasks in the join stage finish in 2 minutes; one task runs for over 2.5 hours.
          """,
          "What's going on and how do you fix it?",
          [("Confirm skew", "Task time and shuffle-read size for the slow task vs the median."),
           ("Find the hot key", "Count rows per join key - often NULL/unknown or one giant user."),
           ("Quick fix", "Enable AQE skew join; filter or separately handle NULL keys."),
           ("Structural fix", "Salt the hot keys or broadcast-join the hot-key slice."),
           ("Verify", "Compare runtime and output row counts; add a skew check to monitoring.")],
          """
          One task running 75x longer than the rest is classic **data skew**: one join key holds a huge share of
          the rows, so a single partition gets them all.

          I'd confirm by counting rows per `user_id` on the click side. Very often the culprit is a NULL or default
          id (e.g. logged-out traffic with user_id = 0). If the hot key is NULL/unknown and can't match anyway,
          I'd filter it out of the join and union those rows back afterwards - that alone usually fixes it.

          Otherwise: enable **AQE skew-join handling**, which splits oversized partitions automatically; if that's
          not enough, **salt** the hot keys - add a random salt 0..19 to clicks for those keys and replicate the
          matching user rows 20 times - so the work spreads over 20 tasks. I'd validate that output row counts
          match the previous run and add a check that alerts when one key exceeds a share threshold.
          """,
          ["Recognises skew from the task pattern", "Checks for NULL/default keys", "Knows AQE and salting",
           "Validates correctness after tuning"],
          ["Adding more executors (doesn't help a single task)", "Increasing shuffle partitions blindly",
           "Salting without explaining the mechanics"],
          ["Write the salting code.", "Why doesn't adding executors help here?"], hot=True),
        S("advanced", """
          The product team wants a live dashboard of user activity (page views, add-to-carts, purchases) with
          under 1 minute of latency, from mobile and web apps generating 50,000 events per second. Events can arrive
          up to 2 hours late when phones are offline.
          """,
          "Design the pipeline.",
          [("Ingest", "Apps -> collector API -> Kafka topics (partitioned by user/session), schema registry."),
           ("Process", "Spark Structured Streaming/Flink: parse, validate, dedupe by event_id, enrich."),
           ("Handle time", "Event-time windows with a watermark; late events update windows or go to correction."),
           ("Store & serve", "Delta tables (bronze/silver/gold) + a real-time OLAP store for the dashboard."),
           ("Operate", "Exactly-once via checkpoints + idempotent sinks; monitoring for lag, volume, schema.")],
          """
          **Ingestion**: apps send events to a lightweight collector that writes to **Kafka**, partitioned by user
          or session id so ordering per user is preserved; a schema registry enforces event contracts (Avro/Protobuf)
          and supports evolution.

          **Processing**: Spark Structured Streaming (or Flink) consumes Kafka, validates and deduplicates on
          `event_id` (apps retry, so delivery is at-least-once), enriches with user/product dimensions (broadcast
          or lookup), and aggregates per minute by **event time**. A **watermark** of 2 hours lets late events still
          update their windows; anything later goes to a correction path that rewrites daily aggregates in batch.

          **Storage/serving**: raw events land in a bronze Delta table, cleaned events in silver, minute-level
          aggregates in gold. Because dashboards need sub-minute freshness with many concurrent queries, gold
          aggregates also feed a real-time OLAP store (e.g. Druid/Pinot or a Databricks SQL endpoint).

          **Reliability**: checkpointing + idempotent/transactional sinks give effectively exactly-once results;
          I'd monitor consumer lag, events/sec by platform, late-event rate and schema errors, with alerts.
          """,
          ["Sound end-to-end architecture", "Event time vs processing time & watermarks", "Dedup / exactly-once",
           "Serving layer for dashboards", "Operational monitoring"],
          ["Processing-time windows only", "No dedup for retries", "Querying the raw stream directly from dashboards"],
          ["What is a watermark exactly?", "Kafka partitions vs consumer parallelism?",
           "How would you reprocess a bad day of events?"]),
    ],
    "quiz": [
        Q("beginner", "Which format is generally best for analytical queries over wide tables?",
          ["CSV", "JSON", "Parquet", "XML"], 2,
          "Parquet is columnar and compressed, supports column pruning and predicate pushdown.",
          ["Row-based, untyped, uncompressed.", "Verbose, row-based.", "Correct.", "Verbose and slow to parse."],
          "Mention Delta/Iceberg as the table layer on top of Parquet.", hot=True),
        Q("beginner", "Which of these is a Spark ACTION (triggers execution)?",
          ["filter()", "select()", "count()", "withColumn()"], 2,
          "Actions like count(), collect() and write trigger the lazy plan to execute.",
          ["Transformation.", "Transformation.", "Correct.", "Transformation."],
          "Explain lazy evaluation in one sentence when answering."),
        Q("intermediate", "Which operation causes a shuffle in Spark?",
          ["filter", "map", "groupBy aggregation", "withColumn"], 2,
          "Grouping needs all rows with the same key in the same partition, requiring data movement across "
          "executors.",
          ["Narrow transformation.", "Narrow transformation.", "Correct - a wide transformation.",
           "Narrow transformation."],
          "Shuffles define stage boundaries - mention that.", hot=True),
        Q("intermediate", "What is the key difference between coalesce(n) and repartition(n)?",
          ["coalesce always increases partitions", "coalesce avoids a full shuffle when reducing partitions",
           "repartition never shuffles", "They are identical"], 1,
          "coalesce merges existing partitions locally; repartition performs a full shuffle for even distribution.",
          ["It only reduces.", "Correct.", "repartition always shuffles.", "They differ in cost and balance."],
          "Use coalesce before writing small outputs to avoid tiny files."),
        Q("advanced", "You join a 2 TB fact table with a 40 MB dimension table. What is the most efficient strategy?",
          ["Sort-merge join with 2,000 shuffle partitions", "Broadcast the dimension table",
           "Collect both to the driver", "Cartesian join then filter"], 1,
          "Broadcasting the small table to every executor avoids shuffling the 2 TB side entirely.",
          ["Works but shuffles 2 TB needlessly.", "Correct.", "Would crash the driver.", "Extremely expensive."],
          "Mention autoBroadcastJoinThreshold and the F.broadcast hint.", hot=True),
    ],
}
