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
for _name in ("PREP_GOOGLE_CLIENT_ID", "PREP_GOOGLE_CLIENT_SECRET", "PREP_SMTP_HOST", "PREP_APP_URL",
              "PREP_COOKIE_SECURE"):
    os.environ.pop(_name, None)

from fastapi.testclient import TestClient  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.main import create_app  # noqa: E402
from app.samples import SAMPLE_INPUT  # noqa: E402

PASSWORD = "Interview2025"
GOOGLE_CLIENT_ID = "test-client-id.apps.googleusercontent.com"


class FakeMailer:
    """Captures outgoing email instead of sending it."""

    configured = True

    def __init__(self):
        self.sent = []

    async def send(self, to, subject, text, html_body):
        self.sent.append({"to": to, "subject": subject, "text": text, "html": html_body})


class FakeGoogle:
    """Stands in for Google's token endpoint: authorization code -> verified ID-token claims."""

    def __init__(self):
        self.codes = {}
        self.exchanges = []

    def add(self, code, **claims):
        self.codes[code] = {"email_verified": True, **claims}

    async def __call__(self, code, redirect_uri, code_verifier):
        self.exchanges.append({"code": code, "redirect_uri": redirect_uri, "code_verifier": code_verifier})
        if code not in self.codes:
            raise ValueError("invalid_grant")
        return dict(self.codes[code])


def signup(client, email="ada@example.com", password=PASSWORD, first="Ada", last="Lovelace", remember=True):
    response = client.post(
        "/api/auth/register",
        json={"first_name": first, "last_name": last, "email": email, "password": password, "remember": remember},
    )
    assert response.status_code == 201, response.text
    return response.json()["user"]


@pytest.fixture
def settings(tmp_path):
    return dataclasses.replace(
        get_settings(),
        db_path=tmp_path / "prep.db",
        demo_step_delay=0.0,
        anthropic_api_key=None,
        google_client_id=GOOGLE_CLIENT_ID,
        google_client_secret="test-secret",
    )


@pytest.fixture
def mailer():
    return FakeMailer()


@pytest.fixture
def google():
    return FakeGoogle()


@pytest.fixture
def anon(settings, mailer, google):
    """A client that has not signed in."""
    with TestClient(create_app(settings, google_exchange=google, mailer=mailer)) as test_client:
        yield test_client


@pytest.fixture
def client(anon):
    """A client signed in as a fresh account."""
    signup(anon)
    return anon


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
