"""
Brightline Analytics — Recruitment Command Centre
Professional Streamlit dashboard for H9IAPA CA.

Design goals:
- Clear visual hierarchy (top bar, sidebar, main content)
- Coloured status system (invite/hold/reject use consistent colours)
- Rich candidate cards with radial score visualisation
- Progressive disclosure (list -> detail -> action)
- Fully responsive within Streamlit's constraints
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

# Promote Streamlit Cloud secrets to env vars
try:
    for key in ("GROQ_API_KEY", "GROQ_MODEL", "SCORER_MODE", "MAILBOX_MODE", "EMAIL_MODE"):
        if key in st.secrets and not os.getenv(key):
            os.environ[key] = str(st.secrets[key])
except Exception:
    pass

from rpa.email_sender import send_email  # noqa: E402
from rpa.tracker import mark_status  # noqa: E402
from agentic.feedback_generator import draft_feedback_email  # noqa: E402

RESULTS_PATH = ROOT / "data" / "screening_results.json"
AUDIT_LOG = ROOT / "data" / "approvals.log"

# ---------------------------------------------------------------------------
# Page config and design tokens
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Brightline Recruitment Centre",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Design tokens (matching the slide deck palette)
NAVY = "#1E2761"
NAVY_LIGHT = "#3D4F8C"
ICE = "#E8F0FF"
BG = "#F8FAFC"
INK = "#0F172A"
MUTED = "#64748B"
SUCCESS = "#059669"
SUCCESS_BG = "#D1FAE5"
WARNING = "#D97706"
WARNING_BG = "#FEF3C7"
DANGER = "#DC2626"
DANGER_BG = "#FEE2E2"

# ---------------------------------------------------------------------------
# Global CSS
# ---------------------------------------------------------------------------
st.markdown(f"""
<style>
    /* Import professional fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    /* Global font */
    html, body, [class*="css"], .stApp, .stMarkdown, .stText, div, p, span, label {{
        font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
    }}
    code, pre {{ font-family: 'JetBrains Mono', monospace !important; }}

    /* Hide default Streamlit chrome */
    #MainMenu, footer, .stDeployButton {{ visibility: hidden; }}
    header[data-testid="stHeader"] {{ background: transparent; height: 0; }}
    .block-container {{ padding-top: 1rem; padding-bottom: 3rem; max-width: 1400px; }}

    /* Top bar */
    .topbar {{
        background: linear-gradient(135deg, {NAVY} 0%, {NAVY_LIGHT} 100%);
        color: white;
        padding: 20px 28px;
        border-radius: 12px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 20px rgba(30, 39, 97, 0.15);
    }}
    .brand {{
        display: flex; align-items: center; gap: 14px;
        font-family: 'Inter', sans-serif;
    }}
    .brand-logo {{
        width: 42px; height: 42px;
        background: white; border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        font-weight: 800; font-size: 22px; color: {NAVY};
    }}
    .brand-text {{ display: flex; flex-direction: column; line-height: 1.2; }}
    .brand-name {{ font-size: 18px; font-weight: 700; letter-spacing: -0.02em; }}
    .brand-sub {{ font-size: 12px; opacity: 0.8; font-weight: 400; }}
    .topbar-meta {{
        display: flex; gap: 20px; align-items: center;
        font-size: 13px;
    }}
    .topbar-role {{
        display: flex; align-items: center; gap: 10px;
        background: rgba(255,255,255,0.12); padding: 8px 14px; border-radius: 20px;
    }}
    .avatar-circle {{
        width: 30px; height: 30px; border-radius: 50%;
        background: {ICE}; color: {NAVY};
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 13px;
    }}

    /* Section header */
    .section-head {{
        display: flex; align-items: center; justify-content: space-between;
        margin: 8px 0 16px 0; padding-bottom: 8px;
    }}
    .section-title {{
        font-size: 20px; font-weight: 700; color: {INK}; letter-spacing: -0.02em;
        margin: 0;
    }}
    .section-sub {{ font-size: 13px; color: {MUTED}; margin: 2px 0 0 0; }}

    /* KPI cards */
    .kpi-row {{ display: flex; gap: 14px; margin-bottom: 24px; }}
    .kpi {{
        flex: 1; background: white; padding: 18px 22px; border-radius: 12px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }}
    .kpi-label {{ font-size: 12px; color: {MUTED}; font-weight: 500;
                  text-transform: uppercase; letter-spacing: 0.05em; }}
    .kpi-value {{ font-size: 28px; font-weight: 700; color: {INK};
                  margin-top: 4px; letter-spacing: -0.02em; }}
    .kpi-delta {{ font-size: 12px; color: {SUCCESS}; margin-top: 4px; font-weight: 500; }}

    /* Candidate cards in the shortlist */
    .cand-row {{
        display: grid;
        grid-template-columns: 46px 1.6fr 1.4fr 1fr 1fr;
        gap: 16px; align-items: center;
        padding: 14px 18px;
        background: white; border-radius: 10px;
        border: 1px solid #E2E8F0;
        margin-bottom: 8px;
        transition: all 0.15s ease;
    }}
    .cand-row:hover {{
        border-color: {NAVY_LIGHT}; box-shadow: 0 2px 12px rgba(30, 39, 97, 0.08);
        transform: translateX(2px);
    }}
    .cand-avatar {{
        width: 42px; height: 42px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-weight: 600; color: white; font-size: 15px;
    }}
    .cand-name {{ font-weight: 600; color: {INK}; font-size: 15px; }}
    .cand-email {{ font-size: 12px; color: {MUTED}; margin-top: 2px;
                   font-family: 'JetBrains Mono', monospace; }}
    .score-bar {{
        background: #F1F5F9; height: 8px; border-radius: 6px; overflow: hidden;
        margin-top: 5px;
    }}
    .score-fill {{ height: 100%; border-radius: 6px; transition: width 0.4s ease; }}
    .score-num {{ font-weight: 700; font-size: 15px; color: {INK}; }}

    /* Status pills */
    .pill {{
        display: inline-flex; align-items: center; gap: 6px;
        padding: 4px 12px; border-radius: 20px;
        font-size: 12px; font-weight: 600;
        letter-spacing: 0.01em;
    }}
    .pill-invite {{ background: {SUCCESS_BG}; color: {SUCCESS}; }}
    .pill-hold {{ background: {WARNING_BG}; color: {WARNING}; }}
    .pill-reject {{ background: {DANGER_BG}; color: {DANGER}; }}
    .pill-neutral {{ background: #F1F5F9; color: {MUTED}; }}
    .pill-dot {{ width: 6px; height: 6px; border-radius: 50%; }}

    /* Detail panel */
    .detail-card {{
        background: white; border: 1px solid #E2E8F0; border-radius: 14px;
        padding: 24px; margin-top: 8px;
    }}
    .detail-header {{
        display: flex; align-items: flex-start; gap: 16px;
        padding-bottom: 20px; border-bottom: 1px solid #F1F5F9;
    }}
    .big-avatar {{
        width: 68px; height: 68px; border-radius: 16px;
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; color: white; font-size: 26px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }}
    .detail-name {{
        font-size: 24px; font-weight: 700; color: {INK}; letter-spacing: -0.02em;
        margin: 0;
    }}
    .detail-role {{ font-size: 13px; color: {MUTED}; margin: 3px 0 0 0; }}
    .detail-email {{
        font-family: 'JetBrains Mono', monospace; font-size: 12px;
        color: {MUTED}; margin-top: 2px;
    }}

    /* Criteria grid */
    .crit-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
                  margin-top: 12px; }}
    .crit-item {{
        background: {BG}; padding: 12px 14px; border-radius: 8px;
        border-left: 3px solid;
    }}
    .crit-name {{ font-size: 12px; color: {MUTED}; font-weight: 500;
                  text-transform: uppercase; letter-spacing: 0.03em; }}
    .crit-row {{ display: flex; align-items: baseline; gap: 6px; margin-top: 4px; }}
    .crit-score {{ font-size: 22px; font-weight: 700; color: {INK}; }}
    .crit-max {{ font-size: 13px; color: {MUTED}; }}
    .crit-evi {{ font-size: 12px; color: #475569; margin-top: 4px;
                 line-height: 1.5; font-style: italic; }}

    /* Tag pills for strengths/gaps */
    .tag-row {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }}
    .tag {{ padding: 5px 11px; border-radius: 6px; font-size: 12px;
            font-weight: 500; line-height: 1.4; }}
    .tag-str {{ background: {SUCCESS_BG}; color: {SUCCESS};
                border: 1px solid rgba(5, 150, 105, 0.2); }}
    .tag-gap {{ background: {DANGER_BG}; color: {DANGER};
                border: 1px solid rgba(220, 38, 38, 0.2); }}

    /* Rationale */
    .rationale {{
        background: {ICE}; padding: 14px 16px; border-radius: 10px;
        border-left: 3px solid {NAVY_LIGHT};
        font-size: 13px; color: {INK}; line-height: 1.6; margin-top: 12px;
    }}
    .rationale-label {{ font-size: 11px; color: {NAVY};
                        text-transform: uppercase; letter-spacing: 0.05em;
                        font-weight: 700; margin-bottom: 4px; }}

    /* Email preview */
    .email-preview {{
        background: white; border: 1px solid #E2E8F0; border-radius: 10px;
        padding: 0; overflow: hidden;
    }}
    .email-head {{
        background: {BG}; padding: 10px 14px;
        border-bottom: 1px solid #E2E8F0; font-size: 12px; color: {MUTED};
    }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background: white; border-right: 1px solid #E2E8F0;
    }}
    section[data-testid="stSidebar"] .stButton>button {{ width: 100%; }}
    .sidebar-label {{
        font-size: 11px; color: {MUTED}; font-weight: 600;
        text-transform: uppercase; letter-spacing: 0.05em; margin: 12px 0 6px 0;
    }}

    /* Primary action */
    .stButton>button[kind="primary"] {{
        background: {NAVY}; border: none; font-weight: 600;
        transition: all 0.15s ease;
    }}
    .stButton>button[kind="primary"]:hover {{
        background: {NAVY_LIGHT}; box-shadow: 0 4px 12px rgba(30, 39, 97, 0.25);
    }}

    /* Empty state */
    .empty-state {{
        background: white; border: 2px dashed #CBD5E1; border-radius: 14px;
        padding: 60px 40px; text-align: center;
    }}
    .empty-icon {{ font-size: 42px; margin-bottom: 10px; }}
    .empty-title {{ font-size: 18px; font-weight: 600; color: {INK}; }}
    .empty-desc {{ font-size: 13px; color: {MUTED}; margin-top: 6px; }}

    /* Section divider */
    .divider {{ height: 1px; background: #E2E8F0; margin: 24px 0; }}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def initials(name: str) -> str:
    parts = [p for p in name.split() if p]
    if not parts:
        return "??"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def avatar_color(name: str) -> str:
    """Deterministic colour from name hash."""
    palette = ["#4F46E5", "#0891B2", "#059669", "#DC2626", "#D97706",
               "#7C3AED", "#DB2777", "#0284C7", "#65A30D", "#EA580C"]
    idx = sum(ord(c) for c in name) % len(palette)
    return palette[idx]


def rec_pill(rec: str) -> str:
    """Return HTML for a recommendation pill."""
    if rec == "invite_to_interview":
        return f'<span class="pill pill-invite"><span class="pill-dot" style="background:{SUCCESS};"></span>Invite</span>'
    elif rec == "reject":
        return f'<span class="pill pill-reject"><span class="pill-dot" style="background:{DANGER};"></span>Reject</span>'
    elif rec == "hold":
        return f'<span class="pill pill-hold"><span class="pill-dot" style="background:{WARNING};"></span>Hold</span>'
    return f'<span class="pill pill-neutral">{rec}</span>'


def score_color(score: int) -> str:
    if score >= 70:
        return SUCCESS
    elif score >= 50:
        return WARNING
    return DANGER


def crit_color(score: int) -> str:
    if score >= 7:
        return SUCCESS
    elif score >= 4:
        return WARNING
    return DANGER


# ---------------------------------------------------------------------------
# Pipeline runner (unchanged logic, better UI feedback)
# ---------------------------------------------------------------------------
def run_pipeline():
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

    progress = st.progress(0.0, text="Starting pipeline...")
    results = []
    total = len(messages)

    for i, m in enumerate(messages, start=1):
        progress.progress(i / (total + 1), text=f"Processing {m['sender_name']}...")
        cv_path = store_cv(m)
        if cv_path is None:
            continue
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
    progress.progress(1.0, text=f"Complete: {len(results)} candidates scored")


# ---------------------------------------------------------------------------
# TOP BAR
# ---------------------------------------------------------------------------
st.markdown(f"""
<div class="topbar">
    <div class="brand">
        <div class="brand-logo">B</div>
        <div class="brand-text">
            <div class="brand-name">Brightline Analytics</div>
            <div class="brand-sub">Recruitment Command Centre</div>
        </div>
    </div>
    <div class="topbar-meta">
        <div class="topbar-role">
            <div class="avatar-circle">HR</div>
            <span>Recruiter</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-label">Current Role</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="padding:12px; background:{BG}; border-radius:8px; border:1px solid #E2E8F0;">
        <div style="font-weight:600; color:{INK}; font-size:14px;">Junior Data Analyst</div>
        <div style="font-size:12px; color:{MUTED}; margin-top:3px;">Brightline Analytics</div>
        <div style="font-size:11px; color:{MUTED}; margin-top:6px;">Requisition #JDA-2026-07</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-label">Pipeline Control</div>', unsafe_allow_html=True)
    if st.button("▶ Run screening pipeline", type="primary", use_container_width=True):
        with st.spinner("Running RPA + Agentic pipeline..."):
            run_pipeline()
        st.rerun()

    if RESULTS_PATH.exists() and st.button("↻ Clear and rescreen", use_container_width=True):
        RESULTS_PATH.unlink()
        st.rerun()

    st.markdown('<div class="sidebar-label">System Mode</div>', unsafe_allow_html=True)
    mode = os.getenv("SCORER_MODE", "llm")
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    mode_color = SUCCESS if mode == "llm" else WARNING
    st.markdown(f"""
    <div style="padding:10px 12px; background:{BG}; border-radius:8px; border:1px solid #E2E8F0; font-size:12px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <span style="color:{MUTED}; font-weight:500;">Scorer</span>
            <span class="pill" style="background:{mode_color}20; color:{mode_color}; padding:2px 8px; font-size:10px;">{mode.upper()}</span>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="color:{MUTED}; font-weight:500;">Model</span>
            <code style="font-size:10px; color:{INK};">{model.split('-')[0]}</code>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-label">About</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="font-size:11px; color:{MUTED}; line-height:1.6;">
        H9IAPA CA · Esvanth Sivanesan · x24311073<br>
        Recruitment intake automation with RPA + Agentic AI (Llama 3.3 via Groq).
        Human-in-the-loop preserved for EU AI Act compliance.
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# EMPTY STATE
# ---------------------------------------------------------------------------
if not RESULTS_PATH.exists():
    st.markdown(f"""
    <div class="empty-state">
        <div class="empty-icon">📥</div>
        <div class="empty-title">No applicants scored yet</div>
        <div class="empty-desc">Click <b>Run screening pipeline</b> in the sidebar to fetch, score, and rank the applicant cohort.</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

with open(RESULTS_PATH) as f:
    results = json.load(f)

if not results:
    st.markdown(f"""
    <div class="empty-state">
        <div class="empty-icon">🔍</div>
        <div class="empty-title">No candidates found</div>
        <div class="empty-desc">The pipeline ran but did not score anyone. Check the mock inbox.</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ---------------------------------------------------------------------------
# KPI BAR
# ---------------------------------------------------------------------------
invited = sum(1 for r in results if r["score"]["recommendation"] == "invite_to_interview")
held = sum(1 for r in results if r["score"]["recommendation"] == "hold")
rejected = sum(1 for r in results if r["score"]["recommendation"] == "reject")
avg_score = round(sum(r["score"]["overall_score"] for r in results) / len(results))

st.markdown(f"""
<div class="kpi-row">
    <div class="kpi">
        <div class="kpi-label">Total Applicants</div>
        <div class="kpi-value">{len(results)}</div>
        <div class="kpi-delta">Fully processed</div>
    </div>
    <div class="kpi">
        <div class="kpi-label">Invited</div>
        <div class="kpi-value" style="color:{SUCCESS};">{invited}</div>
        <div class="kpi-delta">Ready for first-stage interview</div>
    </div>
    <div class="kpi">
        <div class="kpi-label">On Hold</div>
        <div class="kpi-value" style="color:{WARNING};">{held}</div>
        <div class="kpi-delta" style="color:{WARNING};">Pending review</div>
    </div>
    <div class="kpi">
        <div class="kpi-label">Not Progressing</div>
        <div class="kpi-value" style="color:{DANGER};">{rejected}</div>
        <div class="kpi-delta" style="color:{MUTED};">Feedback available</div>
    </div>
    <div class="kpi">
        <div class="kpi-label">Average Score</div>
        <div class="kpi-value">{avg_score}<span style="font-size:16px; color:{MUTED};"> / 100</span></div>
        <div class="kpi-delta" style="color:{MUTED};">Across cohort</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# SHORTLIST
# ---------------------------------------------------------------------------
st.markdown(f"""
<div class="section-head">
    <div>
        <div class="section-title">Ranked Shortlist</div>
        <div class="section-sub">Sorted by fit score (descending). Click a candidate below to review.</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Column headers
st.markdown(f"""
<div style="display:grid; grid-template-columns:46px 1.6fr 1.4fr 1fr 1fr; gap:16px;
     padding:6px 18px; font-size:11px; color:{MUTED}; font-weight:600;
     text-transform:uppercase; letter-spacing:0.05em;">
    <div></div>
    <div>Candidate</div>
    <div>Score</div>
    <div>Recommendation</div>
    <div>Status</div>
</div>
""", unsafe_allow_html=True)

for r in results:
    s = r["score"]
    name = s["candidate_name"]
    color = avatar_color(name)
    inits = initials(name)
    sc = s["overall_score"]
    st.markdown(f"""
    <div class="cand-row">
        <div class="cand-avatar" style="background:{color};">{inits}</div>
        <div>
            <div class="cand-name">{name}</div>
            <div class="cand-email">{r["candidate_email"]}</div>
        </div>
        <div>
            <div style="display:flex; align-items:center; gap:10px;">
                <span class="score-num" style="color:{score_color(sc)};">{sc}</span>
                <span style="color:{MUTED}; font-size:12px;">/ 100</span>
            </div>
            <div class="score-bar">
                <div class="score-fill" style="width:{sc}%; background:{score_color(sc)};"></div>
            </div>
        </div>
        <div>{rec_pill(s["recommendation"])}</div>
        <div><span class="pill pill-neutral">{r["status"].replace("_", " ").title()}</span></div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# CANDIDATE DETAIL
# ---------------------------------------------------------------------------
st.markdown(f"""
<div class="section-head">
    <div>
        <div class="section-title">Candidate Review</div>
        <div class="section-sub">Full score breakdown, evidence, and email draft. Approve to dispatch.</div>
    </div>
</div>
""", unsafe_allow_html=True)

names = [r["score"]["candidate_name"] for r in results]
selection = st.selectbox("Select candidate", names, label_visibility="collapsed")
r = next(x for x in results if x["score"]["candidate_name"] == selection)
s = r["score"]

# Detail header
name = s["candidate_name"]
color = avatar_color(name)
inits = initials(name)
sc = s["overall_score"]

col_left, col_right = st.columns([1.15, 1])

with col_left:
    st.markdown(f"""
    <div class="detail-card">
        <div class="detail-header">
            <div class="big-avatar" style="background:{color};">{inits}</div>
            <div style="flex:1;">
                <div class="detail-name">{name}</div>
                <div class="detail-role">Junior Data Analyst applicant · Brightline Analytics</div>
                <div class="detail-email">{r["candidate_email"]}</div>
                <div style="margin-top:10px; display:flex; gap:10px; align-items:center;">
                    {rec_pill(s["recommendation"])}
                    <span style="font-size:13px; color:{MUTED};">Score</span>
                    <span style="font-weight:700; color:{score_color(sc)}; font-size:18px;">{sc}<span style="color:{MUTED}; font-weight:500; font-size:13px;"> / 100</span></span>
                </div>
            </div>
        </div>

        <div class="rationale">
            <div class="rationale-label">LLM Rationale</div>
            {s["rationale"]}
        </div>

        <div style="margin-top:20px;">
            <div style="font-size:13px; font-weight:600; color:{INK}; margin-bottom:6px;">Strengths</div>
            <div class="tag-row">
                {"".join(f'<span class="tag tag-str">✓ {st_}</span>' for st_ in s["strengths"])}
            </div>
        </div>

        <div style="margin-top:16px;">
            <div style="font-size:13px; font-weight:600; color:{INK}; margin-bottom:6px;">Gaps</div>
            <div class="tag-row">
                {"".join(f'<span class="tag tag-gap">△ {g}</span>' for g in s["gaps"])}
            </div>
        </div>

        <div style="margin-top:22px;">
            <div style="font-size:13px; font-weight:600; color:{INK}; margin-bottom:8px;">Criteria Breakdown</div>
            <div class="crit-grid">
                {"".join(f'''
                <div class="crit-item" style="border-left-color:{crit_color(c["score"])};">
                    <div class="crit-name">{c["name"]}</div>
                    <div class="crit-row">
                        <span class="crit-score" style="color:{crit_color(c["score"])};">{c["score"]}</span>
                        <span class="crit-max">/ 10</span>
                    </div>
                    <div class="crit-evi">{c["evidence"]}</div>
                </div>
                ''' for c in s["criteria"])}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_right:
    if s["recommendation"] in ("invite_to_interview", "reject"):
        st.markdown(f'<div class="section-head" style="margin-bottom:8px;"><div><div class="section-title" style="font-size:16px;">Draft Email</div><div class="section-sub">Review, edit, then approve. Nothing sends without your click.</div></div></div>', unsafe_allow_html=True)

        subject = st.text_input("Subject", r["draft_email"]["subject"], key=f"subj_{selection}")
        body = st.text_area("Body", r["draft_email"]["body"], height=280, key=f"body_{selection}")

        # For rejections: offer the candidate development feedback option
        if s["recommendation"] == "reject":
            st.markdown(f"""
            <div style="background:{ICE}; padding:12px 14px; border-radius:8px;
                 border-left:3px solid {NAVY_LIGHT}; margin-top:8px;">
                <div style="font-size:12px; font-weight:600; color:{NAVY};
                     text-transform:uppercase; letter-spacing:0.05em;">
                    ✨ Candidate Development Feedback
                </div>
                <div style="font-size:12px; color:{INK}; margin-top:4px; line-height:1.5;">
                    Instead of a plain rejection, generate a personalised development
                    feedback email using the score card. Turns rejection into
                    actionable improvement guidance.
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Generate development feedback",
                         use_container_width=True, key=f"fb_gen_{selection}"):
                with st.spinner("Generating personalised feedback..."):
                    try:
                        from agentic.schemas import CandidateScore
                        score_obj = CandidateScore(**s)
                        fb_subject, fb_body = draft_feedback_email(
                            score_obj, "Junior Data Analyst"
                        )
                        # Overwrite draft to feedback version
                        r["draft_email"] = {"subject": fb_subject, "body": fb_body}
                        r["feedback_generated"] = True
                        with open(RESULTS_PATH, "w") as f:
                            json.dump(results, f, indent=2)
                        with open(AUDIT_LOG, "a") as f:
                            f.write(
                                f"FEEDBACK_GEN {r['candidate_email']} "
                                f"(rec={s['recommendation']})\n"
                            )
                        st.success("Feedback email generated. Review the updated draft above.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Feedback generation failed: {e}")

        st.markdown(f'<div style="font-size:12px; color:{MUTED}; margin-top:8px;"><b>Decision</b></div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Approve & Send", type="primary", use_container_width=True, key=f"app_{selection}"):
                res = send_email(r["candidate_email"], name, subject, body)
                mark_status(r["candidate_email"], "Sent")
                r["status"] = "sent"
                with open(RESULTS_PATH, "w") as f:
                    json.dump(results, f, indent=2)
                with open(AUDIT_LOG, "a") as f:
                    f.write(f"APPROVED {r['candidate_email']} -> {res}\n")
                st.success(f"✓ Email dispatched · {res}")
        with c2:
            if st.button("Override", use_container_width=True, key=f"ov_{selection}"):
                new_rec = "reject" if s["recommendation"] == "invite_to_interview" else "invite_to_interview"
                s["recommendation"] = new_rec
                r["status"] = "overridden"
                mark_status(r["candidate_email"], "Overridden")
                with open(RESULTS_PATH, "w") as f:
                    json.dump(results, f, indent=2)
                with open(AUDIT_LOG, "a") as f:
                    f.write(f"OVERRIDE {r['candidate_email']} -> {new_rec}\n")
                st.warning("Recommendation flipped. Refresh to update.")
        with c3:
            if st.button("Hold", use_container_width=True, key=f"hold_{selection}"):
                r["status"] = "held"
                mark_status(r["candidate_email"], "Held")
                with open(RESULTS_PATH, "w") as f:
                    json.dump(results, f, indent=2)
                with open(AUDIT_LOG, "a") as f:
                    f.write(f"HOLD {r['candidate_email']}\n")
                st.info("Held for later review.")
    else:
        # HOLD case - no email
        st.markdown(f"""
        <div style="background:{WARNING_BG}; padding:20px; border-radius:12px;
             border-left:4px solid {WARNING};">
            <div style="font-weight:600; color:{WARNING}; font-size:14px;">Candidate on hold</div>
            <div style="font-size:13px; color:{INK}; margin-top:6px; line-height:1.5;">
                No email is drafted for held candidates. Review the score card,
                then override to invite or reject if you want to progress this candidate.
            </div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Override to Invite", type="primary", use_container_width=True, key=f"ov_inv_{selection}"):
                s["recommendation"] = "invite_to_interview"
                r["status"] = "overridden"
                with open(RESULTS_PATH, "w") as f:
                    json.dump(results, f, indent=2)
                with open(AUDIT_LOG, "a") as f:
                    f.write(f"OVERRIDE {r['candidate_email']} -> invite\n")
                st.rerun()
        with c2:
            if st.button("Override to Reject", use_container_width=True, key=f"ov_rej_{selection}"):
                s["recommendation"] = "reject"
                r["status"] = "overridden"
                with open(RESULTS_PATH, "w") as f:
                    json.dump(results, f, indent=2)
                with open(AUDIT_LOG, "a") as f:
                    f.write(f"OVERRIDE {r['candidate_email']} -> reject\n")
                st.rerun()
