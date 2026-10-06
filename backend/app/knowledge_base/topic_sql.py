from ._build import P, Q, S, T, md, note

TOPIC = {
    "key": "sql",
    "name": "SQL & Databases",
    "keywords": ["sql", "mysql", "postgresql", "postgres", "snowflake", "bigquery", "redshift", "database",
                 "databases", "query", "queries", "rdbms", "data modeling", "data modelling", "oracle"],
    "core": ["sql"],
    "subtopics": ["Joins", "Aggregation & GROUP BY/HAVING", "Window functions", "CTEs & subqueries",
                  "NULL handling", "Indexes & query optimisation", "Data modelling"],
    "revision": note(
        summary="SQL rounds test joins, aggregation, window functions, CTEs/subqueries, NULL semantics, query "
        "optimisation and enough data modelling to reason about grain and keys. Expect to write 2-4 queries live.",
        concepts=[
            ("Logical query order", "FROM/JOIN -> WHERE -> GROUP BY -> HAVING -> SELECT -> DISTINCT -> ORDER BY -> "
             "LIMIT. Explains why SELECT aliases can't be used in WHERE."),
            ("INNER / LEFT / RIGHT / FULL / CROSS JOIN", "Matching rows only / all left rows + matches / all right + "
             "matches / everything from both / Cartesian product."),
            ("WHERE vs HAVING", "WHERE filters rows before grouping; HAVING filters groups after aggregation."),
            ("Window functions", "Compute across a set of related rows without collapsing them: "
             "fn() OVER (PARTITION BY ... ORDER BY ... ROWS BETWEEN ...)."),
            ("ROW_NUMBER / RANK / DENSE_RANK", "Unique sequence / ties share rank with gaps / ties share rank "
             "without gaps."),
            ("LAG / LEAD", "Access the previous / next row's value within the window - MoM growth, churn gaps."),
            ("CTE", "WITH name AS (...) - readable, reusable named subquery; recursive CTEs walk hierarchies."),
            ("NULL semantics", "Comparisons with NULL are UNKNOWN; use IS NULL, COALESCE; COUNT(col) skips NULLs; "
             "NOT IN with a NULL in the list returns nothing."),
            ("Indexes", "B-tree indexes speed lookups/range scans; composite index column order matters; "
             "covering indexes avoid table lookups; indexes slow writes."),
            ("Grain", "What one row of a table represents - the first thing to establish before joining or "
             "aggregating."),
        ],
        explanation=md("""
            **Think in sets and grain.** Before writing a query, say what one row of each table represents
            (an order? an order line? a customer-day?). Most wrong answers come from joining tables at different
            grains and double-counting.

            **Joins.** A `LEFT JOIN` keeps every row from the left table; filtering the right table in `WHERE`
            (e.g. `WHERE o.status = 'paid'`) silently turns it into an inner join - put that condition in the `ON`
            clause instead if you want to keep unmatched rows.

            **Aggregation.** Every non-aggregated column in `SELECT` must be in `GROUP BY`. Use
            `COUNT(DISTINCT ...)` for unique entities and conditional aggregation
            (`SUM(CASE WHEN ... THEN 1 ELSE 0 END)`) to pivot.

            **Window functions** are the most-tested advanced feature:

            | Need | Pattern |
            |---|---|
            | Top-N per group | `ROW_NUMBER() OVER (PARTITION BY g ORDER BY x DESC)` then filter `rn <= N` |
            | Running total | `SUM(x) OVER (ORDER BY d ROWS UNBOUNDED PRECEDING)` |
            | Period-over-period | `LAG(x) OVER (ORDER BY month)` |
            | Moving average | `AVG(x) OVER (ORDER BY d ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)` |
            | Share of total | `x / SUM(x) OVER ()` |

            **Optimisation.** Read the plan (`EXPLAIN`/`EXPLAIN ANALYZE`): look for full scans on large tables,
            bad join orders and row-count misestimates. Keep predicates *sargable* (no functions wrapped around
            indexed columns), select only needed columns, filter early, pre-aggregate before joining, and in
            warehouses rely on partition pruning / clustering keys.

            **Modelling.** OLTP schemas are normalised (3NF) to avoid update anomalies; analytics warehouses use
            star schemas - a fact table at a declared grain surrounded by denormalised dimensions - for simple,
            fast aggregation.
        """),
        code=md("""
            -- Top 2 earners per department (ties included) and their share of department payroll
            WITH ranked AS (
                SELECT
                    e.department_id,
                    e.name,
                    e.salary,
                    DENSE_RANK() OVER (PARTITION BY e.department_id ORDER BY e.salary DESC) AS rnk,
                    e.salary * 1.0 / SUM(e.salary) OVER (PARTITION BY e.department_id) AS payroll_share
                FROM employees e
            )
            SELECT department_id, name, salary, rnk, ROUND(payroll_share, 3) AS payroll_share
            FROM ranked
            WHERE rnk <= 2
            ORDER BY department_id, rnk;
        """),
        language="sql",
        pitfalls=[
            "Filtering the right-hand table of a LEFT JOIN in WHERE (turns it into an INNER JOIN).",
            "Using NOT IN against a column that can contain NULL - use NOT EXISTS.",
            "Hiding duplicate rows from a bad join with DISTINCT instead of fixing the grain.",
            "Wrapping indexed columns in functions (WHERE YEAR(created_at) = 2025) - use a date range.",
            "Forgetting integer division (SUM(a)/SUM(b) may truncate) - multiply by 1.0 or CAST.",
        ],
        tips=[
            "Restate the question and the grain of each table before writing anything.",
            "Write the query incrementally with CTEs and narrate each step.",
            "Mention how you'd verify the result (row counts, a spot-check, totals reconciliation).",
            "Offer the window-function and the self-join/subquery alternatives when relevant.",
        ],
        cheat_sheet=[
            "COUNT(*) counts rows; COUNT(col) ignores NULLs; COUNT(DISTINCT col) counts unique non-NULL values.",
            "UNION removes duplicates (slower); UNION ALL keeps them.",
            "DELETE is row-by-row and can be filtered/rolled back; TRUNCATE empties the table fast; DROP removes it.",
            "Primary key = unique + not null; a table has one primary key but can have many unique constraints.",
            "COALESCE(a, b, c) returns the first non-NULL value.",
            "RANK: 1,1,3  DENSE_RANK: 1,1,2  ROW_NUMBER: 1,2,3.",
            "A clustered index defines the physical order of rows; there is only one per table.",
        ],
        likely_questions=[
            "Find the second highest salary.",
            "Difference between RANK, DENSE_RANK and ROW_NUMBER?",
            "WHERE vs HAVING?",
            "How do you find duplicate records and delete them?",
            "How would you optimise a slow query?",
            "Explain star vs snowflake schema.",
        ],
    ),
    "theory": [
        T("beginner", "Explain the different types of SQL joins with an example.",
          """
          Take `customers` (id, name) and `orders` (id, customer_id, amount).

          - **INNER JOIN** - only customers who have orders (rows that match on both sides).
          - **LEFT JOIN** - every customer, with order columns NULL for those without orders. Great for "customers
            with no orders": `LEFT JOIN orders o ON ... WHERE o.id IS NULL`.
          - **RIGHT JOIN** - mirror of LEFT (rarely used; rewrite as LEFT for readability).
          - **FULL OUTER JOIN** - all rows from both tables, matched where possible - useful for reconciling two
            sources.
          - **CROSS JOIN** - Cartesian product (every customer with every product) - used to build scaffolds such as
            every store x every date.
          - **SELF JOIN** - a table joined to itself, e.g. employees to their managers.

          The key risk is **fan-out**: joining to a table where the key isn't unique multiplies rows, so I always
          check the grain of each table before joining.
          """,
          ["All join types with semantics", "Concrete use case per join", "Anti-join pattern", "Fan-out / grain awareness"],
          "Draw two small tables and walk through the output rows - visual answers stand out.",
          ["How would you find customers who never ordered?", "What happens if the join key has duplicates?",
           "Difference between JOIN ... ON and USING?"], hot=True),
        T("beginner", "What is the difference between WHERE and HAVING, and in what order does SQL evaluate a query?",
          """
          `WHERE` filters **rows** before grouping; `HAVING` filters **groups** after aggregation, so only `HAVING`
          can reference aggregates like `SUM(amount) > 1000`.

          Logical evaluation order:
          1. `FROM` / `JOIN`
          2. `WHERE`
          3. `GROUP BY`
          4. `HAVING`
          5. `SELECT` (expressions, window functions)
          6. `DISTINCT`
          7. `ORDER BY`
          8. `LIMIT` / `OFFSET`

          This order explains common errors: a `SELECT` alias can't be used in `WHERE` (it doesn't exist yet), but
          can be used in `ORDER BY`. Performance-wise, filter as much as possible in `WHERE` so fewer rows reach
          the aggregation.
          """,
          ["Row vs group filtering", "Aggregates only in HAVING", "Correct logical order", "Why aliases fail in WHERE"],
          "Give a one-line query using both clauses, e.g. regions with > 100 paid orders.",
          ["Can you use HAVING without GROUP BY?", "Where are window functions evaluated?"], hot=True),
        T("intermediate", "Explain ROW_NUMBER, RANK and DENSE_RANK. When would you use each?",
          """
          All three are window functions that number rows within a partition, ordered by some column. They differ
          only on ties. For salaries 100, 100, 90:

          | Function | Result |
          |---|---|
          | `ROW_NUMBER()` | 1, 2, 3 (arbitrary tie order) |
          | `RANK()` | 1, 1, 3 (gap after ties) |
          | `DENSE_RANK()` | 1, 1, 2 (no gaps) |

          - **ROW_NUMBER**: exactly one row per group - de-duplication ("keep the latest record per customer") or
            strict top-N. Add tie-breakers to `ORDER BY` for deterministic results.
          - **RANK**: competition-style ranking where ties consume positions.
          - **DENSE_RANK**: "N-th highest value" questions - the 2nd highest salary is `DENSE_RANK() = 2` even if
            several people share the top salary.
          """,
          ["Tie behaviour of each", "De-duplication with ROW_NUMBER", "N-th highest with DENSE_RANK", "Deterministic ordering"],
          "Use the 100/100/90 example - it makes the difference instantly clear.",
          ["Write a query to keep only the latest row per user.", "How would you do top-3 per category?"], hot=True),
        T("intermediate", "How do NULLs behave in SQL, and what traps do they create?",
          """
          NULL means "unknown", so SQL uses three-valued logic (TRUE / FALSE / UNKNOWN):
          - `NULL = NULL` is UNKNOWN, not TRUE -> use `IS NULL` / `IS NOT NULL` (or `IS DISTINCT FROM`).
          - `WHERE` keeps only TRUE rows, so comparisons against NULL silently drop rows.
          - `COUNT(*)` counts rows, `COUNT(col)` skips NULLs; `AVG`/`SUM` ignore NULLs (AVG of 10, NULL = 10).
          - `NOT IN (subquery)` returns **no rows** if the subquery yields a NULL - prefer `NOT EXISTS`.
          - Arithmetic or string concatenation with NULL yields NULL - wrap with `COALESCE(col, 0)`.
          - `GROUP BY` puts all NULLs in one group; sorting places NULLs first or last depending on the engine.

          In analytics I explicitly decide whether NULL means zero, unknown or not applicable, and document it.
          """,
          ["Three-valued logic", "IS NULL vs = NULL", "Aggregate behaviour", "NOT IN trap", "COALESCE"],
          "Mention the NOT IN trap - it is a favourite follow-up and shows real debugging experience.",
          ["What does AVG return if half the values are NULL?", "How would you count NULLs per column?"]),
        T("advanced", "A query on a large table is slow. How do you diagnose and optimise it?",
          """
          1. **Get the plan**: `EXPLAIN ANALYZE` (or the warehouse query profile). Look for full table scans,
             nested-loop joins over big inputs, spills to disk, and big gaps between estimated and actual rows.
          2. **Reduce data read**: select only needed columns, filter early, make predicates *sargable*
             (`created_at >= '2025-01-01'` instead of `YEAR(created_at) = 2025`), use partition pruning.
          3. **Indexes** (OLTP): composite indexes matching the `WHERE`/`JOIN`/`ORDER BY` columns in the right
             order; covering indexes for hot queries. Warehouses: clustering/sort keys, partitioning, materialised
             views.
          4. **Rewrite**: pre-aggregate before joining, replace correlated subqueries with joins or window
             functions, avoid `SELECT DISTINCT` used to hide fan-out, use `UNION ALL` instead of `UNION` when
             duplicates are impossible.
          5. **Statistics & config**: refresh stats so the optimiser estimates correctly; check for data skew.
          6. **Verify**: compare before/after runtime and results.

          I'd also question the need: can the dashboard use an incremental summary table refreshed hourly?
          """,
          ["Starts from the execution plan", "Sargability & pruning", "Index design", "Query rewrites", "Measures impact"],
          "Structure as diagnose -> fix -> verify and quote a real before/after number if you have one.",
          ["What is a covering index?", "Why can an index make writes slower?", "What is partition pruning?"], hot=True),
        T("advanced", "Normalisation vs denormalisation - and how do star and snowflake schemas fit in?",
          """
          **Normalisation** (1NF -> 3NF) splits data so each fact is stored once: no repeating groups (1NF), no
          partial dependency on part of a composite key (2NF), no transitive dependencies (3NF). It prevents
          update anomalies and suits **OLTP** systems with many small writes.

          **Denormalisation** deliberately duplicates data to make reads simpler and faster - the right trade-off
          for **analytics**, where data is written in batches and read by large aggregations.

          - **Star schema**: a central fact table at a declared grain (e.g. one row per order line) with foreign
            keys to denormalised dimensions (date, product, customer, store). Few joins, intuitive for BI tools.
          - **Snowflake schema**: dimensions are further normalised (product -> category -> department). Saves
            storage, but adds joins and complexity.

          Related ideas: slowly changing dimensions (SCD Type 2 keeps history with valid_from/valid_to), surrogate
          keys, and conformed dimensions shared across facts.
          """,
          ["1NF-3NF in one line each", "OLTP vs OLAP trade-off", "Star vs snowflake", "Grain & SCD awareness"],
          "Anchor it with a schema you built - name the fact table and its grain.",
          ["What is SCD Type 2?", "What is a factless fact table?", "How do you choose the grain of a fact table?"]),
    ],
    "practical": [
        P("beginner", "Find the second highest salary overall and the second highest salary in each department.",
          """
          `employees(id, name, department_id, salary)`. If several people share the highest salary, the "second
          highest" is the next distinct value. Return NULL if it doesn't exist.
          """,
          ["Clarify: distinct values and behaviour with ties.", "Overall: MAX below the MAX, or DENSE_RANK.",
           "Per department: DENSE_RANK partitioned by department.", "Discuss NULL/empty handling."],
          "The subquery version is portable and returns NULL automatically when no second value exists. "
          "DENSE_RANK generalises to the N-th highest and to per-group answers.",
          """
          -- Overall (returns NULL if there is no second distinct salary)
          SELECT MAX(salary) AS second_highest
          FROM employees
          WHERE salary < (SELECT MAX(salary) FROM employees);

          -- Per department, N-th highest using DENSE_RANK
          WITH ranked AS (
              SELECT department_id, name, salary,
                     DENSE_RANK() OVER (PARTITION BY department_id ORDER BY salary DESC) AS rnk
              FROM employees
          )
          SELECT department_id, name, salary
          FROM ranked
          WHERE rnk = 2;
          """, "sql",
          "One scan plus a sort per partition (O(n log n)); an index on (department_id, salary) helps.",
          ["All employees share one salary", "Department with a single employee", "NULL salaries"],
          "Ask about ties first - interviewers often wait to see whether you clarify.",
          ["Generalise to the N-th highest salary.", "Return the employee names too, including ties."], hot=True),
        P("intermediate", "Compute month-over-month revenue growth (%) from an orders table.",
          """
          `orders(order_id, order_date, amount, status)`. Only `status = 'completed'` counts as revenue.
          Output: month, revenue, previous month revenue, growth %.
          """,
          ["Aggregate completed orders to month grain.", "Use LAG to fetch the previous month.",
           "Guard against division by zero.", "Consider months with no orders."],
          "First collapse to one row per month in a CTE, then apply LAG over the month order. NULLIF prevents "
          "division by zero and the first month naturally gets NULL growth.",
          """
          WITH monthly AS (
              SELECT DATE_TRUNC('month', order_date) AS month,
                     SUM(amount) AS revenue
              FROM orders
              WHERE status = 'completed'
              GROUP BY 1
          )
          SELECT month,
                 revenue,
                 LAG(revenue) OVER (ORDER BY month) AS prev_revenue,
                 ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
                       / NULLIF(LAG(revenue) OVER (ORDER BY month), 0), 2) AS mom_growth_pct
          FROM monthly
          ORDER BY month;
          """, "sql",
          "Single aggregation pass plus a sort on a small monthly table.",
          ["Missing months (join to a calendar table to show 0)", "Refunds/negative amounts", "Time-zone boundaries"],
          "Mention the calendar-table fix for gaps - it shows you think about real dashboards.",
          ["How would you compute a 3-month moving average?", "Year-over-year growth for the same month?"], hot=True),
        P("advanced", "Find users who logged in on at least 3 consecutive days.",
          """
          `logins(user_id, login_ts)` - a user may log in many times per day.
          Return distinct user_ids with a streak of 3+ consecutive calendar days.
          """,
          ["De-duplicate to one row per user per day.",
           "Gaps-and-islands: date minus ROW_NUMBER is constant within a streak.",
           "Group by user and that constant; count days.", "Filter streaks of length >= 3."],
          "Within a run of consecutive dates, subtracting an increasing row number yields the same 'island key'. "
          "Grouping by (user, island key) gives each streak and its length.",
          """
          WITH days AS (
              SELECT DISTINCT user_id, CAST(login_ts AS DATE) AS login_day
              FROM logins
          ),
          islands AS (
              SELECT user_id, login_day,
                     login_day - CAST(ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY login_day) AS INT) AS grp
              FROM days
          )
          SELECT DISTINCT user_id
          FROM islands
          GROUP BY user_id, grp
          HAVING COUNT(*) >= 3;
          -- Date arithmetic varies by engine: in PostgreSQL date - integer works; elsewhere use DATEADD/DATE_SUB.
          """, "sql",
          "O(n log n) for the window sort per user.",
          ["Multiple logins on the same day", "Time zones changing the calendar day", "Streaks spanning month boundaries"],
          "Name the pattern ('gaps and islands') - it signals you have seen advanced SQL problems before.",
          ["Return the longest streak per user.", "How would you solve it with LAG instead?"], hot=True),
    ],
    "scenario": [
        S("beginner", """
          The revenue number on your new Power BI dashboard is 8% higher than the figure the finance team reports
          for the same month. A director has asked which one is right before tomorrow's leadership meeting.
          """,
          "How do you investigate and resolve the mismatch?",
          [("Align definitions", "Confirm what finance counts: gross vs net, refunds, taxes, booking vs payment date."),
           ("Reconcile top-down", "Compare totals by day/region/channel to localise the gap."),
           ("Check the SQL", "Look for join fan-out, duplicate rows, time-zone cut-offs, status filters."),
           ("Fix & document", "Correct the logic, write the metric definition down, add a reconciliation test."),
           ("Communicate", "Tell the director which number is right, why, and what changed.")],
          """
          My first assumption would be a **definition** difference, not a bug. I'd ask finance exactly how they
          compute revenue - net of refunds and discounts? excluding tax? recognised on order date or payment date?
          in which time zone?

          Then I'd reconcile top-down: compare both numbers by day and by channel to find where the 8% comes from.
          If the gap sits in a few days, it's usually a cut-off or time-zone issue; if it's spread evenly, it's
          usually a definition or a join that duplicates rows (e.g. joining orders to a payments table with
          multiple payment attempts per order).

          Once found, I'd fix the query, add a reconciliation check against finance's ledger, and document the
          metric definition in the dashboard. To the director I'd send a short note: which number is right, the
          root cause, and the corrected figure - before the meeting, not after.
          """,
          ["Starts with metric definitions", "Systematic top-down reconciliation", "Knows common SQL causes",
           "Clear, timely stakeholder communication"],
          ["Assuming finance is wrong", "Patching the number without finding the root cause",
           "Not documenting the agreed definition"],
          ["How would you prevent metric drift across teams?", "What is a semantic layer?"]),
        S("intermediate", """
          A daily sales report query that used to finish in 30 seconds now takes 20 minutes. Nobody changed the
          SQL, but the orders table grew from 50 million to 400 million rows over the year.
          """,
          "How do you bring it back under a minute?",
          [("Confirm", "Check whether the plan changed and which step dominates (EXPLAIN ANALYZE / query profile)."),
           ("Prune", "Filter on the partition/cluster key; make date predicates sargable."),
           ("Index / cluster", "Add or fix indexes or clustering keys that match the filters and joins."),
           ("Pre-aggregate", "Build an incremental daily summary table instead of scanning raw rows."),
           ("Monitor", "Add query-time alerts and review plans as data grows.")],
          """
          Since the SQL didn't change, I'd suspect the plan: with 8x more data the optimiser may have switched to a
          full scan or a worse join strategy, or statistics are stale. I'd run `EXPLAIN ANALYZE` (or the Snowflake
          query profile) and find the dominant step.

          Typical fixes, in order of effort:
          1. Make the date filter prunable - e.g. replace `WHERE TO_CHAR(order_date, 'YYYY-MM') = ...` with a
             range on the partition column so only recent partitions are scanned.
          2. Refresh statistics, and add the right composite index or clustering key on (order_date, store_id).
          3. Since the report only needs daily aggregates, build an **incremental summary table** updated by the
             nightly pipeline; the report then reads a few thousand rows instead of 400 million.

          I'd validate that results are identical, then add an alert on query duration so we catch the next
          regression early.
          """,
          ["Hypothesis-driven (plan change, stats)", "Uses the execution plan", "Prefers structural fixes like "
           "pre-aggregation", "Validates and monitors"],
          ["Throwing more compute at it first", "Adding random indexes without reading the plan",
           "Changing results while optimising"],
          ["What is partition pruning?", "How would you build the summary table incrementally?"], hot=True),
        S("advanced", """
          An e-commerce client wants a warehouse that answers: daily revenue by category and region, conversion
          funnel (visit -> add to cart -> purchase), and customer lifetime value. Product categories and customer
          addresses change over time.
          """,
          "Design the data model.",
          [("Clarify", "Key questions, data sources, freshness needs and history requirements."),
           ("Choose grains", "Order-line fact, event fact and a daily customer snapshot - one grain per fact."),
           ("Dimensions", "Date, product, customer, region, channel; SCD Type 2 where history matters."),
           ("Physical design", "Partition facts by date, cluster on common filters, add summary tables."),
           ("Quality", "Tests on keys, freshness and reconciliation to source totals.")],
          """
          I'd build a **star schema** with three facts, each with an explicit grain:
          - `fact_order_line` - one row per product per order: quantity, price, discount, net revenue, plus keys to
            date, product, customer, region, channel.
          - `fact_web_event` - one row per tracked event (visit, add_to_cart, checkout, purchase) with session and
            customer keys - this powers the funnel with conditional counts per session.
          - `fact_customer_daily` (snapshot) - for LTV and retention without rescanning history.

          Dimensions are denormalised for BI: `dim_product` with category hierarchy flattened, `dim_customer` with
          address/region as **SCD Type 2** (valid_from/valid_to/is_current) so revenue is attributed to the region
          at the time of purchase, and a `dim_date` calendar.

          Physically: partition facts by date, cluster on (category, region), and pre-aggregate a daily revenue
          mart for dashboards. dbt tests on uniqueness, not-null keys, accepted values and a daily reconciliation
          against the order system keep it trustworthy.
          """,
          ["Declares grain for every fact", "Handles history with SCD2", "Connects model to the business questions",
           "Considers performance and data quality"],
          ["One giant flat table for everything", "Mixing grains in one fact table", "Ignoring history requirements"],
          ["SCD Type 1 vs Type 2?", "How would you model returns?", "How do you handle late-arriving events?"]),
    ],
    "quiz": [
        Q("beginner", "Which clause filters rows AFTER aggregation?",
          ["WHERE", "HAVING", "ORDER BY", "LIMIT"], 1,
          "HAVING is evaluated after GROUP BY, so it can filter on aggregate values such as SUM(amount).",
          ["WHERE runs before grouping and cannot use aggregates.", "Correct.", "ORDER BY only sorts.",
           "LIMIT only restricts the number of rows returned."],
          "Pair the answer with the full logical evaluation order.", hot=True),
        Q("beginner", "A column has values 5, NULL, 7. What do COUNT(*) and COUNT(col) return?",
          ["3 and 3", "3 and 2", "2 and 2", "2 and 3"], 1,
          "COUNT(*) counts all rows; COUNT(col) counts non-NULL values only.",
          ["COUNT(col) skips the NULL.", "Correct.", "COUNT(*) includes the NULL row.", "Reversed."],
          "Mention COUNT(DISTINCT col) too - it also ignores NULLs."),
        Q("intermediate", "For salaries 100, 100, 90 ordered descending, what does DENSE_RANK() return?",
          ["1, 2, 3", "1, 1, 3", "1, 1, 2", "1, 2, 2"], 2,
          "DENSE_RANK gives ties the same rank and does not leave gaps.",
          ["That is ROW_NUMBER.", "That is RANK (gap after the tie).", "Correct.", "Not produced by any of the three."],
          "This is the basis of 'N-th highest salary' questions.", hot=True),
        Q("intermediate", "`customers c LEFT JOIN orders o ON c.id = o.customer_id WHERE o.status = 'paid'` behaves like:",
          ["A LEFT JOIN keeping all customers", "An INNER JOIN on paid orders", "A FULL OUTER JOIN", "A CROSS JOIN"], 1,
          "Unmatched customers get NULL o.status, and the WHERE condition removes them - so only customers with paid "
          "orders remain.",
          ["Customers without paid orders are filtered out by WHERE.", "Correct - move the filter into ON to keep them.",
           "Nothing makes this a full join.", "There is a join condition."],
          "Explain the fix: put o.status = 'paid' in the ON clause."),
        Q("advanced", "`SELECT * FROM a WHERE id NOT IN (SELECT id FROM b)` returns no rows even though some a.id are "
          "missing from b. Most likely cause?",
          ["b.id contains a NULL", "a has no primary key", "The subquery is not indexed", "NOT IN is deprecated"], 0,
          "x NOT IN (..., NULL) evaluates to UNKNOWN for every x, so WHERE filters everything out. Use NOT EXISTS or "
          "filter NULLs in the subquery.",
          ["Correct.", "Keys don't affect NOT IN semantics.", "Indexing affects speed, not results.",
           "NOT IN is valid SQL."],
          "A classic debugging question - mention NOT EXISTS as the robust alternative.", hot=True),
    ],
}
