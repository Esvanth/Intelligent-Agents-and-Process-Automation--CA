"""Agentic component: score a CV using Groq (Llama 3.3 70B) with JSON mode."""
import json, os, re
from pydantic import ValidationError
from .schemas import CandidateScore

SCORER_MODE = os.getenv("SCORER_MODE", "llm")
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
MAX_TOKENS = 1500

SYSTEM_PROMPT = """You are a careful, evidence-based recruitment screener.
You score a single candidate's CV against the provided job description.
You must return JSON only, with no preamble, no commentary, no markdown
code fences. The JSON must conform exactly to the schema given by the user.

Scoring rules:
- overall_score is an integer 0 to 100 representing fit for THIS role.
- For each major JD criterion, give a 0-10 score with one-line evidence
  pulled from the CV text (or note "not stated" if absent).
- strengths and gaps must be concrete and cite the CV.
- recommendation is one of: invite_to_interview, reject, hold.
- rationale is two to four sentences. Be fair, calibrated, and avoid bias
  on names or backgrounds; weigh only role-relevant evidence.
"""

USER_TEMPLATE = """Job description:
<job_description>
{jd}
</job_description>

Candidate CV text:
<cv>
{cv}
</cv>

Return a JSON object with these exact fields:
{{
  "candidate_name": str,
  "overall_score": int (0-100),
  "criteria": [{{"name": str, "score": int (0-10), "evidence": str}}],
  "strengths": [str, ...],
  "gaps": [str, ...],
  "recommendation": "invite_to_interview" | "reject" | "hold",
  "rationale": str
}}

Use the candidate's actual name from the CV. Cover at minimum these
criteria: education, programming and SQL skills, visualisation tools,
relevant experience, communication and presentation evidence.
"""


def _client():
    from groq import Groq
    return Groq()


def _mock_score(cv_text: str, jd: str) -> CandidateScore:
    text = cv_text.lower()
    name_match = re.search(r"^([A-Z][a-z]+(?:\s+[A-Z][a-z'\u2019]+)+)", cv_text.strip(), re.M)
    name = name_match.group(1) if name_match else "Unknown Candidate"

    def has(*kw): return any(k in text for k in kw)
    def count(*kw): return sum(1 for k in kw if k in text)

    edu = 8 if has("bsc data", "bsc statistics", "msc data", "meng computer") else \
          6 if has("bsc", "bachelor", "beng", "be ") else \
          5 if has("bbs", "ba ", "bachelor of arts") else 4
    if "in progress" in text: edu = max(edu - 2, 3)
    py = min(10, 3 + 2 * count("pandas", "numpy", "scikit"))
    sql = 8 if has("window function", "cte") else 6 if has("sql") else 3
    viz = 8 if has("power bi", "tableau", "looker") else 4
    exp = 9 if has("data analyst", "data scientist") else 7 if has("intern") else 5 if has("operations", "finance") else 3
    comm = 7 if has("presented", "communication") else 5
    cloud = 7 if has("aws", "gcp", "azure", "bigquery", "snowflake") else 4

    criteria = [
        {"name": "Education", "score": edu, "evidence": "Degree subject inferred from CV header."},
        {"name": "Python", "score": py, "evidence": "Mentions of pandas, NumPy, scikit-learn."},
        {"name": "SQL", "score": sql, "evidence": "SQL depth signals."},
        {"name": "Visualisation (Power BI / Tableau)", "score": viz, "evidence": "Tooling named in skills."},
        {"name": "Relevant experience", "score": exp, "evidence": "Data analyst or adjacent roles."},
        {"name": "Communication and presentation", "score": comm, "evidence": "Examples of presenting to stakeholders."},
        {"name": "Cloud platform exposure", "score": cloud, "evidence": "Mentions of AWS, GCP, Azure."},
    ]
    overall = int(sum(c["score"] for c in criteria) / (len(criteria) * 10) * 100)

    strengths, gaps = [], []
    if py >= 7: strengths.append("Solid hands-on Python.")
    if viz >= 7: strengths.append("Direct experience with Power BI or Tableau.")
    if exp >= 7: strengths.append("Prior analyst experience.")
    if comm >= 7: strengths.append("Evidence of presenting to stakeholders.")
    if not strengths: strengths.append("Eager learner with foundational skills.")
    if py < 5: gaps.append("Limited Python depth.")
    if sql < 5: gaps.append("Weak SQL background.")
    if viz < 5: gaps.append("No clear Power BI / Tableau usage.")
    if exp < 5: gaps.append("Little analyst-relevant experience.")
    if "in progress" in text: gaps.append("Degree still in progress.")
    if not gaps: gaps.append("Cloud exposure could be broadened.")

    if overall >= 70:
        rec, rat = "invite_to_interview", f"Strong fit; core stack present with relevant experience. Score {overall}/100."
    elif overall >= 50:
        rec, rat = "hold", f"Borderline; some signals present but key gaps remain. Score {overall}/100."
    else:
        rec, rat = "reject", f"Insufficient alignment with the JD. Score {overall}/100."

    return CandidateScore(candidate_name=name, overall_score=overall, criteria=criteria,
                          strengths=strengths, gaps=gaps, recommendation=rec, rationale=rat)


def score_cv(cv_text: str, jd: str) -> CandidateScore:
    if SCORER_MODE == "mock":
        return _mock_score(cv_text, jd)
    client = _client()
    prompt = USER_TEMPLATE.format(jd=jd, cv=cv_text)
    for attempt in range(2):
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM_PROMPT},
                      {"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2, max_tokens=MAX_TOKENS,
        )
        text = response.choices[0].message.content.strip()
        try:
            return CandidateScore(**json.loads(text))
        except (json.JSONDecodeError, ValidationError) as e:
            if attempt == 0:
                prompt += f"\n\nYour last response did not parse. Error: {e}. Return ONLY the JSON."
                continue
            raise RuntimeError(f"LLM returned invalid JSON: {e}")
