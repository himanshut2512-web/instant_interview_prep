"""Content model for a prep kit + normalisation helpers.

Everything the agent (or the offline knowledge base) produces is passed
through these models so the frontend can rely on a stable shape: missing
fields get defaults, levels are canonicalised, malformed items are dropped.
"""

from __future__ import annotations

import re
import uuid
from typing import Annotated, Any, Iterable

from pydantic import BaseModel, BeforeValidator, ConfigDict, ValidationError, field_validator, model_validator

LEVELS = ("beginner", "intermediate", "advanced")
QUESTION_SECTIONS = ("theory", "practical", "scenario", "quiz")
ALL_SECTIONS = ("revision", *QUESTION_SECTIONS)
PRIORITIES = ("high", "medium", "low")

_LEVEL_ALIASES = {
    "easy": "beginner", "basic": "beginner", "basics": "beginner", "fresher": "beginner",
    "junior": "beginner", "entry": "beginner", "foundation": "beginner", "fundamental": "beginner",
    "medium": "intermediate", "moderate": "intermediate", "mid": "intermediate", "intermediate-level": "intermediate",
    "hard": "advanced", "expert": "advanced", "senior": "advanced", "difficult": "advanced", "tough": "advanced",
}

_ID_PREFIX = {"theory": "th", "practical": "pr", "scenario": "sc", "quiz": "qz", "revision": "rv", "topic": "tp"}


def new_id(section: str) -> str:
    return f"{_ID_PREFIX.get(section, section[:2])}-{uuid.uuid4().hex[:10]}"


def norm_level(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in LEVELS:
        return text
    if text in _LEVEL_ALIASES:
        return _LEVEL_ALIASES[text]
    for level in LEVELS:
        if level in text:
            return level
    return "intermediate"


def norm_priority(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in PRIORITIES:
        return text
    if text in ("critical", "must", "must-know", "very high", "top"):
        return "high"
    if text in ("nice", "optional", "nice-to-have", "minor"):
        return "low"
    return "medium"


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return "\n".join(_text(v) for v in value if v is not None).strip()
    return str(value).strip()


def _str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [line for line in re.split(r"\n+", value)]
    out = []
    for item in value:
        if isinstance(item, dict):
            item = " — ".join(str(v) for v in item.values() if v)
        text = _text(item).lstrip("-•* ").strip()
        if text:
            out.append(text)
    return out


def _positional_list(value: Any) -> list[str]:
    """Like _str_list but keeps empty entries so positions (e.g. MCQ options) stay aligned."""
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    return [_text(item) for item in value]


Text = Annotated[str, BeforeValidator(_text)]
StrList = Annotated[list[str], BeforeValidator(_str_list)]
PosList = Annotated[list[str], BeforeValidator(_positional_list)]


class Loose(BaseModel):
    model_config = ConfigDict(extra="ignore")


# ---------------------------------------------------------------- building blocks
class CodeSnippet(Loose):
    language: Text = ""
    code: Text = ""

    @model_validator(mode="before")
    @classmethod
    def _from_string(cls, value: Any) -> Any:
        if value is None:
            return {}
        if isinstance(value, str):
            return {"language": "", "code": value}
        return value


class KeyConcept(Loose):
    term: Text = ""
    explanation: Text = ""

    @model_validator(mode="before")
    @classmethod
    def _from_string(cls, value: Any) -> Any:
        if isinstance(value, str):
            term, _, rest = value.partition(":")
            return {"term": term, "explanation": rest} if rest else {"term": value, "explanation": ""}
        return value


class ApproachStep(Loose):
    step: Text = ""
    detail: Text = ""

    @model_validator(mode="before")
    @classmethod
    def _from_string(cls, value: Any) -> Any:
        if isinstance(value, str):
            step, _, rest = value.partition(":")
            return {"step": step, "detail": rest} if rest else {"step": value, "detail": ""}
        return value


class Source(Loose):
    title: Text = ""
    url: Text = ""


# ------------------------------------------------------------------ question items
class BaseItem(Loose):
    id: Text = ""
    topic: Text = "General"
    level: Text = "intermediate"
    hot: bool = False
    hot_reason: Text = ""
    question: Text
    origin: Text = "ai"

    @field_validator("level", mode="before")
    @classmethod
    def _level(cls, value: Any) -> str:
        return norm_level(value)

    @field_validator("hot", mode="before")
    @classmethod
    def _hot(cls, value: Any) -> bool:
        if isinstance(value, str):
            return value.strip().lower() in ("true", "yes", "1", "hot")
        return bool(value)

    @field_validator("question")
    @classmethod
    def _question(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("question too short")
        return value

    @field_validator("topic")
    @classmethod
    def _topic(cls, value: str) -> str:
        return value or "General"


class TheoryItem(BaseItem):
    answer_md: Text = ""
    key_points: StrList = []
    interview_tip: Text = ""
    follow_ups: StrList = []


class PracticalItem(BaseItem):
    context: Text = ""
    approach: StrList = []
    solution_md: Text = ""
    code: CodeSnippet = CodeSnippet()
    complexity: Text = ""
    edge_cases: StrList = []
    interview_tip: Text = ""
    follow_ups: StrList = []


class ScenarioItem(BaseItem):
    scenario: Text = ""
    approach_steps: list[ApproachStep] = []
    model_answer_md: Text = ""
    what_interviewer_looks_for: StrList = []
    mistakes_to_avoid: StrList = []
    follow_ups: StrList = []


class QuizItem(BaseItem):
    options: PosList
    correct_index: int
    explanation: Text = ""
    option_explanations: PosList = []
    interview_tip: Text = ""

    @model_validator(mode="after")
    def _check_options(self) -> "QuizItem":
        if not 2 <= len(self.options) <= 6 or any(not o for o in self.options):
            raise ValueError("an MCQ needs 2-6 non-empty options")
        if len({o.lower() for o in self.options}) != len(self.options):
            raise ValueError("duplicate MCQ options")
        if not 0 <= self.correct_index < len(self.options):
            raise ValueError("correct_index out of range")
        size = len(self.options)
        self.option_explanations = (self.option_explanations + [""] * size)[:size]
        return self


class RevisionNote(Loose):
    id: Text = ""
    topic: Text
    priority: Text = "medium"
    summary: Text = ""
    why_it_matters: Text = ""
    key_concepts: list[KeyConcept] = []
    explanation_md: Text = ""
    code_example: CodeSnippet = CodeSnippet()
    pitfalls: StrList = []
    interview_tips: StrList = []
    cheat_sheet: StrList = []
    likely_questions: StrList = []
    origin: Text = "ai"

    @field_validator("priority", mode="before")
    @classmethod
    def _priority(cls, value: Any) -> str:
        return norm_priority(value)

    @field_validator("topic")
    @classmethod
    def _topic(cls, value: str) -> str:
        if not value:
            raise ValueError("revision note needs a topic")
        return value


SECTION_MODELS: dict[str, type[Loose]] = {
    "theory": TheoryItem,
    "practical": PracticalItem,
    "scenario": ScenarioItem,
    "quiz": QuizItem,
    "revision": RevisionNote,
}


# ---------------------------------------------------------------- blueprint parts
class Topic(Loose):
    id: Text = ""
    name: Text
    priority: Text = "medium"
    weight: int = 50
    why: Text = ""
    subtopics: StrList = []

    @field_validator("priority", mode="before")
    @classmethod
    def _priority(cls, value: Any) -> str:
        return norm_priority(value)

    @field_validator("weight", mode="before")
    @classmethod
    def _weight(cls, value: Any) -> int:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return 50
        if 0 < number <= 1:  # model answered with a fraction
            number *= 100
        return int(max(1, min(100, round(number))))


class InterviewRound(Loose):
    name: Text = ""
    format: Text = ""
    what_they_test: Text = ""
    tips: Text = ""


class ReportedQuestion(Loose):
    question: Text = ""
    round: Text = ""
    source: Text = ""

    @model_validator(mode="before")
    @classmethod
    def _from_string(cls, value: Any) -> Any:
        return {"question": value} if isinstance(value, str) else value


class ResumeProbe(Loose):
    item: Text = ""
    likely_questions: StrList = []


class Profile(Loose):
    candidate_name: Text = ""
    current_title: Text = ""
    target_role: Text = ""
    seniority: Text = ""
    summary: Text = ""
    elevator_pitch: Text = ""
    strengths: StrList = []
    gaps: StrList = []
    matched_skills: StrList = []
    missing_skills: StrList = []
    resume_probes: list[ResumeProbe] = []


class CompanyIntel(Loose):
    name: Text = ""
    overview: Text = ""
    hiring_focus: Text = ""
    interview_rounds: list[InterviewRound] = []
    focus_areas: StrList = []
    culture_values: StrList = []
    insider_tips: StrList = []
    reported_questions: list[ReportedQuestion] = []
    questions_to_ask_them: StrList = []
    research_mode: Text = "model_knowledge"
    research_md: Text = ""
    sources: list[Source] = []


class StudyBlock(Loose):
    title: Text = ""
    focus: Text = ""
    tasks: StrList = []


# ------------------------------------------------------------------- utilities
def normalize_items(section: str, raw_items: Iterable[Any], origin: str = "ai") -> list[dict[str, Any]]:
    """Validate raw dicts for a section; drop broken ones; assign ids."""
    model = SECTION_MODELS[section]
    out: list[dict[str, Any]] = []
    for raw in raw_items or []:
        if not isinstance(raw, dict):
            continue
        try:
            item = model.model_validate(raw)
        except ValidationError:
            continue
        data = item.model_dump()
        data["id"] = data.get("id") or new_id(section)
        data["origin"] = data.get("origin") if raw.get("origin") else origin
        out.append(data)
    return out


def normalize_topics(raw_topics: Iterable[Any]) -> list[dict[str, Any]]:
    topics: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in raw_topics or []:
        if isinstance(raw, str):
            raw = {"name": raw}
        try:
            topic = Topic.model_validate(raw)
        except ValidationError:
            continue
        key = topic.name.lower()
        if not topic.name or key in seen:
            continue
        seen.add(key)
        data = topic.model_dump()
        data["id"] = data["id"] or new_id("topic")
        topics.append(data)
    return topics


_WORD = re.compile(r"[a-z0-9+#]+")


def _signature(text: str) -> frozenset[str]:
    words = _WORD.findall(text.lower())
    stop = {"the", "a", "an", "of", "in", "to", "and", "or", "is", "what", "how", "why", "you", "your", "for",
            "with", "do", "does", "are", "be", "on", "it", "between", "explain", "describe", "would", "can"}
    return frozenset(w for w in words if w not in stop)


def is_duplicate(question: str, seen: list[frozenset[str]], threshold: float = 0.8) -> bool:
    sig = _signature(question)
    if not sig:
        return False
    for other in seen:
        if not other:
            continue
        overlap = len(sig & other) / len(sig | other)
        if overlap >= threshold:
            return True
    return False


def dedupe(existing: list[dict[str, Any]], new_items: list[dict[str, Any]], key: str = "question") -> list[dict[str, Any]]:
    """Return the items from new_items that are not near-duplicates of existing ones (or each other)."""
    seen = [_signature(str(item.get(key, ""))) for item in existing]
    kept = []
    for item in new_items:
        text = str(item.get(key, ""))
        if is_duplicate(text, seen):
            continue
        seen.append(_signature(text))
        kept.append(item)
    return kept


def empty_result() -> dict[str, Any]:
    return {
        "profile": Profile().model_dump(),
        "company": CompanyIntel().model_dump(),
        "topics": [],
        "study_plan": [],
        "revision": [],
        "theory": [],
        "practical": [],
        "scenario": [],
        "quiz": [],
    }


def result_counts(result: dict[str, Any] | None) -> dict[str, int]:
    result = result or {}
    counts = {section: len(result.get(section) or []) for section in ALL_SECTIONS}
    counts["topics"] = len(result.get("topics") or [])
    counts["questions"] = sum(counts[s] for s in QUESTION_SECTIONS)
    counts["hot"] = sum(1 for s in QUESTION_SECTIONS for item in (result.get(s) or []) if item.get("hot"))
    return counts
