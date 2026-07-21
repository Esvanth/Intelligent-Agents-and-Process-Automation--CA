"""Agentic component: draft personalised candidate emails via Groq."""
import os
from .schemas import CandidateScore

SCORER_MODE = os.getenv("SCORER_MODE", "llm")
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

INVITE_PROMPT = """Write a short, warm, professional interview invitation email.
- Address the candidate by name.
- Reference ONE specific strength from the screening notes so it does not feel generic.
- Mention the role title and that this is for a first-stage interview (30 min video).
- Offer to propose times once they reply.
- Sign off as "Recruitment Team, Brightline Analytics".
- Plain text only, three short paragraphs maximum.

Candidate: {name}
Role: {role}
Specific strength: {strength}

Return only the email body."""

REJECT_PROMPT = """Write a polite, respectful rejection email.
- Address the candidate by name.
- Thank them sincerely.
- Acknowledge ONE thing the screening identified positively.
- State that we will not be moving forward at this time.
- Keep it warm, never harsh, three short paragraphs maximum.
- Sign off as "Recruitment Team, Brightline Analytics".
- Plain text only.

Candidate: {name}
Role: {role}
Positive note: {positive}

Return only the email body."""


def _client():
    from groq import Groq
    return Groq()


def _mock_invite(name, role, strength):
    return (f"Dear {name.split()[0]},\n\n"
            f"Thank you for your application for the {role} role at Brightline Analytics. "
            f"Your background stood out because: {strength.lower()}\n\n"
            f"We would like to invite you to a 30-minute first-stage video interview. "
            f"Please reply with two or three time windows that suit you.\n\n"
            f"Looking forward to speaking with you.\n\n"
            f"Recruitment Team\nBrightline Analytics")


def _mock_reject(name, role, positive):
    return (f"Dear {name.split()[0]},\n\n"
            f"Thank you sincerely for applying to the {role} role at Brightline Analytics. "
            f"We noted positively that {positive.lower()}\n\n"
            f"After careful review, we will not be progressing your application on this occasion. "
            f"The competition was strong and we hope you will keep an eye out for future openings.\n\n"
            f"Wishing you every success.\n\n"
            f"Recruitment Team\nBrightline Analytics")


def draft_email(score: CandidateScore, role_title: str):
    if score.recommendation == "invite_to_interview":
        subject = f"Interview invitation: {role_title}"
        strength = score.strengths[0] if score.strengths else "your overall profile"
        if SCORER_MODE == "mock":
            return subject, _mock_invite(score.candidate_name, role_title, strength)
        prompt = INVITE_PROMPT.format(name=score.candidate_name, role=role_title, strength=strength)
    elif score.recommendation == "reject":
        subject = f"Update on your application: {role_title}"
        positive = score.strengths[0] if score.strengths else "your interest in the role"
        if SCORER_MODE == "mock":
            return subject, _mock_reject(score.candidate_name, role_title, positive)
        prompt = REJECT_PROMPT.format(name=score.candidate_name, role=role_title, positive=positive)
    else:
        return ("[hold] no email drafted", "")

    client = _client()
    response = client.chat.completions.create(
        model=MODEL, messages=[{"role": "user", "content": prompt}],
        temperature=0.7, max_tokens=400,
    )
    return subject, response.choices[0].message.content.strip()
