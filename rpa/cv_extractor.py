"""RPA component: extract CV attachments to a date-partitioned folder."""
import re
from datetime import datetime
from pathlib import Path

STORE_ROOT = Path("data/received_cvs")


def safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_").lower()


def store_cv(message: dict):
    pdf_att = next((a for a in message["attachments"] if a["filename"].lower().endswith(".pdf")), None)
    if not pdf_att: return None
    today = datetime.now().strftime("%Y-%m-%d")
    target_dir = STORE_ROOT / today
    target_dir.mkdir(parents=True, exist_ok=True)
    candidate_slug = safe_name(message["sender_name"]) or "candidate"
    filename = f"{candidate_slug}_{safe_name(pdf_att['filename'])}"
    target = target_dir / filename
    with open(target, "wb") as f:
        f.write(pdf_att["payload"])
    return target


def extract_metadata(message: dict, cv_path):
    return {
        "received_at": datetime.now().isoformat(timespec="seconds"),
        "candidate_name": message["sender_name"],
        "candidate_email": message["sender_email"],
        "subject": message["subject"],
        "cv_path": str(cv_path),
    }
