"""Runtime settings, read from environment variables (and backend/.env).

App-specific variables use the PREP_ prefix so they never collide with other
tools' variables on the same machine.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent

load_dotenv(BACKEND_DIR / ".env")

EFFORT_LEVELS = ("low", "medium", "high", "xhigh", "max")


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _int(name: str, default: int, lo: int, hi: int) -> int:
    try:
        value = int(os.getenv(name, default))
    except ValueError:
        value = default
    return max(lo, min(hi, value))


def _effort(name: str, default: str) -> str:
    value = (os.getenv(name) or default).strip().lower()
    return value if value in EFFORT_LEVELS else default


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str | None
    model: str
    effort: str
    research_effort: str
    enable_web_search: bool
    enable_fallbacks: bool
    max_concurrency: int
    force_demo: bool
    demo_step_delay: float
    db_path: Path
    frontend_dist: Path
    cors_origins: tuple[str, ...]
    max_upload_mb: int

    @property
    def ai_enabled(self) -> bool:
        return bool(self.anthropic_api_key) and not self.force_demo


@lru_cache
def get_settings() -> Settings:
    data_dir = Path(os.getenv("PREP_DATA_DIR") or (BACKEND_DIR / "data"))
    cors = os.getenv("PREP_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    try:
        demo_delay = float(os.getenv("PREP_DEMO_STEP_DELAY", "0.6"))
    except ValueError:
        demo_delay = 0.6
    return Settings(
        anthropic_api_key=(os.getenv("ANTHROPIC_API_KEY") or "").strip() or None,
        model=(os.getenv("PREP_CLAUDE_MODEL") or "claude-opus-5-5").strip(),
        effort=_effort("PREP_CLAUDE_EFFORT", "medium"),
        research_effort=_effort("PREP_RESEARCH_EFFORT", "medium"),
        enable_web_search=_bool("PREP_ENABLE_WEB_SEARCH", True),
        enable_fallbacks=_bool("PREP_ENABLE_FALLBACKS", True),
        max_concurrency=_int("PREP_MAX_CONCURRENCY", 6, 1, 16),
        force_demo=_bool("PREP_DEMO_MODE", False),
        demo_step_delay=max(0.0, min(demo_delay, 5.0)),
        db_path=data_dir / "prep.db",
        frontend_dist=Path(os.getenv("PREP_FRONTEND_DIST") or (PROJECT_DIR / "frontend" / "dist")),
        cors_origins=tuple(o.strip() for o in cors.split(",") if o.strip()),
        max_upload_mb=_int("PREP_MAX_UPLOAD_MB", 10, 1, 50),
    )
