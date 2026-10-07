"""Compact constructors for knowledge-base content (keeps the topic files readable)."""

from __future__ import annotations

from textwrap import dedent
from typing import Any


def md(text: str) -> str:
    """Dedent a triple-quoted Markdown/code block."""
    return dedent(text).strip("\n")


def T(level: str, question: str, answer: str, key_points: list[str], tip: str, follow_ups: list[str],
      hot: bool = False) -> dict[str, Any]:
    return {
        "level": level, "hot": hot, "question": question, "answer_md": md(answer), "key_points": key_points,
        "interview_tip": tip, "follow_ups": follow_ups,
    }


def P(level: str, question: str, context: str, approach: list[str], solution: str, code: str, language: str,
      complexity: str, edge_cases: list[str], tip: str, follow_ups: list[str], hot: bool = False) -> dict[str, Any]:
    return {
        "level": level, "hot": hot, "question": question, "context": md(context), "approach": approach,
        "solution_md": md(solution), "code": {"language": language, "code": md(code)}, "complexity": complexity,
        "edge_cases": edge_cases, "interview_tip": tip, "follow_ups": follow_ups,
    }


def S(level: str, scenario: str, question: str, steps: list[tuple[str, str]], answer: str, looks_for: list[str],
      mistakes: list[str], follow_ups: list[str], hot: bool = False) -> dict[str, Any]:
    return {
        "level": level, "hot": hot, "scenario": md(scenario), "question": question,
        "approach_steps": [{"step": s, "detail": d} for s, d in steps], "model_answer_md": md(answer),
        "what_interviewer_looks_for": looks_for, "mistakes_to_avoid": mistakes, "follow_ups": follow_ups,
    }


def Q(level: str, question: str, options: list[str], correct: int, explanation: str, why: list[str], tip: str,
      hot: bool = False) -> dict[str, Any]:
    return {
        "level": level, "hot": hot, "question": question, "options": options, "correct_index": correct,
        "explanation": explanation, "option_explanations": why, "interview_tip": tip,
    }


def note(summary: str, concepts: list[tuple[str, str]], explanation: str, pitfalls: list[str], tips: list[str],
         cheat_sheet: list[str], likely_questions: list[str], code: str = "", language: str = "") -> dict[str, Any]:
    return {
        "summary": summary,
        "key_concepts": [{"term": t, "explanation": e} for t, e in concepts],
        "explanation_md": md(explanation),
        "code_example": {"language": language, "code": md(code) if code else ""},
        "pitfalls": pitfalls,
        "interview_tips": tips,
        "cheat_sheet": cheat_sheet,
        "likely_questions": likely_questions,
    }
