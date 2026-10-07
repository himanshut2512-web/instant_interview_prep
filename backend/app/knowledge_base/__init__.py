"""Built-in interview knowledge base used when no Claude API key is configured.

Every topic module exposes TOPIC with: key, name, keywords, subtopics, a crash
revision note and theory / practical / scenario / quiz items at three levels.
"""

from __future__ import annotations

from typing import Any

from . import (
    topic_behavioral,
    topic_bi,
    topic_case_studies,
    topic_data_engineering,
    topic_deep_learning,
    topic_dsa,
    topic_genai,
    topic_ml,
    topic_mlops,
    topic_python,
    topic_sql,
    topic_statistics,
    topic_system_design,
)
from .matching import distinct_hits, keyword_hits

TOPICS: list[dict[str, Any]] = [
    m.TOPIC
    for m in (
        topic_python,
        topic_sql,
        topic_statistics,
        topic_ml,
        topic_deep_learning,
        topic_genai,
        topic_data_engineering,
        topic_mlops,
        topic_bi,
        topic_dsa,
        topic_system_design,
        topic_case_studies,
        topic_behavioral,
    )
]
TOPICS_BY_KEY = {t["key"]: t for t in TOPICS}

# Used to fill the plan when the JD/resume match too few topics.
DEFAULT_FILL_ORDER = ("python", "sql", "case_studies", "statistics", "ml", "dsa", "system_design",
                      "data_engineering", "mlops", "genai", "bi", "deep_learning")


def topic_by_name(name: str) -> dict[str, Any] | None:
    """Find a KB topic by (fuzzy) name or key."""
    wanted = (name or "").strip().lower()
    if not wanted:
        return None
    for topic in TOPICS:
        if wanted in (topic["key"], topic["name"].lower()):
            return topic
    for topic in TOPICS:
        label = topic["name"].lower()
        if wanted in label or label in wanted or any(wanted == k for k in topic["keywords"]):
            return topic
    for topic in TOPICS:
        if keyword_hits(wanted, topic["keywords"]):
            return topic
    return None


def score_topics(jd: str, resume: str, role: str = "", extra: str = "") -> list[tuple[dict[str, Any], int]]:
    """Relevance of each topic: JD matters most, then the candidate's notes, then the resume.

    Distinct keywords count more than repetitions (a JD that says "deploy" five times shouldn't outrank Python),
    and a topic whose core keyword appears in the JD gets a bonus.
    """
    target = f"{role}\n{jd}"
    scored = []
    for topic in TOPICS:
        keywords = topic["keywords"]
        score = (
            (10 if is_core_match(topic, target) else 0)
            + 3 * distinct_hits(target, keywords)
            + min(keyword_hits(target, keywords), 10)
            + 2 * distinct_hits(extra, keywords)
            + distinct_hits(resume, keywords)
        )
        scored.append((topic, score))
    return sorted(scored, key=lambda pair: pair[1], reverse=True)


def is_core_match(topic: dict[str, Any], text: str) -> bool:
    return bool(topic.get("core")) and distinct_hits(text, topic["core"]) > 0


def select_topics(jd: str, resume: str, role: str, extra: str, n: int) -> list[dict[str, Any]]:
    """Pick the n most relevant KB topics; returns [{topic, score, priority, weight}] in priority order."""
    scored = score_topics(jd, resume, role, extra)
    always = [t for t, _ in scored if t.get("always_include")]
    ranked = [(t, s) for t, s in scored if not t.get("always_include") and s > 0]
    chosen = ranked[: max(1, n - len(always))]
    keys = {t["key"] for t, _ in chosen}
    for key in DEFAULT_FILL_ORDER:
        if len(chosen) >= n - len(always):
            break
        if key not in keys:
            chosen.append((TOPICS_BY_KEY[key], 0))
            keys.add(key)
    chosen += [(t, s) for t, s in scored if t.get("always_include")]

    top = max((s for _, s in chosen), default=0) or 1
    target = f"{role}\n{jd}"
    selected = []
    for index, (topic, score) in enumerate(chosen):
        share = index / max(1, len(chosen) - 1)
        if topic.get("always_include"):
            priority = "medium"
        else:
            priority = "high" if share < 0.34 else "medium" if share < 0.7 else "low"
        weight = max(25, min(100, round(100 * score / top))) if score else 30
        if is_core_match(topic, target):  # explicitly named in the JD - never "low"
            priority = "medium" if priority == "low" else priority
            weight = max(weight, 55)
        selected.append({"topic": topic, "score": score, "priority": priority, "weight": weight})
    return selected
