from ._build import P, Q, S, T, md, note

TOPIC = {
    "key": "mlops",
    "name": "Cloud & MLOps",
    "keywords": ["aws", "azure", "gcp", "cloud", "docker", "kubernetes", "k8s", "mlops", "mlflow", "sagemaker",
                 "vertex ai", "azure ml", "deployment", "deploy", "ci/cd", "devops", "monitoring", "production",
                 "terraform", "kubeflow", "feature store", "api"],
    "core": ["mlops", "docker", "kubernetes", "aws", "azure", "gcp"],
    "subtopics": ["ML lifecycle & MLOps", "Docker & Kubernetes", "Model serving patterns", "CI/CD/CT for ML",
                  "Monitoring & drift", "Feature stores & skew", "Cloud services (AWS/Azure/GCP)"],
    "revision": note(
        summary="MLOps questions test whether you can take a model from notebook to a reliable, monitored "
        "production service: packaging, deployment patterns, CI/CD, monitoring and retraining on a cloud platform.",
        concepts=[
            ("MLOps", "Practices that make ML reproducible, deployable, monitorable and continuously improvable - "
             "DevOps plus data and model management."),
            ("Docker image vs container", "An image is an immutable, layered package of code + dependencies; a "
             "container is a running instance of it."),
            ("Kubernetes", "Orchestrates containers: Deployments, Pods, Services, autoscaling (HPA), rolling updates."),
            ("Experiment tracking & registry", "MLflow/W&B log params, metrics and artefacts; a registry versions "
             "models and their stage (staging/production)."),
            ("Batch vs online inference", "Score in scheduled bulk jobs vs respond per request via an API with "
             "latency SLAs."),
            ("Shadow / canary / blue-green", "Mirror traffic without using answers / send a small % to the new "
             "model / switch all traffic between two environments with instant rollback."),
            ("Data drift vs concept drift", "Input distribution changes vs the input-output relationship changes."),
            ("Training-serving skew", "Features computed differently in training and production - silent accuracy "
             "loss."),
            ("Feature store", "Shared, versioned feature definitions with offline (training) and online (serving) "
             "stores and point-in-time correctness."),
            ("Infrastructure as code", "Terraform/Bicep/CloudFormation make environments reproducible and "
             "reviewable."),
        ],
        explanation=md("""
            **ML lifecycle.** Data ingestion & validation -> feature engineering -> training & experiment tracking
            -> evaluation & approval gates -> packaging (container) -> deployment -> monitoring -> retraining.
            Everything versioned: code (git), data (snapshots/DVC/Delta time travel), models (registry), config.

            **Serving patterns.**

            | Pattern | When |
            |---|---|
            | Batch scoring (Airflow/Spark job) | Predictions needed daily/hourly (churn lists, forecasts) |
            | Online API (FastAPI/BentoML/KServe/SageMaker endpoint) | Per-request decisions with latency SLAs |
            | Streaming | Event-driven decisions (fraud on each transaction) |
            | Edge / on-device | Offline or ultra-low-latency use cases |

            **Safe rollout.** Shadow first (compare predictions, zero risk), then canary 5% -> 25% -> 100% with
            automatic rollback on error rate/latency/business-metric regression; champion-challenger for continuous
            comparison.

            **Monitoring.** Service metrics (latency p95, errors, throughput), data quality (nulls, schema, ranges),
            drift (PSI/KS on features and prediction distribution), and model performance once labels arrive
            (often delayed). Alert on thresholds and feed into retraining (scheduled or drift-triggered).

            **Cloud mapping.** AWS: S3, SageMaker, Lambda, ECS/EKS, Glue. Azure: Blob/ADLS, Azure ML, Functions,
            AKS, Data Factory, Databricks. GCP: GCS, Vertex AI, Cloud Run, GKE, BigQuery. Knowing one well and the
            equivalents in others is usually enough.
        """),
        code=md("""
            # Dockerfile for a FastAPI model service
            FROM python:3.12-slim
            WORKDIR /app
            ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
            COPY requirements.txt .
            RUN pip install --no-cache-dir -r requirements.txt   # cached layer unless deps change
            COPY app/ ./app/
            COPY model/ ./model/
            RUN useradd -m appuser && chown -R appuser /app
            USER appuser
            EXPOSE 8000
            HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
            CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
        """),
        language="dockerfile",
        pitfalls=[
            "Unpinned dependencies - the model behaves differently in production.",
            "Re-implementing feature logic separately for serving (training-serving skew).",
            "Monitoring only uptime, not data drift or model quality.",
            "Deploying a new model to 100% of traffic at once with no rollback plan.",
            "Baking secrets into Docker images.",
        ],
        tips=[
            "Describe one deployment you did end to end: packaging, infra, rollout, monitoring, incidents.",
            "Use the lifecycle framing (build -> deploy -> monitor -> retrain) to structure answers.",
            "Mention cost and latency trade-offs, not just tools.",
            "Show you understand delayed labels and how you monitor without them.",
        ],
        cheat_sheet=[
            "Order Dockerfile steps from least to most frequently changed to maximise layer caching.",
            "Kubernetes HPA scales pods on CPU/memory or custom metrics.",
            "PSI < 0.1 stable, 0.1-0.25 moderate shift, > 0.25 significant shift (common rule of thumb).",
            "CT = continuous training: automatically retrain and validate on new data.",
            "Blue-green = two full environments; canary = gradual traffic shift.",
            "Store models with their training data version, code commit and metrics.",
        ],
        likely_questions=[
            "What is MLOps?",
            "How do you deploy a model to production?",
            "How do you monitor a model and detect drift?",
            "Batch vs real-time inference?",
            "What is a canary or shadow deployment?",
        ],
    ),
    "theory": [
        T("beginner", "What is MLOps and why do teams need it?",
          """
          MLOps applies DevOps principles to machine learning so models can be **built, deployed and maintained
          reliably**. Unlike normal software, an ML system depends on code **and** data **and** a trained model,
          and its quality decays as the world changes.

          It covers:
          - **Reproducibility**: versioned code, data and models; experiment tracking (MLflow).
          - **Automation**: pipelines for training, validation and deployment (CI/CD/CT).
          - **Deployment**: packaging (Docker), serving (batch jobs, APIs), safe rollouts.
          - **Monitoring**: service health, data quality, drift, model performance.
          - **Governance**: approvals, lineage, audit trails, model cards.

          Without it, teams end up with notebooks nobody can rerun, models that silently degrade, and slow, risky
          releases. With it, a retrain-and-redeploy can be a routine, tested pipeline run.
          """,
          ["Why ML differs from normal software", "Key pillars", "Concrete pain it solves"],
          "Close with a before/after from your experience (e.g. release time from weeks to hours).",
          ["What is the difference between CI/CD and CT?", "What tools have you used for MLOps?"], hot=True),
        T("beginner", "What is the difference between a Docker image and a container, and why containerise models?",
          """
          A **Docker image** is a read-only, layered template containing the OS libraries, Python runtime,
          dependencies, code and model artefacts. A **container** is a running, isolated instance of that image -
          you can run many containers from one image.

          Why containerise ML models:
          - **Consistency**: the same environment from laptop to CI to production ("works on my machine" goes away).
          - **Portability**: run on any cloud, Kubernetes or serverless container platform.
          - **Isolation & scaling**: each model service has its own dependencies and can scale independently.
          - **Reproducibility**: an image tag pins exactly what was deployed, enabling rollbacks.

          Best practices: slim base images, pinned versions, layer ordering for caching, non-root user, no secrets
          in images, health checks.
          """,
          ["Image vs container definition", "Consistency/portability/scaling", "Good Dockerfile practices"],
          "Mention one Dockerfile best practice you actually used, e.g. layer caching for requirements.",
          ["What is a multi-stage build?", "How would you reduce image size?"], hot=True),
        T("intermediate", "Batch vs real-time inference - and how do shadow, canary and blue-green deployments differ?",
          """
          **Batch inference** scores large datasets on a schedule (e.g. nightly churn scores written to a table) -
          simple, cheap, efficient, but predictions can be stale. **Real-time inference** serves predictions per
          request through an API within a latency budget - needed for fraud checks or recommendations, but requires
          scalable serving, online features and tighter monitoring.

          Rollout strategies for a new model version:
          - **Shadow**: the new model receives a copy of live traffic; its predictions are logged but not used.
            Zero user risk; validates latency and prediction distributions.
          - **Canary**: route a small share (say 5%) of real traffic to the new model, watch metrics, then ramp up;
            automatic rollback if errors or business KPIs regress.
          - **Blue-green**: run old (blue) and new (green) environments side by side and switch all traffic at
            once - instant rollback by switching back.
          - **A/B test**: split traffic deliberately to measure business impact with statistical rigour.
          """,
          ["Batch vs real-time trade-offs", "Shadow", "Canary", "Blue-green", "A/B for impact"],
          "Pick the strategy you'd use for a specific use case and explain why.",
          ["How would you roll back a bad model?", "What metrics gate a canary?"], hot=True),
        T("intermediate", "What is the difference between data drift and concept drift? How do you monitor them?",
          """
          - **Data (covariate) drift**: the distribution of inputs changes - e.g. a new customer segment after a
            marketing campaign - while the input-output relationship may be unchanged.
          - **Concept drift**: the relationship between inputs and target changes - e.g. after a pricing change,
            the same usage pattern no longer predicts churn the same way.
          - Also watch **label/prior drift** (the base rate changes) and **upstream data issues** (schema changes,
            broken pipelines) that look like drift.

          Monitoring:
          - Feature distributions vs a training baseline: PSI, KS test, Jensen-Shannon distance; null rates.
          - Prediction distribution shifts (cheap, available immediately).
          - Performance metrics once ground truth arrives (often delayed by weeks for churn/credit).
          - Business KPIs and segment-level breakdowns.
          Triggers: alerts lead to investigation, then retraining (scheduled or triggered) with champion-challenger
          validation before promotion.
          """,
          ["Definitions with examples", "Upstream data issues", "Drift metrics", "Delayed labels", "Retraining loop"],
          "Distinguish clearly with one example each - interviewers often probe the difference.",
          ["How do you monitor when labels arrive 90 days later?", "How do you decide when to retrain?"]),
        T("advanced", "Design a CI/CD (and continuous training) pipeline for an ML model.",
          """
          **CI (on every pull request)**
          - Linting, type checks, unit tests for feature code and data transformations.
          - Data validation tests on a sample (schema, ranges, nulls - e.g. Great Expectations).
          - A fast training run on sample data to catch breakages.

          **Continuous training (scheduled or triggered by drift/new data)**
          - Pipeline (Airflow/Kubeflow/Azure ML/SageMaker Pipelines): extract -> validate -> features -> train ->
            evaluate.
          - **Quality gates**: the candidate must beat the production model on a held-out/out-of-time set, pass
            fairness and slice checks, and stay within latency/size limits.
          - Log everything to the experiment tracker; register the candidate with lineage (data version, commit).

          **CD**
          - Build and scan the container image; deploy to staging; run integration and load tests.
          - Shadow or canary in production with automated rollback on SLO/metric regressions.
          - Promote in the registry; keep the previous version ready for instant rollback.

          Infrastructure as code and environment parity (dev/staging/prod) keep it reproducible; approvals can be
          required for regulated use cases.
          """,
          ["CI tests incl. data validation", "CT with evaluation gates", "Registry & lineage", "Staged CD with rollback",
           "IaC/governance"],
          "Draw it as three lanes (CI, CT, CD) - clear structure scores well in design questions.",
          ["What tests would you write for a feature pipeline?", "How do you prevent a worse model being promoted?"],
          hot=True),
        T("advanced", "What is training-serving skew, and how do feature stores help prevent it?",
          """
          **Training-serving skew** is a difference between how features are computed during training and at
          inference, causing silent accuracy loss. Causes: separate code paths (SQL for training, Java for serving),
          different data freshness, time-travel leakage in training data, or different handling of missing values.

          A **feature store** (Feast, Databricks/Tecton/SageMaker/Vertex feature stores) helps by:
          - defining each feature **once** and materialising it to an **offline store** (for training) and an
            **online store** (low-latency serving) from the same logic;
          - **point-in-time correct joins** for training data, so each label only sees feature values available at
            that moment (prevents leakage);
          - reuse, discovery, versioning and monitoring of features across teams.

          Even without a feature store: share one feature library between training and serving, log the features
          used at serving time and compare their distribution with training data.
          """,
          ["Definition and causes", "Single definition -> offline + online", "Point-in-time joins", "Alternatives"],
          "If you've debugged skew before, tell that story - it's a strong signal of production experience.",
          ["What is point-in-time correctness?", "When is a feature store overkill?"]),
    ],
    "practical": [
        P("beginner", "Write a production-ready Dockerfile for a Python model-serving API.",
          """
          Project layout: `requirements.txt`, `app/main.py` (FastAPI app object `app`), `model/model.joblib`.
          The service must listen on port 8000.
          """,
          ["Slim, pinned base image.", "Install dependencies before copying code (layer caching).",
           "Run as a non-root user.", "Add a health check and a production server command."],
          "Copying requirements first means code changes don't invalidate the dependency layer. A non-root user and "
          "no secrets in the image improve security; uvicorn workers serve concurrent requests.",
          """
          FROM python:3.12-slim
          WORKDIR /app
          ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

          COPY requirements.txt .
          RUN pip install --no-cache-dir -r requirements.txt

          COPY app/ ./app/
          COPY model/ ./model/

          RUN useradd --create-home appuser
          USER appuser

          EXPOSE 8000
          CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
          """, "dockerfile",
          "Build time dominated by dependency installation (cached after the first build).",
          ["Large model files (pull from a registry/object storage at start-up instead)", "Native dependencies "
           "needing build tools (multi-stage build)", "Secrets (inject at runtime)"],
          "Explain the reason for each line - layer caching and non-root are what interviewers look for.",
          ["How would you shrink this image?", "How do you pass secrets at runtime?"], hot=True),
        P("intermediate", "Serve a trained scikit-learn model with FastAPI, with input validation and a health check.",
          """
          A pipeline saved with joblib at `model/model.joblib` expects columns `tenure_months` (int),
          `monthly_charges` (float), `plan` (str). Return churn probability.
          """,
          ["Load the model once at start-up.", "Validate inputs with Pydantic models.",
           "Convert to a DataFrame with the training column order.", "Expose /health and /predict; batch support."],
          "Loading once avoids per-request latency; Pydantic rejects malformed inputs with clear 422 errors; "
          "accepting a list enables batching for throughput.",
          """
          from contextlib import asynccontextmanager

          import joblib
          import pandas as pd
          from fastapi import FastAPI
          from pydantic import BaseModel, Field

          state = {}

          @asynccontextmanager
          async def lifespan(app: FastAPI):
              state["model"] = joblib.load("model/model.joblib")
              yield

          app = FastAPI(lifespan=lifespan)

          class Customer(BaseModel):
              tenure_months: int = Field(ge=0, le=600)
              monthly_charges: float = Field(ge=0)
              plan: str

          @app.get("/health")
          def health():
              return {"status": "ok", "model_loaded": "model" in state}

          @app.post("/predict")
          def predict(customers: list[Customer]):
              df = pd.DataFrame([c.model_dump() for c in customers])
              probs = state["model"].predict_proba(df)[:, 1]
              return [{"churn_probability": round(float(p), 4)} for p in probs]
          """, "python",
          "Per request: O(batch size x model inference cost).",
          ["Unknown categories in `plan`", "Empty batch", "Model file missing at start-up"],
          "Mention logging inputs/predictions for monitoring and versioning the model in the response.",
          ["How would you scale this to 1,000 rps?", "How would you add the model version to responses?"], hot=True),
        P("advanced", "Implement the Population Stability Index (PSI) to detect feature drift.",
          """
          `expected`: feature values from the training set; `actual`: values from last week's production traffic.
          Use 10 bins based on the training distribution's quantiles.
          """,
          ["Create bin edges from training-data quantiles.", "Compute the share of each sample per bin.",
           "Avoid zero shares with a small epsilon.", "PSI = sum((a - e) * ln(a / e))."],
          "Quantile bins on the baseline give equally populated reference bins. The epsilon prevents division by "
          "zero and log(0) for empty bins.",
          """
          import numpy as np

          def psi(expected, actual, bins=10, eps=1e-6):
              expected, actual = np.asarray(expected, float), np.asarray(actual, float)
              edges = np.unique(np.quantile(expected, np.linspace(0, 1, bins + 1)))
              edges[0], edges[-1] = -np.inf, np.inf
              e_share = np.histogram(expected, edges)[0] / len(expected)
              a_share = np.histogram(actual, edges)[0] / len(actual)
              e_share, a_share = np.clip(e_share, eps, None), np.clip(a_share, eps, None)
              return float(np.sum((a_share - e_share) * np.log(a_share / e_share)))

          rng = np.random.default_rng(0)
          train = rng.normal(50, 10, 10_000)
          prod = rng.normal(55, 12, 5_000)          # shifted distribution
          print(round(psi(train, prod), 3))         # > 0.1 suggests a meaningful shift
          """, "python",
          "O(n log n) for quantiles plus O(n) for histograms.",
          ["Categorical features (use category shares instead of bins)", "Many identical values collapsing bins",
           "Very small production samples"],
          "Quote the rule-of-thumb thresholds and say you'd tune them per feature.",
          ["How would you monitor categorical drift?", "PSI vs KS test?"]),
    ],
    "scenario": [
        S("beginner", """
          Your model scores fine in your notebook, but the same model throws errors and gives different predictions
          when the engineering team deploys it on their server.
          """,
          "How do you resolve this and stop it happening again?",
          [("Reproduce", "Get the exact error, inputs and environment details from production."),
           ("Compare environments", "Python and library versions, OS, preprocessing code, feature order."),
           ("Package properly", "Pin dependencies, ship preprocessing + model as one pipeline artefact."),
           ("Containerise", "Build one Docker image used in testing and production."),
           ("Add tests", "Golden input/output test in CI to catch differences.")],
          """
          "Different predictions" plus errors usually means **environment or preprocessing mismatch**. I'd collect a
          few failing inputs and compare: library versions (a scikit-learn upgrade can change pickled models),
          feature order, and whether the server re-implemented preprocessing differently.

          The fix is to make the artefact self-contained: save the **whole scikit-learn Pipeline** (preprocessing +
          model) rather than just the estimator, pin exact dependency versions, and package everything in a
          **Docker image** that is the same in staging and production.

          To prevent recurrence I'd add a CI test that loads the artefact and checks predictions on a golden set
          of 100 inputs against expected outputs, and log the model version with every prediction.
          """,
          ["Systematic environment comparison", "Pipeline-as-artefact", "Docker for parity", "Golden tests in CI"],
          ["Blaming the engineering team", "Manually patching the server", "No regression test"],
          ["What should a model artefact include?", "How do you version models?"]),
        S("intermediate", """
          Six months after launch, the business notices your credit-risk model approves more customers who later
          default. Labels (default or not) only become available 90 days after approval.
          """,
          "How do you detect such issues earlier and respond now?",
          [("Investigate now", "Compare recent applicant features and score distributions with training."),
           ("Use leading indicators", "Early delinquency (30 days past due) as a proxy label."),
           ("Check for causes", "Policy, product or macro changes; upstream data changes."),
           ("Respond", "Adjust thresholds as a stopgap; retrain with recent data; champion-challenger."),
           ("Monitor continuously", "Drift dashboards, proxy-label performance, alerting, retrain cadence.")],
          """
          Because true labels lag by 90 days, I'd lean on signals available sooner. First, compare the input
          distributions of recent applicants with the training data (PSI per feature) and the **score
          distribution** - a new marketing channel, for example, may have brought in a different population.

          Second, use **leading indicators** like 30-days-past-due as a proxy label to evaluate recent cohorts. Third,
          check external causes: interest-rate changes, a new product, or an upstream change in a bureau-data field.

          Short term, with risk stakeholders, I'd tighten the approval threshold for affected segments. Then retrain
          on recent data, validate out-of-time, and run the new model as a challenger in shadow mode before
          promoting it. Going forward: monitoring dashboards for drift and proxy-label performance with alerts, and a
          scheduled review of model performance as labels mature.
          """,
          ["Handles delayed labels with proxies", "Drift analysis on inputs and scores", "Considers external causes",
           "Safe remediation & ongoing monitoring"],
          ["Waiting 90 days for labels", "Retraining blindly on drifted data", "Ignoring regulatory/risk stakeholders"],
          ["How would you set alert thresholds?", "What is champion-challenger?"], hot=True),
        S("advanced", """
          You must replace the recommendation model behind an API that serves 2,000 requests per second with a
          p99 latency SLA of 100 ms. The new model is more accurate offline but 3x more expensive to run.
          """,
          "How do you roll it out safely?",
          [("Load-test", "Benchmark latency/throughput at target load; optimise (batching, quantisation, caching)."),
           ("Capacity plan", "Right-size instances/GPUs and autoscaling; estimate cost."),
           ("Shadow", "Mirror live traffic; compare latency and predictions with no user impact."),
           ("Canary + A/B", "Ramp 1% -> 10% -> 50% with automatic rollback; measure business metrics."),
           ("Decide", "Ship if uplift justifies the cost; keep fallback to the old model.")],
          """
          First, prove it can meet the SLA: load-test the new model at 2,000+ rps and measure p99. If it's too slow,
          optimise - dynamic batching, ONNX/TensorRT, quantisation, caching frequent requests, or distilling to a
          smaller model. Then capacity-plan: number of replicas, autoscaling rules and the monthly cost.

          Rollout: deploy in **shadow** mode, mirroring live traffic to compare latency and prediction
          distributions without affecting users. Then a **canary** at 1%, 10%, 50%, with automated rollback if p99
          latency, error rate or click-through regress. At meaningful traffic I'd run it as an **A/B test** to
          measure the real uplift in CTR or revenue per session.

          The decision is economic: if the uplift in revenue exceeds the 3x serving cost, ship it; otherwise use it
          only for high-value traffic or distil it. A circuit breaker falls back to the old model if latency spikes.
          """,
          ["Latency/throughput validation before rollout", "Cost awareness", "Shadow -> canary -> A/B",
           "Automatic rollback & fallback"],
          ["Deploying straight to 100%", "Ignoring the cost increase", "Judging only by offline metrics"],
          ["How does dynamic batching work?", "What metrics trigger an automatic rollback?"]),
    ],
    "quiz": [
        Q("beginner", "What is a Docker container?",
          ["A blueprint used to build images", "A running instance of a Docker image", "A virtual machine with its "
           "own kernel", "A Python virtual environment"], 1,
          "Images are templates; containers are isolated running instances of them sharing the host kernel.",
          ["That describes a Dockerfile/image.", "Correct.", "Containers share the host kernel.",
           "Virtual environments only isolate Python packages."],
          "Contrast containers with VMs in one sentence.", hot=True),
        Q("beginner", "MLflow is mainly used for:",
          ["Data labelling", "Experiment tracking and model registry", "Container orchestration", "Data visualisation"],
          1,
          "MLflow logs parameters, metrics and artefacts and manages model versions and stages.",
          ["Not its purpose.", "Correct.", "That's Kubernetes.", "Not its purpose."],
          "Mention how you used tracking to compare experiments."),
        Q("intermediate", "In which rollout does the new model receive a copy of live traffic while its predictions "
          "are not served to users?",
          ["Canary", "Blue-green", "Shadow", "Rolling update"], 2,
          "Shadow deployments mirror traffic for comparison with zero user impact.",
          ["Canary serves real users a small share.", "Blue-green switches all traffic.", "Correct.",
           "Rolling updates replace instances gradually and serve users."],
          "Shadow is ideal for validating latency and prediction distributions first.", hot=True),
        Q("intermediate", "Input feature distributions change but the input-to-target relationship stays the same. "
          "This is:",
          ["Concept drift", "Data (covariate) drift", "Label leakage", "Overfitting"], 1,
          "Covariate/data drift is a change in P(X); concept drift is a change in P(y|X).",
          ["That changes P(y|X).", "Correct.", "Unrelated.", "A training issue."],
          "Give an example of each to show understanding."),
        Q("advanced", "Which practice best prevents training-serving skew?",
          ["Retraining more often", "Using the same feature definitions/code (e.g. a feature store) for training and "
           "serving", "Increasing model complexity", "Lowering the decision threshold"], 1,
          "Skew comes from computing features differently in two places; a single definition removes the mismatch.",
          ["Doesn't fix mismatched code paths.", "Correct.", "Unrelated.", "Unrelated."],
          "Mention point-in-time correct training data as a related safeguard.", hot=True),
    ],
}
