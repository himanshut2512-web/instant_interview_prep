"""Keyword lexicon used to read skills out of resumes / JDs (offline mode + search hints)."""

from __future__ import annotations

import re
from collections import Counter
from functools import lru_cache

# canonical skill -> aliases (matched case-insensitively on word boundaries)
SKILL_LEXICON: dict[str, tuple[str, ...]] = {
    "Python": ("python",),
    "SQL": ("sql", "mysql", "postgresql", "postgres", "t-sql", "pl/sql", "sql server", "sqlite"),
    "Pandas": ("pandas",),
    "NumPy": ("numpy",),
    "Scikit-learn": ("scikit-learn", "sklearn", "scikit learn"),
    "Statistics": ("statistics", "statistical", "hypothesis testing", "probability", "inferential"),
    "A/B Testing": ("a/b test", "a/b testing", "ab testing", "experimentation", "experiment design", "causal inference"),
    "Machine Learning": ("machine learning", "ml", "ml models", "predictive model", "predictive modelling",
                         "predictive modeling", "supervised learning", "unsupervised learning", "classification",
                         "regression models", "clustering"),
    "XGBoost": ("xgboost", "lightgbm", "catboost", "gradient boosting"),
    "Time Series": ("time series", "time-series", "forecasting", "arima", "prophet"),
    "Deep Learning": ("deep learning", "neural network", "neural networks", "cnn", "rnn", "lstm"),
    "PyTorch": ("pytorch", "torch"),
    "TensorFlow": ("tensorflow", "keras"),
    "Computer Vision": ("computer vision", "image classification", "object detection", "opencv", "yolo"),
    "NLP": ("nlp", "natural language processing", "text mining", "text analytics", "named entity", "sentiment"),
    "Generative AI": ("generative ai", "genai", "gen ai", "llm", "llms", "large language model",
                      "large language models", "gpt", "prompt engineering", "fine-tuning", "fine tuning", "openai",
                      "azure openai", "chatgpt", "claude", "anthropic", "gemini", "llama"),
    "RAG": ("rag", "retrieval augmented", "retrieval-augmented", "vector database", "vector store", "embeddings",
            "langchain", "llamaindex", "faiss", "pinecone"),
    "AI Agents": ("ai agents", "agentic", "multi-agent", "tool calling", "function calling", "mcp"),
    "Spark": ("spark", "pyspark", "spark sql", "databricks"),
    "Hadoop": ("hadoop", "hive", "hdfs", "mapreduce"),
    "Kafka": ("kafka", "streaming data", "event streaming", "kinesis"),
    "Airflow": ("airflow", "orchestration", "prefect", "dagster"),
    "ETL": ("etl", "elt", "data pipeline", "data pipelines", "data ingestion"),
    "Data Warehousing": ("data warehouse", "data warehousing", "snowflake", "redshift", "bigquery", "synapse",
                         "star schema", "dimensional modelling", "dimensional modeling", "data modeling",
                         "data modelling", "lakehouse", "delta lake"),
    "dbt": ("dbt",),
    "AWS": ("aws", "amazon web services", "sagemaker", "ec2", "s3", "aws lambda", "aws glue", "emr"),
    "Azure": ("azure", "azure ml", "azure data factory", "adf"),
    "GCP": ("gcp", "google cloud", "vertex ai"),
    "Docker": ("docker", "containers", "containerization", "containerisation"),
    "Kubernetes": ("kubernetes", "k8s", "aks", "eks", "gke"),
    "MLOps": ("mlops", "mlflow", "kubeflow", "model deployment", "model monitoring", "model registry",
              "feature store", "ml pipelines"),
    "CI/CD": ("ci/cd", "cicd", "jenkins", "github actions", "gitlab ci", "azure devops"),
    "Power BI": ("power bi", "powerbi", "dax"),
    "Tableau": ("tableau",),
    "Excel": ("excel", "vba", "spreadsheets"),
    "Data Visualization": ("data visualization", "data visualisation", "dashboard", "dashboards", "reporting",
                           "storytelling with data", "looker"),
    "Data Structures & Algorithms": ("data structures", "data structures and algorithms", "dsa", "leetcode",
                                     "competitive programming", "coding rounds"),
    "System Design": ("system design", "distributed systems", "scalability", "scalable systems", "microservices",
                      "high availability", "low latency", "architecture"),
    "Java": ("java", "spring boot", "spring"),
    "JavaScript": ("javascript", "typescript", "node.js", "nodejs", "react", "angular"),
    "REST APIs": ("rest api", "rest apis", "restful", "fastapi", "flask", "django", "api development", "graphql"),
    "Git": ("git", "github", "gitlab", "version control"),
    "Linux": ("linux", "shell scripting", "bash"),
    "Stakeholder Management": ("stakeholder", "stakeholders", "client-facing", "client facing",
                               "business stakeholders", "senior leadership"),
    "Communication": ("communication", "presentation", "storytelling"),
    "Leadership": ("mentor", "mentoring", "mentored", "leadership", "team lead", "lead a team", "people management"),
    "Consulting": ("consulting", "consultant", "client engagements", "problem framing", "business problems"),
    "Product Analytics": ("product analytics", "funnel", "retention", "kpi", "kpis", "metrics", "north star"),
}


# Having one skill implies the broader one (XGBoost experience is machine-learning experience).
IMPLIES: dict[str, tuple[str, ...]] = {
    "XGBoost": ("Machine Learning",),
    "Scikit-learn": ("Machine Learning",),
    "Time Series": ("Machine Learning",),
    "Deep Learning": ("Machine Learning",),
    "NLP": ("Machine Learning",),
    "Computer Vision": ("Deep Learning", "Machine Learning"),
    "PyTorch": ("Deep Learning", "Machine Learning"),
    "TensorFlow": ("Deep Learning", "Machine Learning"),
    "RAG": ("Generative AI", "NLP"),
    "AI Agents": ("Generative AI",),
    "Generative AI": ("NLP",),
    "Spark": ("ETL",),
    "Airflow": ("ETL",),
    "dbt": ("ETL", "Data Warehousing"),
    "Pandas": ("Python",),
    "NumPy": ("Python",),
    "A/B Testing": ("Statistics",),
    "Kubernetes": ("Docker",),
}

# Interchangeable tools: knowing one member covers a JD that lists several.
EQUIVALENT_GROUPS: tuple[frozenset[str], ...] = (
    frozenset({"AWS", "Azure", "GCP"}),
    frozenset({"Power BI", "Tableau"}),
    frozenset({"PyTorch", "TensorFlow"}),
    frozenset({"Airflow", "dbt"}),
)

SOFT_SKILLS = frozenset({"Stakeholder Management", "Communication", "Leadership", "Consulting", "Product Analytics"})

# Broad capability areas (as opposed to concrete tools) - used to phrase pitches naturally.
AREA_SKILLS = frozenset({
    "Machine Learning", "Deep Learning", "Statistics", "A/B Testing", "Time Series", "NLP", "Generative AI", "RAG",
    "AI Agents", "Computer Vision", "ETL", "Data Warehousing", "Data Visualization", "MLOps", "System Design",
    "Data Structures & Algorithms", "REST APIs", "CI/CD",
})


def implied_by(skill: str) -> list[str]:
    """Skills whose presence implies `skill` (reverse of IMPLIES)."""
    return [src for src, targets in IMPLIES.items() if skill in targets]


@lru_cache(maxsize=None)
def _alias_pattern(alias: str) -> re.Pattern[str]:
    return re.compile(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])")


def skill_counts(text: str) -> Counter[str]:
    lowered = (text or "").lower()
    counts: Counter[str] = Counter()
    for skill, aliases in SKILL_LEXICON.items():
        hits = sum(len(_alias_pattern(alias).findall(lowered)) for alias in aliases)
        if hits:
            counts[skill] = hits
    return counts


def extract_skills(text: str) -> list[str]:
    """Skills mentioned in the text, most frequent first."""
    return [skill for skill, _ in skill_counts(text).most_common()]


def keyword_hits(text: str, keywords: tuple[str, ...] | list[str]) -> int:
    lowered = (text or "").lower()
    return sum(len(_alias_pattern(k.lower()).findall(lowered)) for k in keywords)


def distinct_hits(text: str, keywords: tuple[str, ...] | list[str]) -> int:
    """How many different keywords appear at least once."""
    lowered = (text or "").lower()
    return sum(1 for k in keywords if _alias_pattern(k.lower()).search(lowered))


def expand_skills(skills: list[str]) -> set[str]:
    """Skills plus everything they imply."""
    out = set(skills)
    for skill in skills:
        out.update(IMPLIES.get(skill, ()))
    return out


def skill_gap(jd_skills: list[str], resume_skills: list[str]) -> tuple[list[str], list[str]]:
    """(matched, missing) JD skills, honouring implications and interchangeable tools."""
    have = expand_skills(resume_skills)
    matched, missing = [], []
    for skill in jd_skills:
        if skill in have:
            matched.append(skill)
            continue
        group = next((g for g in EQUIVALENT_GROUPS if skill in g), None)
        if group and group & have:
            continue  # e.g. JD lists AWS/Azure/GCP and the resume has Azure - not a real gap
        missing.append(skill)
    return matched, missing
