"""Fit Scorer — per Sara_Job_Arch.docx daily pipeline: "Strong/Medium/Weak +
one-line reason; filter out Weak." Weak jobs are auto-skipped so the human
dashboard only ever shows things worth a look — this is NOT a rejection of
the candidate, it's Sara deciding a role isn't worth your time.

Scores against the Profile Brain (profile_facts + resume_variants), fetched
fresh each run rather than cached, since /profile can change at any time.

Uses ask_light (Groq 8b), not ask_bulk (70b) — a real run on 2026-07-27 found
the 70b model's 100k-tokens/day free quota still exhausted from JD Parser
runs earlier the same day (it regenerates slowly, not per-minute), so this
step was stranded waiting on a quota that wouldn't free up in practical time.
Fit scoring is a bounded Strong/Medium/Weak + one-line-reason decision, which
the 8b model handles fine. Switch back to ask_bulk if quality issues show up
or once on a paid Groq tier.
"""

import json

from sqlalchemy import select

from jarvis.core.llm import ask_light
from jarvis.db.models import Job, ProfileFact, ResumeVariant
from jarvis.db.session import get_session

PROMPT_TEMPLATE = """You are scoring how well a job fits a candidate. Reply with ONLY a JSON object, no other text:
{{"rating": "strong|medium|weak", "reason": "one sentence, specific, referencing an actual detail from the JD and the candidate's background"}}

Candidate profile:
{profile_summary}

Job:
Title: {title}
Location: {location} (remote: {remote})
Seniority (parsed): {seniority}
Skills (parsed): {skills}
Visa sponsorship mentioned: {visa_mentioned}
"""


def _build_profile_summary(session) -> str:
    facts = session.scalars(select(ProfileFact)).all()
    resumes = session.scalars(select(ResumeVariant)).all()

    fact_lines = [f"- {f.category}.{f.key}: {f.value}" for f in facts]
    resume_lines = [f"- {r.track}: {r.notes}" for r in resumes]

    return (
        "Facts:\n" + "\n".join(fact_lines)
        + "\n\nResume tracks available:\n" + "\n".join(resume_lines)
    )


def score_job(job: Job, profile_summary: str) -> dict:
    parsed = job.jd_parsed or {}
    prompt = PROMPT_TEMPLATE.format(
        profile_summary=profile_summary,
        title=job.title,
        location=job.location,
        remote=job.remote,
        seniority=parsed.get("seniority", "unknown"),
        skills=", ".join(parsed.get("skills", [])) or "unknown",
        visa_mentioned=parsed.get("visa_sponsorship_mentioned", False),
    )
    raw = ask_light(prompt)
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        result = json.loads(raw)
        if result.get("rating") not in ("strong", "medium", "weak"):
            raise ValueError("bad rating")
        return result
    except (json.JSONDecodeError, ValueError):
        return {"rating": "medium", "reason": f"Fit Scorer couldn't parse a clean response — held at medium for human review. Raw: {raw[:150]}"}


def run_fit_scorer(limit: int = 200) -> dict:
    session = get_session()
    profile_summary = _build_profile_summary(session)

    jobs = session.scalars(
        select(Job)
        .where(Job.jd_parsed.is_not(None), Job.fit_rating.is_(None))
        .limit(limit)
    ).all()

    counts = {"strong": 0, "medium": 0, "weak": 0}
    for job in jobs:
        result = score_job(job, profile_summary)
        job.fit_rating = result["rating"]
        job.fit_reason = result["reason"]
        if result["rating"] == "weak":
            job.status = "skipped"  # filter out Weak, per the docx
        counts[result["rating"]] += 1

    session.commit()
    session.close()
    return {"scored": len(jobs), **counts}


if __name__ == "__main__":
    print(run_fit_scorer())
