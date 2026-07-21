"""Main orchestrator. Runs the full RPA + Agentic pipeline."""
from dotenv import load_dotenv
load_dotenv()

import json, sys
from pathlib import Path
from datetime import datetime

from rpa.inbox_poller import poll_inbox
from rpa.cv_extractor import store_cv, extract_metadata
from rpa.tracker import log_applicant, update_score
from agentic.cv_parser import parse_cv
from agentic.scorer import score_cv
from agentic.email_drafter import draft_email

ROLE_TITLE = "Junior Data Analyst"
RESULTS_PATH = Path("data/screening_results.json")
JD_PATH = Path("data/job_description.txt")


def banner(text):
    print(f"\n{'-'*60}\n{text}\n{'-'*60}")


def run():
    if not JD_PATH.exists():
        sys.exit(f"Job description not found at {JD_PATH}")
    job_description = JD_PATH.read_text()

    banner("STAGE 1 (RPA): Polling inbox")
    messages = poll_inbox()
    if not messages:
        print("No new applications. Exiting.")
        return

    intake = []
    for m in messages:
        cv_path = store_cv(m)
        if cv_path is None:
            print(f"  [skip] {m['sender_email']} has no PDF attachment.")
            continue
        meta = extract_metadata(m, cv_path)
        log_applicant(meta)
        intake.append(meta)
        print(f"  [ok] stored CV for {meta['candidate_name']} -> {cv_path}")

    banner("STAGE 2 (AGENTIC): Parsing and scoring CVs")
    results = []
    for meta in intake:
        print(f"  scoring {meta['candidate_name']}...")
        cv_text = parse_cv(meta["cv_path"])
        try:
            score = score_cv(cv_text, job_description)
        except Exception as e:
            print(f"    [warn] scoring failed: {e}")
            continue
        subject, body = draft_email(score, ROLE_TITLE)
        update_score(meta["candidate_email"], score.overall_score, score.recommendation)
        results.append({
            "candidate_email": meta["candidate_email"],
            "cv_path": meta["cv_path"],
            "score": score.model_dump(),
            "draft_email": {"subject": subject, "body": body},
            "status": "ready_for_review",
            "scored_at": datetime.now().isoformat(timespec="seconds"),
        })
        print(f"    -> {score.overall_score}/100 | {score.recommendation}")

    results.sort(key=lambda r: r["score"]["overall_score"], reverse=True)
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)

    banner("RESULTS WRITTEN")
    print(f"Wrote {len(results)} scored candidate(s) to {RESULTS_PATH}")
    print("Open the dashboard: streamlit run dashboard/app.py")


if __name__ == "__main__":
    run()
