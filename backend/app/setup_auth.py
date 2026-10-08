"""Set up and check sign-in: "Continue with Google" and password-reset email.

    python -m app.setup_auth                        guided setup: asks for the values, checks them live,
                                                    then saves them in backend/.env
    python -m app.setup_auth --check                check the current settings (changes nothing, sends nothing)
    python -m app.setup_auth --test-email you@x.com send a real test email with the current settings

Both integrations are free but need credentials only the site's owner can create:
a Google OAuth client (Google Cloud) and an email account to send from (e.g. Gmail
with an app password).
"""

from __future__ import annotations

import argparse
import dataclasses
import getpass
import re
import shutil
import smtplib
import sys
import webbrowser
from pathlib import Path

import httpx

from .config import BACKEND_DIR, Settings, get_settings
from .mailer import Mailer, open_smtp

ENV_PATH = BACKEND_DIR / ".env"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_CLIENTS_PAGE = "https://console.cloud.google.com/auth/clients"
APP_PASSWORDS_PAGE = "https://myaccount.google.com/apppasswords"
TWO_STEP_PAGE = "https://myaccount.google.com/signinoptions/twosv"
DEV_ORIGINS = ("http://localhost:5173", "http://localhost:8000")
CLIENT_ID_RE = re.compile(r"^\d+-[A-Za-z0-9_]+\.apps\.googleusercontent\.com$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ------------------------------------------------------------------- checks
def redirect_uris(app_url: str | None = None) -> list[str]:
    """The Authorized redirect URIs to register on the Google OAuth client."""
    origins = [*DEV_ORIGINS, *([app_url.rstrip("/")] if app_url else [])]
    return [f"{origin}/api/auth/google/callback" for origin in origins]


def check_google(client_id: str | None, client_secret: str | None, *, http: httpx.Client | None = None) -> tuple[bool, str]:
    """Check a Google OAuth client without signing anyone in.

    Google authenticates the client before it looks at the authorization code, so a
    deliberately fake code is answered with invalid_client when the ID or secret is
    wrong, and with invalid_grant when they are right.
    """
    client_id = (client_id or "").strip()
    client_secret = (client_secret or "").strip()
    if not client_id or not client_secret:
        return False, "not configured (PREP_GOOGLE_CLIENT_ID and PREP_GOOGLE_CLIENT_SECRET are empty)"
    if not CLIENT_ID_RE.match(client_id):
        return False, "that isn't a client ID - it looks like 123456789012-abc123.apps.googleusercontent.com"
    client = http or httpx.Client(timeout=15)
    try:
        response = client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": "setup-check",
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uris()[0],
            },
        )
    except httpx.HTTPError as exc:
        return False, f"couldn't reach Google to check it ({exc.__class__.__name__}); check the internet connection"
    finally:
        if http is None:
            client.close()
    try:
        body = response.json()
    except ValueError:
        body = {}
    error = body.get("error")
    if error == "invalid_grant":
        return True, "Google accepted the client ID and secret"
    if error == "invalid_client":
        if "not found" in str(body.get("error_description", "")).lower():
            return False, "Google doesn't know this client ID - copy it again from Google Auth Platform > Clients"
        return False, "Google rejected the client secret - copy it again, or add a new secret to this client"
    return False, f"unexpected answer from Google ({response.status_code}): {response.text[:200]}"


TEST_TEXT = (
    "This is a test email from InstantInterviewPrep.\n\n"
    "Your email settings work: password-reset emails will be delivered from this address."
)


def check_smtp(s: Settings, send_to: str | None = None) -> tuple[bool, str]:
    """Log in to the mail server (and send a test email when send_to is given)."""
    if not s.email_enabled:
        return False, "not configured (PREP_SMTP_HOST, PREP_SMTP_USER and PREP_SMTP_PASSWORD are empty)"
    try:
        if send_to:
            Mailer(s)._send(send_to, "InstantInterviewPrep test email", TEST_TEXT, f"<p>{TEST_TEXT}</p>".replace("\n\n", "</p><p>"))
            return True, f"sent a test email to {send_to} - check the inbox (and the spam folder)"
        with open_smtp(s, timeout=15):
            pass
        who = f" as {s.smtp_user}" if s.smtp_user else ""
        return True, f"signed in to {s.smtp_host}:{s.smtp_port}{who}"
    except smtplib.SMTPAuthenticationError as exc:
        hint = ""
        if "gmail" in (s.smtp_host or "").lower():
            hint = (" For Gmail, the password must be a 16-letter App Password "
                    f"({APP_PASSWORDS_PAGE}), not your normal Google password.")
        return False, f"the mail server rejected the username or password (code {exc.smtp_code}).{hint}"
    except (smtplib.SMTPException, OSError) as exc:
        return False, f"couldn't send through {s.smtp_host}:{s.smtp_port}: {exc!r}"


# ---------------------------------------------------------------- .env file
def _quote(value: str) -> str:
    if value == "" or re.fullmatch(r"[A-Za-z0-9_.:/@+-]+", value):
        return value
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def update_env(values: dict[str, str], path: Path = ENV_PATH) -> Path | None:
    """Set KEY=value in the .env file, keeping every other line. Returns the backup's path."""
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    backup = None
    if path.exists():
        backup = path.with_name(path.name + ".bak")
        shutil.copy2(path, backup)
    seen: set[str] = set()
    out: list[str] = []
    for line in lines:
        match = re.match(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=", line)
        if match and match.group(1) in values:
            key = match.group(1)
            out.append(f"{key}={_quote(values[key])}")  # every copy, so a later duplicate can't win
            seen.add(key)
        else:
            out.append(line)
    missing = [key for key in values if key not in seen]
    if missing:
        out.append("")
        out.extend(f"{key}={_quote(values[key])}" for key in missing)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return backup


# ------------------------------------------------------------------- wizard
def _ask(prompt: str, default: str = "", secret: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    reader = getpass.getpass if secret else input
    return reader(f"  {prompt}{suffix}: ").strip() or default


def _yes(prompt: str, default: bool = True) -> bool:
    answer = input(f"  {prompt} [{'Y/n' if default else 'y/N'}]: ").strip().lower()
    return default if not answer else answer.startswith("y")


def _open(url: str) -> None:
    print(f"  Opening {url}")
    try:
        webbrowser.open(url)
    except Exception:
        print("  (open that address in your browser)")


def _status(s: Settings) -> None:
    google_ok, google_msg = check_google(s.google_client_id, s.google_client_secret)
    mail_ok, mail_msg = check_smtp(s)
    print(f"  Continue with Google ... {'OK ' if google_ok else '-- '} {google_msg}")
    print(f"  Password-reset email ... {'OK ' if mail_ok else '-- '} {mail_msg}")
    print(f"  Public URL ............. {s.app_url or 'not set (fine for local development; required in production)'}")


def _setup_google(s: Settings) -> dict[str, str]:
    print("\n[1] Continue with Google - a free Google OAuth client\n")
    print("  In the Google Cloud page that opens (sign in with your Google account):")
    print("   1. Create a project if asked (any name, e.g. InstantInterviewPrep).")
    print("   2. If it says the Google Auth Platform isn't configured, click Get started: app name")
    print("      InstantInterviewPrep, your email as support email, Audience: External, your email")
    print("      as contact, agree, Create.")
    print("   3. Clients > Create client > Application type: Web application. Under")
    print("      'Authorized redirect URIs' click Add URI once for each of these:")
    for uri in redirect_uris(s.app_url):
        print(f"         {uri}")
    print("      Click Create, then copy the Client ID and the Client secret.")
    print("   4. Audience > Test users > Add users: the Google accounts allowed to sign in while the app")
    print("      is in Testing - or click Publish app so anyone can (basic sign-in needs no Google review).")
    if _yes("Open the Google Cloud page now?"):
        _open(GOOGLE_CLIENTS_PAGE)
    for _ in range(3):
        client_id = _ask("Client ID")
        client_secret = _ask("Client secret (hidden while you paste)", secret=True)
        ok, message = check_google(client_id, client_secret)
        print(f"  {'OK' if ok else 'Problem'}: {message}")
        if ok or (message.startswith("couldn't reach Google") and _yes("Save it anyway?", default=False)):
            return {"PREP_GOOGLE_CLIENT_ID": client_id, "PREP_GOOGLE_CLIENT_SECRET": client_secret}
        if not _yes("Try again?"):
            break
    print("  Google sign-in not saved.")
    return {}


def _setup_email(s: Settings) -> dict[str, str]:
    print("\n[2] Password-reset email\n")
    use_gmail = _yes("Send from a Gmail address? (free, about 500 emails a day)")
    for _ in range(3):
        if use_gmail:
            address = _ask("Gmail address", s.smtp_user or "")
            if not EMAIL_RE.match(address):
                print("  That doesn't look like an email address.")
                continue
            print("\n  Gmail needs an App Password (your normal password won't work):")
            print(f"   1. 2-Step Verification must be on: {TWO_STEP_PAGE}")
            print(f"   2. At {APP_PASSWORDS_PAGE} type the name InstantInterviewPrep, click Create")
            print("      and copy the 16-letter password.")
            if _yes("Open the App Passwords page now?"):
                _open(APP_PASSWORDS_PAGE)
            password = _ask("App password (hidden while you paste)", secret=True).replace(" ", "")
            candidate = dataclasses.replace(
                s, smtp_host="smtp.gmail.com", smtp_port=587, smtp_security="starttls",
                smtp_user=address, smtp_password=password, smtp_from=f"InstantInterviewPrep <{address}>",
            )
        else:
            host = _ask("SMTP server (e.g. smtp-relay.brevo.com)", s.smtp_host or "")
            port = _ask("Port", str(s.smtp_port or 587))
            security = _ask("Security: starttls, ssl or none", s.smtp_security or "starttls").lower()
            user = _ask("Username", s.smtp_user or "")
            password = _ask("Password (hidden while you paste)", secret=True)
            sender = _ask("Send as (e.g. InstantInterviewPrep <no-reply@your-domain.com>)", s.smtp_from or "")
            if not port.isdigit() or security not in ("starttls", "ssl", "none"):
                print("  The port must be a number and security one of starttls, ssl or none.")
                continue
            candidate = dataclasses.replace(
                s, smtp_host=host, smtp_port=int(port), smtp_security=security,
                smtp_user=user, smtp_password=password, smtp_from=sender,
            )
        default_to = candidate.smtp_user if EMAIL_RE.match(candidate.smtp_user or "") else ""
        while True:
            recipient = _ask("Send a test email to (press Enter for the address shown)", default_to)
            if recipient.lower() in ("y", "yes"):  # answered as if it were a yes/no question
                recipient = default_to
            if EMAIL_RE.match(recipient):
                break
            print("  Type an email address, or press Enter to use the one shown.")
        print("  Sending...")
        ok, message = check_smtp(candidate, send_to=recipient or None)
        print(f"  {'OK' if ok else 'Problem'}: {message}")
        if ok:
            return {
                "PREP_SMTP_HOST": candidate.smtp_host or "",
                "PREP_SMTP_PORT": str(candidate.smtp_port),
                "PREP_SMTP_SECURITY": candidate.smtp_security,
                "PREP_SMTP_USER": candidate.smtp_user or "",
                "PREP_SMTP_PASSWORD": candidate.smtp_password or "",
                "PREP_SMTP_FROM": candidate.smtp_from or "",
            }
        if not _yes("Try again?"):
            break
    print("  Email settings not saved.")
    return {}


def wizard() -> int:
    if not sys.stdin.isatty():
        print("The setup asks questions, so run it in a terminal. To check the current settings: --check")
        return 2
    s = get_settings()
    print("\nInstantInterviewPrep - sign-in setup\n")
    print("Current settings:")
    _status(s)
    values: dict[str, str] = {}
    try:
        if _yes("\nSet up 'Continue with Google'?", default=not s.google_enabled):
            values |= _setup_google(s)
        if _yes("\nSet up password-reset email?", default=not s.email_enabled):
            values |= _setup_email(s)
        if not s.app_url and _yes("\nDeploying to a public site? Set its URL now", default=False):
            url = _ask("Public URL, e.g. https://prep.example.com").rstrip("/")
            if url.startswith(("https://", "http://")):
                values["PREP_APP_URL"] = url
                print(f"  Also add {url}/api/auth/google/callback to the Google client's redirect URIs.")
    except (KeyboardInterrupt, EOFError):
        print("\nStopped - nothing was saved.")
        return 1
    if not values:
        print("\nNothing changed.")
        return 0
    backup = update_env(values, ENV_PATH)
    print(f"\nSaved to {ENV_PATH}" + (f" (previous version kept as {backup.name})." if backup else "."))
    print("Restart the backend to use the new settings (scripts/dev.ps1 and dev.sh restart it automatically).")
    return 0


def check() -> int:
    s = get_settings()
    print("Sign-in settings:")
    _status(s)
    google_ok, _ = check_google(s.google_client_id, s.google_client_secret)
    mail_ok, _ = check_smtp(s)
    return 0 if google_ok and mail_ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.setup_auth", description=__doc__.split("\n\n")[0])
    parser.add_argument("--check", action="store_true", help="check the current settings without changing anything")
    parser.add_argument("--test-email", metavar="ADDRESS", help="send a test email with the current settings")
    args = parser.parse_args(argv)
    if args.test_email:
        ok, message = check_smtp(get_settings(), send_to=args.test_email)
        print(("OK: " if ok else "Problem: ") + message)
        return 0 if ok else 1
    return check() if args.check else wizard()


if __name__ == "__main__":
    raise SystemExit(main())
