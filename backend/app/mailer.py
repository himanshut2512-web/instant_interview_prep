"""Outgoing email over SMTP (works with any provider, including free tiers such
as Gmail with an app password or Brevo).

Without SMTP settings, emails are written to the server log instead, so the
password-reset flow can still be tested locally.

Set up or check the settings with:  python -m app.setup_auth
"""

from __future__ import annotations

import asyncio
import html
import logging
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid, parseaddr

from .config import Settings

log = logging.getLogger("prep.mail")


def open_smtp(s: Settings, timeout: float = 20) -> smtplib.SMTP:
    """Connect to the configured SMTP server, switch on TLS and log in. The caller closes it."""
    context = ssl.create_default_context()
    if s.smtp_security == "ssl":
        server: smtplib.SMTP = smtplib.SMTP_SSL(s.smtp_host, s.smtp_port, context=context, timeout=timeout)
    else:
        server = smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=timeout)
    try:
        if s.smtp_security == "starttls":
            server.starttls(context=context)
        if s.smtp_user and s.smtp_password:
            password = s.smtp_password
            if "gmail.com" in (s.smtp_host or "").lower():
                password = password.replace(" ", "")  # Google shows app passwords in groups of four
            server.ehlo_or_helo_if_needed()
            if "PLAIN" in server.esmtp_features.get("auth", "").upper().split():
                # one attempt, so a rejected password surfaces as 535 instead of the
                # disconnect Gmail answers to smtplib's retry with another method
                server.user, server.password = s.smtp_user, password
                server.auth("PLAIN", server.auth_plain)
            else:
                server.login(s.smtp_user, password)
    except BaseException:
        server.close()
        raise
    return server


class Mailer:
    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def configured(self) -> bool:
        return self.settings.email_enabled

    @property
    def sender_address(self) -> str:
        """The bare address emails come from, e.g. you@gmail.com."""
        return parseaddr(self.settings.smtp_from or self.settings.smtp_user or "")[1]

    async def send(self, to: str, subject: str, text: str, html_body: str) -> None:
        if not self.configured:
            log.warning("Email delivery is not configured (PREP_SMTP_*). Email to %s - %s:\n%s", to, subject, text)
            return
        await asyncio.to_thread(self._send, to, subject, text, html_body)

    def _send(self, to: str, subject: str, text: str, html_body: str) -> None:
        s = self.settings
        sender = s.smtp_from or s.smtp_user or ""
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = sender if "<" in sender else formataddr(("InstantInterviewPrep", sender))
        message["To"] = to
        message["Date"] = formatdate(localtime=True)
        message["Message-ID"] = make_msgid(domain=self.sender_address.rsplit("@", 1)[-1] or None)
        message["Auto-Submitted"] = "auto-generated"  # RFC 3834: no out-of-office replies to this
        message.set_content(text)
        message.add_alternative(html_body, subtype="html")
        with open_smtp(s) as server:
            server.send_message(message)
        log.info("Sent '%s' to %s", subject, to)


def _layout(inner: str) -> str:
    """Wrap email content in the branded card (table layout and inline styles for mail clients)."""
    return f"""<!doctype html>
<html><body style="margin:0;padding:0;background:#f5f6fa;font-family:Segoe UI,Arial,sans-serif;color:#141729">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="padding:32px 12px">
<tr><td align="center">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"
       style="max-width:520px;background:#ffffff;border-radius:16px;border:1px solid #e4e7f0;overflow:hidden">
<tr><td style="background:linear-gradient(135deg,#5a52ec,#4f46e5 48%,#7c3aed);background-color:#4f46e5;padding:24px 28px;
              color:#ffffff;font-size:18px;font-weight:700">InstantInterviewPrep</td></tr>
<tr><td style="padding:28px">
{inner}
</td></tr></table></td></tr></table></body></html>"""


def _button(href: str, label: str) -> str:
    return (f'<p style="margin:0 0 22px"><a href="{href}" style="display:inline-block;background:#4f46e5;'
            f'color:#ffffff;text-decoration:none;font-weight:600;padding:12px 22px;border-radius:10px">{label}</a></p>')


def reset_email(first_name: str, link: str, minutes: int, email: str = "") -> tuple[str, str, str]:
    """Return (subject, text, html) for a password-reset email."""
    subject = "Reset your InstantInterviewPrep password"
    account = f" for {email}" if email else ""
    text = (
        f"Hi {first_name},\n\n"
        f"We received a request to reset the InstantInterviewPrep password{account}. "
        "Open this link to choose a new one:\n\n"
        f"{link}\n\n"
        f"The link works once and expires in {minutes} minutes. If you didn't ask for this, you can ignore this "
        "email - your password stays the same.\n"
    )
    name = html.escape(first_name)
    href = html.escape(link, quote=True)
    who = f" for <strong>{html.escape(email)}</strong>" if email else ""
    body = _layout(f"""<p style="margin:0 0 14px;font-size:16px">Hi {name},</p>
<p style="margin:0 0 22px;font-size:15px;line-height:1.6;color:#3d4258">We received a request to reset the
InstantInterviewPrep password{who}. Choose a new one with the button below.</p>
{_button(href, "Reset password")}
<p style="margin:0 0 8px;font-size:13px;color:#646a82">The link works once and expires in {minutes} minutes.
If you didn't ask for this, ignore this email - your password stays the same.</p>
<p style="margin:16px 0 0;font-size:12px;color:#8a90a6;word-break:break-all">{href}</p>""")
    return subject, text, body


def no_account_email(email: str, signup_link: str) -> tuple[str, str, str]:
    """Return (subject, text, html) for a reset request on an address that has no account."""
    subject = "About your InstantInterviewPrep password reset"
    text = (
        "Hi,\n\n"
        f"Someone - hopefully you - asked to reset the InstantInterviewPrep password for {email}, "
        "but there's no account with this email address, so there's no password to reset.\n\n"
        "If you have an account, you may have signed up with a different email address: try that one, "
        "or use Continue with Google if you signed up with Google.\n\n"
        f"To create an account with this address: {signup_link}\n\n"
        "If you didn't ask for this, you can ignore this email.\n"
    )
    href = html.escape(signup_link, quote=True)
    body = _layout(f"""<p style="margin:0 0 14px;font-size:16px">Hi,</p>
<p style="margin:0 0 14px;font-size:15px;line-height:1.6;color:#3d4258">Someone - hopefully you - asked to reset the
InstantInterviewPrep password for <strong>{html.escape(email)}</strong>, but there's no account with this email
address, so there's no password to reset.</p>
<p style="margin:0 0 22px;font-size:15px;line-height:1.6;color:#3d4258">If you have an account, you may have signed up
with a different email address, or with Continue with Google. Otherwise you can create one now:</p>
{_button(href, "Create an account")}
<p style="margin:0;font-size:13px;color:#646a82">If you didn't ask for this, you can ignore this email.</p>""")
    return subject, text, body
