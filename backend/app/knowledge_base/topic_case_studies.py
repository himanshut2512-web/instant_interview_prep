from ._build import P, Q, S, T, md, note

TOPIC = {
    "key": "case_studies",
    "name": "Case Studies & Guesstimates",
    "keywords": ["consulting", "consultant", "client", "clients", "business", "analytics", "analyst", "strategy",
                 "product", "metrics", "kpi", "insights", "problem solving", "stakeholder", "guesstimate",
                 "case study", "market", "revenue", "growth"],
    "core": ["consulting", "case study", "guesstimate", "business problems", "business problem"],
    "subtopics": ["Guesstimates & market sizing", "Metric investigation (root cause)", "Profitability & growth cases",
                  "Product & success metrics", "Analytics problem framing", "Structured communication"],
    "revision": note(
        summary="Analytics and consulting firms use guesstimates and business cases to test structured thinking, "
        "comfort with numbers, business sense and clear communication - the same skills you use with clients.",
        concepts=[
            ("Clarify first", "Restate the problem, confirm scope, timeframe, geography and the decision it informs."),
            ("MECE structure", "Break problems into Mutually Exclusive, Collectively Exhaustive parts (issue trees)."),
            ("Top-down vs bottom-up sizing", "Start from population and filter down, or from unit economics and scale "
             "up; use both to sanity-check."),
            ("Segmentation", "Split by customer type, age, income, region or usage intensity to make assumptions "
             "realistic."),
            ("Sanity check", "Compare the answer with a known benchmark or a second method."),
            ("Profit tree", "Profit = Revenue (price x volume) - Costs (fixed + variable)."),
            ("Metric drop framework", "Check data -> scope it (when, where, who) -> internal vs external causes -> "
             "segment -> hypothesis -> validate."),
            ("North-star metric", "The one metric that best captures customer value delivered (e.g. weekly orders "
             "per active user)."),
            ("Leading vs lagging indicators", "Engagement predicts churn (leading); revenue reports what happened "
             "(lagging)."),
            ("Pyramid principle", "Lead with the answer, then the supporting arguments, then data."),
        ],
        explanation=md("""
            **Guesstimate method.**
            1. Clarify: what exactly are we estimating, where, over what period?
            2. Choose an approach (population-based top-down, or supply-side bottom-up) and say why.
            3. Segment into 2-4 groups with different behaviour.
            4. State round, defensible assumptions aloud; write the tree on paper.
            5. Calculate step by step; keep numbers simple (powers of ten).
            6. Sanity-check with another method or benchmark; state the range and key sensitivities.

            **"Metric X dropped 20%" framework.**

            | Step | Questions |
            |---|---|
            | Data | Is it real? Tracking/pipeline changes, definition changes, partial data? |
            | Scope | Sudden or gradual? Which dates, regions, platforms, segments? |
            | Internal | Releases, pricing changes, marketing spend, outages, inventory? |
            | External | Seasonality, holidays, competitors, macro events, regulations? |
            | Decompose | Metric = components (traffic x conversion x AOV) - which moved? |
            | Validate & act | Test the top hypotheses with data; recommend fixes and monitoring. |

            **Business cases.** Use a profit tree for profitability, the 4Ps/3Cs for market entry, the funnel for
            growth, and always end with a clear recommendation, risks and next steps. For analytics cases, describe
            data you'd need, analysis/models, how you'd measure impact (A/B test), and implementation.
        """),
        code=md("""
            Revenue dropped 20%
            ├── Data issue? (tracking, pipeline, definition change)
            ├── Traffic (sessions)
            │   ├── Channel: organic / paid / referral / app
            │   └── Platform: web / Android / iOS
            ├── Conversion rate
            │   ├── Funnel step: product view -> cart -> checkout -> payment
            │   └── Payment failures / stock-outs / price changes
            └── Average order value
                ├── Mix shift (cheaper categories)
                └── Discounts / promotions ended
        """),
        language="text",
        pitfalls=[
            "Starting calculations before clarifying the question.",
            "Unstructured lists of reasons instead of a MECE tree.",
            "Over-precise numbers that slow you down (use round numbers).",
            "No sanity check or final recommendation.",
            "Ignoring data-quality explanations for sudden metric changes.",
        ],
        tips=[
            "Think aloud and write the structure down where the interviewer can see it.",
            "Lead with the answer at the end: 'about 150 million, driven mainly by replacements'.",
            "Tie the case back to how you'd use data/ML to help the client.",
            "Be coachable - if the interviewer nudges an assumption, adapt gracefully.",
        ],
        cheat_sheet=[
            "India population about 1.4 billion; about 300 million households.",
            "Days per year 365; working days about 250; weeks 52.",
            "Funnel: visits x conversion x average order value = revenue.",
            "LTV about ARPU x gross margin / churn rate (per period).",
            "CAC payback = CAC / (monthly ARPU x margin).",
            "Always give a range and the main driver of uncertainty.",
        ],
        likely_questions=[
            "Estimate the number of smartphones sold in India per year.",
            "Sales dropped 15% last month - how do you investigate?",
            "How would you increase revenue for a client's e-commerce site?",
            "Which metrics would you track for a new feature?",
            "How would you use data to reduce customer churn?",
        ],
    ),
    "theory": [
        T("beginner", "How do you approach a guesstimate question in an interview?",
          """
          1. **Clarify** the exact quantity, geography and time period ("new smartphones sold in India per year,
             including all price bands?").
          2. **Pick an approach**: demand-side (population -> users -> purchase frequency) or supply-side
             (stores x sales per store); say why.
          3. **Segment** the population where behaviour differs (urban/rural, age groups, income bands).
          4. **Make round, defensible assumptions** aloud and write the tree.
          5. **Calculate** step by step with simple numbers.
          6. **Sanity-check** with a second approach or a known benchmark, and give a range plus the most sensitive
             assumption.

          The interviewer cares far more about structure, logic and communication than the final number.
          """,
          ["Clarification", "Approach choice", "Segmentation", "Stated assumptions", "Sanity check & range"],
          "Write the tree visibly and narrate - silence during guesstimates is the most common mistake.",
          ["How would you sanity-check your answer?", "Which assumption is your answer most sensitive to?"], hot=True),
        T("beginner", "What makes a good KPI? Explain north-star metrics and leading vs lagging indicators.",
          """
          A good KPI is **aligned with a business goal**, **actionable** (teams can move it), **measurable and
          reliable**, **understandable**, and **hard to game**, with a clear definition and owner.

          - **North-star metric**: the single metric that best captures the value customers get and predicts
            long-term success - e.g. weekly active buyers for a marketplace, minutes listened for a music app. It's
            supported by input metrics teams can influence.
          - **Lagging indicators** report outcomes after the fact (revenue, churn, profit).
          - **Leading indicators** move earlier and predict outcomes (declining logins predict churn; add-to-cart
            rate predicts revenue).
          - Pair goal metrics with **guardrail/counter metrics** (e.g. if you push notifications to raise
            engagement, watch opt-out and uninstall rates).
          """,
          ["Properties of a good KPI", "North-star with example", "Leading vs lagging", "Guardrails"],
          "Give a north-star example from the company's own business if you can.",
          ["What north-star metric would you choose for our business?", "How can a KPI be gamed?"]),
        T("intermediate", "A key metric (e.g. daily orders) dropped 20% week over week. How do you investigate?",
          """
          1. **Verify the data**: tracking or pipeline changes, metric-definition changes, delayed data, bot filters.
             Many "drops" are data issues.
          2. **Scope it**: sudden or gradual? Which dates, regions, platforms (Android/iOS/web), channels, customer
             segments, product categories?
          3. **Decompose the metric**: orders = sessions x conversion rate; then split conversion by funnel step.
          4. **Internal causes**: app releases, pricing/discount changes, marketing spend cuts, outages, payment
             gateway errors, stock-outs, logistics capacity.
          5. **External causes**: seasonality, holidays, weather, competitor campaigns, news, regulations.
          6. **Form and test hypotheses** with data (e.g. the drop is only on Android after the latest release ->
             crash rates confirm it).
          7. **Recommend**: fix/rollback, quantify impact, and add monitoring/alerts to catch it earlier.
          """,
          ["Data validity first", "Scoping/segmenting", "Metric decomposition", "Internal vs external causes",
           "Hypothesis testing & action"],
          "Use the framework but quickly propose your top 2 hypotheses - shows business intuition.",
          ["What if the drop is spread evenly across all segments?", "How would you set up an alert for this?"],
          hot=True),
        T("intermediate", "How would you structure a profitability case (e.g. a client's profits fell 15%)?",
          """
          Use the **profit tree**: Profit = Revenue - Costs.

          - **Revenue** = price x volume, split by product line, channel, region and customer segment.
            - Price: discounting, mix shift to cheaper products, competitive pricing.
            - Volume: market shrinking vs share loss; new competitors; customer churn vs fewer new customers.
          - **Costs** = fixed + variable.
            - Variable: raw materials, logistics, commissions per unit - did unit costs rise?
            - Fixed: rent, salaries, technology - did they grow faster than revenue?

          Approach: compare against the previous period and competitors to see whether it's industry-wide or
          company-specific, find the branch that explains most of the 15%, dig into root causes, then recommend
          actions with estimated impact (e.g. renegotiate logistics contracts, reprice low-margin SKUs, reduce churn
          among high-value customers) and how to track them.
          """,
          ["Profit tree decomposition", "Price/volume/mix", "Fixed vs variable costs", "Industry vs company-specific",
           "Actionable recommendations"],
          "Ask for data at each branch rather than speculating - interviewers usually have numbers to give you.",
          ["What data would you request first?", "How would analytics/ML help here?"]),
        T("advanced", "How do you frame and deliver an analytics solution for a client's business problem?",
          """
          1. **Understand the business problem and decision**: who decides what, how often, and what success looks
             like in business terms (e.g. reduce stock-outs by 10% without increasing inventory).
          2. **Build a hypothesis tree** of drivers and agree on priorities with stakeholders.
          3. **Data assessment**: sources, granularity, history, quality issues, access; quick EDA to validate
             hypotheses.
          4. **Approach**: start simple (rules/baseline), then models where they add value (forecasting,
             classification, optimisation); define evaluation metrics that map to business value.
          5. **Pilot**: deploy to a subset (stores/regions) with a control group to measure real impact.
          6. **Scale & embed**: integrate into workflows/tools, train users, set up monitoring and ownership.
          7. **Communicate** throughout: weekly demos, insight storytelling, quantified results.

          Consulting interviewers look for business framing before technique, stakeholder management, and
          measurable impact.
          """,
          ["Decision-focused framing", "Hypothesis tree", "Data assessment", "Baseline -> model", "Pilot with control",
           "Adoption & communication"],
          "Illustrate with a past project mapped to these steps.",
          ["How would you handle a client with poor data quality?", "How do you prove ROI?"], hot=True),
        T("advanced", "How would you define success metrics for launching a new feature (e.g. 'Buy Now, Pay Later' "
          "at checkout)?",
          """
          1. **Goal**: increase completed purchases and order value by giving customers payment flexibility.
          2. **Primary metric**: checkout conversion rate (orders / checkout starts) among eligible users.
          3. **Secondary metrics**: average order value, adoption rate of the feature, repeat purchase rate.
          4. **Guardrails**: default/credit-loss rate, refund/return rate, payment latency, customer-support
             contacts, cannibalisation of other payment methods (with fee differences).
          5. **Segments**: new vs returning users, basket-size bands, categories.
          6. **Measurement**: A/B test at user level with pre-registered duration and MDE; monitor long-term effects
             (repayment behaviour) after launch.
          7. **Decision rule**: ship if conversion lift is significant and guardrails stay within agreed limits.
          """,
          ["Goal-first", "Primary vs secondary vs guardrail metrics", "Segments", "Experiment & decision rule"],
          "Structure as goal -> primary -> secondary -> guardrails -> measurement.",
          ["What could make the primary metric misleading?", "How would you measure long-term impact?"]),
    ],
    "practical": [
        P("beginner", "Guesstimate: how many new smartphones are sold in India each year?",
          """
          Work it out aloud with a clear structure, state assumptions and sanity-check the result.
          """,
          ["Clarify: new units, all price bands, India, one year.",
           "Users: population -> eligible age -> smartphone penetration.",
           "Replacement cycle -> replacement purchases; adjust for second-hand phones.",
           "Add first-time buyers; sanity-check vs benchmark."],
          "A demand-side approach based on the user base and replacement cycle is the most defensible. The answer "
          "of roughly 150-160 million is in line with publicly reported annual shipment figures (around 150 million "
          "in recent years), which makes a good sanity check.",
          """
          Population                              1,400 M
          x share aged 10+                        ~83%      -> ~1,160 M
          x smartphone penetration                ~60%      -> ~700 M users
          Replacement purchases: 700 M / 4-year cycle       -> ~175 M phones
          - share bought second-hand/refurbished  ~15%      -> ~150 M new units
          + first-time buyers buying new          ~10 M     -> ~160 M
          Answer: roughly 150-160 million new smartphones per year
          Most sensitive assumption: replacement cycle (3 years -> ~210 M; 5 years -> ~130 M)
          """, "text",
          "",
          ["Feature phones vs smartphones", "Multiple phones per person", "Grey-market imports"],
          "State the sensitivity of the key assumption - it shows analytical maturity.",
          ["How would a supply-side estimate look?", "How would you estimate the premium (> INR 30k) segment?"],
          hot=True),
        P("intermediate", "Guesstimate: how many food-delivery orders are placed in Bengaluru per day?",
          """
          Use a demand-side approach with segmentation by order frequency.
          """,
          ["Clarify: all platforms, restaurant food only, a typical weekday.",
           "Population -> relevant age group -> users of food-delivery apps.",
           "Segment users by order frequency.", "Compute weekly orders -> daily; sanity-check."],
          "Segmenting heavy, medium and light users makes the frequency assumption realistic. The result, about "
          "0.6-0.8 million orders a day, is plausible for one of India's largest food-delivery markets.",
          """
          Population                                    ~13 M
          x age 18-50 (students + working)              ~55%  -> ~7 M
          x actively use food-delivery apps             ~50%  -> ~3.5 M users
          Frequency segments (orders per week):
            heavy 20% x 3.0  = 0.60
            medium 40% x 1.0 = 0.40
            light 40% x 0.5  = 0.20
            weighted average = 1.2 orders/user/week
          Weekly orders: 3.5 M x 1.2 = 4.2 M -> daily ~0.6 M
          Weekend/peak adjustment +20% on busy days      -> ~0.7 M
          Answer: roughly 0.6-0.8 million orders per day
          """, "text",
          "",
          ["Group orders (one order feeding several people)", "Corporate/office orders", "Weekday vs weekend demand"],
          "Explain why you segmented by frequency instead of using one average.",
          ["How would you estimate the number of delivery partners needed?", "Supply-side check via restaurants?"],
          hot=True),
        P("advanced", "Market sizing: estimate the annual revenue opportunity for public EV charging in a metro city "
          "of about 10 million people.",
          """
          Build TAM from vehicle segments and charging behaviour, then discuss what share a new operator could
          capture.
          """,
          ["Segment vehicles: private 2-wheelers, private cars, commercial fleets (cabs/autos).",
           "EV adoption and annual energy use per segment.", "Share of charging done at public chargers.",
           "Energy x price per kWh = revenue; identify the biggest driver."],
          "Fleets dominate public charging revenue even though they are few vehicles, because they drive long "
          "distances and rely on public fast charging. That insight shapes the go-to-market (fleet partnerships, "
          "hubs near depots).",
          """
          Vehicles: ~4 M (2W ~3 M, cars ~1 M) + commercial fleet ~10 k EVs (cabs/autos)
          EVs: 2W 6% -> 180 k; cars 2% -> 20 k; fleet EVs 10 k
          Annual energy per vehicle:
            2W   7,000 km x 0.03 kWh/km  =   210 kWh   (public share 10%)
            car 12,000 km x 0.15 kWh/km  = 1,800 kWh   (public share 30%)
            fleet 60,000 km x 0.15       = 9,000 kWh   (public share 70%)
          Public energy:
            2W    180 k x 210 x 10%      =  3.8 GWh
            cars   20 k x 1,800 x 30%    = 10.8 GWh
            fleet  10 k x 9,000 x 70%    = 63.0 GWh
            total                        ~ 78 GWh / year
          x price ~INR 18/kWh            -> ~INR 140 Cr / year (TAM today)
          SAM (fast-charging hubs in 3 target zones, ~40%) -> ~INR 56 Cr
          SOM (new entrant, ~15% of SAM in 3 years)       -> ~INR 8-9 Cr / year
          Insight: ~80% of revenue comes from fleets -> partner with fleet operators first
          """, "text",
          "",
          ["Home charging cannibalisation", "Rapid EV adoption growth (model a 3-5 year view)",
           "Electricity cost and utilisation drive profitability, not just revenue"],
          "Close with the business implication, not just the number.",
          ["How would profitability differ from revenue?", "Which data would you collect to refine this?"]),
    ],
    "scenario": [
        S("beginner", """
          A retail client tells you: "Sales in our South region fell 15% last month while other regions were flat.
          Find out why."
          """,
          "How do you structure your investigation?",
          [("Validate data", "Confirm the drop isn't a reporting or store-mapping issue."),
           ("Locate", "Which stores, categories, weeks, channels drive the drop?"),
           ("Decompose", "Sales = footfall x conversion x basket size - which component moved?"),
           ("Hypothesise", "Store closures, stock-outs, competitor openings, local events, price changes."),
           ("Recommend", "Targeted fixes plus monitoring; quantify recovery potential.")],
          """
          I'd first confirm the data: were stores re-mapped between regions, did any stores stop reporting, did a
          new POS system go live? Then I'd locate the drop - is it all South stores or a few, all categories or a
          few, gradual across the month or after a specific date?

          Next I'd decompose sales into **footfall x conversion x average basket**. If footfall fell, likely causes
          are external (competitor opening nearby, monsoon flooding, local festival timing) or store closures. If
          conversion fell, I'd look at stock-outs (perhaps a regional warehouse issue), staffing, or pricing. If
          basket size fell, I'd check promotions ending or a mix shift.

          Suppose the data shows the drop concentrated in 12 stores served by one warehouse whose stock-outs tripled -
          the recommendation would be fixing replenishment from that warehouse, with an estimate of recovered sales,
          plus a stock-out alert for the future.
          """,
          ["Checks data first", "Localises the problem", "Decomposes the metric", "Prioritised hypotheses",
           "Concrete, quantified recommendation"],
          ["Listing random reasons without structure", "Ignoring data issues", "No recommendation"],
          ["What data would you request from the client?", "How would you present this to the regional head?"]),
        S("intermediate", """
          An e-commerce client wants to cut average delivery time from 4 days to 2 days in major cities without
          significantly increasing costs.
          """,
          "How would you use data and analytics to approach this?",
          [("Map the journey", "Order -> fulfilment centre -> sort -> line haul -> last mile; time per stage."),
           ("Find bottlenecks", "Stage-wise distributions by city, SKU and carrier; where is time lost?"),
           ("Forecast demand", "SKU x city demand forecasts to pre-position inventory closer to customers."),
           ("Optimise", "Inventory placement, carrier allocation, cut-off times, route optimisation."),
           ("Pilot & measure", "Pilot in 2 cities with control cities; track delivery time and cost per order.")],
          """
          I'd start by decomposing the 4 days into stages - order processing, picking/packing, line-haul transfer,
          last-mile delivery - using timestamp data, and look at distributions by city, SKU and carrier. Often most
          of the time is lost because items are shipped from a distant warehouse, or orders miss a dispatch cut-off.

          The biggest lever is usually **inventory placement**: forecast demand per SKU per city and stock the fast
          movers in local fulfilment centres so they skip line-haul. A demand-forecasting model plus an optimisation
          model (which SKUs, how much, where, given storage costs) balances speed and cost. Other levers: later
          cut-off times, carrier allocation by performance, and route optimisation for the last mile.

          I'd pilot in two cities against comparable control cities, tracking delivery time, on-time %, cost per
          order and conversion uplift (faster delivery promises often increase conversion, which helps pay for it).
          """,
          ["Process decomposition with data", "Identifies inventory placement as key lever",
           "Combines forecasting with optimisation", "Pilot with control and cost tracking"],
          ["Suggesting 'hire more delivery staff' only", "No cost consideration", "No measurement plan"],
          ["Which SKUs would you place locally first?", "How would you measure the conversion impact?"], hot=True),
        S("advanced", """
          A bank's credit-card division wants to increase card spend by 10% in a year. They have transaction data,
          customer demographics and campaign history for 3 million cardholders.
          """,
          "Propose an analytics-driven plan and how you'd measure success.",
          [("Diagnose spend", "Segment customers by spend, engagement, wallet share and lifecycle stage."),
           ("Find levers", "Activation of dormant cards, category expansion, merchant offers, credit-limit increases."),
           ("Model", "Propensity/uplift models for each lever; next-best-offer engine."),
           ("Experiment", "Randomised campaigns with holdouts to measure incremental spend."),
           ("Scale & govern", "Roll out winners, monitor risk (defaults), ROI per campaign.")],
          """
          First I'd **diagnose** where spend growth can come from: segment cardholders into dormant, low-engaged,
          regular and high spenders, and estimate "share of wallet" from transaction patterns. Typically the biggest
          pools are dormant/inactive cards and customers using the card in only one or two categories.

          Then match **levers** to segments: activation offers for dormant cards, category-expansion offers (e.g.
          groceries, fuel) for single-category users, merchant partnerships, EMI conversion for big purchases, and
          credit-limit increases for creditworthy customers who are limit-constrained.

          For targeting, I'd build **uplift models** (not just propensity) to find customers whose spend increases
          *because of* an offer, and a next-best-offer engine across levers with offer-cost constraints. Every
          campaign runs with a **randomised holdout** to measure incremental spend and ROI; risk guardrails track
          delinquency for credit-limit actions.

          Success = +10% total spend measured as incremental to holdouts, at positive ROI, with defaults within
          appetite. I'd report monthly by segment and lever and reallocate budget to the best performers.
          """,
          ["Segment-driven diagnosis", "Maps levers to segments", "Uplift modelling & next-best-offer",
           "Holdout-based measurement", "Risk guardrails & ROI"],
          ["One generic campaign for everyone", "Measuring success without holdouts", "Ignoring credit risk"],
          ["Propensity vs uplift modelling?", "How would you size each lever's contribution?"], hot=True),
    ],
    "quiz": [
        Q("beginner", "What should you do first when given a guesstimate question?",
          ["Start multiplying numbers immediately", "Clarify scope and define what exactly is being estimated",
           "Give a final number", "Ask for the exact answer"], 1,
          "Clarifying scope, geography and timeframe prevents solving the wrong problem.",
          ["Skips structure.", "Correct.", "No structure.", "Misses the point of the exercise."],
          "Write the clarified question down before starting.", hot=True),
        Q("beginner", "Which is a LEADING indicator of customer churn for a subscription app?",
          ["Last quarter's revenue", "Declining weekly active usage", "Annual profit", "Number of churned customers"], 1,
          "Usage drops typically precede cancellation, so they predict churn.",
          ["Lagging.", "Correct.", "Lagging.", "That's the outcome itself."],
          "Leading indicators enable proactive retention."),
        Q("intermediate", "A dashboard shows daily orders fell 30% overnight. What should you check first?",
          ["Competitor pricing", "Whether it's a data/tracking or pipeline issue", "Macroeconomic trends",
           "Customer satisfaction surveys"], 1,
          "Sudden, large drops are often caused by tracking changes, broken pipelines or definition changes.",
          ["Later, if the data is valid.", "Correct.", "Unlikely to cause overnight drops.", "Too slow and indirect."],
          "Mention checking release notes and data-pipeline alerts.", hot=True),
        Q("intermediate", "In a profitability case, revenue can be decomposed as:",
          ["Fixed costs + variable costs", "Price x volume (by product/segment/channel)", "Profit / margin",
           "Market size x growth"], 1,
          "Revenue = price x quantity sold, analysed across products, segments and channels.",
          ["That's costs.", "Correct.", "Circular.", "A market-sizing view."],
          "Use the profit tree: profit = revenue - costs."),
        Q("advanced", "A feature sends more push notifications to boost engagement. Which is the most important "
          "counter-metric to monitor?",
          ["Daily active users", "Notification opt-out and app uninstall rates", "Number of notifications sent",
           "Server CPU usage"], 1,
          "More notifications can raise short-term engagement while annoying users into opting out or uninstalling.",
          ["That's the goal metric.", "Correct.", "An input, not an outcome.", "Operational, not user impact."],
          "Always pair a goal metric with guardrails.", hot=True),
    ],
}
