"""JD Parser — per Sara_Job_Arch.docx daily pipeline: "each job -> structured
fields (skills, seniority, location, remote)." Runs on the LIGHT tier
(Groq 8b) since it processes every scouted job (100-150/day) — a real run
against 113 jobs on 2026-07-27 showed doing this on the 70b model alone
exhausts Groq's free 100k-tokens/day quota before Fit Scorer even starts.
"""

import json

from sqlalchemy import select

from jarvis.core.llm import ask_light
from jarvis.db.models import Job
from jarvis.db.session import get_session

PROMPT_TEMPLATE = """Extract structured fields from this job description. Reply with ONLY a JSON object, no other text, matching exactly this shape:
{{"skills": ["skill1", "skill2", ...], "seniority": "junior|mid|senior|staff|unknown", "remote": true/false, "visa_sponsorship_mentioned": true/false, "screening_questions": ["question1", ...]}}

Title: {title}
Location: {location}
Description:
{jd_text}
"""


def parse_job(job: Job) -> dict:
    prompt = PROMPT_TEMPLATE.format(
        title=job.title, location=job.location, jd_text=job.jd_text[:2500]
    )
    raw = ask_light(prompt)
    # Models sometimes wrap JSON in ```json fences despite instructions — strip if present.
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"skills": [], "seniority": "unknown", "remote": job.remote, "visa_sponsorship_mentioned": False, "screening_questions": [], "parse_error": raw[:200]}


def run_jd_parser(limit: int = 200) -> dict:
    session = get_session()
    jobs = session.scalars(
        select(Job).where(Job.jd_parsed.is_(None)).limit(limit)
    ).all()

    parsed_count = 0
    error_count = 0
    for job in jobs:
        parsed = parse_job(job)
        if "parse_error" in parsed:
            error_count += 1
        job.jd_parsed = parsed
        parsed_count += 1

    session.commit()
    session.close()
    return {"parsed": parsed_count, "errors": error_count}


if __name__ == "__main__":
    print(run_jd_parser())
