"""Render a whole prep kit as a single Markdown "crash learning sheet"."""

from __future__ import annotations

from typing import Any

from .models import LEVELS

LETTERS = "ABCDEF"


def _bullets(items: list[str] | None, indent: str = "") -> list[str]:
    return [f"{indent}- {item}" for item in items or [] if item]


def _code(snippet: dict[str, Any] | None) -> list[str]:
    if not snippet or not snippet.get("code"):
        return []
    return [f"```{snippet.get('language') or ''}", snippet["code"].rstrip(), "```", ""]


def _by_level(items: list[dict[str, Any]]) -> list[tuple[str, list[dict[str, Any]]]]:
    return [(level, [i for i in items if i.get("level") == level]) for level in LEVELS]


def _hot(item: dict[str, Any]) -> str:
    return " 🔥" if item.get("hot") else ""


def export_markdown(session: dict[str, Any]) -> str:
    result = session.get("result") or {}
    profile = result.get("profile") or {}
    company = result.get("company") or {}
    role = session.get("role") or profile.get("target_role") or "Target role"
    years = session.get("years")
    out: list[str] = [
        f"# Interview Prep Kit: {session.get('company')} · {role}",
        "",
        f"_Experience: {years:g} years · Generated {session.get('created_at', '')[:10]} · "
        f"{'Claude AI agent' if session.get('mode') == 'ai' else 'Offline demo knowledge base'}_",
        "",
    ]

    # ------------------------------------------------------------------ overview
    if profile.get("summary") or profile.get("elevator_pitch"):
        out += ["## 1. Your snapshot", ""]
        if profile.get("summary"):
            out += [profile["summary"], ""]
        if profile.get("elevator_pitch"):
            out += ["### \"Tell me about yourself\"", "", f"> {profile['elevator_pitch']}", ""]
        if profile.get("strengths"):
            out += ["**Strengths to lean on**", "", *_bullets(profile["strengths"]), ""]
        if profile.get("gaps"):
            out += ["**Gaps to prepare for**", "", *_bullets(profile["gaps"]), ""]
        for probe in profile.get("resume_probes") or []:
            out += [f"**Resume deep-dive: {probe.get('item')}**", "", *_bullets(probe.get("likely_questions")), ""]

    out += [f"## 2. {company.get('name') or session.get('company')}: company intel", ""]
    if company.get("overview"):
        out += [company["overview"], ""]
    if company.get("hiring_focus"):
        out += [f"**What they look for:** {company['hiring_focus']}", ""]
    if company.get("interview_rounds"):
        out += ["### Interview rounds", ""]
        for n, rnd in enumerate(company["interview_rounds"], 1):
            out.append(f"{n}. **{rnd.get('name')}** ({rnd.get('format')}): {rnd.get('what_they_test')}")
            if rnd.get("tips"):
                out.append(f"   - Tip: {rnd['tips']}")
        out.append("")
    for title, key in (("Focus areas", "focus_areas"), ("Culture & values", "culture_values"),
                       ("Insider tips", "insider_tips"), ("Questions to ask them", "questions_to_ask_them")):
        if company.get(key):
            out += [f"### {title}", "", *_bullets(company[key]), ""]
    if company.get("reported_questions"):
        out += ["### Reported interview questions", ""]
        for q in company["reported_questions"]:
            meta = ", ".join(p for p in (q.get("round"), q.get("source")) if p)
            out.append(f"- {q.get('question')}" + (f" _({meta})_" if meta else ""))
        out.append("")

    if result.get("topics"):
        out += ["## 3. Topic plan", "", "| Topic | Priority | Weight | Why |", "|---|---|---|---|"]
        for t in result["topics"]:
            out.append(f"| {t['name']} | {t['priority']} | {t['weight']} | {t.get('why', '')} |")
        out.append("")
    if result.get("study_plan"):
        out += ["### Study plan", ""]
        for block in result["study_plan"]:
            out += [f"**{block.get('title')}**: {block.get('focus')}", *_bullets(block.get("tasks")), ""]

    # ------------------------------------------------------------------ revision
    if result.get("revision"):
        out += ["## 4. Crash revision", ""]
        for note in result["revision"]:
            out += [f"### {note['topic']}", ""]
            if note.get("summary"):
                out += [f"_{note['summary']}_", ""]
            if note.get("why_it_matters"):
                out += [f"**Why it matters:** {note['why_it_matters']}", ""]
            if note.get("key_concepts"):
                out += ["**Key concepts**", ""]
                out += [f"- **{c.get('term')}**: {c.get('explanation')}" for c in note["key_concepts"]]
                out.append("")
            if note.get("explanation_md"):
                out += [note["explanation_md"], ""]
            out += _code(note.get("code_example"))
            for title, key in (("Pitfalls", "pitfalls"), ("Interview tips", "interview_tips"),
                               ("Cheat sheet", "cheat_sheet"), ("Likely questions", "likely_questions")):
                if note.get(key):
                    out += [f"**{title}**", "", *_bullets(note[key]), ""]

    # ----------------------------------------------------------------- questions
    def question_section(number: int, title: str, items: list[dict[str, Any]], render) -> None:
        if not items:
            return
        out.extend([f"## {number}. {title} ({len(items)})", ""])
        for level, group in _by_level(items):
            if not group:
                continue
            out.extend([f"### {level.title()}", ""])
            for n, item in enumerate(group, 1):
                out.append(f"**Q{n}. {item['question']}**{_hot(item)}  ")
                out.append(f"_Topic: {item.get('topic')}_" + (f" · _{item['hot_reason']}_" if item.get("hot_reason") else ""))
                out.append("")
                render(item)
                out.append("---")
                out.append("")

    def render_theory(item: dict[str, Any]) -> None:
        out.extend([item.get("answer_md", ""), ""])
        if item.get("key_points"):
            out.extend(["**Key points:**", *_bullets(item["key_points"]), ""])
        if item.get("interview_tip"):
            out.extend([f"💡 **In the interview:** {item['interview_tip']}", ""])
        if item.get("follow_ups"):
            out.extend(["**Follow-ups:**", *_bullets(item["follow_ups"]), ""])

    def render_practical(item: dict[str, Any]) -> None:
        if item.get("context"):
            out.extend([item["context"], ""])
        if item.get("approach"):
            out.extend(["**Approach:**", *[f"{i}. {s}" for i, s in enumerate(item["approach"], 1)], ""])
        if item.get("solution_md"):
            out.extend([item["solution_md"], ""])
        out.extend(_code(item.get("code")))
        if item.get("complexity"):
            out.extend([f"**Complexity:** {item['complexity']}", ""])
        if item.get("edge_cases"):
            out.extend(["**Edge cases:**", *_bullets(item["edge_cases"]), ""])
        if item.get("interview_tip"):
            out.extend([f"💡 **In the interview:** {item['interview_tip']}", ""])

    def render_scenario(item: dict[str, Any]) -> None:
        if item.get("scenario"):
            out.extend([f"> {item['scenario']}", ""])
        if item.get("approach_steps"):
            out.append("**How to tackle it:**")
            out.extend(f"{i}. **{s.get('step')}**: {s.get('detail')}" for i, s in enumerate(item["approach_steps"], 1))
            out.append("")
        if item.get("model_answer_md"):
            out.extend(["**Model answer:**", "", item["model_answer_md"], ""])
        if item.get("what_interviewer_looks_for"):
            out.extend(["**What the interviewer looks for:**", *_bullets(item["what_interviewer_looks_for"]), ""])
        if item.get("mistakes_to_avoid"):
            out.extend(["**Mistakes to avoid:**", *_bullets(item["mistakes_to_avoid"]), ""])

    question_section(5, "Theoretical questions", result.get("theory") or [], render_theory)
    question_section(6, "Practical questions", result.get("practical") or [], render_practical)
    question_section(7, "Scenario-based questions", result.get("scenario") or [], render_scenario)

    quiz = result.get("quiz") or []
    if quiz:
        out += [f"## 8. MCQ quiz ({len(quiz)})", ""]
        for n, q in enumerate(quiz, 1):
            out.append(f"**{n}. {q['question']}**{_hot(q)}")
            out.extend(f"   {LETTERS[i]}. {opt}" for i, opt in enumerate(q.get("options") or []))
            out.append("")
        out += ["### Answer key", ""]
        for n, q in enumerate(quiz, 1):
            out.append(f"{n}. **{LETTERS[q['correct_index']]}**: {q.get('explanation', '')}")
        out.append("")

    sources = company.get("sources") or []
    if sources:
        out += ["## Sources", "", *[f"- [{s.get('title') or s.get('url')}]({s.get('url')})" for s in sources], ""]
    return "\n".join(out).strip() + "\n"
