"""RPA component: poll an IMAP inbox for new application emails."""
import os, json, imaplib, email
from email.header import decode_header
from datetime import datetime
from pathlib import Path

MAILBOX_MODE = os.getenv("MAILBOX_MODE", "mock")
MOCK_INBOX = Path("data/mock_inbox.json")


def _decode(value):
    if value is None: return ""
    parts = decode_header(value)
    decoded = ""
    for text, charset in parts:
        if isinstance(text, bytes):
            decoded += text.decode(charset or "utf-8", errors="ignore")
        else:
            decoded += text
    return decoded


def poll_imap():
    host = os.environ["IMAP_HOST"]
    user = os.environ["IMAP_USER"]
    pwd = os.environ["IMAP_PASSWORD"]
    M = imaplib.IMAP4_SSL(host)
    M.login(user, pwd)
    M.select("INBOX")
    status, data = M.search(None, '(UNSEEN SUBJECT "Application")')
    messages = []
    for num in data[0].split():
        status, msg_data = M.fetch(num, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])
        attachments = []
        for part in msg.walk():
            if part.get_content_maintype() == "multipart": continue
            if part.get("Content-Disposition") and "attachment" in part["Content-Disposition"]:
                filename = _decode(part.get_filename())
                payload = part.get_payload(decode=True)
                attachments.append({"filename": filename, "payload": payload})
        messages.append({
            "sender_name": _decode(msg.get("From")).split("<")[0].strip(),
            "sender_email": _decode(msg.get("From")).split("<")[-1].rstrip(">"),
            "subject": _decode(msg.get("Subject")),
            "date": _decode(msg.get("Date")),
            "attachments": attachments,
        })
    M.logout()
    return messages


def poll_mock():
    if not MOCK_INBOX.exists(): return []
    with open(MOCK_INBOX) as f:
        entries = json.load(f)
    messages = []
    for e in entries:
        cv_path = Path(e["cv_path"])
        if not cv_path.exists():
            print(f"  [warn] CV file missing: {cv_path}")
            continue
        with open(cv_path, "rb") as f:
            payload = f.read()
        messages.append({
            "sender_name": e["sender_name"],
            "sender_email": e["sender_email"],
            "subject": e["subject"],
            "date": e.get("date", datetime.now().isoformat()),
            "attachments": [{"filename": cv_path.name, "payload": payload}],
        })
    return messages


def poll_inbox():
    if MAILBOX_MODE == "imap":
        print("[RPA] Polling IMAP inbox...")
        return poll_imap()
    print("[RPA] Polling mock inbox (set MAILBOX_MODE=imap for real IMAP)")
    return poll_mock()
