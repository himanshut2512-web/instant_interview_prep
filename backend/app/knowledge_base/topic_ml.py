from ._build import P, Q, S, T, md, note

TOPIC = {
    "key": "ml",
    "name": "Machine Learning",
    "keywords": ["machine learning", "ml", "predictive", "classification", "regression", "clustering",
                 "scikit-learn", "sklearn", "xgboost", "lightgbm", "random forest", "feature engineering",
                 "model", "models", "modelling", "modeling", "data science", "data scientist", "forecasting",
                 "churn", "recommendation"],
    "core": ["machine learning", "data science", "data scientist"],
    "subtopics": ["Bias-variance & regularisation", "Model evaluation & metrics", "Tree ensembles",
                  "Linear & logistic regression", "Imbalanced data", "Feature engineering & leakage",
                  "Clustering & PCA", "Interpretability (SHAP)"],
    "revision": note(
        summary="ML rounds probe whether you understand why models work, how to evaluate them honestly and how "
        "to choose, tune and explain them for a business problem - not just which library call to make.",
        concepts=[
            ("Bias-variance trade-off", "Simple models underfit (high bias); flexible models overfit (high variance). "
             "Total error = bias^2 + variance + noise."),
            ("Regularisation", "L1 (lasso) adds |w| and drives some weights to zero; L2 (ridge) adds w^2 and shrinks "
             "all weights; elastic net mixes both."),
            ("Cross-validation", "k-fold for i.i.d. data, stratified for imbalance, time-series split for temporal "
             "data, group k-fold when entities repeat."),
            ("Precision / recall / F1", "Of predicted positives, how many are right / of actual positives, how many "
             "we caught / their harmonic mean."),
            ("ROC-AUC vs PR-AUC", "ROC-AUC = ranking quality across thresholds; PR-AUC is more informative when "
             "positives are rare."),
            ("Bagging vs boosting", "Bagging trains models in parallel on bootstrap samples and averages (reduces "
             "variance, e.g. random forest); boosting trains sequentially on errors (reduces bias, e.g. XGBoost)."),
            ("Logistic regression", "Linear model of log-odds, outputs calibrated-ish probabilities, interpretable "
             "coefficients (odds ratios)."),
            ("Data leakage", "Information unavailable at prediction time sneaking into training - gives great "
             "offline scores and poor production performance."),
            ("K-means / PCA", "Partition into k clusters minimising within-cluster variance / project onto "
             "orthogonal directions of maximum variance."),
            ("SHAP", "Game-theoretic feature attributions per prediction - global and local interpretability."),
        ],
        explanation=md("""
            **The ML workflow interviewers expect:** frame the problem (target, unit, horizon, decision it drives)
            -> data audit -> baseline -> features -> model -> honest validation -> error analysis -> deployment &
            monitoring -> business impact.

            **Choosing a model.**

            | Situation | Good default |
            |---|---|
            | Tabular data, mixed types | Gradient boosting (LightGBM/XGBoost/CatBoost) |
            | Need interpretability / few rows | Regularised linear/logistic regression |
            | Many categorical high-cardinality features | CatBoost or target encoding + GBM |
            | Images, text, audio | Deep learning / pre-trained models |
            | No labels | Clustering, anomaly detection, PCA for structure |

            **Evaluation.** Pick the metric from the cost of errors: recall when misses are expensive (fraud,
            disease), precision when false alarms are expensive (spam to inbox), F1/PR-AUC for imbalance, RMSE when
            large errors matter, MAE/MAPE/WAPE for forecasts communicated to business. Then choose the decision
            threshold using costs, not 0.5 by default.

            **Overfitting toolkit.** More data, regularisation, simpler models, early stopping, dropout (DL),
            cross-validation for tuning, and keeping a truly untouched test set.

            **Imbalanced data.** Stratified splits, class weights, resampling (SMOTE/undersampling) *inside* CV
            folds only, threshold tuning, and evaluating with PR-AUC/recall at fixed precision.

            **Leakage checklist.** Fit scalers/encoders inside a Pipeline, split by time for temporal problems,
            remove features generated after the prediction moment (e.g. "days_since_cancellation" in a churn
            model), and group-split when the same customer appears many times.
        """),
        code=md("""
            from sklearn.compose import ColumnTransformer
            from sklearn.impute import SimpleImputer
            from sklearn.linear_model import LogisticRegression
            from sklearn.model_selection import StratifiedKFold, cross_val_score
            from sklearn.pipeline import Pipeline
            from sklearn.preprocessing import OneHotEncoder, StandardScaler

            num_cols = ["tenure_months", "monthly_charges", "support_tickets"]
            cat_cols = ["plan", "region", "payment_method"]

            preprocess = ColumnTransformer([
                ("num", Pipeline([("impute", SimpleImputer(strategy="median")),
                                  ("scale", StandardScaler())]), num_cols),
                ("cat", Pipeline([("impute", SimpleImputer(strategy="most_frequent")),
                                  ("onehot", OneHotEncoder(handle_unknown="ignore"))]), cat_cols),
            ])
            model = Pipeline([("prep", preprocess),
                              ("clf", LogisticRegression(class_weight="balanced", max_iter=1000))])

            cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
            scores = cross_val_score(model, X, y, cv=cv, scoring="average_precision")  # PR-AUC
            print(scores.mean(), scores.std())
        """),
        language="python",
        pitfalls=[
            "Reporting accuracy on an imbalanced dataset.",
            "Fitting scalers, encoders or SMOTE on the full dataset before splitting (leakage).",
            "Random K-fold on time-series data - future information leaks into training.",
            "Tuning hyper-parameters on the test set.",
            "Using a 0.5 threshold without considering the business cost of errors.",
        ],
        tips=[
            "Start answers with the intuition, then the maths, then a real example.",
            "Always mention a simple baseline and how much your model beat it.",
            "Talk about error analysis and what you would try next - it signals maturity.",
            "Translate model metrics into business value (revenue saved, hours reduced).",
        ],
        cheat_sheet=[
            "Precision = TP/(TP+FP); Recall = TP/(TP+FN); F1 = 2PR/(P+R).",
            "Random forest: bagging + random feature subsets; GBM: sequential trees fitting residuals/gradients.",
            "Standardise features for distance-based models (KNN, k-means, SVM) and regularised linear models.",
            "Trees don't need scaling and handle non-linearities and interactions natively.",
            "Elbow / silhouette score help choose k in k-means.",
            "PCA requires scaled features; components are orthogonal and ordered by explained variance.",
            "Use TimeSeriesSplit for temporal validation.",
        ],
        likely_questions=[
            "Explain the bias-variance trade-off.",
            "Precision vs recall - which would you optimise for fraud?",
            "Random forest vs XGBoost?",
            "L1 vs L2 regularisation?",
            "How do you handle imbalanced data?",
            "What is data leakage? Give an example.",
        ],
    ),
    "theory": [
        T("beginner", "Explain the bias-variance trade-off and how you detect overfitting and underfitting.",
          """
          - **Bias** is error from overly simple assumptions - the model misses real patterns (underfitting):
            training and validation error are both high.
          - **Variance** is error from sensitivity to the particular training sample - the model memorises noise
            (overfitting): training error is low but validation error is much higher.

          Expected error = bias^2 + variance + irreducible noise. Increasing model complexity lowers bias but raises
          variance, so we look for the sweet spot using validation curves.

          Fixes:
          - Underfitting: richer features, more flexible model, less regularisation, train longer.
          - Overfitting: more data, regularisation (L1/L2, dropout), simpler model or shallower trees, early
            stopping, bagging/ensembles, feature selection.

          Example: a depth-20 decision tree gave 99% train / 71% validation accuracy on churn; limiting depth and
          moving to a regularised gradient-boosting model gave 86% / 84%.
          """,
          ["Correct definitions", "Train vs validation error diagnosis", "Remedies for each", "Concrete example"],
          "Draw the U-shaped validation-error curve if there is a whiteboard.",
          ["How does k in KNN affect bias and variance?", "Why does bagging reduce variance?"], hot=True),
        T("beginner", "What are precision, recall and F1? When do you prioritise one over the other?",
          """
          From the confusion matrix:
          - **Precision** = TP / (TP + FP) - when the model says "positive", how often is it right?
          - **Recall** = TP / (TP + FN) - of all real positives, how many did we catch?
          - **F1** = harmonic mean of the two - useful when you need a single number balancing both.

          Prioritise **recall** when missing a positive is costly: fraud, cancer screening, safety defects.
          Prioritise **precision** when false alarms are costly: flagging legitimate transactions, marketing spend
          per contacted customer, spam filtering important mail.

          The trade-off is controlled by the classification threshold. In a churn project, retention offers cost
          money, so we picked the threshold that maximised expected profit = (saved revenue x precision) - offer
          cost - instead of using 0.5.
          """,
          ["Formulas", "Intuitive meaning", "Context-driven choice", "Threshold controls the trade-off"],
          "Give one example for each side, ideally from your own domain.",
          ["What is the F-beta score?", "How do you pick a threshold?", "Why is accuracy misleading for imbalance?"],
          hot=True),
        T("intermediate", "Bagging vs boosting - how do Random Forest and XGBoost differ?",
          """
          | | Random Forest (bagging) | XGBoost / LightGBM (boosting) |
          |---|---|---|
          | Training | Trees built **independently in parallel** on bootstrap samples, random feature subsets | Trees built **sequentially**, each fitting the errors (gradients) of the ensemble so far |
          | Main effect | Reduces **variance** | Reduces **bias** (and variance with regularisation) |
          | Trees | Deep, low-bias trees | Shallow trees (weak learners) |
          | Tuning | Few sensitive parameters, robust defaults | More parameters (learning rate, depth, n_estimators, regularisation) |
          | Overfitting | Hard to overfit by adding trees | Can overfit - use early stopping |
          | Accuracy | Strong baseline | Usually best on tabular data when tuned |

          XGBoost adds L1/L2 regularisation on leaf weights, second-order gradient information, built-in missing
          value handling and efficient parallel split finding. LightGBM grows trees leaf-wise with histogram binning
          - faster on large data.

          I typically start with a random forest or default LightGBM as a baseline, then tune a boosted model with
          early stopping on a validation set.
          """,
          ["Parallel vs sequential", "Variance vs bias reduction", "Tuning & overfitting behaviour", "XGBoost extras"],
          "The comparison table structure works well verbally: training, effect, tuning, overfitting.",
          ["What does the learning rate do in boosting?", "How does XGBoost handle missing values?",
           "What is feature importance and why can it mislead?"], hot=True),
        T("intermediate", "What is the difference between L1 and L2 regularisation?",
          """
          Both add a penalty on model weights to the loss to reduce overfitting:
          - **L1 (lasso)**: penalty lambda * sum(|w|). Its diamond-shaped constraint makes the optimum land on axes,
            so many weights become **exactly zero** -> built-in feature selection, sparse models.
          - **L2 (ridge)**: penalty lambda * sum(w^2). Shrinks all weights smoothly toward zero but rarely to zero;
            handles **correlated features** well by spreading weight among them.
          - **Elastic net** combines both - sparse but stable with correlated groups.

          Larger lambda means a simpler model (more bias, less variance). Features must be standardised, otherwise
          the penalty treats features on different scales unfairly. In scikit-learn, `C` in LogisticRegression is
          the inverse of regularisation strength.
          """,
          ["Penalty forms", "Sparsity vs shrinkage", "Correlated features behaviour", "Scaling requirement"],
          "Mention the geometric intuition (diamond vs circle) - it impresses without being long.",
          ["Why does L1 produce zeros?", "How do you choose lambda?"], hot=True),
        T("advanced", "How do you handle a highly imbalanced classification problem (e.g. 1% fraud)?",
          """
          1. **Evaluate correctly**: drop accuracy; use PR-AUC, recall at a fixed precision, or expected cost.
             Use stratified splits (or time-based splits for fraud).
          2. **Algorithm-level**: class weights (`class_weight="balanced"`, `scale_pos_weight` in XGBoost), focal
             loss in deep learning.
          3. **Data-level**: random undersampling of the majority, oversampling or SMOTE - applied **only inside
             training folds**, never before splitting.
          4. **Threshold tuning**: choose the operating point from business costs (cost of a missed fraud vs a
             blocked good customer).
          5. **Better signal**: features that separate the rare class (velocity features, device/IP history),
             anomaly-detection scores as features.
          6. **Calibrate** probabilities after resampling/weighting if downstream decisions use them.

          In production I'd monitor precision/recall weekly because the base rate drifts.
          """,
          ["Right metrics and splits", "Class weights vs resampling", "Resampling inside folds", "Cost-based threshold",
           "Calibration & monitoring"],
          "Emphasise that resampling changes predicted probabilities - calibration is a senior-level detail.",
          ["SMOTE pros and cons?", "How do you calibrate probabilities?", "Anomaly detection vs classification?"],
          hot=True),
        T("advanced", "What is data leakage? Give real examples and how you prevent it.",
          """
          Leakage happens when the model is trained with information that **won't be available at prediction
          time**, producing great offline metrics and disappointing production results.

          Examples:
          - **Target leakage**: a churn model using "cancellation_reason" or "account_closed_date"; a loan model
            using "collections_flag" set after default.
          - **Train-test contamination**: scaling, imputing or SMOTE-ing on the full dataset before splitting;
            duplicates of the same customer in train and test.
          - **Temporal leakage**: random splits on time-series data, or features computed with future data (e.g.
            30-day rolling average centred on the prediction date).

          Prevention: define the **prediction moment** and build features only from data before it; split by time
          or by group; put all preprocessing inside a scikit-learn Pipeline fitted per fold; be suspicious of any
          feature with extreme importance or near-perfect AUC; and validate on a recent out-of-time period.
          """,
          ["Clear definition", "Several kinds of leakage", "Prediction-moment discipline", "Practical prevention"],
          "Share a story where a suspiciously good metric led you to discover leakage - very memorable.",
          ["How would you detect leakage after the fact?", "What is an out-of-time validation?"]),
    ],
    "practical": [
        P("beginner", "Build a scikit-learn pipeline that preprocesses mixed numeric/categorical data and evaluates "
          "a logistic regression with stratified cross-validation.",
          """
          DataFrame `df` with numeric columns `tenure_months`, `monthly_charges`, categorical `plan`, `region`, and
          a binary target `churned` (about 20% positives). Some values are missing.
          """,
          ["Separate numeric and categorical columns.", "Impute + scale numerics; impute + one-hot categoricals.",
           "Wrap preprocessing and model in one Pipeline to avoid leakage.",
           "Use StratifiedKFold and an imbalance-aware metric."],
          "Putting preprocessing inside the Pipeline means each CV fold fits imputers/scalers on its training part "
          "only. Stratification keeps the 20% churn ratio stable across folds, and ROC-AUC plus average precision "
          "give an honest view of ranking quality.",
          """
          import pandas as pd
          from sklearn.compose import ColumnTransformer
          from sklearn.impute import SimpleImputer
          from sklearn.linear_model import LogisticRegression
          from sklearn.model_selection import StratifiedKFold, cross_validate
          from sklearn.pipeline import Pipeline
          from sklearn.preprocessing import OneHotEncoder, StandardScaler

          X, y = df.drop(columns="churned"), df["churned"]
          num, cat = ["tenure_months", "monthly_charges"], ["plan", "region"]

          prep = ColumnTransformer([
              ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), num),
              ("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                                ("oh", OneHotEncoder(handle_unknown="ignore"))]), cat),
          ])
          pipe = Pipeline([("prep", prep), ("clf", LogisticRegression(max_iter=1000, class_weight="balanced"))])

          cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=7)
          res = cross_validate(pipe, X, y, cv=cv, scoring=["roc_auc", "average_precision"])
          print({k: v.mean().round(3) for k, v in res.items() if k.startswith("test_")})
          """, "python",
          "Training cost of k logistic regressions: roughly O(k * n * d * iterations).",
          ["Unseen categories at prediction time (handle_unknown='ignore')", "All-missing columns",
           "Severe imbalance (consider PR-AUC)"],
          "Narrate why each step exists - especially why the pipeline prevents leakage.",
          ["How would you tune C with GridSearchCV?", "How would you swap in LightGBM?"], hot=True),
        P("intermediate", "Given predicted probabilities and labels, choose the threshold that maximises precision "
          "while keeping recall at least 80%.",
          """
          `y_true` (0/1) and `y_prob` arrays from a validation set for a fraud model.
          Return the threshold, precision and recall at that point.
          """,
          ["Compute the precision-recall curve over all thresholds.", "Keep points with recall >= 0.8.",
           "Pick the one with the highest precision.", "Validate the chosen threshold on a hold-out set."],
          "precision_recall_curve returns one more precision/recall value than thresholds, so we drop the last "
          "point before aligning. Among thresholds meeting the recall constraint, we choose the highest precision.",
          """
          import numpy as np
          from sklearn.metrics import precision_recall_curve

          def pick_threshold(y_true, y_prob, min_recall=0.8):
              precision, recall, thresholds = precision_recall_curve(y_true, y_prob)
              precision, recall = precision[:-1], recall[:-1]          # align with thresholds
              ok = recall >= min_recall
              if not ok.any():
                  raise ValueError("No threshold reaches the recall target")
              best = np.argmax(np.where(ok, precision, -1))
              return thresholds[best], precision[best], recall[best]

          t, p, r = pick_threshold(y_true, y_prob)
          print(f"threshold={t:.3f} precision={p:.3f} recall={r:.3f}")
          """, "python",
          "O(n log n) for sorting probabilities inside precision_recall_curve.",
          ["No threshold meets the recall target", "Ties in predicted probabilities",
           "Choosing on the same data used for final evaluation"],
          "Mention picking the threshold on validation data and confirming on a separate test set.",
          ["How would you choose a threshold from business costs instead?", "What is probability calibration?"],
          hot=True),
        P("advanced", "Implement k-means clustering from scratch with NumPy.",
          """
          Input: `X` of shape (n_samples, n_features), `k`, `max_iter`, `tol`.
          Return the cluster labels and centroids. Use k-means++ initialisation if you can.
          """,
          ["Initialise centroids (k-means++ spreads them out).", "Assign each point to the nearest centroid.",
           "Recompute centroids as cluster means.", "Stop when centroids move less than tol."],
          "Vectorised distance computation keeps it fast: squared distances via broadcasting. Empty clusters are "
          "re-seeded with the point farthest from its centroid.",
          """
          import numpy as np

          def kmeans(X, k, max_iter=300, tol=1e-4, seed=0):
              rng = np.random.default_rng(seed)
              centroids = [X[rng.integers(len(X))]]
              for _ in range(1, k):                                   # k-means++ init
                  d2 = np.min(((X[:, None, :] - np.array(centroids)[None]) ** 2).sum(-1), axis=1)
                  centroids.append(X[rng.choice(len(X), p=d2 / d2.sum())])
              centroids = np.array(centroids, dtype=float)

              for _ in range(max_iter):
                  dists = ((X[:, None, :] - centroids[None]) ** 2).sum(-1)    # (n, k)
                  labels = dists.argmin(axis=1)
                  new = np.array([X[labels == j].mean(axis=0) if np.any(labels == j)
                                  else X[dists.min(axis=1).argmax()] for j in range(k)])
                  shift = np.linalg.norm(new - centroids)
                  centroids = new
                  if shift < tol:
                      break
              return labels, centroids
          """, "python",
          "O(n * k * d) per iteration; memory O(n * k) for the distance matrix.",
          ["Empty clusters", "k > n", "Features on different scales (standardise first)", "Duplicate points"],
          "Explain k-means++ and why scaling matters before writing code.",
          ["How do you choose k?", "When does k-means fail (non-spherical clusters)?", "K-means vs DBSCAN?"]),
    ],
    "scenario": [
        S("beginner", """
          You built a churn model with 95% accuracy. The retention team says it's useless - it hardly flags anyone
          who actually leaves. Only 5% of customers churn each month.
          """,
          "What went wrong and how do you fix it?",
          [("Diagnose", "With 5% churn, predicting 'no churn' for everyone already scores 95% accuracy."),
           ("Re-measure", "Look at recall, precision and PR-AUC on churners."),
           ("Re-train", "Class weights or resampling within folds; better churn signals."),
           ("Tune threshold", "Pick an operating point from retention budget and offer economics."),
           ("Prove value", "Measure saved customers via a holdout/A-B test of the campaign.")],
          """
          The 95% accuracy is the **accuracy paradox**: with 5% churners, a model that always predicts "stays" is
          95% accurate and useless. The retention team is right.

          I'd re-evaluate with metrics that focus on churners - recall, precision and PR-AUC - and look at the
          confusion matrix at the current threshold. Then I'd retrain with `class_weight="balanced"` (or
          `scale_pos_weight` in XGBoost), add stronger signals (usage drop, support tickets, payment failures), and
          use a time-based validation split.

          Next, I'd choose the threshold with the retention team: if they can call 2,000 customers a month, we rank
          by churn probability and pick the top 2,000, reporting precision@2000 and expected revenue saved. Finally,
          I'd propose a holdout group to measure the campaign's true uplift.
          """,
          ["Explains the accuracy paradox", "Chooses business-relevant metrics", "Concrete modelling fixes",
           "Ties threshold to operational capacity"],
          ["Defending the 95% accuracy", "Only resampling without changing evaluation", "Ignoring capacity constraints"],
          ["What is uplift modelling and why might it be better here?", "How would you explain PR-AUC to the business?"],
          hot=True),
        S("intermediate", """
          Your demand-forecasting model had 12% MAPE in back-testing, but two months after deployment its error has
          climbed to 30% and planners have stopped trusting it.
          """,
          "How do you investigate and recover?",
          [("Triage", "Is it all stores/SKUs or a segment? Sudden or gradual?"),
           ("Check the data", "Pipeline failures, schema/unit changes, missing promos, train-serve skew."),
           ("Check for drift", "Compare feature and target distributions with training data."),
           ("Fix", "Repair pipeline issues, retrain with recent data, add features for new drivers."),
           ("Restore trust", "Share findings, add monitoring and a fallback/override process.")],
          """
          I'd first slice the error: by region, category, store and week. A sudden jump across everything usually
          means a **data/pipeline problem**; a gradual rise in some segments points to **drift**.

          Data checks: did an upstream table change units or definitions? Are promotions or price features arriving
          late or null in production (train-serve skew)? I'd compare the production feature values with what the
          offline pipeline would compute for the same dates.

          Drift checks: population stability index on key features, and whether new behaviour appeared (a competitor
          launch, new store formats, a holiday not in the training window).

          In a similar case, a promotion calendar feed stopped updating, so the model treated promo weeks as normal.
          We fixed the feed, backfilled, retrained on recent data and added data-quality checks and error alerts per
          segment. To rebuild trust I'd share a short RCA with planners and give them an override mechanism with
          feedback captured for the next retrain.
          """,
          ["Segments the error before acting", "Separates data issues from drift", "Knows train-serve skew",
           "Plans monitoring and stakeholder trust"],
          ["Immediately retraining without diagnosis", "Blaming planners or the data team", "No monitoring afterwards"],
          ["How would you set up model monitoring?", "What is PSI?", "How often should you retrain?"], hot=True),
        S("advanced", """
          A telecom client asks your team to "use AI to reduce churn" within 8 weeks. They have billing, usage,
          complaints and network data across 5 million subscribers, but no clear definition of churn or success.
          """,
          "How would you scope and deliver this engagement?",
          [("Frame", "Define churn (e.g. no recharge in 30 days), prediction horizon, and the action it drives."),
           ("Size value", "Estimate revenue at risk and success metric (incremental retained revenue)."),
           ("Data & baseline", "Audit data, build a simple rules/logistic baseline in week 2-3."),
           ("Model & explain", "Gradient boosting with SHAP reasons; uplift modelling if offers are planned."),
           ("Deploy & measure", "Scored lists to CRM, randomised holdout to prove incremental impact.")],
          """
          I'd spend week 1 on framing with business stakeholders: what counts as churn (prepaid vs postpaid
          differ), how far ahead we need to predict to act (e.g. 30 days), and which action we'll take - retention
          offers, network fixes, or service calls. Success is **incremental retained revenue**, not AUC.

          Weeks 2-3: data audit and a baseline - a simple rule set or logistic regression on tenure, recharge gaps,
          usage drop and complaints - so we have something to beat and an early win to show.

          Weeks 4-6: a gradient-boosting model with time-based validation, features like usage trend, network drop
          rate, and complaint recency; SHAP to give per-customer reasons that the call-centre can use. If the
          client will give offers, I'd suggest **uplift modelling** to target customers who are *persuadable*, not
          just likely to churn.

          Weeks 7-8: integrate scores into the CRM, run a randomised holdout to measure incremental impact, and
          hand over monitoring and a retraining plan. Throughout, weekly demos keep stakeholders aligned.
          """,
          ["Business framing before modelling", "Value-based success metric", "Baseline + iteration plan",
           "Explainability and uplift awareness", "Proves impact with a holdout"],
          ["Jumping straight to model selection", "Measuring success by AUC only", "No plan for adoption/measurement"],
          ["How would you design the holdout?", "What is uplift modelling?", "How do you handle prepaid vs postpaid?"],
          hot=True),
    ],
    "quiz": [
        Q("beginner", "A model scores 99% on training data but 70% on test data. This is most likely:",
          ["Underfitting", "Overfitting", "Data drift", "A perfect model"], 1,
          "A large train-test gap means the model memorised training noise - high variance.",
          ["Underfitting shows poor training performance too.", "Correct.", "Drift relates to production over time.",
           "The test score shows it generalises poorly."],
          "Follow up with the remedies: regularisation, more data, simpler model, early stopping.", hot=True),
        Q("beginner", "For cancer screening, where missing a positive case is very costly, which metric matters most?",
          ["Precision", "Recall", "Accuracy", "Specificity"], 1,
          "Recall measures how many actual positives we catch; false negatives are the costly error here.",
          ["Precision matters when false positives are costly.", "Correct.", "Misleading with rare positives.",
           "Specificity focuses on true negatives."],
          "Always justify a metric from the cost of each error type.", hot=True),
        Q("intermediate", "What is a characteristic effect of L1 regularisation?",
          ["It makes all weights equal", "It drives some weights exactly to zero", "It increases variance",
           "It only works for trees"], 1,
          "The L1 penalty's geometry produces sparse solutions - built-in feature selection.",
          ["No such effect.", "Correct.", "Regularisation reduces variance.", "It is used in linear models and more."],
          "Contrast with L2, which shrinks weights without zeroing them."),
        Q("intermediate", "Random forests mainly reduce error through:",
          ["Sequentially fitting residuals", "Averaging many de-correlated trees (bagging + feature sampling)",
           "Pruning a single deep tree", "Gradient descent on weights"], 1,
          "Bootstrap samples plus random feature subsets create diverse trees; averaging them lowers variance.",
          ["That is boosting.", "Correct.", "A forest uses many trees.", "Trees are not trained by gradient descent."],
          "Mention that this is why random forests are hard to overfit by adding more trees."),
        Q("advanced", "For a fraud dataset with 0.1% positives, which metric gives the most informative single "
          "summary of model quality?",
          ["Accuracy", "ROC-AUC", "PR-AUC (average precision)", "R-squared"], 2,
          "PR-AUC focuses on performance on the rare positive class; ROC-AUC can look excellent because the huge "
          "number of true negatives keeps the false-positive rate low.",
          ["A trivial model scores 99.9%.", "Informative, but optimistic under extreme imbalance.", "Correct.",
           "A regression metric."],
          "Explain why ROC-AUC can mislead under heavy imbalance - a senior-level insight.", hot=True),
    ],
}
