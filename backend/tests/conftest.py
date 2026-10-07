import dataclasses
import os
import tempfile
import time
from pathlib import Path

import pytest

# Configure the environment before app.main (which builds a default app) is imported.
_TMP = Path(tempfile.mkdtemp(prefix="prep-tests-"))
os.environ["PREP_DATA_DIR"] = str(_TMP)
os.environ["PREP_DEMO_STEP_DELAY"] = "0"
os.environ.pop("ANTHROPIC_API_KEY", None)
os.environ["PREP_FRONTEND_DIST"] = str(_TMP / "no-frontend")

from fastapi.testclient import TestClient  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.main import create_app  # noqa: E402
from app.samples import SAMPLE_INPUT  # noqa: E402


@pytest.fixture
def settings(tmp_path):
    return dataclasses.replace(get_settings(), db_path=tmp_path / "prep.db", demo_step_delay=0.0, anthropic_api_key=None)


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def sample_form(**overrides):
    data = {
        "company": SAMPLE_INPUT["company"],
        "role": SAMPLE_INPUT["role"],
        "years_experience": str(SAMPLE_INPUT["years_experience"]),
        "job_description": SAMPLE_INPUT["job_description"],
        "resume_text": SAMPLE_INPUT["resume_text"],
        "extra_notes": SAMPLE_INPUT["extra_notes"],
        "depth": "standard",
    }
    data.update(overrides)
    return data


def wait_for(client, session_id, timeout=30.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        status = client.get(f"/api/sessions/{session_id}/status").json()
        if status["status"] in ("completed", "failed"):
            return status
        time.sleep(0.05)
    raise AssertionError("session did not finish in time")
