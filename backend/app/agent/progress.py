"""Live progress + incremental results for a running prep session.

The pipeline reports into a ProgressTracker; every change is persisted so the
frontend can poll /status and render the agent's timeline, its live log and
any dashboard section that is already complete.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from ..models import QUESTION_SECTIONS, dedupe, empty_result, result_counts
from ..storage import Store

STEP_DEFS = (
    ("parse", "Read your resume & job description"),
    ("research", "Research {company} interviews on the web"),
    ("blueprint", "Match your profile to the JD & plan topics"),
    ("revision", "Write crash revision notes"),
    ("theory", "Generate theoretical questions"),
    ("practical", "Generate practical questions"),
    ("scenario", "Generate scenario-based questions"),
    ("quiz", "Build the MCQ quiz"),
)
STEP_WEIGHTS = {
    "parse": 3, "research": 22, "blueprint": 15, "revision": 15,
    "theory": 15, "practical": 10, "scenario": 10, "quiz": 10,
}
MAX_LOGS = 200
MAX_SOURCES = 60


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def initial_progress(company: str) -> dict[str, Any]:
    return {
        "percent": 0,
        "started_at": _now(),
        "finished_at": None,
        "steps": [
            {"key": key, "label": label.format(company=company or "the company"), "status": "pending",
             "detail": "", "fraction": 0.0}
            for key, label in STEP_DEFS
        ],
        "logs": [],
        "sources": [],
        "sections_ready": [],
    }


class ProgressTracker:
    def __init__(self, store: Store, session_id: str, company: str):
        self.store = store
        self.session_id = session_id
        self.state = initial_progress(company)
        self._last_flush = 0.0

    # ------------------------------------------------------------------ steps
    def _step(self, key: str) -> dict[str, Any]:
        for step in self.state["steps"]:
            if step["key"] == key:
                return step
        raise KeyError(key)

    def step(self, key: str, status: str | None = None, detail: str | None = None,
             fraction: float | None = None) -> None:
        step = self._step(key)
        if status:
            step["status"] = status
            if status == "done":
                step["fraction"] = 1.0
        if detail is not None:
            step["detail"] = detail
        if fraction is not None:
            step["fraction"] = max(0.0, min(1.0, fraction))
        self._recompute()
        self.flush(force=True)

    def _recompute(self) -> None:
        total = sum(STEP_WEIGHTS.values())
        done = 0.0
        for step in self.state["steps"]:
            weight = STEP_WEIGHTS.get(step["key"], 0)
            if step["status"] in ("done", "skipped", "failed"):
                done += weight
            elif step["status"] == "running":
                done += weight * float(step.get("fraction") or 0.0)
        self.state["percent"] = int(round(100 * done / total))

    # ------------------------------------------------------------------- logs
    def log(self, message: str, kind: str = "info") -> None:
        logs = self.state["logs"]
        logs.append({"t": _now(), "kind": kind, "msg": message[:400]})
        if len(logs) > MAX_LOGS:
            del logs[: len(logs) - MAX_LOGS]
        self.flush()

    def add_sources(self, sources: list[dict[str, str]]) -> int:
        known = {s["url"] for s in self.state["sources"]}
        added = 0
        for source in sources:
            url = (source.get("url") or "").strip()
            if not url or url in known or len(self.state["sources"]) >= MAX_SOURCES:
                continue
            known.add(url)
            self.state["sources"].append({"url": url, "title": (source.get("title") or url)[:200]})
            added += 1
        if added:
            self.flush()
        return added

    def section_ready(self, section: str) -> None:
        if section not in self.state["sections_ready"]:
            self.state["sections_ready"].append(section)
            self.flush(force=True)

    def finish(self) -> None:
        self.state["finished_at"] = _now()
        for step in self.state["steps"]:
            if step["status"] in ("pending", "running"):
                step["status"] = "skipped"
        self._recompute()
        self.state["percent"] = 100
        self.flush(force=True)

    def flush(self, force: bool = False) -> None:
        now = time.monotonic()
        if not force and now - self._last_flush < 0.25:
            return
        self._last_flush = now
        self.store.update(self.session_id, progress=self.state)


class ResultBuilder:
    """Accumulates generated content and persists it after each change."""

    def __init__(self, store: Store, session_id: str, result: dict[str, Any] | None = None):
        self.store = store
        self.session_id = session_id
        self.result = result or empty_result()

    def set(self, **parts: Any) -> None:
        self.result.update(parts)
        self.save()

    def add_items(self, section: str, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        existing = self.result.setdefault(section, [])
        key = "topic" if section == "revision" else "question"
        if section == "revision":
            known = {n["topic"].lower() for n in existing}
            fresh = [n for n in items if n["topic"].lower() not in known]
        else:
            fresh = dedupe(existing, items, key=key)
        existing.extend(fresh)
        if fresh:
            self.save()
        return fresh

    def question_texts(self, section: str, limit: int = 80) -> list[str]:
        items = self.result.get(section) or []
        return [str(i.get("question", ""))[:140] for i in items][-limit:]

    def counts(self) -> dict[str, int]:
        return result_counts(self.result)

    def save(self) -> None:
        self.store.update(self.session_id, result=self.result, summary=self.counts())


def total_questions(result: dict[str, Any]) -> int:
    return sum(len(result.get(s) or []) for s in QUESTION_SECTIONS)
