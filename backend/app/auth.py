"""Sign-up, sign-in (email + password or Google), sign-out and password reset.

Signed-in users carry an httpOnly, SameSite=Lax session cookie; the browser
never sees the token from JavaScript. `current_user` is the FastAPI dependency
every protected route uses.

Google sign-in is the standard OAuth 2.0 authorization-code flow with PKCE:
/api/auth/google/start sends the browser to Google, Google sends it back to
/api/auth/google/callback with a one-time code, and the server exchanges that
code for Google's signed ID token. A state value bound to a short-lived cookie
stops forged callbacks, and a nonce ties the ID token to this attempt.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import logging
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from .accounts import (
    PASSWORD_MAX,
    RESET_TTL,
    AccountError,
    Accounts,
    IssuedSession,
    PasswordServiceBusy,
    check_password,
    clean_name,
    hash_password,
    needs_rehash,
    normalize_email,
    public_user,
    verify_password,
)
from .config import Settings
from .mailer import Mailer, no_account_email, reset_email
from .ratelimit import RateLimiter

log = logging.getLogger("prep.auth")

COOKIE_NAME = "iip_session"
OAUTH_COOKIE = "iip_oauth"
OAUTH_COOKIE_PATH = "/api/auth/google"
GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}

# (code, redirect_uri, code_verifier) -> verified ID-token claims
GoogleExchange = Callable[[str, str, str], Awaitable[dict[str, Any]]]


class GoogleSignInError(Exception):
    pass


def _verify_id_token(token: str, client_id: str) -> dict[str, Any]:
    """Check the ID token's Google signature, audience, issuer and expiry."""
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token

    return id_token.verify_oauth2_token(token, google_requests.Request(), client_id, clock_skew_in_seconds=10)


def google_code_exchange(settings: Settings) -> GoogleExchange:
    async def exchange(code: str, redirect_uri: str, code_verifier: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                    "code_verifier": code_verifier,
                },
                headers={"Accept": "application/json"},
            )
        if response.status_code != 200:
            raise GoogleSignInError(f"token endpoint answered {response.status_code}: {response.text[:300]}")
        token = (response.json() or {}).get("id_token")
        if not token:
            raise GoogleSignInError("token endpoint returned no ID token")
        return await asyncio.to_thread(_verify_id_token, token, settings.google_client_id or "")

    return exchange


def safe_next(path: str | None) -> str:
    """Only same-site paths are allowed as post-sign-in destinations."""
    path = (path or "").strip()
    if not path.startswith("/") or path.startswith("//") or "\\" in path or len(path) > 500:
        return ""
    return path


def _with_param(path: str, key: str, value: str) -> str:
    parts = urlsplit(path)
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k != key]
    query.append((key, value))
    return urlunsplit(("", "", parts.path or "/", urlencode(query), parts.fragment))


def _pkce_challenge(verifier: str) -> str:
    return base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()


# ----------------------------------------------------------------------- bodies
class RegisterBody(BaseModel):
    first_name: str = Field(..., max_length=200)
    last_name: str = Field(..., max_length=200)
    email: str = Field(..., max_length=320)
    password: str = Field(..., max_length=PASSWORD_MAX * 4)
    remember: bool = True


class LoginBody(BaseModel):
    email: str = Field(..., max_length=320)
    password: str = Field(..., max_length=PASSWORD_MAX * 4)
    remember: bool = True


class ForgotBody(BaseModel):
    email: str = Field(..., max_length=320)


class ResetBody(BaseModel):
    token: str = Field(..., min_length=10, max_length=200)
    password: str = Field(..., max_length=PASSWORD_MAX * 4)
    remember: bool = True


# ----------------------------------------------------------------------- router
def build_auth(
    settings: Settings,
    accounts: Accounts,
    mailer: Mailer,
    limiter: RateLimiter,
    google_exchange: GoogleExchange,
) -> tuple[APIRouter, Callable[..., Any]]:
    router = APIRouter(prefix="/api/auth", tags=["auth"])

    def client_ip(request: Request) -> str:
        return request.client.host if request.client else "unknown"

    def wait_message(wait: int) -> str:
        minutes = max(1, round(wait / 60))
        return f"Too many attempts. Please wait {minutes} minute{'s' if minutes != 1 else ''} and try again."

    def guard(key: str, limit: int, window: float, *, record: bool = True) -> None:
        wait = limiter.retry_after(key, limit, window)
        if wait:
            raise HTTPException(429, wait_message(wait), headers={"Retry-After": str(wait)})
        if record:
            limiter.hit(key)

    def secure_cookies(request: Request) -> bool:
        if settings.cookie_secure is not None:
            return settings.cookie_secure
        if settings.app_url:
            return settings.app_url.startswith("https://")
        return request.url.scheme == "https"

    def set_session_cookie(response: Response, request: Request, issued: IssuedSession) -> None:
        max_age = None
        if issued.persistent:
            max_age = int((issued.expires_at - datetime.now(timezone.utc)).total_seconds())
        response.set_cookie(
            COOKIE_NAME,
            issued.token,
            max_age=max_age,
            httponly=True,
            secure=secure_cookies(request),
            samesite="lax",
            path="/",
        )

    def open_session(request: Request, response: Response, user: dict[str, Any], remember: bool) -> None:
        issued = accounts.issue_session(
            user["id"], persistent=remember, user_agent=request.headers.get("user-agent", ""), ip=client_ip(request)
        )
        set_session_cookie(response, request, issued)
        response.headers["Cache-Control"] = "no-store"

    def signed_in(
        request: Request, response: Response, user: dict[str, Any], remember: bool, *, new_account: bool = False
    ) -> dict[str, Any]:
        open_session(request, response, user, remember)
        return {"user": public_user(accounts.by_id(user["id"]) or user), "new_account": new_account}

    def email_link_base(request: Request) -> str | None:
        """Where links in emails point. Never derived from headers an attacker could forge."""
        if settings.app_url:
            return settings.app_url
        origin = (request.headers.get("origin") or "").rstrip("/")
        if origin and origin in settings.cors_origins:
            return origin
        if request.url.hostname in LOCAL_HOSTS:
            return str(request.base_url).rstrip("/")
        return None

    def google_redirect_uri(request: Request) -> str:
        # Google only redirects to URIs registered for the client, so a forged Host can't redirect elsewhere.
        base = settings.app_url or str(request.base_url).rstrip("/")
        return f"{base}/api/auth/google/callback"

    async def current_user(request: Request, response: Response) -> dict[str, Any]:
        resolved = accounts.resolve_session(request.cookies.get(COOKIE_NAME))
        if resolved is None:
            raise HTTPException(401, "Please sign in to continue.")
        user, refreshed = resolved
        if refreshed is not None:
            set_session_cookie(response, request, refreshed)
        return user

    def google_account(claims: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        """Find, link or create the account for verified Google claims. Returns (user, created)."""
        sub = str(claims["sub"])
        email = normalize_email(str(claims["email"]))
        picture = claims.get("picture")
        user = accounts.by_google_sub(sub)
        if user is not None:
            if picture and picture != user.get("avatar_url"):
                user = accounts.update_user(user["id"], avatar_url=picture)
            return user, False
        existing = accounts.by_email(email)
        if existing is not None:
            fields: dict[str, Any] = {"google_sub": sub, "email_verified": 1}
            if not existing["email_verified"]:
                # Google proved who owns this inbox. A password set by someone who
                # registered the address without verifying it must not keep working.
                fields["password_hash"] = None
                accounts.revoke_all_sessions(existing["id"])
            if picture and not existing.get("avatar_url"):
                fields["avatar_url"] = picture
            return accounts.update_user(existing["id"], **fields), False
        full = str(claims.get("name") or "").split()
        first = str(claims.get("given_name") or (full[0] if full else email.split("@")[0]))
        last = str(claims.get("family_name") or " ".join(full[1:]))
        user = accounts.create_user(
            email=email,
            first_name=clean_name(first, "first_name", "first name"),
            last_name=" ".join(last.split())[:60],
            google_sub=sub,
            avatar_url=picture,
            email_verified=True,
        )
        log.info("New account %s (Google)", user["id"])
        return user, True

    # ------------------------------------------------------------- endpoints
    @router.get("/config")
    async def auth_config() -> dict[str, Any]:
        return {
            "google_enabled": settings.google_enabled,
            "email_delivery": mailer.configured,
            # shown as "look for an email from …"; it's on every email anyway
            "email_sender": mailer.sender_address if mailer.configured else None,
            # without a public URL this is a local install: the UI may show its owner setup hints
            "setup_hints": settings.app_url is None,
        }

    @router.get("/me")
    async def me(response: Response, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
        response.headers["Cache-Control"] = "no-store"
        return {"user": public_user(user)}

    @router.post("/register", status_code=201)
    async def register(body: RegisterBody, request: Request, response: Response) -> dict[str, Any]:
        guard(f"register:ip:{client_ip(request)}", 10, 3600)
        first_name = clean_name(body.first_name, "first_name", "first name")
        last_name = clean_name(body.last_name, "last_name", "last name")
        email = normalize_email(body.email)
        check_password(body.password, email)
        password_hash = await asyncio.to_thread(hash_password, body.password)
        user = accounts.create_user(email=email, first_name=first_name, last_name=last_name, password_hash=password_hash)
        log.info("New account %s", user["id"])
        return signed_in(request, response, user, body.remember, new_account=True)

    @router.post("/login")
    async def login(body: LoginBody, request: Request, response: Response) -> dict[str, Any]:
        ip_key = f"login:ip:{client_ip(request)}"
        email = normalize_email(body.email)
        email_key = f"login:email:{email}"
        guard(ip_key, 30, 900, record=False)
        guard(email_key, 8, 900, record=False)
        user = accounts.by_email(email)
        valid = await asyncio.to_thread(verify_password, user.get("password_hash") if user else None, body.password)
        if not user or not valid:
            limiter.hit(ip_key)
            limiter.hit(email_key)
            raise AccountError(
                "Incorrect email or password. If you signed up with Google, use Continue with Google.", None, 401
            )
        limiter.reset(email_key)
        if needs_rehash(user["password_hash"]):  # upgrade older hashes; never worth failing a sign-in over
            try:
                accounts.update_user(user["id"], password_hash=await asyncio.to_thread(hash_password, body.password))
            except PasswordServiceBusy:
                log.warning("Skipped upgrading a password hash: the server is short of memory")
        return signed_in(request, response, user, body.remember)

    @router.get("/google/start")
    async def google_start(request: Request, next: str = "", remember: bool = True) -> Response:
        if not settings.google_enabled:
            return RedirectResponse("/login?error=google_unavailable", status_code=303)
        ip_key = f"google:ip:{client_ip(request)}"
        if limiter.retry_after(ip_key, 20, 900):
            return RedirectResponse("/login?error=too_many", status_code=303)
        limiter.hit(ip_key)
        state, verifier, nonce = accounts.create_oauth_state(safe_next(next), remember)
        params = {
            "client_id": settings.google_client_id,
            "redirect_uri": google_redirect_uri(request),
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "nonce": nonce,
            "code_challenge": _pkce_challenge(verifier),
            "code_challenge_method": "S256",
            "prompt": "select_account",
        }
        response = RedirectResponse(f"{GOOGLE_AUTHORIZE_URL}?{urlencode(params)}", status_code=303)
        response.set_cookie(
            OAUTH_COOKIE,
            state,
            max_age=600,
            httponly=True,
            secure=secure_cookies(request),
            samesite="lax",
            path=OAUTH_COOKIE_PATH,
        )
        response.headers["Cache-Control"] = "no-store"
        return response

    @router.get("/google/callback")
    async def google_callback(request: Request, code: str = "", state: str = "", error: str = "") -> Response:
        def back_to_login(reason: str) -> Response:
            response = RedirectResponse(f"/login?error={reason}", status_code=303)
            response.delete_cookie(OAUTH_COOKIE, path=OAUTH_COOKIE_PATH)
            return response

        if error:
            return back_to_login("google_cancelled" if error == "access_denied" else "google_failed")
        # the state must match the cookie set when this browser started the sign-in
        cookie_state = request.cookies.get(OAUTH_COOKIE, "")
        if not state or not cookie_state or not hmac.compare_digest(state, cookie_state):
            return back_to_login("google_expired")
        pending = accounts.take_oauth_state(state)
        if pending is None:
            return back_to_login("google_expired")
        if not code or not settings.google_enabled:
            return back_to_login("google_failed")
        try:
            claims = await google_exchange(code, google_redirect_uri(request), pending["code_verifier"])
        except Exception as exc:
            log.warning("Google sign-in failed during the code exchange: %s", exc)
            return back_to_login("google_failed")
        if not hmac.compare_digest(str(claims.get("nonce") or ""), pending["nonce"]):
            log.warning("Google sign-in rejected: nonce mismatch")
            return back_to_login("google_failed")
        if not claims.get("sub") or not claims.get("email") or not claims.get("email_verified"):
            return back_to_login("google_email")

        user, created = google_account(claims)
        target = pending["next_path"] or ("/new" if created else "/")
        response = RedirectResponse(_with_param(target, "welcome", "new" if created else "back"), status_code=303)
        open_session(request, response, user, bool(pending["remember"]))
        response.delete_cookie(OAUTH_COOKIE, path=OAUTH_COOKIE_PATH)
        return response

    @router.post("/logout", status_code=204)
    async def logout(request: Request) -> Response:
        accounts.revoke_session(request.cookies.get(COOKIE_NAME))
        response = Response(status_code=204)
        response.delete_cookie(COOKIE_NAME, path="/", httponly=True, samesite="lax")
        return response

    async def deliver(to: str, message: tuple[str, str, str], what: str) -> None:
        subject, text, html_body = message
        try:
            await mailer.send(to, subject, text, html_body)
        except Exception:
            log.exception("Could not send the %s email", what)

    @router.post("/forgot-password", status_code=202)
    async def forgot_password(body: ForgotBody, request: Request, background: BackgroundTasks) -> dict[str, Any]:
        guard(f"forgot:ip:{client_ip(request)}", 10, 3600)
        email = normalize_email(body.email)
        email_key = f"forgot:email:{email}"
        # The same answer, in the same time, whether or not the account exists: the page never
        # says which, and the email goes out after the response. The inbox tells the owner: a
        # reset link if the account exists, otherwise a note that there's no account yet.
        if limiter.retry_after(email_key, 3, 3600) == 0:
            limiter.hit(email_key)
            user = accounts.by_email(email)
            base = email_link_base(request)
            if base is None:
                log.error("Can't build links for emails: set PREP_APP_URL to the site's public URL.")
            elif user is not None:
                token = accounts.create_reset_token(user["id"])
                link = f"{base}/reset-password?token={token}"
                minutes = int(RESET_TTL.total_seconds() // 60)
                background.add_task(deliver, user["email"], reset_email(user["first_name"], link, minutes, user["email"]),
                                    "password-reset")
            elif limiter.retry_after("forgot:unknown", 30, 3600) == 0:
                # capped site-wide too, so the form can't be used to mail strangers in bulk
                limiter.hit("forgot:unknown")
                signup = f"{base}/signup?{urlencode({'email': email})}"
                background.add_task(deliver, email, no_account_email(email, signup), "no-account")
        return {"ok": True}

    @router.get("/reset-password")
    async def check_reset_token(token: str = "") -> dict[str, Any]:
        user = accounts.reset_token_user(token)
        return {"valid": user is not None, "email": user["email"] if user else None}

    @router.post("/reset-password")
    async def reset_password(body: ResetBody, request: Request, response: Response) -> dict[str, Any]:
        guard(f"reset:ip:{client_ip(request)}", 20, 3600)
        invalid = AccountError("This reset link is invalid or has expired. Request a new one.", "token", 400)
        user = accounts.reset_token_user(body.token)
        if user is None:
            raise invalid
        check_password(body.password, user["email"])  # a rejected password doesn't use up the link
        # hash before using up the link: if hashing fails (e.g. the server is short of memory)
        # the link still works for another try
        password_hash = await asyncio.to_thread(hash_password, body.password)
        if not accounts.consume_reset_token(body.token):  # single use, even under concurrent requests
            raise invalid
        accounts.revoke_all_sessions(user["id"])  # sign out everywhere else
        user = accounts.update_user(user["id"], password_hash=password_hash, email_verified=1)
        return signed_in(request, response, user, body.remember)

    return router, current_user
