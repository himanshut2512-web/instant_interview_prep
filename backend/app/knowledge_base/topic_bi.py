from ._build import P, Q, S, T, md, note

TOPIC = {
    "key": "bi",
    "name": "BI & Data Visualisation",
    "keywords": ["power bi", "powerbi", "dax", "tableau", "looker", "excel", "dashboard", "dashboards",
                 "visualization", "visualisation", "reporting", "bi", "business intelligence", "kpi", "kpis",
                 "storytelling", "insights", "analyst", "mis"],
    "core": ["power bi", "tableau", "dashboard", "dashboards", "data visualization", "data visualisation"],
    "subtopics": ["Chart selection", "Dashboard design", "Power BI data model & DAX", "Filter context & CALCULATE",
                  "Tableau LOD expressions", "Performance & RLS", "Data storytelling"],
    "revision": note(
        summary="BI rounds check that you can turn data into decisions: pick the right visual, model data for "
        "reporting, write correct DAX/LOD calculations, keep reports fast and secure, and tell a clear story to "
        "business users.",
        concepts=[
            ("Chart choice", "Trend -> line; comparison -> bar; part-to-whole -> stacked bar (pie only for 2-3 parts); "
             "distribution -> histogram/box; relationship -> scatter."),
            ("Star schema in BI", "Facts (sales) related to dimensions (date, product, customer) with one-to-many "
             "single-direction relationships - fast and predictable."),
            ("Calculated column vs measure", "Column: computed row by row at refresh and stored; measure: computed at "
             "query time in the current filter context."),
            ("Row vs filter context", "Row context = the current row in an iteration; filter context = filters from "
             "slicers, visuals and CALCULATE."),
            ("CALCULATE", "Evaluates an expression in a modified filter context - the most important DAX function."),
            ("Time intelligence", "TOTALYTD, SAMEPERIODLASTYEAR, DATEADD - require a marked date table."),
            ("Import vs DirectQuery", "Cached in-memory model (fast) vs live queries to the source (fresh, slower)."),
            ("Row-level security", "Roles with DAX filters so each user sees only permitted rows."),
            ("Tableau LOD", "FIXED / INCLUDE / EXCLUDE control the level of detail of a calculation independent of "
             "the view."),
            ("Storytelling", "Context -> insight -> implication -> recommended action."),
        ],
        explanation=md("""
            **Start from decisions, not charts.** Ask who uses the dashboard, which decisions they make and how
            often. Then design a KPI hierarchy: 3-5 headline KPIs at the top (with targets and trends), drivers in
            the middle, detail tables and drill-through at the bottom.

            **Design rules.** One question per visual; consistent colours (one accent for what matters); sort bars;
            start bar axes at zero; label directly instead of legends where possible; avoid 3D and dual axes that
            mislead; show comparisons (vs target, vs last year).

            **Power BI modelling.** Use a star schema, a dedicated date table, single-direction relationships,
            measures instead of calculated columns where possible, and remove unused columns (high-cardinality
            columns bloat the model).

            **DAX essentials.**

            | Pattern | DAX |
            |---|---|
            | Total | `Total Sales = SUM(Sales[Amount])` |
            | Filtered total | `CALCULATE([Total Sales], Product[Category] = "Bikes")` |
            | Last year | `CALCULATE([Total Sales], SAMEPERIODLASTYEAR('Date'[Date]))` |
            | Share of total | `DIVIDE([Total Sales], CALCULATE([Total Sales], ALL(Product)))` |
            | Rank | `RANKX(ALL(Product[Name]), [Total Sales])` |

            **Performance.** Use Performance Analyzer, reduce visuals per page, prefer Import mode with incremental
            refresh, aggregate tables for big facts, avoid bi-directional relationships and complex iterators over
            large tables, and push transformations upstream (SQL/Power Query folding).

            **Tableau.** Dimensions vs measures, discrete vs continuous, extracts vs live connections, and LOD
            expressions such as `{FIXED [Customer ID] : MIN([Order Date])}` for cohort analysis.
        """),
        code=md("""
            Total Sales = SUM ( Sales[Amount] )

            Sales LY = CALCULATE ( [Total Sales], SAMEPERIODLASTYEAR ( 'Date'[Date] ) )

            YoY % = DIVIDE ( [Total Sales] - [Sales LY], [Sales LY] )

            Category Share % =
            DIVIDE ( [Total Sales], CALCULATE ( [Total Sales], ALL ( Product[Category] ) ) )
        """),
        language="dax",
        pitfalls=[
            "Using calculated columns for aggregations that should be measures.",
            "Bi-directional relationships everywhere (ambiguity and slow models).",
            "Time-intelligence functions without a proper, marked date table.",
            "Dashboards with 20 visuals and no clear headline.",
            "Pie charts with many slices, truncated bar axes, misleading dual axes.",
        ],
        tips=[
            "Talk about the business decision your dashboard supported and its adoption/impact.",
            "When writing DAX, explain the filter context step by step.",
            "Mention data validation: reconciling dashboard totals with the source system.",
            "Show empathy for users: training, documentation, feedback loops.",
        ],
        cheat_sheet=[
            "DIVIDE() handles division by zero safely.",
            "ALL removes filters; ALLEXCEPT keeps selected ones; REMOVEFILTERS is the explicit modern form.",
            "SUMX iterates rows (row context) then sums - needed for row-level calculations like qty * price.",
            "Incremental refresh keeps large Import models fresh without full reloads.",
            "Tableau order of operations: extract -> data source -> context -> FIXED -> dimension filters -> INCLUDE/EXCLUDE.",
            "XLOOKUP/INDEX-MATCH beat VLOOKUP (no column-index fragility, can look left).",
        ],
        likely_questions=[
            "Calculated column vs measure?",
            "What does CALCULATE do?",
            "How would you speed up a slow Power BI report?",
            "How do you choose a chart type?",
            "What is row-level security?",
            "Explain Tableau LOD expressions.",
        ],
    ),
    "theory": [
        T("beginner", "How do you choose the right chart for a piece of data?",
          """
          I start from the **question** the viewer needs answered:
          - **Trend over time** -> line chart (column chart for few periods).
          - **Comparison across categories** -> sorted bar chart.
          - **Part-to-whole** -> stacked bar or 100% bar; a pie/donut only for 2-3 parts.
          - **Distribution** -> histogram or box plot.
          - **Relationship between two measures** -> scatter plot (bubble for a third).
          - **Geography** -> filled/symbol map, only when location matters.
          - **Single KPI** -> big number card with comparison to target/last period.

          Then I simplify: remove chart junk, label directly, use one highlight colour for the key insight, start
          bar axes at zero, and add context such as targets or previous-year lines.
          """,
          ["Question-first approach", "Correct mapping of chart types", "Design simplicity", "Context/comparisons"],
          "Give a quick example of redesigning a cluttered chart you inherited.",
          ["When is a pie chart acceptable?", "How would you show actual vs target?"], hot=True),
        T("beginner", "In Power BI, what is the difference between a calculated column and a measure?",
          """
          - A **calculated column** is computed **row by row** when the data refreshes and stored in the model. It
            has row context, can be used in slicers/axes/relationships, but increases model size.
            Example: `Profit Band = IF(Sales[Profit] > 1000, "High", "Low")`.
          - A **measure** is computed **at query time**, in the current **filter context** (slicers, visual
            axes, filters), and isn't stored. Example: `Total Sales = SUM(Sales[Amount])` returns different values
            for each region on a chart.

          Rule of thumb: use measures for aggregations and KPIs; use calculated columns only when you need to
          slice/filter by the value or need it at row level - and ideally create those upstream in Power Query or
          SQL.
          """,
          ["Row-level vs query-time", "Storage impact", "When to use each", "Example of each"],
          "Mention that most performance problems come from overusing calculated columns.",
          ["What is row context vs filter context?", "Why push columns upstream to Power Query?"], hot=True),
        T("intermediate", "Explain filter context and what CALCULATE does in DAX.",
          """
          **Filter context** is the set of filters applied when a measure is evaluated - from slicers, page filters,
          and the row/column headers of the visual. `Total Sales` shows a different number in each cell of a matrix
          because each cell has its own filter context (e.g. Region = West, Year = 2025).

          **CALCULATE(expression, filters...)** evaluates the expression in a **modified** filter context:
          - add or overwrite filters: `CALCULATE([Total Sales], Product[Category] = "Bikes")`;
          - remove filters: `CALCULATE([Total Sales], ALL(Product))` for a grand total used in share-of-total;
          - change time windows with time-intelligence functions: `SAMEPERIODLASTYEAR('Date'[Date])`.

          CALCULATE also performs **context transition**: inside a row context (e.g. in a calculated column or an
          iterator like SUMX), it turns the current row into an equivalent filter context.
          """,
          ["Definition of filter context", "CALCULATE modifies filters", "ALL for totals", "Context transition"],
          "Walk through one matrix cell and say which filters apply - very clear for interviewers.",
          ["What is context transition?", "ALL vs ALLEXCEPT vs ALLSELECTED?"], hot=True),
        T("intermediate", "Import vs DirectQuery vs Live connection in Power BI - how do you choose?",
          """
          - **Import**: data is loaded into Power BI's in-memory engine (VertiPaq). Fastest queries and full DAX,
            but data is only as fresh as the last refresh and model size is limited by capacity. Default choice;
            use incremental refresh for large facts.
          - **DirectQuery**: every visual sends queries to the source (SQL Server, Snowflake, Databricks). Near
            real-time data and no size limit, but slower visuals, some DAX limitations, and load on the source.
          - **Live connection**: connect to an existing published semantic model/Analysis Services - reuse a
            governed model, no local modelling.
          - **Composite models** mix modes, e.g. Import aggregations over a DirectQuery detail table.

          I choose based on freshness needs, data volume, performance expectations and governance.
          """,
          ["Characteristics of each mode", "Trade-offs", "Composite/aggregations", "Decision criteria"],
          "Tie the answer to a real requirement, e.g. hourly freshness on a 2-billion-row table.",
          ["How do aggregation tables work?", "What is query folding?"]),
        T("advanced", "How would you design an executive KPI dashboard that people actually use?",
          """
          1. **Discover**: interview executives - what decisions, which KPIs, how often, on which device.
          2. **Define metrics**: precise, agreed definitions (owner, formula, grain, source) - a metric dictionary.
          3. **Information hierarchy**: top row of 3-5 KPI cards with target and trend; second layer explains
             drivers (by region/product/channel); drill-through to detail pages for analysts.
          4. **Design**: consistent layout and colour semantics (red = below target), comparisons (vs target, LY),
             annotations for anomalies, mobile layout if needed.
          5. **Trust**: certified dataset, reconciliation with finance, data-freshness indicator.
          6. **Performance**: < 3-5 s page loads - Import mode, aggregations, limited visuals per page.
          7. **Adoption**: walkthrough sessions, usage metrics, quarterly review to retire unused visuals.
          """,
          ["Starts with decisions", "Metric definitions & trust", "Layered layout", "Performance & adoption"],
          "Quote adoption or time-saved metrics from a dashboard you shipped.",
          ["How do you handle conflicting KPI definitions?", "How do you measure dashboard adoption?"]),
        T("advanced", "A Power BI report is slow and different users must see different data. How do you fix "
          "performance and implement security?",
          """
          **Performance**
          - Use **Performance Analyzer** to find slow visuals and copy their DAX queries into DAX Studio.
          - **Model**: star schema, remove unused/high-cardinality columns, integer keys, disable auto date/time,
            avoid bi-directional relationships.
          - **DAX**: replace heavy iterators over large tables, use variables (VAR), avoid FILTER on whole tables
            inside CALCULATE when a simple column filter works.
          - **Data volume**: Import with incremental refresh; aggregation tables over DirectQuery detail.
          - **Report**: fewer visuals per page, avoid high-cardinality tables on landing pages.

          **Row-level security (RLS)**
          - Define roles with DAX filters, e.g. on a `UserRegion` mapping table: `[Email] = USERPRINCIPALNAME()`,
            related to the Region dimension so filters flow to facts (dynamic RLS).
          - Test with "View as role", assign users/groups in the service, and remember RLS doesn't apply to
            workspace admins/members with edit rights.
          """,
          ["Diagnosis with Performance Analyzer/DAX Studio", "Model and DAX optimisations", "Volume strategies",
           "Dynamic RLS with USERPRINCIPALNAME"],
          "Separate the two parts clearly - interviewers often ask them together to test structure.",
          ["Static vs dynamic RLS?", "What is object-level security?"], hot=True),
    ],
    "practical": [
        P("beginner", "Write DAX measures for total sales, sales last year and year-over-year growth %.",
          """
          Model: `Sales[Amount]`, `Sales[OrderDate]` related to a marked date table `'Date'[Date]`.
          """,
          ["Base measure with SUM.", "Last year via CALCULATE + SAMEPERIODLASTYEAR.",
           "Growth with DIVIDE to avoid division by zero.", "Format as percentage."],
          "Building measures on top of a base measure keeps logic consistent and reusable. Time intelligence needs "
          "a continuous, marked date table related to the fact table.",
          """
          Total Sales = SUM ( Sales[Amount] )

          Sales LY =
          CALCULATE ( [Total Sales], SAMEPERIODLASTYEAR ( 'Date'[Date] ) )

          YoY Growth % =
          VAR Curr = [Total Sales]
          VAR Prev = [Sales LY]
          RETURN DIVIDE ( Curr - Prev, Prev )
          """, "dax",
          "Evaluated per visual cell at query time.",
          ["Missing dates in the date table", "First year with no LY data (BLANK)", "Fiscal vs calendar years"],
          "Explain why a marked date table is required for time intelligence.",
          ["How would you compute YTD?", "How would you handle a fiscal year starting in April?"], hot=True),
        P("intermediate", "Write DAX for each product's share of its category total and a Top-5 product ranking.",
          """
          Tables: `Sales[Amount]`, `Product[Name]`, `Product[Category]`. The visual is a table by product name.
          """,
          ["Base measure Total Sales.", "Category total: CALCULATE removing the product-name filter but keeping category.",
           "Share = DIVIDE(product, category total).", "Rank with RANKX over ALL product names."],
          "ALLEXCEPT keeps the category filter while removing others on the Product table, so each product is "
          "divided by its own category's total. RANKX over ALL(Product[Name]) ranks across all products.",
          """
          Total Sales = SUM ( Sales[Amount] )

          Category Sales =
          CALCULATE ( [Total Sales], ALLEXCEPT ( Product, Product[Category] ) )

          Share of Category % = DIVIDE ( [Total Sales], [Category Sales] )

          Product Rank =
          RANKX ( ALL ( Product[Name] ), [Total Sales], , DESC, DENSE )

          Top 5 Sales =
          IF ( [Product Rank] <= 5, [Total Sales] )
          """, "dax",
          "RANKX iterates all products per evaluated cell - fine for thousands of products.",
          ["Ties in sales (DENSE ranking)", "Products with blank sales", "Slicers on category changing totals"],
          "Talk through the filter context of one row of the table.",
          ["ALLEXCEPT vs REMOVEFILTERS + VALUES?", "How do you show 'Others' for products outside the top 5?"],
          hot=True),
        P("advanced", "In Tableau, build a monthly customer cohort retention analysis with LOD expressions.",
          """
          Orders data: `Customer ID`, `Order Date`, `Sales`. Show, for each first-purchase month (cohort), the % of
          customers who purchased again in month 1, 2, 3... after their first order.
          """,
          ["FIXED LOD for each customer's first order month (cohort).",
           "Months since first purchase for every order.", "Distinct customers per cohort and month offset.",
           "Divide by cohort size (another FIXED LOD) for retention %."],
          "FIXED LODs compute per-customer values regardless of the view, which is exactly what a cohort definition "
          "needs. A table calculation or second LOD gives the cohort size denominator.",
          """
          // Cohort Month
          { FIXED [Customer ID] : MIN( DATETRUNC('month', [Order Date]) ) }

          // Months Since First Purchase
          DATEDIFF('month', [Cohort Month], DATETRUNC('month', [Order Date]))

          // Cohort Size
          { FIXED [Cohort Month] : COUNTD([Customer ID]) }

          // Retention %   (view: Rows = Cohort Month, Columns = Months Since First Purchase)
          COUNTD([Customer ID]) / MIN([Cohort Size])
          """, "tableau",
          "LODs run as subqueries in the data source; extracts keep them fast.",
          ["Customers with a single order", "Partial current month", "Dimension filters vs FIXED order of operations"],
          "Mention that dimension filters don't affect FIXED LODs unless promoted to context filters.",
          ["FIXED vs INCLUDE vs EXCLUDE?", "How would you build the same in SQL?"]),
    ],
    "scenario": [
        S("beginner", """
          A sales director asks you for a dashboard "with everything" and sends a list of 25 charts they'd like on a
          single page by Friday.
          """,
          "How do you handle the request?",
          [("Understand decisions", "Ask what decisions they make weekly and what questions they need answered."),
           ("Prioritise", "Agree on 3-5 headline KPIs and the drivers behind them."),
           ("Prototype", "Sketch a layered layout: KPIs, drivers, drill-through details."),
           ("Iterate", "Review a draft early; move secondary charts to detail pages."),
           ("Deliver & measure", "Launch, train users, track usage and refine.")],
          """
          I'd book 30 minutes with the director to understand the **decisions** behind the request: "When you open
          this on Monday, what do you need to know and what will you do differently?" Usually the 25 charts collapse
          into a handful of questions: are we on target, where are we behind, and why.

          I'd propose a layered design: a top row with 4-5 KPI cards (revenue vs target, pipeline, win rate,
          average deal size) with trends; a middle section of drivers by region and product; and drill-through pages
          for detail. Everything else from the list stays available on secondary pages.

          I'd share a wireframe by Wednesday to get early feedback, deliver on Friday, and then check usage after a
          few weeks to retire visuals no one uses. This respects the request while delivering something usable.
          """,
          ["Asks about decisions, not charts", "Negotiates scope diplomatically", "Prototypes early",
           "Measures adoption"],
          ["Building all 25 charts on one page", "Refusing the request", "Skipping the early review"],
          ["How would you prioritise if two stakeholders disagree?", "What would your wireframe show?"]),
        S("intermediate", """
          The main Power BI sales report now takes 40 seconds to load. Users have started exporting data to Excel
          instead. The model has a 300-million-row fact table in Import mode.
          """,
          "How do you make it fast again?",
          [("Measure", "Performance Analyzer: which visuals/queries are slow; DAX Studio for timings."),
           ("Model", "Remove unused/high-cardinality columns, star schema, integer keys, disable auto date/time."),
           ("DAX", "Optimise heavy measures (variables, avoid FILTER on big tables, avoid nested iterators)."),
           ("Volume", "Aggregation tables, incremental refresh, summarised landing page."),
           ("Report design", "Fewer visuals per page, drill-through for detail, test and communicate.")],
          """
          I'd first measure with **Performance Analyzer** to see which visuals are slow and whether time is spent in
          the DAX query or in rendering, then analyse the slow queries in DAX Studio.

          Typical culprits at this scale: (1) high-cardinality columns like transaction IDs or timestamps bloating
          the model - remove or split them (date and time separately); (2) a measure using `FILTER(Sales, ...)`
          inside CALCULATE over 300M rows - rewrite it as a column filter; (3) a landing page with 25 visuals and a
          giant table visual.

          Then structural fixes: an **aggregation table** at day x store x product-category grain that serves 90%
          of queries, with the detail table only for drill-through; incremental refresh for the fact table. I'd
          redesign the landing page to a few KPI visuals. Target: under 5 seconds, measured and shared with users -
          and I'd ask the Excel exporters what they were doing so the report covers that need.
          """,
          ["Uses Performance Analyzer/DAX Studio", "Knows cardinality and DAX anti-patterns", "Aggregations & "
           "incremental refresh", "Addresses user behaviour"],
          ["Upgrading capacity first", "Switching to DirectQuery (often slower)", "Ignoring why users export to Excel"],
          ["How do aggregation tables work?", "Why is cardinality so important in VertiPaq?"], hot=True),
        S("advanced", """
          The North and South regional teams present different "active customer" numbers for the same month in a
          leadership meeting. Each built its own report on its own extract.
          """,
          "How do you fix this for good?",
          [("Find the gap", "Compare definitions, filters, sources and refresh times of both reports."),
           ("Agree a definition", "Facilitate a single business definition with an owner."),
           ("Single source of truth", "One certified semantic model/dataset with the governed measure."),
           ("Migrate & retire", "Move regional reports onto it; retire private extracts."),
           ("Govern", "Metric catalogue, certification process, change control.")],
          """
          The immediate job is to explain the difference: I'd compare both calculations. Typically one region counts
          customers with any transaction in the month, the other with a purchase above a threshold, or they use
          different extract dates and status filters.

          The lasting fix is organisational as much as technical. I'd bring finance/sales operations and both
          regional leads together to agree **one definition** of "active customer" with a named owner, documented in
          a metric catalogue. Then implement it once in a **certified semantic model** (shared Power BI dataset or a
          dbt metrics/semantic layer) that both regional reports connect to via live connection. Private extracts are
          retired, and changes to certified measures go through a lightweight review.

          I'd present the reconciliation to leadership with the corrected number - that transparency builds trust in
          the new single source of truth.
          """,
          ["Diagnoses definition differences", "Drives agreement with stakeholders", "Certified semantic model",
           "Governance process"],
          ["Picking one region's number arbitrarily", "Purely technical fix without agreement",
           "Leaving duplicate extracts in place"],
          ["What is a semantic layer?", "How do you handle a definition change historically?"]),
    ],
    "quiz": [
        Q("beginner", "Which chart is usually best to show a KPI's trend over 24 months?",
          ["Pie chart", "Line chart", "Scatter plot", "Treemap"], 1,
          "Line charts show continuous change over time clearly.",
          ["Part-to-whole only.", "Correct.", "For relationships between two measures.", "For hierarchical parts."],
          "Add a target or last-year line for context.", hot=True),
        Q("beginner", "In Power BI, which is evaluated at query time and responds to slicers and visual filters?",
          ["Calculated column", "Measure", "Calculated table", "Power Query step"], 1,
          "Measures are computed on the fly in the current filter context.",
          ["Computed at refresh and stored.", "Correct.", "Computed at refresh.", "Runs at refresh time."],
          "Default to measures for aggregations."),
        Q("intermediate", "What is CALCULATE's main role in DAX?",
          ["Formatting numbers", "Modifying the filter context in which an expression is evaluated",
           "Creating relationships", "Loading data"], 1,
          "CALCULATE adds, removes or changes filters before evaluating its expression.",
          ["No.", "Correct.", "Relationships are defined in the model.", "Power Query loads data."],
          "Mention context transition as the advanced detail.", hot=True),
        Q("intermediate", "A Tableau FIXED LOD expression computes values:",
          ["Only at the level of detail of the current view", "At the specified dimensions regardless of the view's "
           "dimensions", "Only for the top 10 rows", "After all table calculations"], 1,
          "FIXED computes at the declared dimensions; regular dimension filters don't affect it (context filters do).",
          ["That's a regular aggregate.", "Correct.", "No.", "LODs are computed before table calcs."],
          "Mention the order-of-operations nuance with context filters."),
        Q("advanced", "What is the standard way to ensure each regional manager sees only their region in a shared "
          "Power BI report?",
          ["Create a separate report per region", "Row-level security roles with DAX filters (e.g. USERPRINCIPALNAME)",
           "Hide the region column", "Use bookmarks"], 1,
          "RLS filters data per user at query time; dynamic RLS maps user identity to permitted regions.",
          ["Doesn't scale and duplicates logic.", "Correct.", "Hiding is not security.", "Bookmarks aren't security."],
          "Mention testing with 'View as role'.", hot=True),
    ],
}
