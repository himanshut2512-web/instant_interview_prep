"""Offline demo agent.

Builds a complete, personalised prep kit from the built-in knowledge base when
no Claude API key is configured: topics are chosen from the JD/resume, levels
follow the candidate's experience, and the profile/gap analysis is computed
from skill keywords. The same dashboards and actions work, just without live
web research or freshly generated content.
"""

from __future__ import annotations

import asyncio
import re
from collections import deque
from typing import Any

from ..config import Settings
from ..knowledge_base import TOPICS, select_topics, topic_by_name
from ..knowledge_base.matching import (
    AREA_SKILLS,
    SKILL_LEXICON,
    SOFT_SKILLS,
    _alias_pattern,
    extract_skills,
    implied_by,
    skill_gap,
)
from ..models import (
    LEVELS,
    CompanyIntel,
    Profile,
    _signature,
    normalize_items,
)
from ..storage import Store
from .plan import PrepContext, split_by_level
from .progress import ProgressTracker, ResultBuilder

OFFLINE_NOTE = (
    "Demo mode: content comes from the built-in interview knowledge base, matched to your JD and resume. "
    "Add ANTHROPIC_API_KEY on the server for live company research and freshly generated, fully personalised "
    "questions."
)

HOT_SHARE = 0.4

STOPWORDS = set(
    "the a an and or of to in on for with is are was were be been being it this that these those as at by from "
    "into about than then so such can could would should will may might must do does did done have has had having "
    "you your we our they their them i me my he she his her its what which who whom how why when where while also "
    "not no yes more most less very just only each every any all some other use used using like".split()
)


# ----------------------------------------------------------------------------- helpers
def _hot_reason(item: dict[str, Any], ctx: PrepContext) -> str:
    if not item.get("hot"):
        return ""
    role = ctx.role or "this kind of"
    return f"Very frequently asked in {role} interviews"


def _with_topic(raw: dict[str, Any], topic: dict[str, Any], ctx: PrepContext) -> dict[str, Any]:
    item = dict(raw)
    item["topic"] = topic["name"]
    item["hot_reason"] = _hot_reason(item, ctx)
    return item


def _interleave(lists: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Round-robin across topics so higher-priority topics come first but every topic is represented."""
    queues = [deque(items) for items in lists if items]
    out: list[dict[str, Any]] = []
    while queues:
        for queue in list(queues):
            out.append(queue.popleft())
            if not queue:
                queues.remove(queue)
    return out


def pick_items(section: str, selected: list[dict[str, Any]], ctx: PrepContext) -> list[dict[str, Any]]:
    target = ctx.targets[section]
    split = split_by_level(target, ctx.years)
    pools: dict[str, deque] = {}
    for level in LEVELS:
        per_topic = []
        for entry in selected:
            topic = entry["topic"]
            items = [i for i in topic[section] if i["level"] == level]
            items.sort(key=lambda i: not i.get("hot"))  # hot first
            per_topic.append([_with_topic(i, topic, ctx) for i in items])
        pools[level] = deque(_interleave(per_topic))

    chosen: list[dict[str, Any]] = []
    for level, count in split.items():
        while count and pools[level]:
            chosen.append(pools[level].popleft())
            count -= 1
    leftovers = _interleave([list(pools[level]) for level in ("intermediate", "advanced", "beginner")])
    for item in leftovers:
        if len(chosen) >= target:
            break
        chosen.append(item)
    # Keep the 🔥 label meaningful: at most ~40% of each level, favouring higher-priority topics (chosen order).
    for level in LEVELS:
        in_level = [item for item in chosen if item["level"] == level]
        allowed = round(HOT_SHARE * len(in_level))
        for item in in_level:
            if item.get("hot"):
                if allowed > 0:
                    allowed -= 1
                else:
                    item["hot"], item["hot_reason"] = False, ""
    order = {level: i for i, level in enumerate(LEVELS)}
    chosen.sort(key=lambda i: order[i["level"]])
    return normalize_items(section, chosen, origin="kb")


def _resume_lines(resume: str) -> list[str]:
    """Resume lines with wrapped bullet continuations joined back onto their bullet."""
    merged: list[str] = []
    for raw in resume.splitlines():
        clean = raw.strip()
        if not clean:
            continue
        is_bullet = clean[:1] in "-•*·"
        text = clean.lstrip("-•*·").strip()
        if merged and not is_bullet and text[:1].islower() and not merged[-1].endswith((".", ":")):
            merged[-1] = f"{merged[-1]} {text}"
        else:
            merged.append(text)
    return [line for line in merged if 25 <= len(line) <= 400]


def _clip(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip(",;:") + "…"


ACTION_VERBS = (
    "built", "designed", "developed", "created", "led", "reduced", "increased", "improved", "cut", "saved",
    "delivered", "launched", "implemented", "automated", "optimised", "optimized", "migrated", "deployed",
    "productionised", "productionized", "architected", "drove", "owned", "ran", "wrote", "mentored", "scaled",
    "managed", "analysed", "analyzed", "established", "spearheaded", "streamlined", "won",
)
_DATE_ONLY = re.compile(r"^[\w .,&/-]*\(?\s*\w{3,9}\.? ?\d{4}\s*[-–]\s*(present|\w{3,9}\.? ?\d{4})\s*\)?$", re.I)


def _achievements(lines: list[str]) -> list[str]:
    """Resume bullets that start with an action verb, metric-bearing ones first."""
    verb_lines = [l for l in lines if l.split()[0].lower().rstrip(",:") in ACTION_VERBS and not _DATE_ONLY.match(l)]
    with_metrics = [l for l in verb_lines if re.search(r"\d|%", l)]
    return with_metrics + [l for l in verb_lines if l not in with_metrics]


def _line_for_skill(lines: list[str], skill: str) -> str:
    aliases = list(SKILL_LEXICON.get(skill, (skill.lower(),)))
    for source in implied_by(skill):  # e.g. an XGBoost bullet is evidence of machine learning
        aliases += SKILL_LEXICON.get(source, ())
    for line in _achievements(lines) + lines:
        lowered = line.lower()
        if any(_alias_pattern(alias).search(lowered) for alias in aliases):
            return line
    return ""


def _join(items: list[str]) -> str:
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def _guess_name(resume: str) -> str:
    for line in resume.splitlines()[:5]:
        clean = re.sub(r"\(.*?\)", "", line).strip()
        if not clean or any(w in clean.lower() for w in ("resume", "curriculum", "vitae", "@", "http")):
            continue
        words = clean.replace(",", " ").split()
        if 2 <= len(words) <= 4 and all(re.fullmatch(r"[A-Za-z.'-]+", w) for w in words):
            return " ".join(w.capitalize() if w.isupper() else w for w in words)
        break
    return ""


_TITLE_RE = re.compile(
    r"\b((?:senior|sr\.?|junior|jr\.?|lead|principal|staff|associate)?\s*"
    r"(?:data scientist|data analyst|data engineer|machine learning engineer|ml engineer|ai engineer|"
    r"software engineer|software developer|developer|business analyst|analytics consultant|consultant|"
    r"product analyst|analyst|engineer|scientist|architect|manager))\b",
    re.IGNORECASE,
)


def _guess_title(resume: str) -> str:
    match = _TITLE_RE.search(resume)
    return match.group(1).strip().title() if match else ""


def build_profile(ctx: PrepContext) -> dict[str, Any]:
    jd_skills = extract_skills(f"{ctx.role}\n{ctx.jd_text}")
    resume_skills = extract_skills(ctx.resume_text)
    matched, missing = skill_gap(jd_skills, resume_skills)
    # hard skills first: they make better evidence and better prep targets
    matched.sort(key=lambda sk: sk in SOFT_SKILLS)
    missing.sort(key=lambda sk: sk in SOFT_SKILLS)
    lines = _resume_lines(ctx.resume_text)
    achievements = _achievements(lines)[:6]
    title = _guess_title(ctx.resume_text)
    role = ctx.role or "the role"

    strengths = []
    for skill in matched[:5]:
        evidence = _line_for_skill(lines, skill)
        strengths.append(f"{skill} - your resume shows it: \"{_clip(evidence, 150)}\"" if evidence else
                         f"{skill} - required by the JD and present on your resume; prepare a concrete example.")
    if not strengths:
        strengths.append("Transferable experience - map each JD requirement to a project you have done.")

    gaps = [
        f"{skill} - the JD stresses it but your resume doesn't show it. Prepare a STAR story that demonstrates it."
        if skill in SOFT_SKILLS else
        f"{skill} - emphasised in the JD but not visible on your resume. Revise the fundamentals and prepare an "
        f"honest answer about how you would ramp up quickly."
        for skill in missing[:5]
    ]

    areas = [sk for sk in matched if sk in AREA_SKILLS][:3] or [sk for sk in resume_skills if sk in AREA_SKILLS][:3]
    tools = [sk for sk in resume_skills if sk not in AREA_SKILLS and sk not in SOFT_SKILLS][:4]
    top_jd = ", ".join([sk for sk in jd_skills if sk not in SOFT_SKILLS][:3]) or "the skills in this JD"
    highlight = achievements[0].rstrip(".;") if achievements else ""
    article = "an" if title[:1].lower() in "aeiou" else "a"
    focus = f" in {_join(areas)}" if areas else ""
    hands_on = f", working hands-on with {_join(tools)}" if tools else ""
    pitch = (
        f"I'm {(article + ' ' + title) if title else 'a professional'} with {ctx.years_label} of experience"
        f"{focus}{hands_on}. "
        + (f"Recently, I {highlight[0].lower() + highlight[1:]}. " if highlight else "")
        + f"What I enjoy most is turning ambiguous business problems into solutions that are actually used. "
        f"I'm excited about {role} at {ctx.company} because it brings together {top_jd} - exactly the work I want "
        f"to deepen - and I'd love to bring my experience to your team."
    )
    coverage = f"{len(matched)} of the {len(jd_skills)}" if jd_skills else "several of the"
    summary = (
        f"Your resume covers {coverage} skills highlighted in the JD"
        + (f" ({', '.join(matched[:4])})" if matched else "")
        + "."
        + (f" Biggest gaps to prepare: {', '.join(missing[:3])}." if missing else " No major keyword gaps found.")
        + " Expect deep-dives into the projects on your resume - have numbers ready."
    )
    probes = [
        {
            "item": _clip(line, 170),
            "likely_questions": [
                "Walk me through this end to end - what was your exact role?",
                "How did you measure the impact, and how confident are you in that number?",
                "What would you do differently if you rebuilt it today?",
            ],
        }
        for line in achievements[:4]
    ]
    return Profile.model_validate(
        {
            "candidate_name": _guess_name(ctx.resume_text),
            "current_title": title,
            "target_role": ctx.role,
            "seniority": ctx.band,
            "summary": summary,
            "elevator_pitch": pitch,
            "strengths": strengths,
            "gaps": gaps,
            "matched_skills": matched,
            "missing_skills": missing,
            "resume_probes": probes,
        }
    ).model_dump()


def build_company(ctx: PrepContext, jd_skills: list[str]) -> dict[str, Any]:
    skills = ", ".join(jd_skills[:3]) or "the core skills in the JD"
    senior = ctx.years >= 5
    consulting = bool(re.search(r"consult|client", ctx.jd_text, re.IGNORECASE))
    rounds = [
        {"name": "Recruiter / HR screen", "format": "Phone or video call, 20-30 min (typical)",
         "what_they_test": "Motivation, experience summary, notice period and compensation expectations",
         "tips": "Have your 60-second pitch, notice period and salary range ready."},
        {"name": "Online assessment or technical screen", "format": "Timed test or live coding (typical)",
         "what_they_test": f"Fundamentals in {skills}; coding / SQL problem solving",
         "tips": "Practise timed problems and explain your approach before coding."},
        {"name": "Technical deep-dive", "format": "1-2 rounds with senior team members (typical)",
         "what_they_test": "Your resume projects, technical depth, trade-offs and problem solving",
         "tips": "Prepare two project deep-dives with numbers, alternatives considered and lessons."},
    ]
    if senior or consulting:
        rounds.append(
            {"name": "Case study / design round" if consulting else "System design round",
             "format": "Whiteboard discussion or take-home (typical)",
             "what_they_test": "Structured thinking, business framing and design trade-offs",
             "tips": "Clarify, structure, state assumptions, and finish with a recommendation."})
    rounds.append(
        {"name": "Managerial / culture-fit round", "format": "Hiring manager or leadership (typical)",
         "what_they_test": "Ownership, communication, stakeholder management and motivation",
         "tips": f"Use STAR stories and show genuine interest in {ctx.company}'s work."})
    research_md = (
        f"## Offline mode\n\nLive web research is disabled because no Claude API key is configured, so this kit "
        f"does not contain researched facts about **{ctx.company}**.\n\n"
        f"**Skills detected in the job description:** {', '.join(jd_skills) or 'none detected'}\n\n"
        "Connect Claude to get: the company's interview process, questions candidates actually reported "
        "(Glassdoor, AmbitionBox, GeeksforGeeks...), culture themes and recent news."
    )
    return CompanyIntel.model_validate(
        {
            "name": ctx.company,
            "overview": f"Offline demo mode can't look up {ctx.company} on the web. Connect Claude "
            "(ANTHROPIC_API_KEY) for a researched company snapshot, real interview rounds and reported questions.",
            "hiring_focus": f"Based on the JD: {', '.join(jd_skills[:6]) or 'see the job description'}.",
            "interview_rounds": rounds,
            "focus_areas": jd_skills[:8],
            "culture_values": ["Ownership and accountability (typical)", "Client / customer focus (typical)",
                               "Collaboration across teams (typical)", "Continuous learning (typical)"],
            "insider_tips": [
                f"Read {ctx.company}'s website, recent case studies/blog posts and news before each round.",
                "Expect questions on every tool on your resume - remove anything you can't discuss in depth.",
                "Quantify the impact of every project you mention.",
                "Prepare 3 thoughtful questions for each interviewer.",
            ],
            "reported_questions": [],
            "questions_to_ask_them": [
                "What does success look like in the first 90 days for this role?",
                "What are the biggest challenges the team is working on right now?",
                "How are projects scoped and prioritised with clients/stakeholders?",
                "How do you support learning and growth for people in this role?",
                "What do the best people on this team do differently?",
            ],
            "research_mode": "offline",
            "research_md": research_md,
            "sources": [],
        }
    ).model_dump()


def build_study_plan(topics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    names = [t["name"] for t in topics]
    high = [t["name"] for t in topics if t["priority"] == "high"] or names[:3]
    rest = [n for n in names if n not in high and n != "Behavioural & HR"]
    return [
        {"title": "Block 1 · 2 hours", "focus": "High-priority technical topics: " + ", ".join(high[:4]),
         "tasks": ["Read the crash-revision notes for each high-priority topic.",
                   "Answer every 🔥 hot theory question aloud, then compare with the model answer.",
                   "Mark anything shaky as 'Review later'."]},
        {"title": "Block 2 · 2 hours", "focus": "Hands-on practice",
         "tasks": ["Solve the practical questions without looking at the solution first.",
                   "Time yourself: about 15 minutes per problem.",
                   "Write down edge cases and complexity for each solution."]},
        {"title": "Block 3 · 1.5 hours", "focus": "Scenarios and your projects",
         "tasks": ["Work through the scenario questions using the approach steps.",
                   "Prepare two project deep-dives from your resume with numbers.",
                   "Use 'Practise' on two answers to get feedback."]},
        {"title": "Block 4 · 1 hour", "focus": "Secondary topics: " + (", ".join(rest[:5]) or "remaining topics"),
         "tasks": ["Skim the cheat sheets and key concepts.", "Answer the beginner and intermediate questions quickly."]},
        {"title": "Block 5 · 1 hour", "focus": "Behavioural round and final self-test",
         "tasks": ["Rehearse 'Tell me about yourself' and three STAR stories.",
                   "Take the full MCQ quiz and revisit topics you got wrong.",
                   "Prepare your questions for the interviewers."]},
    ]


# --------------------------------------------------------------------------- run
async def run_demo(
    ctx: PrepContext,
    *,
    settings: Settings,
    tracker: ProgressTracker,
    builder: ResultBuilder,
    warnings: list[str],
    store: Store,
) -> None:
    delay = settings.demo_step_delay

    async def pause(factor: float = 1.0) -> None:
        if delay:
            await asyncio.sleep(delay * factor)

    tracker.step("parse", "running")
    await pause(0.5)
    tracker.step("parse", "done", detail=f"Resume {len(ctx.resume_text):,} chars · JD {len(ctx.jd_text):,} chars")

    tracker.step("research", "running", detail="Offline knowledge base")
    tracker.log("Offline demo mode: live web research needs ANTHROPIC_API_KEY - using the built-in knowledge base.",
                "warn")
    jd_skills = extract_skills(f"{ctx.role}\n{ctx.jd_text}")
    tracker.log(f"Skills found in the JD: {', '.join(jd_skills[:12]) or 'none detected'}", "result")
    resume_skills = extract_skills(ctx.resume_text)
    tracker.log(f"Skills found in your resume: {', '.join(resume_skills[:12]) or 'none detected'}", "result")
    await pause()
    tracker.step("research", "done", detail="Offline knowledge base (no live web research)")
    warnings.append(OFFLINE_NOTE)

    tracker.step("blueprint", "running", detail="Matching JD skills to interview topics…")
    selected = select_topics(ctx.jd_text, ctx.resume_text, ctx.role, ctx.additional_context, ctx.targets["topics"])
    topics = [
        {"id": f"tp-{entry['topic']['key']}", "name": entry["topic"]["name"], "priority": entry["priority"],
         "weight": entry["weight"],
         "why": ("Matched keywords in your JD/resume" if entry["score"] else "Core topic for most interviews")
         + (f" (relevance score {entry['score']})" if entry["score"] else ""),
         "subtopics": entry["topic"]["subtopics"]}
        for entry in selected
    ]
    builder.set(
        profile=build_profile(ctx),
        company=build_company(ctx, jd_skills),
        topics=topics,
        study_plan=build_study_plan(topics),
    )
    await pause()
    tracker.step("blueprint", "done", detail=f"{len(topics)} topics planned")
    tracker.log(f"Topic plan: {', '.join(t['name'] for t in topics)}", "result")
    tracker.section_ready("overview")

    revision = []
    for entry in selected:
        topic = entry["topic"]
        revision.append({"topic": topic["name"], "priority": entry["priority"],
                         "why_it_matters": f"{topic['name']} came up as {entry['priority']} priority for this JD.",
                         **topic["revision"]})
    for section, items in (
        ("revision", normalize_items("revision", revision, origin="kb")),
        ("theory", pick_items("theory", selected, ctx)),
        ("practical", pick_items("practical", selected, ctx)),
        ("scenario", pick_items("scenario", selected, ctx)),
        ("quiz", pick_items("quiz", selected, ctx)),
    ):
        tracker.step(section, "running")
        await pause(0.6)
        added = builder.add_items(section, items)
        tracker.log(f"+{len(added)} {section} items from the knowledge base", "result")
        tracker.step(section, "done", detail=f"{len(builder.result[section])} ready")
        tracker.section_ready(section)

    counts = builder.counts()
    tracker.log(f"Done: {counts['questions']} questions across {counts['topics']} topics.", "success")


# ----------------------------------------------------------------- on-demand
def demo_generate_more(session: dict[str, Any], *, section: str, count: int, level: str, topic: str) -> list[dict[str, Any]]:
    result = session.get("result") or {}
    ctx = PrepContext.from_session(session)
    planned = [topic_by_name(t["name"]) for t in result.get("topics") or []]
    if topic:
        match = topic_by_name(topic)
        order = [match] if match else []
    else:
        order = [t for t in planned if t] + [t for t in TOPICS if t not in planned]

    if section == "revision":
        covered = {n["topic"].lower() for n in result.get("revision") or []}
        notes = []
        for kb_topic in order:
            if kb_topic["name"].lower() in covered:
                continue
            notes.append({"topic": kb_topic["name"], "priority": "medium", **kb_topic["revision"]})
            if len(notes) >= count:
                break
        return normalize_items("revision", notes, origin="more")

    seen = [_signature(str(i.get("question", ""))) for i in result.get(section) or []]
    picked = []
    for kb_topic in order:
        for raw in kb_topic[section]:
            if level in LEVELS and raw["level"] != level:
                continue
            if _signature(raw["question"]) in seen:
                continue
            picked.append(_with_topic(raw, kb_topic, ctx))
            if len(picked) >= count:
                return normalize_items(section, picked, origin="more")
    return normalize_items(section, picked, origin="more")


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9+#/]+", (text or "").lower()) if len(w) > 2 and w not in STOPWORDS}


def demo_evaluate(section: str, item: dict[str, Any], answer: str) -> dict[str, Any]:
    """Heuristic answer scoring against the reference key points (offline mode)."""
    points = list(item.get("key_points") or item.get("what_interviewer_looks_for") or item.get("approach") or [])
    if section == "scenario":
        points += [s.get("step", "") for s in item.get("approach_steps") or []]
    reference = item.get("answer_md") or item.get("solution_md") or item.get("model_answer_md") or ""
    if not points:
        points = [s for s in re.split(r"(?<=[.!?])\s+", reference) if len(s) > 30][:5]

    answer_words = _words(answer)
    n_words = len(answer.split())
    covered, missing = [], []
    for point in points:
        words = _words(point)
        if not words:
            continue
        overlap = len(words & answer_words)
        (covered if overlap >= max(1, round(len(words) * 0.34)) else missing).append(point)
    coverage = len(covered) / max(1, len(covered) + len(missing))

    lowered = answer.lower()
    has_example = any(k in lowered for k in ("for example", "e.g", "for instance", "in my", "we built", "i built",
                                             "i used", "in one project", "at my"))
    has_numbers = bool(re.search(r"\d", answer))
    has_tradeoff = any(k in lowered for k in ("trade-off", "tradeoff", "however", "depends", "downside", "but "))
    structure = (has_example + has_numbers + has_tradeoff) / 3
    length = min(1.0, n_words / 120)
    score = round(10 * (0.6 * coverage + 0.25 * length + 0.15 * structure))
    if n_words < 8:
        score = min(score, 2)
    score = max(0, min(10, score))

    if score >= 8:
        verdict = "Strong answer - it covers the key points an interviewer listens for."
    elif score >= 6:
        verdict = "Solid answer with a few gaps - tighten it with the missing points below."
    elif score >= 4:
        verdict = "Partially there - the core idea is visible but important points are missing."
    else:
        verdict = "Needs work - compare carefully with the model answer and try again."

    strengths = [f"Covered: {p}" for p in covered[:3]]
    if has_example:
        strengths.append("Used a concrete example - interviewers value that.")
    if has_numbers:
        strengths.append("Quantified details make the answer credible.")
    improvements = []
    if missing:
        improvements.append("Address the missing key points listed below.")
    if not has_example:
        improvements.append("Add a concrete example from your own projects.")
    if not has_numbers and section != "theory":
        improvements.append("Quantify the impact or scale (%, time, money, data volume).")
    if not has_tradeoff:
        improvements.append("Mention a trade-off or limitation to show depth.")
    if n_words < 60:
        improvements.append("Expand the answer - aim for 1-2 minutes when spoken (about 150-250 words).")

    return {
        "score": score,
        "verdict": verdict,
        "strengths": strengths,
        "improvements": improvements,
        "missing_points": missing[:6],
        "improved_answer_md": ("**Model answer (knowledge base):**\n\n" + reference) if reference else "",
        "engine": "offline",
    }
