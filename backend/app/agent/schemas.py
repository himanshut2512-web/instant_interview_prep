"""JSON schemas for Claude structured outputs (output_config.format).

Structured outputs require `additionalProperties: false` on every object and
do not support numeric/length constraints, so ranges are enforced afterwards
by the pydantic models in app.models. Every property is required; the prompt
tells the model to use "" / [] when something does not apply.
"""

from __future__ import annotations

from typing import Any

STR: dict[str, Any] = {"type": "string"}
INT: dict[str, Any] = {"type": "integer"}
BOOL: dict[str, Any] = {"type": "boolean"}


def arr(items: dict[str, Any]) -> dict[str, Any]:
    return {"type": "array", "items": items}


def obj(properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


def enum(values: tuple[str, ...] | list[str]) -> dict[str, Any]:
    return {"type": "string", "enum": list(values)}


LEVEL = enum(("beginner", "intermediate", "advanced"))
PRIORITY = enum(("high", "medium", "low"))
CODE = obj({"language": STR, "code": STR})

_ITEM_BASE = {"topic": STR, "level": LEVEL, "hot": BOOL, "hot_reason": STR, "question": STR}

BLUEPRINT = obj(
    {
        "profile": obj(
            {
                "candidate_name": STR,
                "current_title": STR,
                "target_role": STR,
                "seniority": STR,
                "summary": STR,
                "elevator_pitch": STR,
                "strengths": arr(STR),
                "gaps": arr(STR),
                "matched_skills": arr(STR),
                "missing_skills": arr(STR),
                "resume_probes": arr(obj({"item": STR, "likely_questions": arr(STR)})),
            }
        ),
        "company": obj(
            {
                "name": STR,
                "overview": STR,
                "hiring_focus": STR,
                "interview_rounds": arr(obj({"name": STR, "format": STR, "what_they_test": STR, "tips": STR})),
                "focus_areas": arr(STR),
                "culture_values": arr(STR),
                "insider_tips": arr(STR),
                "reported_questions": arr(obj({"question": STR, "round": STR, "source": STR})),
                "questions_to_ask_them": arr(STR),
            }
        ),
        "topics": arr(
            obj({"name": STR, "priority": PRIORITY, "weight": INT, "why": STR, "subtopics": arr(STR)})
        ),
        "study_plan": arr(obj({"title": STR, "focus": STR, "tasks": arr(STR)})),
    }
)

REVISION = obj(
    {
        "notes": arr(
            obj(
                {
                    "topic": STR,
                    "priority": PRIORITY,
                    "summary": STR,
                    "why_it_matters": STR,
                    "key_concepts": arr(obj({"term": STR, "explanation": STR})),
                    "explanation_md": STR,
                    "code_example": CODE,
                    "pitfalls": arr(STR),
                    "interview_tips": arr(STR),
                    "cheat_sheet": arr(STR),
                    "likely_questions": arr(STR),
                }
            )
        )
    }
)

THEORY = obj(
    {
        "questions": arr(
            obj(
                {
                    **_ITEM_BASE,
                    "answer_md": STR,
                    "key_points": arr(STR),
                    "interview_tip": STR,
                    "follow_ups": arr(STR),
                }
            )
        )
    }
)

PRACTICAL = obj(
    {
        "questions": arr(
            obj(
                {
                    **_ITEM_BASE,
                    "context": STR,
                    "approach": arr(STR),
                    "solution_md": STR,
                    "code": CODE,
                    "complexity": STR,
                    "edge_cases": arr(STR),
                    "interview_tip": STR,
                    "follow_ups": arr(STR),
                }
            )
        )
    }
)

SCENARIO = obj(
    {
        "questions": arr(
            obj(
                {
                    **_ITEM_BASE,
                    "scenario": STR,
                    "approach_steps": arr(obj({"step": STR, "detail": STR})),
                    "model_answer_md": STR,
                    "what_interviewer_looks_for": arr(STR),
                    "mistakes_to_avoid": arr(STR),
                    "follow_ups": arr(STR),
                }
            )
        )
    }
)

QUIZ = obj(
    {
        "questions": arr(
            obj(
                {
                    **_ITEM_BASE,
                    "options": arr(STR),
                    "correct_index": INT,
                    "explanation": STR,
                    "option_explanations": arr(STR),
                    "interview_tip": STR,
                }
            )
        )
    }
)

EVALUATION = obj(
    {
        "score": INT,
        "verdict": STR,
        "strengths": arr(STR),
        "improvements": arr(STR),
        "missing_points": arr(STR),
        "improved_answer_md": STR,
    }
)

SECTION_SCHEMAS = {
    "revision": REVISION,
    "theory": THEORY,
    "practical": PRACTICAL,
    "scenario": SCENARIO,
    "quiz": QUIZ,
}
