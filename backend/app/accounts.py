"""User accounts: registration, password hashing, login sessions and reset tokens.

Passwords are hashed with Argon2id. Login sessions and password-reset links use
random tokens; only their SHA-256 hashes are stored, so a leaked database
cannot be used to sign in or reset a password.
"""

from __future__ import annotations

import hashlib
import re
import secrets
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from argon2 import PasswordHasher
from argon2.exceptions import HashingError, InvalidHashError, VerificationError, VerifyMismatchError
from email_validator import EmailNotValidError, validate_email

from .storage import Store, utcnow

PASSWORD_MIN = 8
PASSWORD_MAX = 128
NAME_MAX = 60
RESET_TTL = timedelta(hours=1)
OAUTH_STATE_TTL = timedelta(minutes=10)
SHORT_SESSION_TTL = timedelta(hours=24)  # "keep me signed in" unticked
SESSION_REFRESH_AFTER = timedelta(days=1)

# Argon2id with OWASP's recommended settings: 19 MiB of memory, 2 passes, 1 lane. Hashes made
# with other settings (e.g. the library default of 64 MiB) still verify and are upgraded on the
# next successful sign-in (see needs_rehash).
_hasher = PasswordHasher(time_cost=2, memory_cost=19 * 1024, parallelism=1)
# Each hash briefly needs that memory; cap how many run at once so a burst of sign-ins can't
# exhaust the server's memory.
_hash_slots = threading.BoundedSemaphore(4)
_MEMORY_ATTEMPTS = 3
# Verified against when the email is unknown, so response times don't reveal which emails exist.
_dummy_hash: str | None = None
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


class PasswordServiceBusy(Exception):
    """Hashing ran out of memory even after retrying. Nothing was changed; the request can be retried."""


class AccountError(ValueError):
    """A problem the user can fix (shown as-is in the UI)."""

    def __init__(self, message: str, field: str | None = None, status: int = 422):
        super().__init__(message)
        self.field = field
        self.status = status


# ----------------------------------------------------------------- validation
def normalize_email(raw: str) -> str:
    try:
        info = validate_email((raw or "").strip(), check_deliverability=False)
    except EmailNotValidError as exc:
        raise AccountError("Enter a valid email address.", "email") from exc
    return info.normalized.lower()


def clean_name(raw: str, field: str, label: str) -> str:
    name = re.sub(r"\s+", " ", _CONTROL.sub("", raw or "")).strip()
    if not name:
        raise AccountError(f"Enter your {label}.", field)
    if len(name) > NAME_MAX:
        raise AccountError(f"{label.capitalize()} must be at most {NAME_MAX} characters.", field)
    return name


def check_password(password: str, email: str = "") -> None:
    if len(password) < PASSWORD_MIN:
        raise AccountError(f"Use at least {PASSWORD_MIN} characters.", "password")
    if len(password) > PASSWORD_MAX:
        raise AccountError(f"Use at most {PASSWORD_MAX} characters.", "password")
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise AccountError("Include at least one letter and one number.", "password")
    if email and password.lower() == email.lower():
        raise AccountError("Your password can't be your email address.", "password")


def _out_of_memory(exc: Exception) -> bool:
    return not isinstance(exc, VerifyMismatchError) and "memory" in str(exc).lower()


def _argon2(work: Callable[[], Any]) -> Any:
    """Run one Argon2 operation in a free slot, retrying briefly if memory is short."""
    for attempt in range(_MEMORY_ATTEMPTS):
        with _hash_slots:
            try:
                return work()
            except (HashingError, VerificationError) as exc:
                if not _out_of_memory(exc):
                    raise
        time.sleep(0.25 * (attempt + 1))
    raise PasswordServiceBusy("not enough free memory to hash a password")


def hash_password(password: str) -> str:
    return _argon2(lambda: _hasher.hash(password))


def verify_password(password_hash: str | None, password: str) -> bool:
    """True only for a correct password. Raises PasswordServiceBusy instead of guessing when
    memory runs out, so a correct password is never reported as wrong."""
    global _dummy_hash
    if password_hash is None:
        if _dummy_hash is None:
            _dummy_hash = hash_password(secrets.token_urlsafe(16))
        target = _dummy_hash
    else:
        target = password_hash
    try:
        matched = _argon2(lambda: _hasher.verify(target, password))
    except (VerificationError, InvalidHashError):  # wrong password, or a damaged hash
        return False
    return bool(matched) and password_hash is not None


def needs_rehash(password_hash: str) -> bool:
    try:
        return _hasher.check_needs_rehash(password_hash)
    except InvalidHashError:
        return False


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(moment: datetime) -> str:
    return moment.isoformat(timespec="seconds")


def public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": user["id"],
        "email": user["email"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "avatar_url": user.get("avatar_url"),
        "email_verified": bool(user.get("email_verified")),
        "has_password": bool(user.get("password_hash")),
        "google_linked": bool(user.get("google_sub")),
        "created_at": user["created_at"],
    }


@dataclass
class IssuedSession:
    token: str
    expires_at: datetime
    persistent: bool


class Accounts:
    def __init__(self, store: Store, session_days: int = 30):
        self.store = store
        self.session_ttl = timedelta(days=session_days)

    # ------------------------------------------------------------------ users
    def by_id(self, user_id: str) -> dict[str, Any] | None:
        return self.store.fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))

    def by_email(self, email: str) -> dict[str, Any] | None:
        return self.store.fetch_one("SELECT * FROM users WHERE email = ?", (email,))

    def by_google_sub(self, sub: str) -> dict[str, Any] | None:
        return self.store.fetch_one("SELECT * FROM users WHERE google_sub = ?", (sub,))

    def create_user(
        self,
        *,
        email: str,
        first_name: str,
        last_name: str,
        password_hash: str | None = None,
        google_sub: str | None = None,
        avatar_url: str | None = None,
        email_verified: bool = False,
    ) -> dict[str, Any]:
        if self.by_email(email):
            raise AccountError("An account with this email already exists. Sign in instead.", "email", 409)
        first_user = self.store.fetch_one("SELECT 1 AS one FROM users LIMIT 1") is None
        now = utcnow()
        user_id = uuid.uuid4().hex
        self.store.execute(
            "INSERT INTO users (id, email, first_name, last_name, password_hash, google_sub, avatar_url, "
            "email_verified, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, email, first_name, last_name, password_hash, google_sub, avatar_url,
             int(email_verified), now, now),
        )
        if first_user:  # the first account inherits prep kits made before sign-in existed
            self.store.adopt_unowned(user_id)
        user = self.by_id(user_id)
        assert user is not None
        return user

    def update_user(self, user_id: str, **fields: Any) -> dict[str, Any]:
        allowed = {"first_name", "last_name", "password_hash", "google_sub", "avatar_url", "email_verified",
                   "last_login_at"}
        unknown = set(fields) - allowed
        if unknown:
            raise ValueError(f"Unknown user fields: {sorted(unknown)}")
        if fields:
            assignments = ", ".join(f"{k} = ?" for k in fields)
            self.store.execute(
                f"UPDATE users SET {assignments}, updated_at = ? WHERE id = ?",
                (*fields.values(), utcnow(), user_id),
            )
        user = self.by_id(user_id)
        assert user is not None
        return user

    # --------------------------------------------------------- login sessions
    def issue_session(self, user_id: str, *, persistent: bool, user_agent: str = "", ip: str = "") -> IssuedSession:
        token = secrets.token_urlsafe(32)
        now = _now()
        expires = now + (self.session_ttl if persistent else SHORT_SESSION_TTL)
        self.store.execute(
            "INSERT INTO auth_sessions (token_hash, user_id, created_at, expires_at, last_seen_at, persistent, "
            "user_agent, ip) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (_token_hash(token), user_id, _iso(now), _iso(expires), _iso(now), int(persistent),
             (user_agent or "")[:300], (ip or "")[:64]),
        )
        self.store.execute("UPDATE users SET last_login_at = ? WHERE id = ?", (_iso(now), user_id))
        self.store.execute("DELETE FROM auth_sessions WHERE expires_at < ?", (_iso(now),))
        return IssuedSession(token, expires, persistent)

    def resolve_session(self, token: str | None) -> tuple[dict[str, Any], IssuedSession | None] | None:
        """Return (user, refreshed session or None) for a valid token, else None.

        Persistent sessions slide: once a day of use they are extended to the full
        lifetime again, and the caller re-sends the cookie.
        """
        if not token or len(token) > 200:
            return None
        row = self.store.fetch_one("SELECT * FROM auth_sessions WHERE token_hash = ?", (_token_hash(token),))
        if row is None:
            return None
        now = _now()
        if datetime.fromisoformat(row["expires_at"]) <= now:
            self.store.execute("DELETE FROM auth_sessions WHERE token_hash = ?", (row["token_hash"],))
            return None
        user = self.by_id(row["user_id"])
        if user is None:
            return None
        refreshed = None
        if row["persistent"] and now - datetime.fromisoformat(row["last_seen_at"]) > SESSION_REFRESH_AFTER:
            expires = now + self.session_ttl
            self.store.execute(
                "UPDATE auth_sessions SET last_seen_at = ?, expires_at = ? WHERE token_hash = ?",
                (_iso(now), _iso(expires), row["token_hash"]),
            )
            refreshed = IssuedSession(token, expires, True)
        return user, refreshed

    def revoke_session(self, token: str | None) -> None:
        if token:
            self.store.execute("DELETE FROM auth_sessions WHERE token_hash = ?", (_token_hash(token),))

    def revoke_all_sessions(self, user_id: str) -> None:
        self.store.execute("DELETE FROM auth_sessions WHERE user_id = ?", (user_id,))

    # -------------------------------------------------------- password resets
    def create_reset_token(self, user_id: str) -> str:
        token = secrets.token_urlsafe(32)
        now = _now()
        # only the newest link works
        self.store.execute("DELETE FROM password_resets WHERE user_id = ?", (user_id,))
        self.store.execute(
            "INSERT INTO password_resets (token_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (_token_hash(token), user_id, _iso(now), _iso(now + RESET_TTL)),
        )
        return token

    def reset_token_user(self, token: str) -> dict[str, Any] | None:
        if not token or len(token) > 200:
            return None
        row = self.store.fetch_one("SELECT * FROM password_resets WHERE token_hash = ?", (_token_hash(token),))
        if row is None or row["used_at"] or datetime.fromisoformat(row["expires_at"]) <= _now():
            return None
        return self.by_id(row["user_id"])

    def consume_reset_token(self, token: str) -> bool:
        """Mark a reset link used. False if it was already used (e.g. two tabs at once)."""
        changed = self.store.execute(
            "UPDATE password_resets SET used_at = ? WHERE token_hash = ? AND used_at IS NULL",
            (utcnow(), _token_hash(token)),
        )
        return changed == 1

    # ------------------------------------------------------ Google sign-in
    def create_oauth_state(self, next_path: str, remember: bool) -> tuple[str, str, str]:
        """Start one Google sign-in attempt. Returns (state, PKCE code verifier, nonce)."""
        state = secrets.token_urlsafe(32)
        verifier = secrets.token_urlsafe(48)  # 64 characters, inside PKCE's 43-128
        nonce = secrets.token_urlsafe(24)
        now = _now()
        self.store.execute("DELETE FROM oauth_states WHERE expires_at < ?", (_iso(now),))
        self.store.execute(
            "INSERT INTO oauth_states (state_hash, code_verifier, nonce, next_path, remember, created_at, expires_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (_token_hash(state), verifier, nonce, next_path, int(remember), _iso(now), _iso(now + OAUTH_STATE_TTL)),
        )
        return state, verifier, nonce

    def take_oauth_state(self, state: str) -> dict[str, Any] | None:
        """Claim a pending Google sign-in; each state works once and only for 10 minutes."""
        if not state or len(state) > 200:
            return None
        key = _token_hash(state)
        row = self.store.fetch_one("SELECT * FROM oauth_states WHERE state_hash = ?", (key,))
        if row is None or self.store.execute("DELETE FROM oauth_states WHERE state_hash = ?", (key,)) != 1:
            return None
        if datetime.fromisoformat(row["expires_at"]) <= _now():
            return None
        return row
