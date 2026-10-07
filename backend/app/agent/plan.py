"""Inputs of a prep run and how much content each depth produces."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from ..models import LEVELS

DEPTHS: dict[str, dict[str, int]] = {
    # theory+practical+scenario >= 35 and quiz >= 15 so even "quick" has 50+ questions
    "quick": {"topics": 8, "theory": 15, "practical": 10, "scenario": 10, "quiz": 15, "searches": 6, "fetches": 3},
    "standard": {"topics": 10, "theory": 24, "practical": 15, "scenario": 15, "quiz": 25, "searches": 10, "fetches": 5},
    "deep": {"topics": 14, "theory": 36, "practical": 21, "scenario": 21, "quiz": 36, "searches": 14, "fetches": 8},
}
DEFAULT_DEPTH = "standard"

# Upper bound of items requested from the model in one call (keeps calls short & parallel).
MAX_PER_CALL = {"theory": 12, "practical": 8, "scenario": 8, "quiz": 13}
REVISION_TOPICS_PER_CALL = 4


def seniority_band(years: float) -> str:
    if years < 1:
        return "Fresher / entry level (0-1 yrs)"
    if years < 3:
        return "Junior (1-3 yrs)"
    if years < 6:
        return "Mid-level (3-6 yrs)"
    if years < 10:
        return "Senior (6-10 yrs)"
    return "Lead / principal (10+ yrs)"


def level_mix(years: float) -> tuple[float, float, float]:
    """Share of beginner / intermediate / advanced questions for an experience level."""
    if years < 2:
        return (0.4, 0.4, 0.2)
    if years < 5:
        return (0.3, 0.45, 0.25)
    if years < 9:
        return (0.2, 0.4, 0.4)
    return (0.15, 0.35, 0.5)


def split_by_level(total: int, years: float) -> dict[str, int]:
    """Largest-remainder split of `total` questions across the three levels."""
    if total <= 0:
        return {level: 0 for level in LEVELS}
    raw = [total * share for share in level_mix(years)]
    counts = [math.floor(r) for r in raw]
    by_remainder = sorted(range(3), key=lambda i: raw[i] - counts[i], reverse=True)
    for i in by_remainder[: total - sum(counts)]:
        counts[i] += 1
    if total >= 3:  # every level gets at least one question
        for i in range(3):
            if counts[i] == 0:
                donor = max(range(3), key=lambda k: counts[k])
                counts[donor] -= 1
                counts[i] += 1
    return dict(zip(LEVELS, counts))


def chunk_count(count: int, max_per_call: int) -> list[int]:
    """Split `count` into near-equal chunks no larger than max_per_call."""
    if count <= 0:
        return []
    parts = math.ceil(count / max_per_call)
    base, extra = divmod(count, parts)
    return [base + (1 if i < extra else 0) for i in range(parts)]


@dataclass
class PrepContext:
    session_id: str
    company: str
    role: str
    years: float
    depth: str
    resume_text: str
    jd_text: str
    extra_notes: str = ""
    extra_files_text: str = ""
    targets: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.depth not in DEPTHS:
            self.depth = DEFAULT_DEPTH
        self.targets = dict(DEPTHS[self.depth])

    @property
    def band(self) -> str:
        return seniority_band(self.years)

    @property
    def years_label(self) -> str:
        years = int(self.years) if float(self.years).is_integer() else self.years
        return f"{years} year{'s' if self.years != 1 else ''}"

    @property
    def role_or_default(self) -> str:
        return self.role or "the role described in the job description"

    @property
    def additional_context(self) -> str:
        parts = [p for p in (self.extra_notes.strip(), self.extra_files_text.strip()) if p]
        return "\n\n".join(parts)

    @classmethod
    def from_session(cls, session: dict[str, Any]) -> "PrepContext":
        inputs = session.get("inputs") or {}
        return cls(
            session_id=session["id"],
            company=session.get("company") or "",
            role=session.get("role") or "",
            years=float(session.get("years") or 0),
            depth=session.get("depth") or DEFAULT_DEPTH,
            resume_text=inputs.get("resume_text") or "",
            jd_text=inputs.get("jd_text") or "",
            extra_notes=inputs.get("extra_notes") or "",
            extra_files_text=inputs.get("extra_files_text") or "",
        )
