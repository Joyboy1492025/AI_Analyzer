"""Send the PDF report by email via SMTP."""

import re
import smtplib
from email.message import EmailMessage
from pathlib import Path

from config import SMTP_APP_PASSWORD, SMTP_EMAIL, SMTP_HOST, SMTP_PORT

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

DEFAULT_BODY = """Hi,

Please find attached the AI-generated analysis report.

Regards,
AI Assistant
"""


def is_valid_email(address: str) -> bool:
    return bool(_EMAIL_RE.match((address or "").strip()))


def send_email_with_pdf(
    receiver_email: str,
    pdf_file: str,
    sender_email: str = "",
    app_password: str = "",
    subject: str = "AI Analysis Report",
    body: str = DEFAULT_BODY,
) -> None:
    sender_email = (sender_email or SMTP_EMAIL).strip()
    app_password = (app_password or SMTP_APP_PASSWORD).strip()

    if not is_valid_email(receiver_email):
        raise ValueError("Receiver email address is not valid.")
    if not is_valid_email(sender_email) or not app_password:
        raise ValueError(
            "Sender email and app password are required "
            "(enter them in the UI or set SMTP_EMAIL / SMTP_APP_PASSWORD in .env)."
        )

    msg = EmailMessage()
    msg["From"] = sender_email
    msg["To"] = receiver_email.strip()
    msg["Subject"] = subject or "AI Analysis Report"
    msg.set_content(body or DEFAULT_BODY)

    pdf = Path(pdf_file)
    msg.add_attachment(
        pdf.read_bytes(),
        maintype="application",
        subtype="pdf",
        filename=pdf.name,
    )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
        server.starttls()
        server.login(sender_email, app_password)
        server.send_message(msg)