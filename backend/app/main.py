"""FastAPI application: REST API for the prep agent (+ the built React app, if present)."""

from __future__ import annotations

import asyncio
import logging
import re
import uuid
from contextlib import asynccontextmanager
from typing import Any, Callable, Literal
from urllib.parse import urlsplit

import anthropic
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import __version__
from .accounts import AccountError, Accounts, PasswordServiceBusy
from .agent import actions
from .agent.llm import ClaudeLLM, LLMError
from .agent.pipeline import friendly_error, run_session
from .agent.plan import DEPTHS
from .agent.progress import initial_progress
from .auth import GoogleExchange, build_auth, google_code_exchange
from .config import Settings, get_settings
from .export import export_markdown
from .mailer import Mailer
from .models import ALL_SECTIONS, QUESTION_SECTIONS, dedupe, empty_result, result_counts
from .parsing import UnsupportedFileError, extract_text, is_pdf
from .ratelimit import RateLimiter
from .samples import SAMPLE_INPUT
from .storage import Store, utcnow

log = logging.getLogger("prep.api")

MIN_DOC_CHARS = 80
MAX_RESUME_CHARS = 60_000
MAX_JD_CHARS = 40_000
MAX_EXTRA_CHARS = 30_000
MAX_QUIZ_ATTEMPTS = 50
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


# ----------------------------------------------------------------------------- bodies
class GenerateBody(BaseModel):
    section: Literal["revision", "theory", "practical", "scenario", "quiz"]
    count: int = Field(5, ge=1, le=15)
    level: Literal["mixed", "beginner", "intermediate", "advanced"] = "mixed"
    topic: str = Field("", max_length=120)
    focus: str = Field("", max_length=500)


class EvaluateBody(BaseModel):
    section: Literal["theory", "practical", "scenario"]
    item_id: str = Field(..., max_length=64)
    answer: str = Field(..., min_length=1, max_length=8000)


class StateBody(BaseModel):
    item_id: str | None = Field(None, max_length=64)
    status: Literal["mastered", "review"] | None = None
    topic_id: str | None = Field(None, max_length=64)
    revised: bool | None = None


class QuizAnswer(BaseModel):
    id: str = Field(..., max_length=64)
    selected: int | None = None
    correct: bool


class QuizAttemptBody(BaseModel):
    total: int = Field(..., ge=1, le=500)
    correct: int = Field(..., ge=0, le=500)
    duration_sec: int = Field(0, ge=0, le=86_400)
    filters: dict[str, Any] = Field(default_factory=dict)
    answers: list[QuizAnswer] = Field(default_factory=list, max_length=500)


# ------------------------------------------------------------------------------- app
def create_app(
    settings: Settings | None = None,
    llm_factory: Callable[[Settings], ClaudeLLM] | None = None,
    google_exchange: GoogleExchange | None = None,
    mailer: Mailer | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    store = Store(settings.db_path)
    accounts = Accounts(store, session_days=settings.session_days)
    mailer = mailer or Mailer(settings)
    llm: ClaudeLLM | None = None
    if settings.ai_enabled:
        llm = (llm_factory or ClaudeLLM)(settings)
    running: dict[str, asyncio.Task] = {}
    locks: dict[str, asyncio.Lock] = {}

    def lock_for(session_id: str) -> asyncio.Lock:
        return locks.setdefault(session_id, asyncio.Lock())

    async def check_sign_in_setup() -> None:
        """Check the Google and SMTP credentials once at boot, so mistakes show up in the log
        straight away instead of at a user's first sign-in or password reset."""
        from .setup_auth import check_google, check_smtp

        hint = "run `python -m app.setup_auth` in the backend folder to fix it"
        if google_exchange is None and settings.google_enabled:
            ok, message = await asyncio.to_thread(check_google, settings.google_client_id, settings.google_client_secret)
            if ok:
                log.info("Google sign-in check: %s", message)
            else:
                log.error("Google sign-in check failed: %s - %s", message, hint)
        if isinstance(mailer, Mailer) and mailer.configured:
            ok, message = await asyncio.to_thread(check_smtp, settings)
            if ok:
                log.info("Password-reset email check: %s", message)
            else:
                log.error("Password-reset email check failed: %s - %s", message, hint)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        interrupted = store.mark_interrupted()
        if interrupted:
            log.warning("Marked %d interrupted session(s) as failed", interrupted)
        log.info("InstantInterviewPrep %s ready - mode: %s", __version__, "AI (Claude)" if llm else "offline demo")
        log.info(
            "Sign-in: email + password%s; password-reset email %s",
            " + Google" if settings.google_enabled else " (Google NOT configured)",
            "enabled" if mailer.configured else "NOT configured - reset links are written to this log",
        )
        missing = [name for name, ready in (("Google sign-in", settings.google_enabled),
                                            ("password-reset email", mailer.configured)) if not ready]
        if missing:
            log.warning("To turn on %s, run `python -m app.setup_auth` in the backend folder (free, about 5 minutes).",
                        " and ".join(missing))
        if settings.google_client_id and not settings.google_client_secret:
            log.warning("PREP_GOOGLE_CLIENT_ID is set but PREP_GOOGLE_CLIENT_SECRET is not - Google sign-in is off.")
        setup_check = asyncio.create_task(check_sign_in_setup())
        yield
        setup_check.cancel()
        for task in list(running.values()):
            task.cancel()
        store.close()

    app = FastAPI(title="InstantInterviewPrep API", version=__version__, lifespan=lifespan)
    app.state.settings = settings
    app.state.store = store
    app.state.running = running
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def origin_allowed(origin: str, request: Request) -> bool:
        return (
            origin in settings.cors_origins
            or origin == settings.app_url
            or urlsplit(origin).netloc == request.url.netloc
        )

    @app.middleware("http")
    async def protect(request: Request, call_next):
        # Cookies are SameSite=Lax; refusing state-changing API calls from foreign
        # origins adds a second layer against cross-site request forgery.
        origin = request.headers.get("origin")
        if request.method not in SAFE_METHODS and request.url.path.startswith("/api/") and origin:
            if not origin_allowed(origin, request):
                return JSONResponse({"detail": "Cross-site request blocked."}, status_code=403)
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("X-Frame-Options", "DENY")
        return response

    @app.exception_handler(AccountError)
    async def account_error(_: Request, exc: AccountError) -> JSONResponse:
        return JSONResponse({"detail": str(exc), "field": exc.field}, status_code=exc.status)

    @app.exception_handler(PasswordServiceBusy)
    async def password_busy(_: Request, exc: PasswordServiceBusy) -> JSONResponse:
        log.error("Password hashing is short of memory: %s", exc)
        return JSONResponse(
            {"detail": "The server is busy right now. Nothing was changed - please try again in a few seconds."},
            status_code=503,
            headers={"Retry-After": "5"},
        )

    auth_router, current_user = build_auth(
        settings, accounts, mailer, RateLimiter(), google_exchange or google_code_exchange(settings)
    )
    app.include_router(auth_router)
    app.state.accounts = accounts

    def launch(session_id: str) -> None:
        task = asyncio.create_task(
            run_session(session_id, store=store, settings=settings, make_llm=(lambda: llm) if llm else None)
        )
        running[session_id] = task
        task.add_done_callback(lambda _t, sid=session_id: running.pop(sid, None))

    def load(session_id: str, user: dict[str, Any]) -> dict[str, Any]:
        session = store.get(session_id)
        # another user's kit looks exactly like a missing one
        if session is None or session.get("user_id") != user["id"]:
            raise HTTPException(404, "Prep kit not found.")
        return session

    def public(session: dict[str, Any]) -> dict[str, Any]:
        inputs = session.get("inputs") or {}
        data = {k: v for k, v in session.items() if k not in ("inputs", "user_id")}
        data["years_experience"] = data.pop("years", None)
        data["inputs"] = {
            "resume_filename": inputs.get("resume_filename", ""),
            "resume_chars": len(inputs.get("resume_text") or ""),
            "jd_chars": len(inputs.get("jd_text") or ""),
            "extra_notes": inputs.get("extra_notes", ""),
            "extra_files": inputs.get("extra_files", []),
        }
        data["running"] = session["id"] in running
        return data

    # ----------------------------------------------------------------- health
    @app.get("/api/health")
    async def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "version": __version__,
            "mode": "ai" if llm else "demo",
            "ai_available": llm is not None,
            "model": settings.model if llm else None,
            "web_search": bool(llm) and settings.enable_web_search,
            "depths": {name: {k: v for k, v in plan.items() if k in ("topics", *QUESTION_SECTIONS)}
                       for name, plan in DEPTHS.items()},
        }

    @app.get("/api/sample")
    async def sample() -> dict[str, Any]:
        return SAMPLE_INPUT

    # ------------------------------------------------------------- sessions
    async def read_upload(upload: UploadFile, label: str) -> tuple[str, bytes]:
        data = await upload.read()
        if len(data) > settings.max_upload_mb * 1024 * 1024:
            raise HTTPException(413, f"{label} is larger than {settings.max_upload_mb} MB.")
        return upload.filename or label, data

    async def document_text(upload: UploadFile | None, pasted: str, label: str, max_chars: int) -> tuple[str, str]:
        """Return (text, filename) from an uploaded file or pasted text."""
        filename = ""
        text = (pasted or "").strip()
        if upload is not None and upload.filename:
            filename, data = await read_upload(upload, label)
            try:
                text = extract_text(filename, data)
            except UnsupportedFileError as exc:
                raise HTTPException(422, str(exc)) from exc
            except Exception as exc:
                raise HTTPException(422, f"Could not read the {label.lower()} file: {exc}") from exc
            if len(text) < MIN_DOC_CHARS and is_pdf(filename) and llm is not None:
                try:  # scanned / image-only PDF: let Claude read it
                    text = (await llm.transcribe_pdf(data)).strip()
                except Exception as exc:
                    log.warning("PDF transcription failed: %s", exc)
            if len(text) < MIN_DOC_CHARS:
                raise HTTPException(
                    422,
                    f"Could not extract enough text from '{filename}'. If it is a scanned PDF, paste the text instead.",
                )
        if len(text) < MIN_DOC_CHARS:
            raise HTTPException(422, f"Please provide your {label.lower()} (at least {MIN_DOC_CHARS} characters).")
        if len(text) > max_chars:
            raise HTTPException(
                422, f"The {label.lower()} is very long ({len(text):,} characters). Trim it below {max_chars:,}."
            )
        return text, filename

    @app.post("/api/sessions", status_code=201)
    async def create_session(
        company: str = Form(...),
        years_experience: float = Form(...),
        job_description: str = Form(""),
        resume_text: str = Form(""),
        role: str = Form(""),
        extra_notes: str = Form(""),
        depth: str = Form("standard"),
        mode: str = Form("auto"),
        resume_file: UploadFile | None = File(None),
        jd_file: UploadFile | None = File(None),
        extra_files: list[UploadFile] | None = File(None),
        user: dict[str, Any] = Depends(current_user),
    ) -> dict[str, Any]:
        company = re.sub(r"\s+", " ", company).strip()
        role = re.sub(r"\s+", " ", role).strip()
        if not company:
            raise HTTPException(422, "Please enter the target company name.")
        if len(company) > 120 or len(role) > 160:
            raise HTTPException(422, "Company or role name is too long.")
        if not 0 <= years_experience <= 50:
            raise HTTPException(422, "Years of experience must be between 0 and 50.")
        if depth not in DEPTHS:
            raise HTTPException(422, f"Depth must be one of: {', '.join(DEPTHS)}.")
        if mode not in ("auto", "ai", "demo"):
            raise HTTPException(422, "Mode must be auto, ai or demo.")
        if mode == "ai" and llm is None:
            raise HTTPException(400, "AI mode needs ANTHROPIC_API_KEY to be set on the server.")
        run_mode = "ai" if (llm is not None and mode != "demo") else "demo"

        resume, resume_filename = await document_text(resume_file, resume_text, "Resume", MAX_RESUME_CHARS)
        jd, _ = await document_text(jd_file, job_description, "Job description", MAX_JD_CHARS)

        extra_text_parts: list[str] = []
        extra_meta: list[dict[str, Any]] = []
        for upload in extra_files or []:
            if not upload or not upload.filename:
                continue
            name, data = await read_upload(upload, "Attachment")
            try:
                text = extract_text(name, data)
            except Exception as exc:
                raise HTTPException(422, f"Could not read '{name}': {exc}") from exc
            extra_text_parts.append(f"[{name}]\n{text}")
            extra_meta.append({"name": name, "chars": len(text)})
        extra_files_text = "\n\n".join(extra_text_parts)
        if len(extra_notes) + len(extra_files_text) > MAX_EXTRA_CHARS:
            raise HTTPException(422, f"Additional context is too long - keep it under {MAX_EXTRA_CHARS:,} characters.")

        session_id = uuid.uuid4().hex[:12]
        store.create(
            session_id,
            user_id=user["id"],
            status="queued",
            mode=run_mode,
            company=company,
            role=role,
            years=float(years_experience),
            depth=depth,
            inputs={
                "resume_text": resume,
                "resume_filename": resume_filename,
                "jd_text": jd,
                "extra_notes": extra_notes.strip(),
                "extra_files": extra_meta,
                "extra_files_text": extra_files_text,
            },
            progress=initial_progress(company),
            result=empty_result(),
            user_state={"items": {}, "topics": {}, "evaluations": {}},
            quiz_attempts=[],
            warnings=[],
            summary=result_counts(None),
        )
        launch(session_id)
        return {"id": session_id, "status": "queued", "mode": run_mode}

    @app.get("/api/sessions")
    async def list_sessions(user: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
        rows = store.list(user["id"])
        for row in rows:
            row["years_experience"] = row.pop("years", None)
            row["running"] = row["id"] in running
        return rows

    @app.get("/api/sessions/{session_id}")
    async def get_session(session_id: str, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
        return public(load(session_id, user))

    @app.get("/api/sessions/{session_id}/status")
    async def get_status(session_id: str, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
        session = store.get(
            session_id,
            columns=("user_id", "status", "mode", "company", "role", "progress", "error", "warnings", "summary"),
        )
        if session is None or session.pop("user_id", None) != user["id"]:
            raise HTTPException(404, "Prep kit not found.")
        session["running"] = session_id in running
        return session

    @app.delete("/api/sessions/{session_id}", status_code=204)
    async def delete_session(session_id: str, user: dict[str, Any] = Depends(current_user)) -> Response:
        load(session_id, user)
        task = running.pop(session_id, None)
        if task is not None:
            task.cancel()
        if not store.delete(session_id):
            raise HTTPException(404, "Prep kit not found.")
        locks.pop(session_id, None)
        return Response(status_code=204)

    @app.post("/api/sessions/{session_id}/retry")
    async def retry_session(session_id: str, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
        session = load(session_id, user)
        if session_id in running:
            raise HTTPException(409, "This prep kit is still being generated.")
        if session["mode"] == "ai" and llm is None:
            store.update(session_id, mode="demo")
        store.update(session_id, status="queued", error=None, progress=initial_progress(session["company"]))
        launch(session_id)
        return {"id": session_id, "status": "queued"}

    # -------------------------------------------------------------- actions
    def require_ready(session: dict[str, Any]) -> dict[str, Any]:
        if session["id"] in running:
            raise HTTPException(409, "Wait for the agent to finish generating this prep kit.")
        result = session.get("result") or {}
        if not result.get("topics"):
            raise HTTPException(409, "This prep kit has no content yet.")
        return result

    def llm_for(session: dict[str, Any]) -> ClaudeLLM | None:
        return llm if session.get("mode") == "ai" else None

    @app.post("/api/sessions/{session_id}/generate")
    async def generate_more(
        session_id: str, body: GenerateBody, user: dict[str, Any] = Depends(current_user)
    ) -> dict[str, Any]:
        async with lock_for(session_id):
            session = load(session_id, user)
            result = require_ready(session)
            try:
                items = await actions.generate_more(
                    session,
                    section=body.section,
                    count=body.count,
                    level=body.level,
                    topic=body.topic.strip(),
                    focus=body.focus.strip(),
                    llm=llm_for(session),
                )
            except actions.ActionError as exc:
                raise HTTPException(400, str(exc)) from exc
            except (LLMError, anthropic.APIError) as exc:
                raise HTTPException(502, friendly_error(exc, settings)) from exc
            # re-read: another request may have changed progress/quiz state meanwhile
            fresh_session = load(session_id, user)
            result = fresh_session.get("result") or result
            existing = result.setdefault(body.section, [])
            if body.section == "revision":
                known = {n["topic"].lower() for n in existing}
                added = [n for n in items if n["topic"].lower() not in known]
            else:
                added = dedupe(existing, items)
            existing.extend(added)
            store.update(session_id, result=result, summary=result_counts(result))
            message = "" if added else "No new content was found for these filters - try another topic or level."
            return {"added": added, "counts": result_counts(result), "message": message}

    @app.post("/api/sessions/{session_id}/evaluate")
    async def evaluate(
        session_id: str, body: EvaluateBody, user: dict[str, Any] = Depends(current_user)
    ) -> dict[str, Any]:
        session = load(session_id, user)
        result = session.get("result") or {}
        item = actions.find_item(result, body.section, body.item_id)
        if item is None:
            raise HTTPException(404, "Question not found.")
        try:
            evaluation = await actions.evaluate_answer(
                session, section=body.section, item=item, answer=body.answer.strip(), llm=llm_for(session)
            )
        except (LLMError, anthropic.APIError) as exc:
            raise HTTPException(502, friendly_error(exc, settings)) from exc
        async with lock_for(session_id):
            state = load(session_id, user).get("user_state") or {}
            evaluations = state.setdefault("evaluations", {})
            previous = evaluations.get(body.item_id) or {}
            evaluations[body.item_id] = {
                "score": evaluation["score"],
                "best": max(evaluation["score"], previous.get("best", 0)),
                "attempts": previous.get("attempts", 0) + 1,
            }
            store.update(session_id, user_state=state)
        return evaluation

    @app.put("/api/sessions/{session_id}/state")
    async def update_state(
        session_id: str, body: StateBody, user: dict[str, Any] = Depends(current_user)
    ) -> dict[str, Any]:
        async with lock_for(session_id):
            state = load(session_id, user).get("user_state") or {}
            state.setdefault("items", {})
            state.setdefault("topics", {})
            if body.item_id:
                if body.status:
                    state["items"][body.item_id] = body.status
                else:
                    state["items"].pop(body.item_id, None)
            if body.topic_id is not None and body.revised is not None:
                if body.revised:
                    state["topics"][body.topic_id] = True
                else:
                    state["topics"].pop(body.topic_id, None)
            store.update(session_id, user_state=state)
            return state

    @app.post("/api/sessions/{session_id}/quiz-attempts", status_code=201)
    async def add_quiz_attempt(
        session_id: str, body: QuizAttemptBody, user: dict[str, Any] = Depends(current_user)
    ) -> list[dict[str, Any]]:
        if body.correct > body.total:
            raise HTTPException(422, "correct cannot exceed total.")
        async with lock_for(session_id):
            attempts = load(session_id, user).get("quiz_attempts") or []
            attempt = body.model_dump()
            attempt["id"] = uuid.uuid4().hex[:10]
            attempt["score_pct"] = round(100 * body.correct / body.total)
            attempt["at"] = utcnow()
            attempts.append(attempt)
            attempts = attempts[-MAX_QUIZ_ATTEMPTS:]
            store.update(session_id, quiz_attempts=attempts)
            return attempts

    @app.get("/api/sessions/{session_id}/export.md")
    async def export(session_id: str, user: dict[str, Any] = Depends(current_user)) -> Response:
        session = load(session_id, user)
        markdown = export_markdown(session)
        slug = re.sub(r"[^a-z0-9]+", "-", f"{session['company']} {session.get('role') or ''}".lower()).strip("-")
        return Response(
            markdown,
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{slug or "interview"}-prep-kit.md"'},
        )

    @app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
    async def api_not_found(path: str) -> JSONResponse:
        return JSONResponse({"detail": f"Unknown API route: /api/{path}"}, status_code=404)

    # ------------------------------------------------------- frontend (built)
    dist = settings.frontend_dist
    if (dist / "index.html").is_file():
        if (dist / "assets").is_dir():
            app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")
        dist_root = dist.resolve()

        @app.get("/{full_path:path}", include_in_schema=False)
        async def spa(full_path: str) -> FileResponse:
            candidate = (dist / full_path).resolve()
            if full_path and candidate.is_file() and candidate.is_relative_to(dist_root):
                return FileResponse(candidate)
            return FileResponse(dist / "index.html")

    return app


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
app = create_app()
