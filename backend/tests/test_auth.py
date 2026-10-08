"""Accounts: sign-up, sign-in, Google, password reset, sessions and data isolation."""

import base64
import hashlib
import re
import sqlite3
from types import SimpleNamespace
from urllib.parse import parse_qsl, urlsplit

import pytest
from argon2 import PasswordHasher
from argon2.exceptions import HashingError, VerificationError

import app.accounts as accounts
from app.storage import Store
from conftest import GOOGLE_CLIENT_ID, PASSWORD, sample_form, signup, wait_for


def cookie_header(response):
    return response.headers.get("set-cookie", "")


def login(client, email="ada@example.com", password=PASSWORD, remember=True):
    return client.post("/api/auth/login", json={"email": email, "password": password, "remember": remember})


def forgot(client, email):
    # browsers always send Origin on these requests; links are built from a trusted one
    return client.post("/api/auth/forgot-password", json={"email": email}, headers={"Origin": "http://localhost:5173"})


# ----------------------------------------------------------------- basics
def test_everything_needs_a_signed_in_user(anon):
    assert anon.get("/api/auth/me").status_code == 401
    assert anon.get("/api/sessions").status_code == 401
    assert anon.post("/api/sessions", data=sample_form()).status_code == 401
    assert anon.get("/api/sessions/abc").status_code == 401
    assert anon.get("/api/sessions/abc/export.md").status_code == 401
    # public endpoints stay public
    assert anon.get("/api/health").status_code == 200
    assert anon.get("/api/auth/config").json() == {
        "google_enabled": True,
        "email_delivery": True,
        "email_sender": "noreply@example.com",
        "setup_hints": True,
    }


def test_register_login_logout(anon):
    response = anon.post(
        "/api/auth/register",
        json={"first_name": "  Ada ", "last_name": "Lovelace", "email": "Ada@Example.COM", "password": PASSWORD},
    )
    assert response.status_code == 201 and response.json()["new_account"] is True
    user = response.json()["user"]
    assert user["email"] == "ada@example.com" and user["first_name"] == "Ada"
    assert user["has_password"] and not user["google_linked"] and not user["email_verified"]
    assert "password_hash" not in user
    cookie = cookie_header(response)
    assert "iip_session=" in cookie and "HttpOnly" in cookie and "samesite=lax" in cookie.lower()

    assert anon.get("/api/auth/me").json()["user"]["id"] == user["id"]
    assert anon.post("/api/auth/logout").status_code == 204
    assert anon.get("/api/auth/me").status_code == 401

    signed_in = login(anon, email="ADA@example.com")
    assert signed_in.status_code == 200 and signed_in.json()["user"]["id"] == user["id"]
    assert signed_in.json()["new_account"] is False
    assert anon.get("/api/auth/me").status_code == 200


def test_keep_me_signed_in_controls_cookie_lifetime(anon):
    signup(anon, remember=True)
    persistent = login(anon, remember=True)
    assert "Max-Age=" in cookie_header(persistent)
    browser_session = login(anon, remember=False)
    assert "Max-Age=" not in cookie_header(browser_session)


@pytest.mark.parametrize(
    "body, field, status",
    [
        ({"first_name": "", "last_name": "L", "email": "a@example.com", "password": PASSWORD}, "first_name", 422),
        ({"first_name": "A", "last_name": " ", "email": "a@example.com", "password": PASSWORD}, "last_name", 422),
        ({"first_name": "A", "last_name": "L", "email": "not-an-email", "password": PASSWORD}, "email", 422),
        ({"first_name": "A", "last_name": "L", "email": "a@example.com", "password": "short1"}, "password", 422),
        ({"first_name": "A", "last_name": "L", "email": "a@example.com", "password": "lettersonly"}, "password", 422),
        ({"first_name": "A", "last_name": "L", "email": "a@example.com", "password": "12345678"}, "password", 422),
    ],
)
def test_registration_validation(anon, body, field, status):
    response = anon.post("/api/auth/register", json=body)
    assert response.status_code == status
    assert response.json()["field"] == field


def test_duplicate_email_and_wrong_password(anon):
    signup(anon)
    duplicate = anon.post(
        "/api/auth/register",
        json={"first_name": "B", "last_name": "C", "email": "ada@example.com", "password": PASSWORD},
    )
    assert duplicate.status_code == 409 and duplicate.json()["field"] == "email"
    wrong = login(anon, password="Wrong-password-1")
    unknown = login(anon, email="nobody@example.com")
    # the same message whether the account exists or not
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json()["detail"] == unknown.json()["detail"]


def test_login_is_rate_limited(anon):
    signup(anon)
    for _ in range(8):
        assert login(anon, password="Wrong-password-1").status_code == 401
    blocked = login(anon, password="Wrong-password-1")
    assert blocked.status_code == 429 and "Retry-After" in blocked.headers
    # even the right password waits until the window passes
    assert login(anon).status_code == 429


def test_session_tokens_are_stored_hashed(anon, settings):
    signup(anon)
    token = anon.cookies.get("iip_session")
    with sqlite3.connect(settings.db_path) as conn:
        hashes = [row[0] for row in conn.execute("SELECT token_hash FROM auth_sessions")]
        password_hashes = [row[0] for row in conn.execute("SELECT password_hash FROM users")]
    assert token and token not in hashes and len(hashes[0]) == 64
    assert password_hashes[0].startswith("$argon2id$")


def test_cross_site_writes_are_blocked(anon):
    blocked = anon.post(
        "/api/auth/login",
        json={"email": "a@example.com", "password": PASSWORD},
        headers={"Origin": "https://evil.example"},
    )
    assert blocked.status_code == 403
    allowed = anon.post(
        "/api/auth/login",
        json={"email": "a@example.com", "password": PASSWORD},
        headers={"Origin": "http://localhost:5173"},
    )
    assert allowed.status_code == 401  # reached the endpoint
    assert anon.get("/api/health").headers["x-content-type-options"] == "nosniff"


# ----------------------------------------------------------------- isolation
def test_users_only_see_their_own_prep_kits(anon):
    signup(anon, email="owner@example.com")
    session_id = anon.post("/api/sessions", data=sample_form(depth="quick")).json()["id"]
    assert wait_for(anon, session_id)["status"] == "completed"
    assert "user_id" not in anon.get(f"/api/sessions/{session_id}").json()

    anon.cookies.clear()
    signup(anon, email="other@example.com")
    assert anon.get("/api/sessions").json() == []
    for path in ("", "/status", "/export.md"):
        assert anon.get(f"/api/sessions/{session_id}{path}").status_code == 404
    assert anon.delete(f"/api/sessions/{session_id}").status_code == 404
    assert anon.post(f"/api/sessions/{session_id}/retry").status_code == 404
    assert anon.put(f"/api/sessions/{session_id}/state", json={"topic_id": "x", "revised": True}).status_code == 404

    anon.cookies.clear()
    assert login(anon, email="owner@example.com").status_code == 200
    assert [s["id"] for s in anon.get("/api/sessions").json()] == [session_id]


def test_first_account_adopts_kits_made_before_sign_in(settings, mailer, google):
    from fastapi.testclient import TestClient

    from app.main import create_app

    legacy = Store(settings.db_path)
    legacy.create("legacy123456", status="completed", mode="demo", company="Old Co", summary={})
    legacy.close()
    with TestClient(create_app(settings, google_exchange=google, mailer=mailer)) as client:
        signup(client, email="first@example.com")
        assert [s["id"] for s in client.get("/api/sessions").json()] == ["legacy123456"]
        client.cookies.clear()
        signup(client, email="second@example.com")
        assert client.get("/api/sessions").json() == []


# ----------------------------------------------------------- password reset
def reset_link(mailer):
    match = re.search(r"(\S+)/reset-password\?token=([\w-]+)", mailer.sent[-1]["text"])
    assert match
    return match.group(2)


def test_password_reset_flow(anon, mailer):
    signup(anon)
    other_device = anon.cookies.get("iip_session")
    anon.cookies.clear()

    assert forgot(anon, "ADA@example.com").status_code == 202
    assert mailer.sent[-1]["to"] == "ada@example.com" and "Reset password" in mailer.sent[-1]["html"]
    token = reset_link(mailer)
    assert anon.get("/api/auth/reset-password", params={"token": token}).json() == {
        "valid": True,
        "email": "ada@example.com",
    }
    weak = anon.post("/api/auth/reset-password", json={"token": token, "password": "weak"})
    assert weak.status_code == 422 and weak.json()["field"] == "password"

    done = anon.post("/api/auth/reset-password", json={"token": token, "password": "BrandNew2026"})
    assert done.status_code == 200 and done.json()["user"]["email_verified"] is True
    assert anon.get("/api/auth/me").status_code == 200
    # the link works once, the old password stops working, other devices are signed out
    assert anon.post("/api/auth/reset-password", json={"token": token, "password": "Another2026"}).status_code == 400
    assert anon.get("/api/auth/reset-password", params={"token": token}).json()["valid"] is False
    assert login(anon).status_code == 401
    assert login(anon, password="BrandNew2026").status_code == 200
    anon.cookies.clear()
    anon.cookies.set("iip_session", other_device)
    assert anon.get("/api/auth/me").status_code == 401


def test_reset_links_point_at_a_trusted_address(anon, mailer):
    signup(anon)
    forgot(anon, "ada@example.com")
    assert "http://localhost:5173/reset-password?token=" in mailer.sent[-1]["text"]
    # a forged Host must never end up in a reset link (password-reset poisoning)
    sent = len(mailer.sent)
    anon.post("/api/auth/forgot-password", json={"email": "ada@example.com"}, headers={"Host": "evil.example"})
    assert len(mailer.sent) == sent


def test_forgot_password_does_not_reveal_accounts(anon, mailer):
    signup(anon)
    known, unknown = forgot(anon, "ada@example.com"), forgot(anon, "ghost@example.com")
    # the page gets the same answer either way...
    assert known.status_code == unknown.status_code == 202 and known.json() == unknown.json() == {"ok": True}
    # ...and the inbox tells its owner: a reset link, or that there's no account with this address
    reset, no_account = mailer.sent
    assert reset["to"] == "ada@example.com" and "/reset-password?token=" in reset["text"]
    assert no_account["to"] == "ghost@example.com" and "no account with this email" in no_account["text"]
    assert "/signup?email=ghost%40example.com" in no_account["text"]
    assert "reset-password" not in no_account["text"]


def test_no_account_emails_are_rate_limited(anon, mailer):
    for _ in range(5):
        forgot(anon, "stranger@example.com")
    assert len(mailer.sent) == 3  # at most 3 an hour per address


# ------------------------------------------------------------------ Google
def google_start(client, **params):
    response = client.get("/api/auth/google/start", params=params, follow_redirects=False)
    assert response.status_code == 303
    return response, dict(parse_qsl(urlsplit(response.headers["location"]).query))


def google_sign_in(client, google, *, code="g-code", nonce=None, next=None, **claims):
    """Run start -> (Google) -> callback; returns the callback response."""
    _, query = google_start(client, **({"next": next} if next else {}))
    google.add(code, nonce=query["nonce"] if nonce is None else nonce, **claims)
    return client.get(
        "/api/auth/google/callback", params={"code": code, "state": query["state"]}, follow_redirects=False
    )


def test_google_start_sends_the_browser_to_google_with_pkce(anon):
    response, query = google_start(anon, next="/preps", remember="false")
    assert response.headers["location"].startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert query["client_id"] == GOOGLE_CLIENT_ID
    assert query["redirect_uri"] == "http://testserver/api/auth/google/callback"
    assert query["response_type"] == "code" and set(query["scope"].split()) == {"openid", "email", "profile"}
    assert query["code_challenge_method"] == "S256" and len(query["code_challenge"]) == 43
    assert query["state"] and query["nonce"] and query["state"] != query["nonce"]
    cookie = cookie_header(response)
    assert "iip_oauth=" in cookie and "HttpOnly" in cookie and "Path=/api/auth/google" in cookie


def test_google_creates_then_signs_in_the_same_account(anon, google):
    profile = {"sub": "google-1", "email": "Grace@Example.com", "given_name": "Grace", "family_name": "Hopper",
               "picture": "https://lh3.googleusercontent.com/a/photo"}
    first = google_sign_in(anon, google, **profile)
    assert first.status_code == 303 and first.headers["location"] == "/new?welcome=new"
    # PKCE: the verifier sent to Google's token endpoint matches the challenge in the start URL
    exchange = google.exchanges[-1]
    assert exchange["redirect_uri"] == "http://testserver/api/auth/google/callback"
    assert 43 <= len(exchange["code_verifier"]) <= 128
    user = anon.get("/api/auth/me").json()["user"]
    assert (user["first_name"], user["last_name"], user["email"]) == ("Grace", "Hopper", "grace@example.com")
    assert user["google_linked"] and user["email_verified"] and not user["has_password"]
    assert user["avatar_url"].startswith("https://lh3.")

    anon.cookies.clear()
    again = google_sign_in(anon, google, code="g-code-2", next="/preps", **profile)
    assert again.headers["location"] == "/preps?welcome=back"
    assert anon.get("/api/auth/me").json()["user"]["id"] == user["id"]
    # a Google-only account has no password to guess
    assert login(anon, email="grace@example.com", password=PASSWORD).status_code == 401


def test_google_pkce_challenge_matches_the_verifier(anon, google):
    _, query = google_start(anon)
    google.add("pkce-code", sub="g-pkce", email="pk@example.com", given_name="P", nonce=query["nonce"])
    anon.get("/api/auth/google/callback", params={"code": "pkce-code", "state": query["state"]}, follow_redirects=False)
    verifier = google.exchanges[-1]["code_verifier"]
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    assert challenge == query["code_challenge"]


def test_google_links_a_verified_password_account(anon, google, mailer):
    signup(anon)
    forgot(anon, "ada@example.com")
    anon.post("/api/auth/reset-password", json={"token": reset_link(mailer), "password": PASSWORD})  # verifies email
    anon.cookies.clear()
    response = google_sign_in(anon, google, sub="google-ada", email="ada@example.com", given_name="Ada")
    assert response.headers["location"] == "/?welcome=back"
    linked = anon.get("/api/auth/me").json()["user"]
    assert linked["google_linked"] and linked["has_password"]
    assert login(anon).status_code == 200  # the password still works


def test_google_takes_over_an_unverified_squatted_email(anon, google):
    signup(anon, email="victim@example.com")  # someone registered an address they don't own
    squatter_cookie = anon.cookies.get("iip_session")
    anon.cookies.clear()
    google_sign_in(anon, google, sub="google-victim", email="victim@example.com", given_name="Real")
    owner = anon.get("/api/auth/me").json()["user"]
    assert owner["google_linked"] and not owner["has_password"]
    assert login(anon, email="victim@example.com").status_code == 401
    anon.cookies.clear()
    anon.cookies.set("iip_session", squatter_cookie)
    assert anon.get("/api/auth/me").status_code == 401


def test_google_callback_rejects_forged_and_replayed_requests(anon, google):
    # login CSRF: a callback with someone else's state (no matching cookie in this browser)
    _, query = google_start(anon)
    anon.cookies.clear()
    google.add("forged", sub="attacker", email="attacker@example.com", nonce=query["nonce"])
    forged = anon.get("/api/auth/google/callback", params={"code": "forged", "state": query["state"]},
                      follow_redirects=False)
    assert forged.headers["location"] == "/login?error=google_expired"
    assert anon.get("/api/auth/me").status_code == 401
    assert google.exchanges == []  # the code was never even exchanged

    # a state works once
    first = google_sign_in(anon, google, code="once", sub="g-once", email="once@example.com", given_name="O")
    assert first.status_code == 303 and first.headers["location"].startswith("/new")
    state = [e for e in google.exchanges if e["code"] == "once"]
    assert len(state) == 1


def test_google_callback_failures_return_to_sign_in(anon, google):
    cancelled = anon.get("/api/auth/google/callback", params={"error": "access_denied"}, follow_redirects=False)
    assert cancelled.headers["location"] == "/login?error=google_cancelled"
    bad_nonce = google_sign_in(anon, google, code="n1", nonce="wrong", sub="g-n", email="n@example.com")
    assert bad_nonce.headers["location"] == "/login?error=google_failed"
    unverified = google_sign_in(anon, google, code="n2", sub="g-u", email="u@example.com", email_verified=False)
    assert unverified.headers["location"] == "/login?error=google_email"
    unknown_code = anon.get("/api/auth/google/callback", params={"code": "nope", "state": "nope"},
                            follow_redirects=False)
    assert unknown_code.headers["location"] == "/login?error=google_expired"
    assert anon.get("/api/auth/me").status_code == 401


def test_google_redirects_ignore_foreign_destinations(anon, google):
    response = google_sign_in(anon, google, next="//evil.example/path", sub="g-x", email="x@example.com",
                              given_name="X")
    assert response.headers["location"] == "/new?welcome=new"


def test_google_needs_configuration(settings, mailer, google):
    import dataclasses

    from fastapi.testclient import TestClient

    from app.main import create_app

    plain = dataclasses.replace(settings, google_client_secret=None)
    with TestClient(create_app(plain, google_exchange=google, mailer=mailer)) as client:
        assert client.get("/api/auth/config").json()["google_enabled"] is False
        start = client.get("/api/auth/google/start", follow_redirects=False)
        assert start.status_code == 303 and start.headers["location"] == "/login?error=google_unavailable"


# ------------------------------------------------- a server short of memory
class FlakyHasher:
    """Wraps the real hasher; the next `failures` calls fail the way Argon2 does when memory runs out."""

    def __init__(self, real, failures):
        self.real, self.failures = real, failures

    def _maybe_fail(self, error):
        if self.failures > 0:
            self.failures -= 1
            raise error("Memory allocation error")

    def hash(self, password):
        self._maybe_fail(HashingError)
        return self.real.hash(password)

    def verify(self, password_hash, password):
        self._maybe_fail(VerificationError)
        return self.real.verify(password_hash, password)

    def check_needs_rehash(self, password_hash):
        return self.real.check_needs_rehash(password_hash)


@pytest.fixture
def short_of_memory(monkeypatch):
    real = accounts._hasher
    monkeypatch.setattr(accounts, "time", SimpleNamespace(sleep=lambda seconds: None))

    def fail_next(failures):
        monkeypatch.setattr(accounts, "_hasher", FlakyHasher(real, failures))

    return fail_next


def test_password_reset_survives_a_server_short_of_memory(anon, mailer, short_of_memory):
    signup(anon)
    anon.cookies.clear()
    forgot(anon, "ada@example.com")
    token = reset_link(mailer)

    short_of_memory(99)  # never recovers
    busy = anon.post("/api/auth/reset-password", json={"token": token, "password": "BrandNew2026"})
    assert busy.status_code == 503 and "try again" in busy.json()["detail"]
    # nothing changed: the link still works and the old password still signs in
    assert anon.get("/api/auth/reset-password", params={"token": token}).json()["valid"] is True

    short_of_memory(2)  # recovers within the retries
    done = anon.post("/api/auth/reset-password", json={"token": token, "password": "BrandNew2026"})
    assert done.status_code == 200
    anon.cookies.clear()
    assert login(anon, password="BrandNew2026").status_code == 200


def test_sign_in_never_mistakes_a_memory_error_for_a_wrong_password(anon, short_of_memory):
    signup(anon)
    anon.cookies.clear()
    short_of_memory(99)
    for _ in range(10):  # more than the 8 wrong-password attempts that lock an address
        busy = login(anon)
        assert busy.status_code == 503 and "Incorrect" not in busy.json()["detail"]
    short_of_memory(1)
    assert login(anon).status_code == 200  # not locked out, and a single failure is retried


def test_older_password_hashes_are_upgraded_on_sign_in(anon, settings):
    signup(anon)
    with sqlite3.connect(settings.db_path) as conn:  # as stored before: the library's 64 MiB default
        conn.execute("UPDATE users SET password_hash = ?", (PasswordHasher().hash(PASSWORD),))
    anon.cookies.clear()
    assert login(anon).status_code == 200
    with sqlite3.connect(settings.db_path) as conn:
        upgraded = conn.execute("SELECT password_hash FROM users").fetchone()[0]
    assert "$m=19456,t=2,p=1$" in upgraded
    anon.cookies.clear()
    assert login(anon).status_code == 200
