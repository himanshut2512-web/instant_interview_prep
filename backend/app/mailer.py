"""Outgoing email over SMTP (works with any provider, including free tiers such
as Gmail with an app password or Brevo).

Without SMTP settings, emails are written to the server log instead, so the
password-reset flow can still be tested locally.

Check the settings with:  python -m app.mailer you@example.com
"""

from __future__ import annotations

import asyncio
import html
import logging
import smtplib
import ssl
import sys
from email.message import EmailMessage
from email.utils import formataddr, make_msgid

from .config import Settings

log = logging.getLogger("prep.mail")


class Mailer:
    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def configured(self) -> bool:
        return self.settings.email_enabled

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
        message["Message-ID"] = make_msgid(domain=sender.rsplit("@", 1)[-1].strip(">") or None)
        message.set_content(text)
        message.add_alternative(html_body, subtype="html")
        context = ssl.create_default_context()
        if s.smtp_security == "ssl":
            server: smtplib.SMTP = smtplib.SMTP_SSL(s.smtp_host, s.smtp_port, context=context, timeout=20)
        else:
            server = smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=20)
        with server:
            if s.smtp_security == "starttls":
                server.starttls(context=context)
            if s.smtp_user and s.smtp_password:
                password = s.smtp_password
                if "gmail.com" in (s.smtp_host or "").lower():
                    password = password.replace(" ", "")  # Google shows app passwords in groups of four
                server.login(s.smtp_user, password)
            server.send_message(message)
        log.info("Sent '%s' to %s", subject, to)


def reset_email(first_name: str, link: str, minutes: int) -> tuple[str, str, str]:
    """Return (subject, text, html) for a password-reset email."""
    subject = "Reset your InstantInterviewPrep password"
    text = (
        f"Hi {first_name},\n\n"
        "We received a request to reset your InstantInterviewPrep password. Open this link to choose a new one:\n\n"
        f"{link}\n\n"
        f"The link works once and expires in {minutes} minutes. If you didn't ask for this, you can ignore this "
        "email - your password stays the same.\n"
    )
    name = html.escape(first_name)
    href = html.escape(link, quote=True)
    body = f"""<!doctype html>
<html><body style="margin:0;padding:0;background:#f5f6fa;font-family:Segoe UI,Arial,sans-serif;color:#141729">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="padding:32px 12px">
<tr><td align="center">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"
       style="max-width:520px;background:#ffffff;border-radius:16px;border:1px solid #e4e7f0;overflow:hidden">
<tr><td style="background:linear-gradient(135deg,#5a52ec,#4f46e5 48%,#7c3aed);background-color:#4f46e5;padding:24px 28px;
              color:#ffffff;font-size:18px;font-weight:700">InstantInterviewPrep</td></tr>
<tr><td style="padding:28px">
<p style="margin:0 0 14px;font-size:16px">Hi {name},</p>
<p style="margin:0 0 22px;font-size:15px;line-height:1.6;color:#3d4258">We received a request to reset your password.
Choose a new one with the button below.</p>
<p style="margin:0 0 22px"><a href="{href}" style="display:inline-block;background:#4f46e5;color:#ffffff;
text-decoration:none;font-weight:600;padding:12px 22px;border-radius:10px">Reset password</a></p>
<p style="margin:0 0 8px;font-size:13px;color:#646a82">The link works once and expires in {minutes} minutes.
If you didn't ask for this, ignore this email - your password stays the same.</p>
<p style="margin:16px 0 0;font-size:12px;color:#8a90a6;word-break:break-all">{href}</p>
</td></tr></table></td></tr></table></body></html>"""
    return subject, text, body


def _main(argv: list[str]) -> int:
    """Send a test email with the configured settings and explain common failures."""
    from .config import get_settings

    if len(argv) != 1 or "@" not in argv[0]:
        print("Usage: python -m app.mailer recipient@example.com")
        return 2
    settings = get_settings()
    mailer = Mailer(settings)
    if not mailer.configured:
        print("Email is not configured. Set PREP_SMTP_HOST, PREP_SMTP_USER, PREP_SMTP_PASSWORD and PREP_SMTP_FROM "
              "in backend/.env (see .env.example).")
        return 1
    text = "Your InstantInterviewPrep email settings work: password-reset emails will be delivered."
    try:
        mailer._send(argv[0], "InstantInterviewPrep test email", text, f"<p>{html.escape(text)}</p>")
    except smtplib.SMTPAuthenticationError as exc:
        print(f"The SMTP server rejected the username or password: {exc.smtp_code} {exc.smtp_error!r}")
        if "gmail" in (settings.smtp_host or "").lower():
            print("For Gmail, PREP_SMTP_PASSWORD must be a 16-character App Password from "
                  "https://myaccount.google.com/apppasswords (2-Step Verification must be on), not your normal password.")
        return 1
    except Exception as exc:  # network, TLS or relay errors
        print(f"Sending failed: {exc!r}")
        return 1
    print(f"Sent a test email to {argv[0]} through {settings.smtp_host}:{settings.smtp_port}. "
          "Check the inbox (and the spam folder).")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
