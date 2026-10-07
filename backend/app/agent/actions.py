"""On-demand agent actions on an existing prep kit: generate more, evaluate an answer."""

from __future__ import annotations

from typing import Any, Callable

from ..models import QUESTION_SECTIONS, normalize_items
from . import prompts, schemas
from .llm import ClaudeLLM
from .pipeline import Job, generate_items
from .plan import PrepContext


class ActionError(ValueError):
    pass


class _NullTracker:
    """generate_items logs retries through a tracker; on-demand calls have no timeline."""

    def log(self, message: str, kind: str = "info") -> None:  # noqa: D401 - tiny shim
        pass


def _blocks(session: dict[str, Any], ctx: PrepContext, with_blueprint: bool = True) -> list[dict[str, Any]]:
    result = session.get("result") or {}
    company = result.get("company") or {}
    base = prompts.base_context(ctx, company.get("research_md", ""), company.get("research_mode", "model_knowledge"))
    blueprint = prompts.blueprint_context(result) if with_blueprint else None
    return prompts.context_blocks(base, blueprint)


def find_item(result: dict[str, Any], section: str, item_id: str) -> dict[str, Any] | None:
    for item in result.get(section) or []:
        if item.get("id") == item_id:
            return item
    return None


async def generate_more(
    session: dict[str, Any],
    *,
    section: str,
    count: int,
    level: str,
    topic: str,
    focus: str,
    llm: ClaudeLLM | None,
) -> list[dict[str, Any]]:
    result = session.get("result") or {}
    if llm is None:
        from .demo import demo_generate_more

        return demo_generate_more(session, section=section, count=count, level=level, topic=topic)

    ctx = PrepContext.from_session(session)
    blocks = _blocks(session, ctx)
    if section == "revision":
        covered = {n["topic"].lower() for n in result.get("revision") or []}
        if topic:
            topics = [topic]
        else:
            topics = [t["name"] for t in result.get("topics") or [] if t["name"].lower() not in covered][:count]
        if not topics:
            raise ActionError("Every planned topic already has notes - type a topic name to add a new one.")
        job = Job("revision", len(topics), topics=topics)
        return await generate_items(llm, ctx, blocks, job, existing=[], tracker=_NullTracker(), origin="more")

    if section not in QUESTION_SECTIONS:
        raise ActionError(f"Unknown section '{section}'.")
    existing = [str(i.get("question", ""))[:140] for i in result.get(section) or []]
    job = Job(section, count, level=level if level in ("beginner", "intermediate", "advanced") else "mixed")
    return await generate_items(
        llm,
        ctx,
        blocks,
        job,
        existing=existing,
        tracker=_NullTracker(),
        focus=focus,
        topics=[topic] if topic else None,
        origin="more",
    )


async def evaluate_answer(
    session: dict[str, Any],
    *,
    section: str,
    item: dict[str, Any],
    answer: str,
    llm: ClaudeLLM | None,
) -> dict[str, Any]:
    if llm is None:
        from .demo import demo_evaluate

        return demo_evaluate(section, item, answer)

    ctx = PrepContext.from_session(session)
    data = await llm.generate_json(
        system=prompts.COACH_SYSTEM,
        context_blocks=_blocks(session, ctx, with_blueprint=False),
        task=prompts.evaluate_task(ctx, section, item, answer),
        schema=schemas.EVALUATION,
        max_tokens=16000,
        effort="low",
    )
    return normalize_evaluation(data, engine="ai")


def normalize_evaluation(data: dict[str, Any], engine: str) -> dict[str, Any]:
    def strings(value: Any) -> list[str]:
        return [str(v).strip() for v in (value or []) if str(v).strip()]

    try:
        score = int(round(float(data.get("score", 0))))
    except (TypeError, ValueError):
        score = 0
    return {
        "score": max(0, min(10, score)),
        "verdict": str(data.get("verdict") or "").strip(),
        "strengths": strings(data.get("strengths")),
        "improvements": strings(data.get("improvements")),
        "missing_points": strings(data.get("missing_points")),
        "improved_answer_md": str(data.get("improved_answer_md") or "").strip(),
        "engine": engine,
    }


MakeLLM = Callable[[], ClaudeLLM]
