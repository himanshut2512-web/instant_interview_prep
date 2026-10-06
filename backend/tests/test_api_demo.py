"""End-to-end API flow in offline demo mode (no API key)."""

import io

import docx
import pytest

from conftest import sample_form, wait_for


def test_health_reports_demo_mode(client):
    body = client.get("/api/health").json()
    assert body["mode"] == "demo" and body["ai_available"] is False
    assert set(body["depths"]) == {"quick", "standard", "deep"}
    assert client.get("/api/sample").json()["company"]


@pytest.mark.parametrize("depth", ["quick", "standard", "deep"])
def test_full_prep_kit_has_at_least_50_questions(client, depth):
    created = client.post("/api/sessions", data=sample_form(depth=depth))
    assert created.status_code == 201
    session_id = created.json()["id"]
    status = wait_for(client, session_id)
    assert status["status"] == "completed", status
    assert status["progress"]["percent"] == 100

    session = client.get(f"/api/sessions/{session_id}").json()
    result = session["result"]
    counts = session["summary"]
    assert counts["questions"] >= 50
    for section in ("revision", "theory", "practical", "scenario", "quiz"):
        assert result[section], section
    assert {i["level"] for i in result["theory"]} == {"beginner", "intermediate", "advanced"}
    assert any(i["hot"] for i in result["theory"])
    assert result["profile"]["elevator_pitch"] and result["company"]["interview_rounds"]
    assert result["company"]["research_mode"] == "offline"
    assert set(status["progress"]["sections_ready"]) >= {"overview", "revision", "theory", "practical", "scenario", "quiz"}
    assert session["inputs"]["resume_chars"] > 100 and "resume_text" not in session["inputs"]


def test_uploads_actions_export_and_delete(client):
    document = docx.Document()
    for line in ("Priya Sharma", "Data Analyst with 3 years of experience.",
                 "Built Power BI dashboards and SQL reports for 40 stores, cutting reporting time by 60%.",
                 "Skills: SQL, Python, Power BI, Excel, statistics, A/B testing."):
        document.add_paragraph(line)
    buffer = io.BytesIO()
    document.save(buffer)
    files = {
        "resume_file": ("resume.docx", buffer.getvalue(),
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        "extra_files": ("notes.txt", b"Recruiter said: expect a SQL test and a Power BI case study.", "text/plain"),
    }
    analyst_jd = ("Data Analyst - build Power BI dashboards and DAX measures, write SQL on Snowflake, "
                  "analyse A/B tests and present insights to business stakeholders. Excel and Python a plus.")
    form = sample_form(resume_text="", role="Data Analyst", years_experience="3", depth="quick",
                       job_description=analyst_jd)
    created = client.post("/api/sessions", data=form, files=files)
    assert created.status_code == 201, created.text
    session_id = created.json()["id"]
    assert wait_for(client, session_id)["status"] == "completed"

    session = client.get(f"/api/sessions/{session_id}").json()
    assert session["inputs"]["resume_filename"] == "resume.docx"
    assert session["inputs"]["extra_files"][0]["name"] == "notes.txt"
    result = session["result"]
    assert result["profile"]["candidate_name"] == "Priya Sharma"
    assert "BI & Data Visualisation" in [t["name"] for t in result["topics"]]

    # generate more questions (demo: pulled from the knowledge base, never duplicates)
    before = len(result["practical"])
    more = client.post(f"/api/sessions/{session_id}/generate",
                       json={"section": "practical", "count": 3, "level": "mixed", "topic": ""}).json()
    assert len(more["added"]) == 3 and more["counts"]["practical"] == before + 3
    texts = [q["question"] for q in client.get(f"/api/sessions/{session_id}").json()["result"]["practical"]]
    assert len(texts) == len(set(texts))

    # new revision topic on demand
    revision = client.post(f"/api/sessions/{session_id}/generate",
                           json={"section": "revision", "count": 1, "topic": "System Design"}).json()
    assert revision["added"][0]["topic"] == "System Design"

    # answer evaluation (offline heuristic)
    item = result["theory"][0]
    evaluation = client.post(f"/api/sessions/{session_id}/evaluate",
                             json={"section": "theory", "item_id": item["id"], "answer": item["answer_md"]}).json()
    assert evaluation["engine"] == "offline" and evaluation["score"] >= 6
    weak = client.post(f"/api/sessions/{session_id}/evaluate",
                       json={"section": "theory", "item_id": item["id"], "answer": "not sure"}).json()
    assert weak["score"] <= 2 and weak["improvements"]
    assert client.post(f"/api/sessions/{session_id}/evaluate",
                       json={"section": "theory", "item_id": "missing", "answer": "x"}).status_code == 404

    # progress state + quiz attempts
    state = client.put(f"/api/sessions/{session_id}/state", json={"item_id": item["id"], "status": "mastered"}).json()
    assert state["items"][item["id"]] == "mastered"
    assert state["evaluations"][item["id"]] == {"score": weak["score"], "best": evaluation["score"], "attempts": 2}
    state = client.put(f"/api/sessions/{session_id}/state", json={"topic_id": "tp-sql", "revised": True}).json()
    assert state["topics"] == {"tp-sql": True}
    state = client.put(f"/api/sessions/{session_id}/state", json={"item_id": item["id"], "status": None}).json()
    assert item["id"] not in state["items"]
    attempts = client.post(f"/api/sessions/{session_id}/quiz-attempts",
                           json={"total": 10, "correct": 8, "duration_sec": 95,
                                 "answers": [{"id": "q1", "selected": 2, "correct": True}]}).json()
    assert attempts[-1]["score_pct"] == 80
    assert client.post(f"/api/sessions/{session_id}/quiz-attempts", json={"total": 5, "correct": 6}).status_code == 422

    # export + listing + delete
    export = client.get(f"/api/sessions/{session_id}/export.md")
    assert export.status_code == 200 and "# Interview Prep Kit" in export.text and "## 8. MCQ quiz" in export.text
    assert any(s["id"] == session_id for s in client.get("/api/sessions").json())
    assert client.delete(f"/api/sessions/{session_id}").status_code == 204
    assert client.get(f"/api/sessions/{session_id}").status_code == 404


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"company": "  "}, "company"),
        ({"resume_text": "too short"}, "resume"),
        ({"job_description": ""}, "job description"),
        ({"years_experience": "75"}, "Years of experience"),
        ({"depth": "huge"}, "Depth"),
        ({"mode": "ai"}, "ANTHROPIC_API_KEY"),
    ],
)
def test_validation_errors(client, overrides, message):
    response = client.post("/api/sessions", data=sample_form(**overrides))
    assert response.status_code in (400, 422)
    assert message.lower() in response.json()["detail"].lower()


def test_unsupported_upload_and_unknown_routes(client):
    response = client.post("/api/sessions", data=sample_form(resume_text=""),
                           files={"resume_file": ("photo.png", b"\x89PNG....", "image/png")})
    assert response.status_code == 422 and "Unsupported file type" in response.json()["detail"]
    assert client.get("/api/nope").status_code == 404
    assert client.get("/api/sessions/doesnotexist").status_code == 404


def test_retry_regenerates_a_session(client):
    session_id = client.post("/api/sessions", data=sample_form(depth="quick")).json()["id"]
    assert wait_for(client, session_id)["status"] == "completed"
    assert client.post(f"/api/sessions/{session_id}/retry").json()["status"] == "queued"
    assert wait_for(client, session_id)["status"] == "completed"
