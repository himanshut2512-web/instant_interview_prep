"""AI-mode pipeline tests with a fake Anthropic client (no network, no API key needed).

The fake implements `client.beta.messages.stream(**params)` and answers based on
what the request asks for: research requests (with web tools) return
server-tool blocks + a report; structured-output requests return JSON matching
the requested schema.
"""

import dataclasses
import json
import re
from types import SimpleNamespace

import anthropic
import httpx
import pytest
from fastapi.testclient import TestClient

from app.agent import research as research_module
from app.agent.llm import ClaudeLLM
from app.main import create_app
from conftest import FakeGoogle, sample_form, signup, wait_for


def text_block(text):
    return SimpleNamespace(type="text", text=text, citations=None)


def message(blocks, stop_reason="end_turn"):
    return SimpleNamespace(content=blocks, stop_reason=stop_reason, stop_details=None)


class FakeStream:
    def __init__(self, msg):
        self.msg = msg

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    def __aiter__(self):
        async def gen():
            for block in self.msg.content:
                yield SimpleNamespace(type="content_block_stop", content_block=block)
        return gen()

    async def get_final_message(self):
        return self.msg


def _prompt_text(params):
    parts = []
    for msg in params["messages"]:
        content = msg["content"]
        if isinstance(content, str):
            parts.append(content)
        else:
            parts.extend(b.get("text", "") for b in content if isinstance(b, dict))
    return "\n".join(parts)


class FakeMessages:
    def __init__(self, owner):
        self.owner = owner

    def stream(self, **params):
        self.owner.calls.append(params)
        return FakeStream(self.owner.respond(params))


class FakeClient:
    """Mimics the parts of anthropic.AsyncAnthropic the agent uses."""

    def __init__(self, web_search_fails=False, reject_betas=False):
        self.calls = []
        self.web_search_fails = web_search_fails
        self.reject_betas = reject_betas
        self.beta = SimpleNamespace(messages=FakeMessages(self))

    def respond(self, params):
        if self.reject_betas and "betas" in params:
            request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
            raise anthropic.BadRequestError("unknown beta", response=httpx.Response(400, request=request), body=None)
        prompt = _prompt_text(params)
        if params.get("tools"):
            return self.research(params)
        schema = (params.get("output_config") or {}).get("format", {}).get("schema")
        if schema is None:  # plain text request (fallback research summary)
            return message([text_block("## Company snapshot\n- Fallback research report " + "x" * 300)])
        props = schema["properties"]
        if "profile" in props:
            return message([text_block(json.dumps(self.blueprint()))])
        if "notes" in props:
            topics = re.search(r"in this order: (.+?)\.\n", prompt).group(1).split("; ")
            return message([text_block(json.dumps({"notes": [self.note(t) for t in topics]}))])
        if "score" in props:
            return message([text_block(json.dumps({
                "score": 7, "verdict": "Good", "strengths": ["clear"], "improvements": ["add numbers"],
                "missing_points": [], "improved_answer_md": "Better answer"}))])
        item_props = props["questions"]["items"]["properties"]
        count = int(re.search(r"Write (\d+)", prompt).group(1))
        level = re.search(r"at \*\*(\w+)\*\* level", prompt).group(1)
        kind = next(k for k in ("answer_md", "solution_md", "model_answer_md", "options") if k in item_props)
        start = len(self.calls) * 100
        return message([text_block(json.dumps({"questions": [self.question(kind, level, start + i) for i in range(count)]}))])

    # -------------------------------------------------------------- canned data
    def research(self, params):
        if self.web_search_fails:
            request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
            raise anthropic.BadRequestError("web search is not enabled", response=httpx.Response(400, request=request),
                                            body=None)
        blocks = [
            SimpleNamespace(type="thinking", thinking="Looking for interview experiences first."),
            SimpleNamespace(type="server_tool_use", name="web_search", input={"query": "Acme data scientist interview"}),
            SimpleNamespace(type="web_search_tool_result", content=[
                SimpleNamespace(url="https://www.glassdoor.com/acme", title="Acme interview questions"),
                SimpleNamespace(url="https://www.ambitionbox.com/acme", title="Acme interviews | AmbitionBox"),
            ]),
            SimpleNamespace(type="server_tool_use", name="web_fetch", input={"url": "https://www.glassdoor.com/acme"}),
            SimpleNamespace(type="web_fetch_tool_result", content=SimpleNamespace(
                type="web_fetch_result", url="https://www.glassdoor.com/acme", content=SimpleNamespace(title="Glassdoor"))),
            text_block("## Company snapshot\n- Acme builds analytics.\n## Reported interview questions\n"
                       "- Explain bias-variance trade-off [Technical] (Glassdoor)\n" + "More detail. " * 30),
        ]
        return message(blocks)

    @staticmethod
    def blueprint():
        topics = ["Machine Learning", "SQL", "Python", "Statistics", "GenAI", "Spark", "MLOps", "Case Studies",
                  "Deep Learning", "Behavioural"]
        return {
            "profile": {"candidate_name": "Aarav", "current_title": "Data Scientist", "target_role": "Senior DS",
                        "seniority": "Mid", "summary": "Good fit", "elevator_pitch": "I am...", "strengths": ["ML"],
                        "gaps": ["Spark"], "matched_skills": ["Python"], "missing_skills": ["Spark"],
                        "resume_probes": [{"item": "Forecasting", "likely_questions": ["How?"]}]},
            "company": {"name": "Acme", "overview": "Analytics firm", "hiring_focus": "Applied ML",
                        "interview_rounds": [{"name": "Tech 1", "format": "Live", "what_they_test": "ML", "tips": "Prep"}],
                        "focus_areas": ["ML"], "culture_values": ["Ownership"], "insider_tips": ["Be crisp"],
                        "reported_questions": [{"question": "Explain bias-variance", "round": "Tech", "source": "Glassdoor"}],
                        "questions_to_ask_them": ["What does success look like?"]},
            "topics": [{"name": n, "priority": "high" if i < 3 else "medium", "weight": 90 - i * 5, "why": "JD",
                        "subtopics": ["a", "b"]} for i, n in enumerate(topics)],
            "study_plan": [{"title": "Block 1", "focus": "ML", "tasks": ["Revise"]}],
        }

    @staticmethod
    def note(topic):
        return {"topic": topic, "priority": "high", "summary": f"{topic} summary", "why_it_matters": "JD",
                "key_concepts": [{"term": "T", "explanation": "E"}], "explanation_md": "Long explanation",
                "code_example": {"language": "python", "code": "print(1)"}, "pitfalls": ["p"],
                "interview_tips": ["t"], "cheat_sheet": ["c"], "likely_questions": ["q?"]}

    @staticmethod
    def question(kind, level, n):
        base = {"topic": "Machine Learning", "level": level, "hot": n % 3 == 0, "hot_reason": "Glassdoor" if n % 3 == 0 else "",
                "question": f"Unique interview question number {n} about topic {n * 7}?"}
        if kind == "answer_md":
            return {**base, "answer_md": "Answer", "key_points": ["k"], "interview_tip": "tip", "follow_ups": ["f"]}
        if kind == "solution_md":
            return {**base, "context": "ctx", "approach": ["a"], "solution_md": "sol",
                    "code": {"language": "python", "code": "x = 1"}, "complexity": "O(n)", "edge_cases": ["e"],
                    "interview_tip": "tip", "follow_ups": ["f"]}
        if kind == "model_answer_md":
            return {**base, "scenario": "A situation", "approach_steps": [{"step": "Clarify", "detail": "d"}],
                    "model_answer_md": "Answer", "what_interviewer_looks_for": ["w"], "mistakes_to_avoid": ["m"],
                    "follow_ups": ["f"]}
        return {**base, "options": ["A", "B", "C", "D"], "correct_index": n % 4, "explanation": "because",
                "option_explanations": ["1", "2", "3", "4"], "interview_tip": "tip"}


@pytest.fixture
def ai_setup(tmp_path, settings):
    def make(**fake_kwargs):
        fake = FakeClient(**fake_kwargs)
        ai_settings = dataclasses.replace(settings, anthropic_api_key="test-key", max_concurrency=4)
        app = create_app(ai_settings, llm_factory=lambda s: ClaudeLLM(s, client=fake), google_exchange=FakeGoogle())
        test_client = TestClient(app)
        signup(test_client)
        return fake, test_client
    return make


def test_ai_pipeline_end_to_end(ai_setup):
    fake, test_client = ai_setup()
    with test_client as client:
        assert client.get("/api/health").json()["mode"] == "ai"
        session_id = client.post("/api/sessions", data=sample_form(company="Acme")).json()["id"]
        status = wait_for(client, session_id)
        assert status["status"] == "completed", status
        session = client.get(f"/api/sessions/{session_id}").json()
        result = session["result"]

        # research captured live sources and progress notes
        assert result["company"]["research_mode"] == "live_web"
        assert {s["url"] for s in result["company"]["sources"]} >= {"https://www.glassdoor.com/acme",
                                                                     "https://www.ambitionbox.com/acme"}
        logs = " ".join(entry["msg"] for entry in status["progress"]["logs"])
        assert "Acme data scientist interview" in logs and "Looking for interview experiences" in logs

        # every section hit its target for the standard depth (24/15/15/25) with all three levels
        assert len(result["topics"]) == 10 and len(result["revision"]) == 10
        assert (len(result["theory"]), len(result["practical"]), len(result["scenario"]), len(result["quiz"])) == (24, 15, 15, 25)
        assert {q["level"] for q in result["quiz"]} == {"beginner", "intermediate", "advanced"}
        assert session["summary"]["questions"] == 79

        # requests used Claude correctly: structured outputs, effort, cache breakpoints, refusal fallbacks
        generation = [c for c in fake.calls if "format" in (c.get("output_config") or {})]
        assert all(c["model"] == "claude-opus-5-5" and c["fallbacks"] == "default" for c in generation)
        assert all("server-side-fallback-2026-07-01" in c["betas"] for c in generation)
        assert all(c["output_config"]["effort"] in ("low", "medium", "high", "xhigh", "max") for c in generation)
        assert all(c["messages"][0]["content"][0]["cache_control"] == {"type": "ephemeral"} for c in generation)
        research_call = next(c for c in fake.calls if c.get("tools"))
        assert {t["type"] for t in research_call["tools"]} == {"web_search_20260209", "web_fetch_20260209"}
        assert research_call["thinking"] == {"type": "adaptive", "display": "updates"}

        # on-demand actions go through Claude in AI mode
        more = client.post(f"/api/sessions/{session_id}/generate",
                           json={"section": "scenario", "count": 4, "level": "advanced", "focus": "client escalations"}).json()
        assert len(more["added"]) == 4 and all(i["origin"] == "more" for i in more["added"])
        assert "client escalations" in _prompt_text(fake.calls[-1])
        item = result["theory"][0]
        evaluation = client.post(f"/api/sessions/{session_id}/evaluate",
                                 json={"section": "theory", "item_id": item["id"], "answer": "My answer"}).json()
        assert evaluation == {"score": 7, "verdict": "Good", "strengths": ["clear"], "improvements": ["add numbers"],
                              "missing_points": [], "improved_answer_md": "Better answer", "engine": "ai"}
        assert fake.calls[-1]["output_config"]["effort"] == "low"


def test_research_falls_back_when_web_search_is_unavailable(ai_setup, monkeypatch):
    def fake_ddgs(queries, per_query):
        return [{"query": q, "title": f"Result for {q}", "url": f"https://example.com/{i}", "snippet": "snippet"}
                for i, q in enumerate(queries)]

    async def no_pages(urls, limit_chars=6000):
        return {}

    monkeypatch.setattr(research_module, "_ddgs_search", fake_ddgs)
    monkeypatch.setattr(research_module, "_fetch_pages", no_pages)
    fake, test_client = ai_setup(web_search_fails=True)
    with test_client as client:
        session_id = client.post("/api/sessions", data=sample_form(company="Acme", depth="quick")).json()["id"]
        assert wait_for(client, session_id)["status"] == "completed"
        company = client.get(f"/api/sessions/{session_id}").json()["result"]["company"]
        assert company["research_mode"] == "search_fallback"
        assert company["sources"][0]["url"].startswith("https://example.com/")


def test_research_uses_model_knowledge_when_no_search_works(ai_setup, monkeypatch):
    def broken(queries, per_query):
        raise RuntimeError("network blocked")

    monkeypatch.setattr(research_module, "_ddgs_search", broken)
    fake, test_client = ai_setup(web_search_fails=True)
    with test_client as client:
        session_id = client.post("/api/sessions", data=sample_form(company="Acme", depth="quick")).json()["id"]
        status = wait_for(client, session_id)
        assert status["status"] == "completed"
        session = client.get(f"/api/sessions/{session_id}").json()
        assert session["result"]["company"]["research_mode"] == "model_knowledge"
        assert any("Claude's own knowledge" in w for w in session["warnings"])


def test_optional_betas_are_dropped_if_rejected(ai_setup):
    fake, test_client = ai_setup(reject_betas=True)
    with test_client as client:
        session_id = client.post("/api/sessions", data=sample_form(company="Acme", depth="quick")).json()["id"]
        assert wait_for(client, session_id)["status"] == "completed"
        later = [c for c in fake.calls if "format" in (c.get("output_config") or {})][-1]
        assert "betas" not in later and "fallbacks" not in later
