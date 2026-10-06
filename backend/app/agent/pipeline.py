"""Orchestrates one prep run.

AI mode:  parse -> web research -> blueprint (profile, company intel, topic plan)
          -> parallel generation of revision notes / theory / practical /
             scenario / quiz batches -> top-up -> done.
Demo mode: the same timeline driven by the offline knowledge base.

Sections are saved as soon as they have content so the dashboards fill up
while the agent is still working.
"""

from __future__ import annotations

import asyncio
import logging
import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Callable

import anthropic

from ..config import Settings
from ..models import (
    ALL_SECTIONS,
    QUESTION_SECTIONS,
    CompanyIntel,
    Profile,
    StudyBlock,
    normalize_items,
    normalize_topics,
)
from ..storage import Store
from . import prompts, schemas
from .llm import ClaudeLLM, LLMError, LLMRefusal, LLMTruncated
from .plan import MAX_PER_CALL, REVISION_TOPICS_PER_CALL, PrepContext, chunk_count, split_by_level
from .progress import ProgressTracker, ResultBuilder
from .research import MODE_LABELS, ResearchResult, research_company

log = logging.getLogger("prep.pipeline")

SECTION_NOUNS = {
    "revision": "revision notes",
    "theory": "theory questions",
    "practical": "practical problems",
    "scenario": "scenario questions",
    "quiz": "MCQs",
}

# Errors that retrying cannot fix.
FATAL_API_ERRORS = (anthropic.AuthenticationError, anthropic.PermissionDeniedError, anthropic.NotFoundError)


class PipelineError(RuntimeError):
    pass


@dataclass
class Job:
    section: str
    count: int
    level: str | None = None
    topics: list[str] = field(default_factory=list)

    @property
    def label(self) -> str:
        if self.section == "revision":
            return ", ".join(self.topics)
        return f"{self.level}" if self.level else "mixed"


def plan_jobs(ctx: PrepContext, topic_names: list[str]) -> list[Job]:
    """Split the work into parallel jobs, interleaved so every dashboard fills early."""
    queues: dict[str, list[Job]] = {}
    queues["revision"] = [
        Job("revision", len(topic_names[i : i + REVISION_TOPICS_PER_CALL]), topics=topic_names[i : i + REVISION_TOPICS_PER_CALL])
        for i in range(0, len(topic_names), REVISION_TOPICS_PER_CALL)
    ]
    for section in QUESTION_SECTIONS:
        jobs: list[Job] = []
        for level, count in split_by_level(ctx.targets[section], ctx.years).items():
            jobs.extend(Job(section, part, level=level) for part in chunk_count(count, MAX_PER_CALL[section]))
        # intermediate first: it is the most common level in real interviews
        jobs.sort(key=lambda j: {"intermediate": 0, "beginner": 1, "advanced": 2}.get(j.level or "", 3))
        queues[section] = jobs
    ordered: list[Job] = []
    while any(queues.values()):
        for section in ALL_SECTIONS:
            if queues.get(section):
                ordered.append(queues[section].pop(0))
    return ordered


def friendly_error(exc: BaseException, settings: Settings) -> str:
    if isinstance(exc, anthropic.AuthenticationError):
        return "Claude rejected the API key (401). Check ANTHROPIC_API_KEY in backend/.env and restart the server."
    if isinstance(exc, anthropic.PermissionDeniedError):
        return "This API key is not allowed to use the configured model or feature (403)."
    if isinstance(exc, anthropic.NotFoundError):
        return f"Model '{settings.model}' was not found (404). Check PREP_CLAUDE_MODEL in backend/.env."
    if isinstance(exc, anthropic.RateLimitError):
        return "The Claude API rate limit was hit. Wait a minute and press Retry, or lower PREP_MAX_CONCURRENCY."
    if isinstance(exc, anthropic.APIConnectionError):
        return "Could not reach the Claude API. Check your internet connection and press Retry."
    if isinstance(exc, anthropic.APIStatusError):
        return f"The Claude API returned an error ({exc.status_code}). Press Retry in a moment."
    if isinstance(exc, (LLMError, PipelineError)):
        return str(exc)
    return f"Unexpected error: {exc}"


async def _call_with_retry(make_call: Callable[[int], Any], *, what: str, tracker: ProgressTracker, retries: int = 1) -> Any:
    """Run make_call(attempt); retry once on recoverable failures."""
    for attempt in range(retries + 1):
        try:
            return await make_call(attempt)
        except (LLMRefusal, *FATAL_API_ERRORS):
            raise
        except (LLMError, anthropic.APIStatusError, anthropic.APIConnectionError) as exc:
            if attempt >= retries:
                raise
            reason = "answer was too long" if isinstance(exc, LLMTruncated) else "call failed"
            tracker.log(f"Retrying {what} ({reason}).", "warn")
            log.warning("retrying %s after: %s", what, exc)
            await asyncio.sleep(3 if isinstance(exc, LLMError) else 8)
    raise AssertionError("unreachable")


async def generate_items(
    llm: ClaudeLLM,
    ctx: PrepContext,
    blocks: list[dict[str, Any]],
    job: Job,
    *,
    existing: list[str],
    tracker: ProgressTracker,
    focus: str = "",
    topics: list[str] | None = None,
    origin: str = "ai",
) -> list[dict[str, Any]]:
    """One generation call (with retry) for a job; returns normalised items."""

    async def call(attempt: int) -> list[dict[str, Any]]:
        if job.section == "revision":
            data = await llm.generate_json(
                system=prompts.COACH_SYSTEM,
                context_blocks=blocks,
                task=prompts.revision_task(ctx, job.topics),
                schema=schemas.REVISION,
                max_tokens=48000,
            )
            return normalize_items("revision", data.get("notes") or [], origin=origin)
        count = job.count if attempt == 0 else max(2, math.ceil(job.count * 0.6))
        data = await llm.generate_json(
            system=prompts.COACH_SYSTEM,
            context_blocks=blocks,
            task=prompts.section_task(
                job.section, ctx, count=count, level=job.level or "mixed", topics=topics, focus=focus, existing=existing
            ),
            schema=schemas.SECTION_SCHEMAS[job.section],
            max_tokens=48000,
        )
        raw = data.get("questions") or []
        for item in raw:
            if isinstance(item, dict) and job.level and not item.get("level"):
                item["level"] = job.level
        return normalize_items(job.section, raw, origin=origin)

    return await _call_with_retry(call, what=f"{SECTION_NOUNS[job.section]} ({job.label})", tracker=tracker)


# ------------------------------------------------------------------------- AI run
async def run_ai(
    ctx: PrepContext,
    *,
    store: Store,
    settings: Settings,
    llm: ClaudeLLM,
    tracker: ProgressTracker,
    builder: ResultBuilder,
    warnings: list[str],
) -> None:
    tracker.step("parse", "done", detail=f"Resume {len(ctx.resume_text):,} chars · JD {len(ctx.jd_text):,} chars")

    # ---------------------------------------------------------------- research
    tracker.step("research", "running", detail="Planning searches…")
    tracker.log(f"Starting deep research on how {ctx.company} interviews for {ctx.role_or_default}.", "info")
    try:
        research = await research_company(
            llm,
            ctx,
            web_search_enabled=settings.enable_web_search,
            log_fn=tracker.log,
            sources_fn=tracker.add_sources,
        )
    except LLMRefusal as exc:
        warnings.append(f"Company research was declined by Claude's safety filters: {exc}")
        tracker.log("Research was declined by Claude's safety filters - continuing without it.", "warn")
        research = ResearchResult("", "model_knowledge")
    source_count = len(tracker.state["sources"])
    tracker.step("research", "done", detail=f"{source_count} sources · {MODE_LABELS.get(research.mode, research.mode)}")
    if research.mode != "live_web":
        warnings.append(f"Company research used {MODE_LABELS.get(research.mode, research.mode)}.")

    base = prompts.base_context(ctx, research.report_md, research.mode)

    # --------------------------------------------------------------- blueprint
    n_topics = ctx.targets["topics"]
    tracker.step("blueprint", "running", detail="Comparing resume, JD and research…")
    tracker.log("Analysing your resume against the job description and the research…", "info")

    async def blueprint_call(_: int) -> dict[str, Any]:
        return await llm.generate_json(
            system=prompts.COACH_SYSTEM,
            context_blocks=prompts.context_blocks(base),
            task=prompts.blueprint_task(n_topics),
            schema=schemas.BLUEPRINT,
            max_tokens=48000,
        )

    data = await _call_with_retry(blueprint_call, what="the prep blueprint", tracker=tracker)
    profile = Profile.model_validate(data.get("profile") or {}).model_dump()
    company = CompanyIntel.model_validate(data.get("company") or {}).model_dump()
    company.update(
        name=company["name"] or ctx.company,
        research_mode=research.mode,
        research_md=research.report_md,
        sources=list(tracker.state["sources"]),
    )
    topics = normalize_topics(data.get("topics"))[:n_topics]
    if not topics:
        raise PipelineError("Claude did not return a topic plan. Press Retry.")
    study_plan = [StudyBlock.model_validate(b).model_dump() for b in data.get("study_plan") or [] if isinstance(b, dict)]
    builder.set(profile=profile, company=company, topics=topics, study_plan=study_plan)
    if not ctx.role and profile.get("target_role"):
        ctx.role = profile["target_role"]
        store.update(ctx.session_id, role=ctx.role)
    tracker.step("blueprint", "done", detail=f"{len(topics)} topics · {len(company['reported_questions'])} reported questions")
    tracker.log(f"Topic plan ready: {', '.join(t['name'] for t in topics)}", "result")
    tracker.section_ready("overview")

    # -------------------------------------------------------------- generation
    blocks = prompts.context_blocks(base, prompts.blueprint_context(builder.result))
    jobs = plan_jobs(ctx, [t["name"] for t in topics])
    await _run_jobs(llm, ctx, blocks, jobs, tracker=tracker, builder=builder, warnings=warnings)

    # one top-up round for sections that came up short because a batch failed
    topups = []
    for section in QUESTION_SECTIONS:
        have, want = len(builder.result[section]), ctx.targets[section]
        if have < 0.8 * want:
            topups.append(Job(section, min(want - have, MAX_PER_CALL[section]), level="mixed"))
    if topups:
        tracker.log("Topping up sections that came up short…", "info")
        await _run_jobs(llm, ctx, blocks, topups, tracker=tracker, builder=builder, warnings=warnings, topup=True)

    counts = builder.counts()
    if counts["questions"] == 0:
        raise PipelineError("No questions could be generated. Check the server logs and press Retry.")
    tracker.log(
        f"Done: {counts['revision']} revision notes, {counts['theory']} theory, {counts['practical']} practical, "
        f"{counts['scenario']} scenario and {counts['quiz']} quiz questions.",
        "success",
    )


async def _run_jobs(
    llm: ClaudeLLM,
    ctx: PrepContext,
    blocks: list[dict[str, Any]],
    jobs: list[Job],
    *,
    tracker: ProgressTracker,
    builder: ResultBuilder,
    warnings: list[str],
    topup: bool = False,
) -> None:
    totals = Counter(job.section for job in jobs)
    finished: Counter[str] = Counter()
    targets = {s: ctx.targets.get(s, 0) for s in QUESTION_SECTIONS}
    targets["revision"] = len(builder.result.get("topics") or [])

    for section in totals:
        tracker.step(section, "running", detail=f"{len(builder.result[section])}/{targets[section]}",
                     fraction=0.02 if not topup else None)

    async def run(job: Job) -> None:
        try:
            items = await generate_items(
                llm, ctx, blocks, job, existing=builder.question_texts(job.section), tracker=tracker
            )
            fresh = builder.add_items(job.section, items)
            if fresh:
                tracker.log(f"+{len(fresh)} {SECTION_NOUNS[job.section]} ({job.label})", "result")
        except FATAL_API_ERRORS:
            raise
        except (LLMError, anthropic.APIStatusError, anthropic.APIConnectionError) as exc:
            message = f"Could not generate {SECTION_NOUNS[job.section]} ({job.label}): {exc}"
            warnings.append(message)
            tracker.log(message, "warn")
        finally:
            finished[job.section] += 1
            section = job.section
            have = len(builder.result[section])
            if finished[section] >= totals[section]:
                tracker.step(section, "done" if have else "failed", detail=f"{have} ready")
                if have:
                    tracker.section_ready(section)
            else:
                tracker.step(section, detail=f"{have}/{targets[section]}", fraction=finished[section] / totals[section])
                if have:
                    tracker.section_ready(section)

    tasks = [asyncio.create_task(run(job)) for job in jobs]
    try:
        await asyncio.gather(*tasks)
    except BaseException:
        # a fatal error (or cancellation) - stop the remaining calls instead of orphaning them
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise


# ----------------------------------------------------------------------- entrypoint
async def run_session(
    session_id: str,
    *,
    store: Store,
    settings: Settings,
    make_llm: Callable[[], ClaudeLLM] | None = None,
) -> None:
    session = store.get(session_id)
    if session is None:
        return
    ctx = PrepContext.from_session(session)
    tracker = ProgressTracker(store, session_id, ctx.company)
    builder = ResultBuilder(store, session_id)
    warnings: list[str] = []
    store.update(
        session_id,
        status="running",
        error=None,
        warnings=[],
        progress=tracker.state,
        result=builder.result,
        summary=builder.counts(),
    )
    try:
        if session["mode"] == "ai":
            if make_llm is None:
                raise PipelineError("AI mode requested but no Claude client is configured.")
            await run_ai(
                ctx, store=store, settings=settings, llm=make_llm(), tracker=tracker, builder=builder, warnings=warnings
            )
        else:
            from .demo import run_demo

            await run_demo(ctx, settings=settings, tracker=tracker, builder=builder, warnings=warnings, store=store)
        tracker.finish()
        store.update(session_id, status="completed", warnings=warnings)
    except asyncio.CancelledError:
        if store.get(session_id, columns=("status",)) is not None:
            store.update(session_id, status="failed", error="Generation was cancelled.", warnings=warnings)
        raise
    except Exception as exc:
        log.exception("prep run %s failed", session_id)
        message = friendly_error(exc, settings)
        for step in tracker.state["steps"]:
            if step["status"] == "running":
                step["status"] = "failed"
        tracker.log(message, "error")
        tracker.flush(force=True)
        store.update(session_id, status="failed", error=message, warnings=warnings)
