"""RPA component: send approved emails via SMTP (or mock outbox)."""
import os, smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

EMAIL_MODE = os.getenv("EMAIL_MODE", "mock")
OUTBOX = Path("data/outbox")


def send_email(to_email: str, to_name: str, subject: str, body: str) -> str:
    msg = EmailMessage()
    msg["From"] = os.getenv("FROM_EMAIL", "recruitment@brightline.example")
    msg["To"] = f"{to_name} <{to_email}>"
    msg["Subject"] = subject
    msg.set_content(body)

    if EMAIL_MODE == "smtp":
        host = os.environ["SMTP_HOST"]
        port = int(os.getenv("SMTP_PORT", "587"))
        user = os.environ["SMTP_USER"]
        pwd = os.environ["SMTP_PASSWORD"]
        with smtplib.SMTP(host, port) as s:
            s.starttls()
            s.login(user, pwd)
            s.send_message(msg)
        return f"sent to {to_email}"

    OUTBOX.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"{ts}_{to_email.replace('@', '_at_')}.eml"
    path = OUTBOX / fname
    with open(path, "wb") as f:
        f.write(bytes(msg))
    return str(path)
