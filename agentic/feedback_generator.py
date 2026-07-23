"""
Agentic component: generate constructive development feedback for rejected
candidates.

The current recruitment process gives rejected applicants a generic
thank-you email with no reason. This module uses the existing CandidateScore
to generate personalised feedback: what the candidate did well, which
specific criteria they scored low on, and concrete suggestions for how to
close those gaps.

This turns rejection from a dead end into useful information the candidate
can act on. Because the score card exists as a byproduct of screening,
feedback generation is close to free.
"""
import os

from .schemas import CandidateScore

SCORER_MODE = os.getenv("SCORER_MODE", "llm")
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

FEEDBACK_PROMPT = """Write a warm, constructive feedback email for a
candidate whose application was not successful. The email should help them
grow, not just soften a rejection.

Structure:
1. Thank them sincerely (one sentence).
2. Acknowledge TWO specific strengths from their CV.
3. Explain the TWO OR THREE specific criteria where the CV did not match
   the role. Reference the exact criterion names, not vague language.
4. Give ONE concrete suggestion per gap on how to close it (a course,
   a tool to learn, a portfolio project). Be specific: name real
   resources or types of resources rather than saying "improve your skills".
5. Encourage them to reapply once they have built these areas.
6. Sign off as "Recruitment Team, Brightline Analytics".

Tone: warm, honest, respectful. Never patronising. Never harsh. Treat the
candidate as a professional who can act on the information.

Plain text only, no markdown, no emojis. Four short paragraphs maximum.

Candidate: {name}
Role: {role}
Strengths: {strengths}
Gaps and criteria they scored low on: {gaps_and_scores}

Return only the email body. Do not include a subject line."""


def _client():
    from groq import Groq
    return Groq()


def _mock_feedback(score: CandidateScore, role_title: str) -> str:
    """Deterministic template used when SCORER_MODE=mock."""
    name = score.candidate_name.split()[0]
    strengths_text = ", ".join(score.strengths[:2]).lower()
    low_criteria = sorted(
        [c for c in score.criteria if c.score < 6],
        key=lambda c: c.score,
    )[:3]
    gaps_lines = "\n".join(
        f"- {c.name} (scored {c.score}/10). Suggested action: "
        f"build hands-on evidence you can show on a CV, for example a "
        f"small project or short course covering this area."
        for c in low_criteria
    )
    return (
        f"Dear {name},\n\n"
        f"Thank you sincerely for applying to the {role_title} role at "
        f"Brightline Analytics. Before you move on, we wanted to share "
        f"some specific feedback so this application is not a dead end.\n\n"
        f"What stood out positively in your CV: {strengths_text}.\n\n"
        f"The areas where the CV did not match this role, and what we would "
        f"suggest working on:\n\n{gaps_lines}\n\n"
        f"We would genuinely welcome an application from you in future once "
        f"these areas are stronger. Wishing you every success.\n\n"
        f"Recruitment Team\nBrightline Analytics"
    )


def draft_feedback_email(score: CandidateScore, role_title: str) -> tuple[str, str]:
    """
    Generate a constructive feedback email for the candidate.
    Returns (subject, body).

    Only intended for candidates recommended for rejection. Called from the
    dashboard when the recruiter clicks "Send development feedback" instead
    of the plain rejection email.
    """
    subject = f"Feedback on your application: {role_title}"

    if SCORER_MODE == "mock":
        return subject, _mock_feedback(score, role_title)

    # Prepare structured inputs for the LLM
    strengths = "; ".join(score.strengths[:3])
    gaps_and_scores = "; ".join(
        f"{c.name} scored {c.score}/10 ({c.evidence})"
        for c in sorted(score.criteria, key=lambda x: x.score)[:4]
        if c.score < 6
    )
    if not gaps_and_scores:
        gaps_and_scores = "; ".join(f"{g}" for g in score.gaps[:3])

    prompt = FEEDBACK_PROMPT.format(
        name=score.candidate_name,
        role=role_title,
        strengths=strengths,
        gaps_and_scores=gaps_and_scores,
    )

    client = _client()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=500,
    )
    body = response.choices[0].message.content.strip()
    return subject, body