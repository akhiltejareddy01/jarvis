"""Cover Letter — per Sara_Job_Arch.docx daily pipeline: "Claude drafts the
'why me'" [OpenAI per Akhil's 2026-07-27 swap, see core/llm.py]. Runs after
Resume Selector, against whichever resume_text ended up on the job (as-is or
tailored) — same honesty lock applies: no fabricated experience.
"""

from sqlalchemy import select

from jarvis.core.llm import ask_premium
from jarvis.db.models import Company, Job
from jarvis.db.session import get_session

PROMPT = """Write a short, specific cover letter (3-4 short paragraphs, no generic filler like "I am excited to apply") for this job, grounded ONLY in the resume text below — do not invent experience, employers, or skills not present in it.

Job:
Title: {title}
Company: {company}
Description excerpt: {jd_excerpt}

Candidate's resume:
{resume_text}

Reply with ONLY the cover letter text, no preamble, no "Dear Hiring Manager" salutation boilerplate beyond a normal greeting, no explanation.
"""


def draft_cover_letter(job: Job, company_name: str) -> str:
    prompt = PROMPT.format(
        title=job.title,
        company=company_name,
        jd_excerpt=job.jd_text[:1500],
        resume_text=(job.resume_text or "")[:3000],
    )
    return ask_premium(prompt).strip()


def run_cover_letter(limit: int = 50) -> dict:
    session = get_session()
    rows = session.execute(
        select(Job, Company.name)
        .join(Company, isouter=True)
        .where(Job.status.in_(["new", "approved"]), Job.resume_text.is_not(None), Job.cover_letter.is_(None))
        .limit(limit)
    ).all()

    drafted = 0
    errors = 0
    for i, (job, company_name) in enumerate(rows, 1):
        try:
            job.cover_letter = draft_cover_letter(job, company_name or "the company")
        except Exception as e:
            errors += 1
            print(f"[cover_letter] {i}/{len(rows)} FAILED on '{job.title}': {e}")
            continue
        session.commit()  # per-job, not one batch at the end — makes progress visible mid-run
        drafted += 1
        print(f"[cover_letter] {i}/{len(rows)} done — '{job.title}'")

    session.close()
    return {"drafted": drafted, "errors": errors}


if __name__ == "__main__":
    print(run_cover_letter())
