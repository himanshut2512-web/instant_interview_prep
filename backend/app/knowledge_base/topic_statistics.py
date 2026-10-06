from ._build import P, Q, S, T, md, note

TOPIC = {
    "key": "statistics",
    "name": "Statistics & A/B Testing",
    "keywords": ["statistics", "statistical", "probability", "hypothesis testing", "a/b test", "a/b testing",
                 "ab testing", "experimentation", "experiment", "inference", "causal", "regression analysis",
                 "econometrics", "analytics"],
    "core": ["statistics", "statistical", "a/b test", "a/b testing", "hypothesis testing", "experimentation"],
    "subtopics": ["Descriptive statistics", "Distributions & CLT", "Hypothesis testing & p-values",
                  "Confidence intervals", "A/B test design", "Bayes' theorem", "Correlation vs causation"],
    "revision": note(
        summary="Statistics questions check whether you can reason under uncertainty: distributions, the CLT, "
        "hypothesis tests, confidence intervals, experiment design and avoiding classic traps (peeking, "
        "confounding, base-rate neglect).",
        concepts=[
            ("Mean / median / mode", "Median is robust to outliers; in right-skewed data (income, order value) the "
             "mean sits above the median."),
            ("Variance & standard deviation", "Average squared deviation from the mean / its square root, in the "
             "original units."),
            ("Central Limit Theorem", "The sampling distribution of the mean approaches normal as n grows (roughly "
             "n >= 30), whatever the population's shape - the basis of most tests and intervals."),
            ("p-value", "Probability of data at least this extreme if the null hypothesis were true. Not the "
             "probability that the null is true."),
            ("Type I / Type II error", "False positive (rate = alpha) / false negative (rate = beta); power = 1 - beta."),
            ("Confidence interval", "A procedure that captures the true parameter in 95% of repeated samples; "
             "mean +/- 1.96 * SE for large n."),
            ("t-test / z-test / chi-square / ANOVA", "Compare means (small/unknown variance) / proportions or known "
             "variance / categorical association / 3+ group means."),
            ("Power & MDE", "Sample size needed depends on baseline, minimum detectable effect, alpha and power."),
            ("Bayes' theorem", "P(A|B) = P(B|A)P(A)/P(B) - updates beliefs with evidence; watch base rates."),
            ("Confounding", "A third variable driving both 'cause' and 'effect'; randomisation removes it."),
        ],
        explanation=md("""
            **Distributions to know.** Normal (heights, measurement error), Binomial (successes in n trials -
            conversions), Poisson (counts per interval - tickets per hour), Exponential (time between events),
            Uniform. Know their mean/variance: Binomial mean np, variance np(1-p); Poisson mean = variance = lambda.

            **Hypothesis testing workflow.**
            1. State H0 (no effect) and H1, choose alpha (0.05) *before* looking at data.
            2. Pick the test that matches the data: two-proportion z-test for conversion rates, Welch's t-test for
               means, chi-square for categorical tables, Mann-Whitney for skewed data, ANOVA for 3+ groups.
            3. Compute the statistic and p-value; reject H0 if p < alpha.
            4. Report the **effect size with a confidence interval**, not just "significant".

            **A/B testing essentials.** Randomise at the right unit (user, not page view), fix the sample size from
            a power calculation, run full weekly cycles, check sample-ratio mismatch (SRM), watch guardrail metrics,
            and don't peek-and-stop (it inflates false positives) unless you use sequential methods. Distinguish
            statistical from practical significance.

            **Causality.** Correlation can come from confounders, reverse causation or selection bias. Randomised
            experiments are the gold standard; otherwise use difference-in-differences, matching/propensity scores,
            regression discontinuity or instrumental variables - and state their assumptions.

            | Situation | Test |
            |---|---|
            | Conversion A vs B | two-proportion z-test / chi-square |
            | Average order value A vs B | Welch's t-test (or bootstrap if skewed) |
            | Same users before/after | paired t-test |
            | Is churn independent of plan type? | chi-square test of independence |
            | Revenue across 4 regions | one-way ANOVA (then post-hoc tests) |
        """),
        code=md("""
            import numpy as np
            from scipy import stats

            control = np.array([0] * 9_000 + [1] * 1_000)    # 10.0% conversion
            variant = np.array([0] * 8_880 + [1] * 1_120)    # 11.2% conversion

            # two-proportion z-test
            p1, p2 = control.mean(), variant.mean()
            p_pool = (control.sum() + variant.sum()) / (len(control) + len(variant))
            se = np.sqrt(p_pool * (1 - p_pool) * (1 / len(control) + 1 / len(variant)))
            z = (p2 - p1) / se
            p_value = 2 * (1 - stats.norm.cdf(abs(z)))

            # 95% CI for the difference (unpooled SE)
            se_diff = np.sqrt(p1 * (1 - p1) / len(control) + p2 * (1 - p2) / len(variant))
            ci = (p2 - p1 - 1.96 * se_diff, p2 - p1 + 1.96 * se_diff)
            print(f"lift={p2 - p1:.4f} z={z:.2f} p={p_value:.4f} CI={ci}")
        """),
        language="python",
        pitfalls=[
            "Saying the p-value is 'the probability the null hypothesis is true'.",
            "Peeking at an A/B test daily and stopping at the first significant result.",
            "Ignoring sample-ratio mismatch, novelty effects or seasonality.",
            "Using the mean on heavily skewed data without checking the median or using a robust test.",
            "Treating correlation in observational data as causation.",
        ],
        tips=[
            "Define terms precisely, then give a business example (conversion, churn, order value).",
            "Always pair 'significant' with effect size and a confidence interval.",
            "For experiment questions, structure the answer: hypothesis -> metric -> unit -> sample size -> "
            "duration -> analysis -> decision.",
            "Do quick mental maths aloud - interviewers value the reasoning more than decimals.",
        ],
        cheat_sheet=[
            "z for 95% two-sided = 1.96; for 80% power z_beta = 0.84.",
            "SE of a mean = s / sqrt(n); SE of a proportion = sqrt(p(1-p)/n).",
            "Halving the MDE roughly quadruples the required sample size.",
            "Right skew: mean > median; left skew: mean < median.",
            "~68/95/99.7% of a normal distribution lies within 1/2/3 standard deviations.",
            "Power = 1 - beta = P(detect an effect | it exists).",
            "Multiple comparisons inflate false positives - correct with Bonferroni or control FDR.",
        ],
        likely_questions=[
            "What is a p-value?",
            "Explain Type I and Type II errors.",
            "What is the Central Limit Theorem?",
            "How would you design an A/B test?",
            "How do you calculate sample size?",
            "Correlation vs causation?",
        ],
    ),
    "theory": [
        T("beginner", "What is a p-value, and what does it NOT mean?",
          """
          The p-value is the probability of observing data **at least as extreme** as what we saw, **assuming the
          null hypothesis is true**. A small p-value (below the pre-chosen alpha, often 0.05) means the data would
          be surprising if there were no effect, so we reject the null.

          What it is **not**:
          - not the probability that the null hypothesis is true;
          - not the probability the result happened "by chance";
          - not a measure of effect size - a tiny, useless effect can have p < 0.001 with a huge sample.

          Example: an A/B test shows variant conversion 11.2% vs 10.0% with p = 0.006. If the variant truly had no
          effect, we'd see a gap this large only about 0.6% of the time. I would still report the lift with a
          confidence interval (e.g. +1.2pp, 95% CI +0.3 to +2.1pp) and judge whether it is worth shipping.
          """,
          ["Conditional on H0 being true", "'At least as extreme'", "Common misinterpretations", "Effect size + CI"],
          "Give the definition in one sentence, then the misconceptions - this order shows depth.",
          ["Why is 0.05 the usual threshold?", "What happens to p-values with very large samples?"], hot=True),
        T("beginner", "Explain Type I and Type II errors and statistical power with a business example.",
          """
          - **Type I error (false positive, rate alpha)**: rejecting a true null - e.g. concluding a new checkout
            page increases conversion when it doesn't. We'd ship a useless change.
          - **Type II error (false negative, rate beta)**: failing to reject a false null - missing a real
            improvement. We'd throw away a good idea.
          - **Power = 1 - beta**: the probability of detecting an effect that really exists (typically target 80%).

          Trade-off: lowering alpha (stricter) increases beta unless you increase the sample size. Power rises with
          sample size, effect size and lower variance.

          Which error is worse depends on context: in fraud detection a false negative (missed fraud) may be costly;
          in medical screening, a false positive triggers expensive follow-ups. I choose alpha and power based on
          those costs.
          """,
          ["Correct definitions", "Concrete example of each", "Power and its drivers", "Context-dependent costs"],
          "Use a confusion-matrix framing - it connects stats to ML metrics, which interviewers like.",
          ["How do you increase power without more users?", "How do alpha and precision/recall relate?"], hot=True),
        T("intermediate", "What is the Central Limit Theorem and why does it matter in practice?",
          """
          The CLT says that the distribution of the **sample mean** of independent observations approaches a
          normal distribution as the sample size grows - regardless of the population's shape - with mean mu and
          standard error sigma / sqrt(n).

          Why it matters:
          - It justifies z/t-tests and confidence intervals for means and proportions even when the raw data
            (order values, session times) is skewed.
          - It tells us precision improves with sqrt(n): 4x the data halves the standard error.
          - It underpins A/B-test sample-size formulas.

          Caveats: it needs independent observations and finite variance; with heavy tails or small samples the
          approximation is poor - then use bootstrapping or non-parametric tests. A rule of thumb of n >= 30 is
          often quoted, but very skewed data needs more.
          """,
          ["Statement about the sampling distribution", "Standard error sigma/sqrt(n)", "Practical uses",
           "Assumptions and caveats"],
          "Clarify it is about the distribution of means, not of the data itself - a common confusion.",
          ["What is the difference between standard deviation and standard error?", "What is bootstrapping?"],
          hot=True),
        T("intermediate", "Correlation vs causation - how would you establish that X causes Y?",
          """
          Correlation means two variables move together; causation means changing X changes Y. Correlation can
          arise from:
          - **confounders** (ice-cream sales and drownings both rise with temperature),
          - **reverse causation** (support tickets correlate with churn, but unhappy users file tickets),
          - **selection bias** (power users adopt a feature *and* retain better).

          To establish causation:
          1. **Randomised experiment** (A/B test) - the gold standard; randomisation balances confounders.
          2. If you can't randomise, quasi-experimental methods: difference-in-differences, propensity-score
             matching, regression discontinuity, instrumental variables, synthetic control - each with stated
             assumptions.
          3. Support with mechanism, dose-response and consistency across segments.
          """,
          ["Three sources of spurious correlation", "Randomisation as gold standard", "Quasi-experimental options",
           "States assumptions"],
          "Use an example from your own domain (e.g. a feature-usage vs retention claim).",
          ["Explain difference-in-differences.", "What is Simpson's paradox?"]),
        T("advanced", "Walk me through designing and analysing an A/B test end to end.",
          """
          1. **Hypothesis & decision**: "Showing delivery dates on product pages increases purchase conversion."
             Define what result leads to shipping.
          2. **Metrics**: one primary metric (conversion per user), secondary metrics, and **guardrails** (refund
             rate, page latency).
          3. **Randomisation unit**: usually user ID (consistent experience), hashed into buckets; avoid
             spill-over between groups.
          4. **Sample size**: from baseline rate, minimum detectable effect, alpha = 0.05, power = 0.8. E.g. 10%
             baseline, +1pp MDE -> about 14.8k users per arm.
          5. **Duration**: at least one or two full weekly cycles; don't stop early on a significant peek (or use a
             sequential method).
          6. **Health checks**: sample-ratio mismatch (chi-square on allocation), A/A tests, logging sanity.
          7. **Analysis**: two-proportion z-test / Welch t-test or CUPED for variance reduction; report lift with
             CI; check key segments without p-hacking (correct for multiple comparisons).
          8. **Decision & learnings**: consider practical significance, novelty effects, long-term impact.
          """,
          ["Clear hypothesis and metrics incl. guardrails", "Correct unit & sample size", "Duration & peeking",
           "SRM and validity checks", "Analysis with effect size and decision"],
          "Speak in numbered steps - it signals you have run real experiments. Mention CUPED or SRM to stand out.",
          ["What is CUPED?", "How do you handle network effects in experiments?", "What if the test is inconclusive?"],
          hot=True),
        T("advanced", "Explain Bayes' theorem with a diagnostic-test example. Why do people get it wrong?",
          """
          Bayes' theorem: P(A|B) = P(B|A) * P(A) / P(B).

          A disease affects 1% of people. The test has 99% sensitivity (P(+|D) = 0.99) and a 5% false-positive rate
          (P(+|not D) = 0.05). If you test positive, what is P(D|+)?

          - P(+) = 0.99 * 0.01 + 0.05 * 0.99 = 0.0099 + 0.0495 = 0.0594
          - P(D|+) = 0.0099 / 0.0594 = **about 17%**

          People expect ~99% because they ignore the **base rate**: with a rare condition, most positives are
          false positives from the large healthy population.

          Business parallels: fraud alerts, anomaly detection and lead scoring - when the positive class is rare,
          even a good classifier has low precision, so we tune thresholds and use a second-stage review.
          """,
          ["Correct formula", "Correct worked calculation", "Base-rate fallacy explanation", "Link to ML precision"],
          "Use a 10,000-people frequency table if you prefer - it is easier to follow aloud.",
          ["Bayesian vs frequentist A/B testing?", "How does this relate to precision and recall?"]),
    ],
    "practical": [
        P("beginner", "Compute the mean, median, standard deviation and a 95% confidence interval for the mean "
          "order value.",
          """
          `values = [120, 95, 300, 80, 150, 110, 2000, 130, 90, 105]` (order values in INR).
          Comment on what the statistics tell you.
          """,
          ["Compute descriptive statistics with NumPy.", "Use the t-distribution for a small-sample CI.",
           "Notice the outlier (2000) and compare mean vs median.", "Suggest a robust alternative."],
          "With n = 10 we use the t critical value (about 2.262 for 9 df). The single 2000 order drags the mean "
          "far above the median, and the CI is very wide - so I'd report the median, investigate the outlier, "
          "or bootstrap the CI.",
          """
          import numpy as np
          from scipy import stats

          values = np.array([120, 95, 300, 80, 150, 110, 2000, 130, 90, 105])
          mean, median = values.mean(), np.median(values)
          sd = values.std(ddof=1)                       # sample standard deviation
          se = sd / np.sqrt(len(values))
          t_crit = stats.t.ppf(0.975, df=len(values) - 1)
          ci = (mean - t_crit * se, mean + t_crit * se)
          print(f"mean={mean:.1f} median={median:.1f} sd={sd:.1f} 95% CI=({ci[0]:.1f}, {ci[1]:.1f})")

          # robust alternative: bootstrap CI for the median
          rng = np.random.default_rng(42)
          boots = [np.median(rng.choice(values, len(values))) for _ in range(5000)]
          print(np.percentile(boots, [2.5, 97.5]))
          """, "python",
          "O(n) for the statistics; O(B * n) for B bootstrap resamples.",
          ["n = 1 (undefined sample SD)", "Many identical values", "Extreme outliers"],
          "Interpret the numbers - the insight about the outlier matters more than the arithmetic.",
          ["Why ddof=1?", "When would you trim or winsorise outliers?"], hot=True),
        P("intermediate", "Test whether variant B's conversion rate is significantly higher than control A's.",
          """
          A: 10,000 users, 1,000 conversions. B: 10,000 users, 1,120 conversions. alpha = 0.05.
          Report the lift, p-value and 95% CI, and recommend a decision.
          """,
          ["Two independent proportions -> two-proportion z-test.", "Pooled SE for the test statistic.",
           "Unpooled SE for the CI of the difference.", "Translate the result into a decision."],
          "Lift = 1.2 percentage points (12% relative). z is about 2.75 with p about 0.006 (two-sided), and the 95% CI "
          "of the difference is roughly +0.35 to +2.05 pp - it excludes zero, so the result is significant. I'd "
          "recommend shipping if guardrails are healthy and the test ran its planned duration.",
          """
          from statsmodels.stats.proportion import proportions_ztest, confint_proportions_2indep

          conversions = [1120, 1000]   # B, A
          users = [10000, 10000]
          z, p = proportions_ztest(conversions, users, alternative="two-sided")
          low, high = confint_proportions_2indep(1120, 10000, 1000, 10000, method="wald")
          print(f"z={z:.2f}, p={p:.4f}, diff CI=({low:.4f}, {high:.4f})")
          """, "python",
          "Constant time once counts are aggregated.",
          ["Unequal group sizes (check for SRM)", "Multiple variants (correct for multiple comparisons)",
           "Very low baseline rates"],
          "End with a business recommendation, not just a p-value.",
          ["One-sided or two-sided - which and why?", "How would CUPED change the analysis?"], hot=True),
        P("advanced", "Calculate the sample size per group for an A/B test.",
          """
          Baseline conversion 10%. You want to detect an absolute lift of 1 percentage point (to 11%) with
          alpha = 0.05 (two-sided) and 80% power. Then estimate the test duration if 6,000 users/day are eligible.
          """,
          ["Use the two-proportion sample-size formula.", "z_alpha/2 = 1.96, z_beta = 0.84.",
           "Compute n per group, then duration from traffic.", "Round duration up to whole weeks."],
          "n = (1.96 * sqrt(2 * 0.105 * 0.895) + 0.84 * sqrt(0.10 * 0.90 + 0.11 * 0.89))^2 / 0.01^2, which is about "
          "14,750 users per group (about 29.5k total). At 6,000 eligible users/day that is ~5 days, so I'd run "
          "a full 7 days (or 14) to cover weekly seasonality.",
          """
          import math
          from scipy.stats import norm

          def sample_size_per_group(p1, p2, alpha=0.05, power=0.8):
              z_a, z_b = norm.ppf(1 - alpha / 2), norm.ppf(power)
              p_bar = (p1 + p2) / 2
              num = (z_a * math.sqrt(2 * p_bar * (1 - p_bar))
                     + z_b * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
              return math.ceil(num / (p2 - p1) ** 2)

          n = sample_size_per_group(0.10, 0.11)        # about 14,750
          days = math.ceil(2 * n / 6000)
          print(n, days, "-> run for", max(7, math.ceil(days / 7) * 7), "days")
          """, "python",
          "Closed-form - O(1).",
          ["Very small MDE (sample size explodes)", "Unequal allocation (e.g. 90/10)", "Relative vs absolute MDE"],
          "Point out that halving the MDE roughly quadruples the sample size - it shows intuition.",
          ["How does unequal allocation change n?", "What if traffic is too low for this MDE?"]),
    ],
    "scenario": [
        S("beginner", """
          A product manager shares a chart: users who used the new "wishlist" feature spend 35% more per month than
          users who didn't. They want to announce that the wishlist increases spending by 35%.
          """,
          "What would you tell them?",
          [("Acknowledge", "The correlation is real and interesting."),
           ("Name the bias", "Self-selection: engaged, high-spending users are more likely to try new features."),
           ("Quantify confounders", "Compare pre-period spend and engagement of both groups."),
           ("Propose a test", "A/B test (or diff-in-diff / matching) to estimate the causal effect."),
           ("Reframe the claim", "Communicate what we can and cannot conclude today.")],
          """
          I'd start by agreeing the pattern is worth investigating, but the claim "the wishlist increases spending by
          35%" isn't supported yet. Users who adopt a new feature are typically already more engaged - they browse
          more and buy more - so the 35% gap mixes the feature's effect with **who chose to use it**.

          A quick check: compare the two groups' spend in the 3 months *before* the feature launched. If adopters
          already spent ~30% more, most of the gap is selection.

          To estimate the real effect, I'd propose an A/B test where the wishlist button is shown to a random half
          of users. If that's not possible, a difference-in-differences on pre/post spend or propensity-score
          matching would give a more credible estimate. Meanwhile, the safe message is: "wishlist users spend more;
          we're measuring how much of that the feature causes."
          """,
          ["Spots selection bias quickly", "Suggests a concrete check", "Offers causal methods",
           "Communicates diplomatically"],
          ["Bluntly calling the PM wrong", "Accepting the claim", "Being vague about how to test it"],
          ["How does difference-in-differences work here?", "What if the A/B test is too slow?"], hot=True),
        S("intermediate", """
          Three days into a planned two-week A/B test of a new checkout flow, the dashboard shows +3% conversion with
          p = 0.04. The product manager wants to stop the test and ship today.
          """,
          "How do you respond?",
          [("Restate the plan", "The sample size and duration were fixed upfront for a reason."),
           ("Explain peeking", "Repeatedly checking and stopping at p < 0.05 inflates false positives."),
           ("Check validity", "SRM, novelty effect, weekday mix, guardrail metrics."),
           ("Offer options", "Continue to plan, or switch to a sequential-testing design next time."),
           ("Align on decision", "Agree on ship criteria and the timeline.")],
          """
          I'd explain that 3 days is a "peek": if we check every day and stop the first time p < 0.05, the real
          false-positive rate can be several times higher than 5%. Our power calculation said we need two weeks of
          traffic, and three days also misses weekend behaviour and a likely **novelty effect** on a new checkout.

          I'd check validity right away: is the traffic split close to 50/50 (sample-ratio mismatch)? Are guardrails
          like payment failures or refunds stable? Is the lift consistent across days rather than one spike?

          Then I'd offer options: continue to the planned end (my recommendation), or, if speed matters, agree now
          on a sequential-testing method with adjusted thresholds for future tests. If the business must ship early,
          I'd frame it as a risk decision with the current confidence interval and a plan to monitor post-launch.
          """,
          ["Explains peeking clearly", "Checks SRM/guardrails/novelty", "Offers pragmatic alternatives",
           "Influences without authority"],
          ["Agreeing to stop just because p < 0.05", "Refusing without explaining", "Ignoring business urgency"],
          ["What is a sequential test?", "How would you detect a novelty effect?"], hot=True),
        S("advanced", """
          Your experiment should split traffic 50/50, but after a week the control has 102,400 users and the treatment
          97,600. The treatment shows a significant +2.5% lift in revenue per user.
          """,
          "Can you trust the result? What do you do?",
          [("Test for SRM", "Chi-square goodness-of-fit on the allocation."),
           ("Treat as a red flag", "SRM means the groups may no longer be comparable."),
           ("Find the cause", "Assignment bugs, redirects, bot filtering, crashes or logging loss in one arm."),
           ("Fix & re-run", "Fix the root cause and restart; don't 'correct' the results."),
           ("Prevent", "Automated SRM alerts and A/A tests in the experimentation platform.")],
          """
          First I'd test the split: a chi-square goodness-of-fit test of 102,400 vs 97,600 against 50/50 gives
          chi-square of about 115 and p far below 0.001 - this is a **sample-ratio mismatch**, not chance.

          SRM means something removed or added users non-randomly in one arm, so the arms may no longer be
          comparable and the +2.5% lift can't be trusted - for example, if the treatment page crashes for users on
          slow devices, those (lower-spending) users drop out of the treatment, inflating its revenue per user.

          I'd investigate the cause: assignment/hashing code, redirects that lose users, bot filtering that applies
          differently, client crashes or event-logging loss in one variant - comparing the split by browser,
          platform and day usually localises it. After fixing it, I'd re-run the test rather than try to reweight.
          Longer term I'd add automatic SRM checks that block results from being shown when the ratio is off.
          """,
          ["Knows and computes SRM", "Explains why SRM invalidates results", "Systematic root-cause search",
           "Prevention via platform checks"],
          ["Reporting the lift anyway", "Reweighting groups to 'fix' SRM", "Not quantifying the imbalance"],
          ["What is an A/A test useful for?", "How would you design automatic SRM alerts?"]),
    ],
    "quiz": [
        Q("beginner", "In a right-skewed distribution (e.g. income), how do the mean and median usually compare?",
          ["Mean < median", "Mean = median", "Mean > median", "No relationship"], 2,
          "The long right tail pulls the mean upward, above the median.",
          ["That is typical of left skew.", "Only for symmetric distributions.", "Correct.",
           "Skewness does imply a typical ordering."],
          "Use this to justify reporting medians for order values or salaries.", hot=True),
        Q("beginner", "With alpha = 0.05, a test returns p = 0.03. What do you conclude?",
          ["Accept the null hypothesis", "Reject the null hypothesis", "The null is true with 97% probability",
           "The effect is large"], 1,
          "p < alpha, so the data would be unusual under H0 and we reject it.",
          ["We never 'accept' H0 - we fail to reject it.", "Correct.", "Misinterpretation of the p-value.",
           "p-values say nothing about effect size."],
          "Follow with the effect size and confidence interval."),
        Q("intermediate", "All else equal, what happens to statistical power if you increase the sample size?",
          ["It decreases", "It increases", "It stays the same", "It becomes exactly alpha"], 1,
          "A larger n shrinks the standard error, making real effects easier to detect.",
          ["Opposite.", "Correct.", "Power depends on n.", "Unrelated."],
          "Power also increases with effect size and lower variance (e.g. CUPED)."),
        Q("intermediate", "Which test compares the means of three or more independent groups?",
          ["Paired t-test", "Chi-square test", "One-way ANOVA", "Pearson correlation"], 2,
          "ANOVA tests whether at least one group mean differs; follow up with post-hoc tests.",
          ["For two related samples.", "For categorical frequencies.", "Correct.", "Measures linear association."],
          "Mention post-hoc tests like Tukey's HSD."),
        Q("advanced", "Disease prevalence is 1%, test sensitivity 99%, false-positive rate 5%. P(disease | positive) "
          "is closest to:",
          ["99%", "95%", "50%", "17%"], 3,
          "P(+) = 0.99*0.01 + 0.05*0.99 = 0.0594; P(D|+) = 0.0099/0.0594, about 16.7%.",
          ["Confuses sensitivity with the posterior.", "Ignores the base rate.", "No basis.", "Correct."],
          "Classic base-rate question - show the calculation aloud.", hot=True),
    ],
}
