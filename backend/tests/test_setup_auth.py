"""The sign-in setup helpers: live credential checks and safe .env editing."""

import dataclasses
import smtplib
from urllib.parse import parse_qsl

import httpx
from dotenv import dotenv_values

import app.mailer as mailer_module
from app.setup_auth import check_google, check_smtp, redirect_uris, update_env

CLIENT = "123456789012-abcdefghijklmnop.apps.googleusercontent.com"


def google_answering(status, body):
    def handler(request):
        assert str(request.url) == "https://oauth2.googleapis.com/token"
        form = dict(parse_qsl(request.content.decode()))
        assert form["client_id"] == CLIENT and form["grant_type"] == "authorization_code"
        return httpx.Response(status, json=body)

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_check_google_reads_googles_answer():
    ok, message = check_google(CLIENT, "GOCSPX-right", http=google_answering(400, {"error": "invalid_grant"}))
    assert ok and "accepted" in message
    ok, message = check_google(
        CLIENT, "GOCSPX-x", http=google_answering(401, {"error": "invalid_client",
                                                       "error_description": "The OAuth client was not found."})
    )
    assert not ok and "client ID" in message
    ok, message = check_google(
        CLIENT, "wrong", http=google_answering(401, {"error": "invalid_client", "error_description": "Unauthorized"})
    )
    assert not ok and "secret" in message
    assert check_google("", "")[0] is False
    ok, message = check_google("my-project-name", "secret")  # rejected before any network call
    assert not ok and "isn't a client ID" in message


def test_redirect_uris_cover_dev_and_production():
    assert redirect_uris("https://prep.example.com/") == [
        "http://localhost:5173/api/auth/google/callback",
        "http://localhost:8000/api/auth/google/callback",
        "https://prep.example.com/api/auth/google/callback",
    ]


class FakeSMTP:
    instances = []

    def __init__(self, host, port, timeout=None, **_):
        self.host, self.port, self.sent, self.logged_in = host, port, [], None
        FakeSMTP.instances.append(self)

    esmtp_features = {"auth": "LOGIN PLAIN"}

    def starttls(self, context=None):
        self.tls = True

    def ehlo_or_helo_if_needed(self):
        pass

    def auth_plain(self, challenge=None):
        return ""

    def auth(self, mechanism, authobject, *, initial_response_ok=True):
        self.login(self.user, self.password)

    def login(self, user, password):
        if password != "abcdefghijklmnop":
            raise smtplib.SMTPAuthenticationError(535, b"5.7.8 Username and Password not accepted")
        self.logged_in = user

    def send_message(self, message):
        self.sent.append(message)

    def close(self):
        pass

    def quit(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.quit()


def gmail(settings, password):
    return dataclasses.replace(settings, smtp_host="smtp.gmail.com", smtp_port=587, smtp_security="starttls",
                               smtp_user="me@gmail.com", smtp_password=password,
                               smtp_from="InstantInterviewPrep <me@gmail.com>")


def test_check_smtp_signs_in_and_sends(monkeypatch, settings):
    monkeypatch.setattr(mailer_module.smtplib, "SMTP", FakeSMTP)
    FakeSMTP.instances.clear()
    assert check_smtp(settings) == (False, check_smtp(settings)[1]) and "not configured" in check_smtp(settings)[1]

    # Google shows app passwords in groups of four; spaces are dropped before signing in
    ok, message = check_smtp(gmail(settings, "abcd efgh ijkl mnop"))
    assert ok and "signed in to smtp.gmail.com" in message
    assert FakeSMTP.instances[-1].logged_in == "me@gmail.com" and FakeSMTP.instances[-1].tls

    ok, message = check_smtp(gmail(settings, "abcdefghijklmnop"), send_to="me@gmail.com")
    assert ok and FakeSMTP.instances[-1].sent[0]["To"] == "me@gmail.com"


def test_check_smtp_explains_a_rejected_gmail_password(monkeypatch, settings):
    monkeypatch.setattr(mailer_module.smtplib, "SMTP", FakeSMTP)
    ok, message = check_smtp(gmail(settings, "my-normal-password"))
    assert not ok and "535" in message and "App Password" in message


def test_update_env_changes_only_the_given_keys(tmp_path):
    env = tmp_path / ".env"
    env.write_text(
        "# my settings\nANTHROPIC_API_KEY=sk-keep-me\nPREP_SMTP_HOST=\nPREP_SMTP_FROM=\n\nPREP_SMTP_HOST=old\n",
        encoding="utf-8",
    )
    secret = 'pa"ss\\word #1'
    backup = update_env(
        {"PREP_SMTP_HOST": "smtp.gmail.com", "PREP_SMTP_FROM": "Prep <me@gmail.com>",
         "PREP_SMTP_PASSWORD": secret, "PREP_GOOGLE_CLIENT_ID": CLIENT},
        env,
    )
    assert backup.read_text(encoding="utf-8").startswith("# my settings")
    text = env.read_text(encoding="utf-8")
    assert text.startswith("# my settings\nANTHROPIC_API_KEY=sk-keep-me\n")
    assert text.count("PREP_SMTP_HOST=smtp.gmail.com") == 2  # a later duplicate can't override the new value
    values = dotenv_values(env)
    assert values["PREP_SMTP_FROM"] == "Prep <me@gmail.com>"
    assert values["PREP_SMTP_PASSWORD"] == secret
    assert values["PREP_GOOGLE_CLIENT_ID"] == CLIENT
    assert values["ANTHROPIC_API_KEY"] == "sk-keep-me"


def test_wizard_saves_checked_values(monkeypatch, tmp_path, settings):
    import app.setup_auth as setup

    env = tmp_path / ".env"
    env.write_text("ANTHROPIC_API_KEY=\nPREP_GOOGLE_CLIENT_ID=\n", encoding="utf-8")
    monkeypatch.setattr(setup, "ENV_PATH", env)
    monkeypatch.setattr(setup, "get_settings",
                        lambda: dataclasses.replace(settings, google_client_id=None, google_client_secret=None))
    monkeypatch.setattr(setup.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(setup.webbrowser, "open", lambda url: True)
    checked = {}

    def fake_check_google(client_id, client_secret, **_):
        checked["google"] = (client_id, client_secret)
        return (True, "accepted") if client_id else (False, "not configured")

    def fake_check_smtp(s, send_to=None):
        checked["smtp"] = (s.smtp_host, s.smtp_user, s.smtp_password, send_to)
        return (True, "sent") if s.email_enabled else (False, "not configured")

    monkeypatch.setattr(setup, "check_google", fake_check_google)
    monkeypatch.setattr(setup, "check_smtp", fake_check_smtp)
    answers = iter([
        "",            # set up Google? yes
        "n",           # open the page? no
        CLIENT,        # client ID
        "",            # set up email? yes
        "",            # Gmail? yes
        "me@gmail.com",
        "n",           # open the page? no
        "",            # test email to: default (me@gmail.com)
        "",            # public site? no
    ])
    secrets = iter(["GOCSPX-secret", "abcd efgh ijkl mnop"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    monkeypatch.setattr(setup.getpass, "getpass", lambda prompt="": next(secrets))

    assert setup.wizard() == 0
    assert checked["google"] == (CLIENT, "GOCSPX-secret")
    assert checked["smtp"] == ("smtp.gmail.com", "me@gmail.com", "abcdefghijklmnop", "me@gmail.com")
    values = dotenv_values(env)
    assert values["PREP_GOOGLE_CLIENT_ID"] == CLIENT and values["PREP_GOOGLE_CLIENT_SECRET"] == "GOCSPX-secret"
    assert values["PREP_SMTP_HOST"] == "smtp.gmail.com" and values["PREP_SMTP_PASSWORD"] == "abcdefghijklmnop"
    assert values["PREP_SMTP_FROM"] == "InstantInterviewPrep <me@gmail.com>"
    assert (tmp_path / ".env.bak").exists()
