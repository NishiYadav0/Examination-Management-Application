"""Very small SMTP helper (no extra library). Locally we send to MailHog."""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

from flask import current_app, render_template


def send_mail(to, subject, html=None, text=None, attachments=None):
    cfg = current_app.config
    msg = MIMEMultipart("mixed")
    msg["From"] = cfg["MAIL_SENDER"]
    msg["To"] = to if isinstance(to, str) else ", ".join(to)
    msg["Subject"] = subject
    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(text or "Please view this e-mail in an HTML capable client.", "plain"))
    if html:
        alt.attach(MIMEText(html, "html"))
    msg.attach(alt)
    for path in attachments or []:
        with open(path, "rb") as fh:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(fh.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{os.path.basename(path)}"')
        msg.attach(part)
    try:
        with smtplib.SMTP(cfg["MAIL_SERVER"], cfg["MAIL_PORT"], timeout=10) as s:
            s.send_message(msg)
        return True
    except Exception as exc:  # MailHog not running etc.
        current_app.logger.warning(f"E-mail to {to} failed: {exc}")
        return False


def send_template(to, subject, template, **ctx):
    ctx.setdefault("frontend_url", current_app.config["FRONTEND_URL"])
    html = render_template(f"emails/{template}", subject=subject, **ctx)
    return send_mail(to, subject, html=html)
