"""Streamlit dashboard: human-in-the-loop review + pipeline runner."""
import json, os, sys
from pathlib import Path

from dotenv import load_dotenv
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

# Promote Streamlit Cloud secrets to env vars for the modules below
try:
    for key in ("GROQ_API_KEY", "GROQ_MODEL", "SCORER_MODE", "MAILBOX_MODE", "EMAIL_MODE"):
        if key in st.secrets and not os.getenv(key):
            os.environ[key] = str(st.secrets[key])
except Exception:
    pass

from rpa.email_sender import send_email  # noqa
from rpa.tracker import mark_status  # noqa

RESULTS_PATH = ROOT / "data" / "screening_results.json"
AUDIT_LOG = ROOT / "data" / "approvals.log"

st.set_page_config(page_title="Recruitment Dashboard", layout="wide")
st.title("Recruitment Screening Dashboard")
st.caption("Junior Data Analyst | Brightline Analytics")


def run_pipeline():
    from datetime import datetime
    from rpa.inbox_poller import poll_inbox
    from rpa.cv_extractor import store_cv, extract_metadata
    from rpa.tracker import log_applicant, update_score
    from agentic.cv_parser import parse_cv
    from agentic.scorer import score_cv
    from agentic.email_drafter import draft_email

    jd_path = ROOT / "data" / "job_description.txt"
    if not jd_path.exists():
        st.error(f"Job description not found at {jd_path}")
        return
    job_description = jd_path.read_text()

    messages = poll_inbox()
    if not messages:
        st.warning("No applications found in the mock inbox.")
        return

    progress = st.progress(0.0, text="Starting...")
    results = []
    total = len(messages)
    for i, m in enumerate(messages, start=1):
        progress.progress(i / (total + 1), text=f"Processing {m['sender_name']}...")
        cv_path = store_cv(m)
        if cv_path is None: continue
        meta = extract_metadata(m, cv_path)
        log_applicant(meta)
        cv_text = parse_cv(meta["cv_path"])
        try:
            score = score_cv(cv_text, job_description)
        except Exception as e:
            st.warning(f"Scoring failed for {meta['candidate_name']}: {e}")
            continue
        subject, body = draft_email(score, "Junior Data Analyst")
        update_score(meta["candidate_email"], score.overall_score, score.recommendation)
        results.append({
            "candidate_email": meta["candidate_email"],
            "cv_path": meta["cv_path"],
            "score": score.model_dump(),
            "draft_email": {"subject": subject, "body": body},
            "status": "ready_for_review",
            "scored_at": datetime.now().isoformat(timespec="seconds"),
        })
    results.sort(key=lambda r: r["score"]["overall_score"], reverse=True)
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)
    progress.progress(1.0, text=f"Scored {len(results)} candidate(s).")


with st.sidebar:
    st.subheader("Pipeline")
    if st.button("Run screening pipeline", type="primary", use_container_width=True):
        with st.spinner("Running RPA + Agentic pipeline..."):
            run_pipeline()
        st.rerun()
    if RESULTS_PATH.exists() and st.button("Clear results", use_container_width=True):
        RESULTS_PATH.unlink()
        st.rerun()
    st.divider()
    st.caption("Mode")
    st.code(f"SCORER_MODE={os.getenv('SCORER_MODE', 'llm')}\nMODEL={os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')}")

if not RESULTS_PATH.exists():
    st.info("No screening results yet. Click **Run screening pipeline** in the sidebar.")
    st.stop()

with open(RESULTS_PATH) as f:
    results = json.load(f)
if not results:
    st.info("No candidates have been scored yet.")
    st.stop()

table = pd.DataFrame([
    {"Name": r["score"]["candidate_name"], "Email": r["candidate_email"],
     "Score": r["score"]["overall_score"],
     "Recommendation": r["score"]["recommendation"], "Status": r["status"]}
    for r in results
])
st.subheader("Ranked shortlist")
st.dataframe(table, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Candidate details")
names = [r["score"]["candidate_name"] for r in results]
selection = st.selectbox("Pick a candidate to review:", names)
r = next(x for x in results if x["score"]["candidate_name"] == selection)

col1, col2 = st.columns([1, 1])
with col1:
    st.markdown(f"### {r['score']['candidate_name']}")
    st.markdown(f"**Email:** {r['candidate_email']}")
    st.markdown(f"**Overall score:** {r['score']['overall_score']} / 100")
    st.markdown(f"**Recommendation:** `{r['score']['recommendation']}`")
    st.markdown(f"**Rationale:** {r['score']['rationale']}")
    st.markdown("**Criteria breakdown**")
    st.dataframe(pd.DataFrame(r["score"]["criteria"]), use_container_width=True, hide_index=True)
    st.markdown("**Strengths**")
    for s in r["score"]["strengths"]: st.write(f"- {s}")
    st.markdown("**Gaps**")
    for g in r["score"]["gaps"]: st.write(f"- {g}")

with col2:
    st.markdown("### Draft email")
    subject = st.text_input("Subject", r["draft_email"]["subject"], key=f"subj_{selection}")
    body = st.text_area("Body", r["draft_email"]["body"], height=320, key=f"body_{selection}")
    st.markdown("### Decide")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Approve and send", type="primary", use_container_width=True):
            res = send_email(r["candidate_email"], r["score"]["candidate_name"], subject, body)
            mark_status(r["candidate_email"], "Sent")
            r["status"] = "sent"
            with open(RESULTS_PATH, "w") as f: json.dump(results, f, indent=2)
            with open(AUDIT_LOG, "a") as f: f.write(f"APPROVED {r['candidate_email']} -> {res}\n")
            st.success(f"Email dispatched: {res}")
    with c2:
        if st.button("Override to reject", use_container_width=True):
            r["score"]["recommendation"] = "reject"
            r["status"] = "overridden"
            mark_status(r["candidate_email"], "Overridden (reject)")
            with open(RESULTS_PATH, "w") as f: json.dump(results, f, indent=2)
            with open(AUDIT_LOG, "a") as f: f.write(f"OVERRIDE {r['candidate_email']} -> reject\n")
            st.warning("Marked as overridden.")
    with c3:
        if st.button("Hold for later", use_container_width=True):
            r["status"] = "held"
            mark_status(r["candidate_email"], "Held")
            with open(RESULTS_PATH, "w") as f: json.dump(results, f, indent=2)
            with open(AUDIT_LOG, "a") as f: f.write(f"HOLD {r['candidate_email']}\n")
            st.info("Held for later review.")
