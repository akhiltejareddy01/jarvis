"""Resume Selector — per Sara_Job_Arch.docx §"Frozen decisions":

"Resume rule: score your 7 resumes against each JD [Akhil actually has 11, not
7 — see resumes/]. If one clears a quality bar → use as-is. If none does →
Claude rewrites a tailored resume [swapped to OpenAI per Akhil's 2026-07-27
instruction, see core/llm.py]. Honesty lock: rewrites only reframe /
re-emphasize what is genuinely in your resumes. Never fabricate experience."

Only runs on jobs that survived Fit Scorer (strong/medium) and haven't been
explicitly skipped — matches the daily pipeline order where Fit Scorer
filters Weak out first.

Scores ALL 11 resumes in a single batched light-tier LLM call per job — not
an embedding-narrowed shortlist. An earlier version pre-filtered to the top 3
by embedding similarity to save tokens, but a real run misranked "PLM" above
"AI Engineer" for a job titled "Distinguished AI Engineer" (embeddings picked
up on generic enterprise/process vocabulary overlap), which would have hidden
the correct resume from the LLM scorer entirely. Scoring all 11 costs more
tokens per call but is a single call regardless, and correctness here matters
more than the token savings — a wrong resume going out is a real-world problem.

Structural (not free-text) honesty lock: resumes are stored as structured JSON
(name/contact/education/employer/dates as fixed fields) once, extracted from
the real PDFs. Tailoring only ever asks the LLM for summary/skills/bullet
rephrasings and copies every fixed field over verbatim in code — so a rewrite
is STRUCTURALLY incapable of inventing an employer, date, or degree, not just
instructed not to. The output is rendered to a real PDF (jarvis/tools/
resume_pdf.py) matching the original template, since an ATS upload field needs
an actual file, not a text blob.

Commits after each job (not one batch at the end) so progress is visible
mid-run via a DB read, and a crash partway through doesn't lose completed work.
"""

import copy
import json
from pathlib import Path

from pypdf import PdfReader
from sqlalchemy import select

from jarvis.core.embeddings import embed
from jarvis.core.llm import ask_light, ask_premium
from jarvis.db.models import Job, ResumeVariant
from jarvis.db.session import get_session
from jarvis.tools.resume_pdf import render_pdf

RESUMES_DIR = Path(__file__).resolve().parent.parent.parent / "resumes"
GENERATED_DIR = Path(__file__).resolve().parent.parent.parent / "generated_resumes"
QUALITY_BAR = 70  # ATS score 0-100 — clears this -> use as-is, else tailor a rewrite

SCORE_PROMPT = """You are an ATS (applicant tracking system) scorer. Score how well EACH candidate resume matches this job on a 0-100 scale (keyword/skill overlap, seniority match, relevant experience) — like a real ATS would, not a generous human reader.

Reply with ONLY a JSON array, no other text: [{{"track": "<resume track name, copied exactly>", "score": 0-100, "reason": "one sentence"}}, ...] — one entry for EVERY resume listed below.

Job:
Title: {title}
Seniority: {seniority}
Required skills: {skills}
Description excerpt: {jd_excerpt}

Resumes:
{resumes_block}
"""

EXTRACT_PROMPT = """Convert this resume's raw PDF-extracted text into structured JSON. The raw text has PDF-extraction artifacts — stray "�" characters were originally bullet points or dashes; reconstruct clean readable text from context.

Reply with ONLY a JSON object matching exactly this shape (use [] for list sections with no content, omit optional string keys you can't find):
{{"name": "...", "tagline": "...", "location": "...", "phone": "...", "email": "...", "linkedin": "...", "github": "...",
"summary": "...",
"experience": [{{"company": "...", "dates": "...", "role": "...", "location": "...", "description": "...", "bullets": ["...", ...]}}],
"projects": [{{"name": "...", "tags": "...", "bullets": ["...", ...]}}],
"skills": [{{"category": "...", "items": "..."}}],
"certifications": ["...", ...],
"publications": ["...", ...],
"education": [{{"institution": "...", "dates": "...", "degree": "...", "location": "..."}}]}}

This must be a COMPLETE, LOSSLESS conversion — preserve every employer, date, bullet, number, and fact exactly as written. Do not summarize or drop anything.

Raw resume text:
{full_text}
"""

TAILOR_PROMPT = """Given this candidate's real resume (structured JSON) and a target job, tailor it to better match — but you may ONLY touch "summary", "skills", and bullet/description phrasing for EACH experience entry.

STRICT RULES:
- NEVER invent, add, or imply a skill, employer, job title, degree, date, achievement, or number not already present somewhere in the source resume below.
- Company names, dates, roles, locations, and education are FIXED — don't bother rewriting them, they will be copied over verbatim regardless of what you output.
- You may reorder/rephrase bullets to surface relevant keywords and reorder/re-emphasize skills — every fact must trace back to the source.
- Reply with ONLY a JSON object: {{"summary": "...", "skills": [{{"category": "...", "items": "..."}}], "experience": [{{"description": "...", "bullets": ["...", ...]}}, ...] — one entry per source experience entry, IN THE SAME ORDER, "score": 0-100}} where score is your honest ATS-match estimate of the tailored version against this job.

Target job:
Title: {title}
Required skills: {skills}
Description excerpt: {jd_excerpt}

Source resume (structured):
{structured_json}
"""


def _extract_pdf_text(file_name: str) -> str:
    path = RESUMES_DIR / file_name
    reader = PdfReader(path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _parse_json(raw: str) -> dict | list | None:
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def ensure_resume_embeddings(session) -> list[ResumeVariant]:
    resumes = session.scalars(select(ResumeVariant)).all()
    changed = False
    for r in resumes:
        if not r.full_text and r.file_name:
            r.full_text = _extract_pdf_text(r.file_name)
            changed = True
        if r.embedding is None and r.full_text:
            r.embedding = embed(r.full_text[:3000])
            changed = True
    if changed:
        session.commit()
    return resumes


def ensure_resume_structured(session, resumes: list[ResumeVariant]) -> None:
    """One-time (per resume) structured extraction. Tried ask_bulk (70b)
    first since this becomes the permanent fixed-fact source of truth for
    every future generated PDF — but the 70b model's 100k-tokens/day quota
    was still exhausted from earlier today and regenerates too slowly
    (~40min+ wait) to be practical, so this uses ask_light (8b) like
    everything else. It's a mechanical lossless-reformatting task, not a
    judgment call, so the smaller model is a reasonable fit anyway."""
    for r in resumes:
        if r.structured is not None or not r.full_text:
            continue
        # Generous max_tokens — a truncated response is invalid JSON, and the default
        # limit silently ate 5/11 resumes' output on a real run before this was added.
        parsed = _parse_json(ask_light(EXTRACT_PROMPT.format(full_text=r.full_text), max_tokens=3000))
        if isinstance(parsed, dict):
            r.structured = parsed
            session.commit()  # per-resume, not one batch at the end — a crash shouldn't lose earlier work
            print(f"[resume_selector] extracted structured resume for '{r.track}'")
        else:
            print(f"[resume_selector] structured extraction FAILED to parse for '{r.track}'")


def score_all_resumes(job: Job, resumes: list[ResumeVariant]) -> list[dict]:
    parsed = job.jd_parsed or {}
    resumes_block = "\n\n".join(f"[{r.track}]\n{r.full_text[:1200]}" for r in resumes)
    prompt = SCORE_PROMPT.format(
        title=job.title,
        seniority=parsed.get("seniority", "unknown"),
        skills=", ".join(parsed.get("skills", [])) or "unknown",
        jd_excerpt=job.jd_text[:1000],
        resumes_block=resumes_block,
    )
    result = _parse_json(ask_light(prompt))
    if isinstance(result, list) and result:
        return result
    # Fall back to a neutral score per resume rather than crashing the batch.
    return [{"track": r.track, "score": 50, "reason": "Scorer response unparseable"} for r in resumes]


def score_all_resumes_averaged(job: Job, resumes: list[ResumeVariant]) -> list[dict]:
    """Two independent scoring calls, averaged per track. A single call proved
    unreliable in practice: asking an 8b model to judge 11 resumes at once in
    one shot occasionally scrambles which score belongs to which track (e.g.
    scoring "GTM Engineer" as the top match for "Distinguished AI Engineer"
    when a repeat call correctly scores "AI Engineer" 85 and "GTM Engineer" 2)
    — a known small-model failure mode on wide batch-judgment prompts, not a
    code bug. Averaging two independent calls smooths out that noise; it
    doesn't guarantee correctness but makes a single bad roll far less likely
    to decide which resume goes out for a real job.
    """
    first = score_all_resumes(job, resumes)
    second = score_all_resumes(job, resumes)
    by_track: dict[str, list[dict]] = {}
    for row in first + second:
        by_track.setdefault(row.get("track", ""), []).append(row)
    return [
        {"track": track, "score": sum(r.get("score", 0) for r in rows) / len(rows)}
        for track, rows in by_track.items()
    ]


def tailor_resume(job: Job, base: ResumeVariant) -> tuple[dict, int]:
    """Returns (structured_resume, score). Fixed fields (name/contact/company/
    dates/role/location/education) are deep-copied from the source untouched;
    only summary/skills/bullets/description get the LLM's tailored values, and
    only if the response is well-formed enough to trust — otherwise that field
    falls back to the real original rather than a broken or empty one."""
    parsed = job.jd_parsed or {}
    prompt = TAILOR_PROMPT.format(
        title=job.title,
        skills=", ".join(parsed.get("skills", [])) or "unknown",
        jd_excerpt=job.jd_text[:1500],
        structured_json=json.dumps(base.structured),
    )
    result = _parse_json(ask_premium(prompt))
    tailored = copy.deepcopy(base.structured)

    if not isinstance(result, dict):
        return tailored, 50  # honesty-locked fallback: ship the real resume, not a broken one

    if isinstance(result.get("summary"), str):
        tailored["summary"] = result["summary"]
    if isinstance(result.get("skills"), list):
        tailored["skills"] = result["skills"]

    tailored_experience = result.get("experience")
    if isinstance(tailored_experience, list):
        for i, exp in enumerate(tailored.get("experience", [])):
            if i >= len(tailored_experience) or not isinstance(tailored_experience[i], dict):
                continue
            override = tailored_experience[i]
            if isinstance(override.get("bullets"), list):
                exp["bullets"] = override["bullets"]
            if isinstance(override.get("description"), str):
                exp["description"] = override["description"]

    try:
        score = int(result.get("score", 50))
    except (TypeError, ValueError):
        score = 50
    return tailored, score


def run_resume_selector(limit: int = 50) -> dict:
    session = get_session()
    resumes = ensure_resume_embeddings(session)
    ensure_resume_structured(session, resumes)

    jobs = session.scalars(
        select(Job)
        .where(
            # "new" per the docx's pipeline order (Resume runs before Dashboard/Approve),
            # "approved" too since in practice a job can get approved from the dashboard
            # before Resume Selector gets to it — don't skip building a resume just
            # because the human moved faster than the pipeline.
            Job.status.in_(["new", "approved"]),
            Job.fit_rating.in_(["strong", "medium"]),
            Job.resume_text.is_(None),
        )
        .limit(limit)
    ).all()

    as_is = 0
    tailored = 0
    errors = 0
    for i, job in enumerate(jobs, 1):
        try:
            scored = score_all_resumes_averaged(job, resumes)
            best = max(scored, key=lambda s: s.get("score", 0))
            best_resume = next((r for r in resumes if r.track == best.get("track")), resumes[0])

            if best.get("score", 0) >= QUALITY_BAR:
                job.resume_track = best_resume.track
                job.resume_text = best_resume.full_text
                job.ats_score = round(best["score"])
                job.resume_file_path = str((RESUMES_DIR / best_resume.file_name).resolve())
                as_is += 1
            else:
                structured, score = tailor_resume(job, best_resume)
                out_path = GENERATED_DIR / f"{job.id}.pdf"
                render_pdf(structured, str(out_path))
                job.resume_track = f"{best_resume.track} (tailored)"
                job.resume_text = json.dumps(structured)  # kept for dashboard preview/debugging
                job.ats_score = score
                job.resume_file_path = str(out_path.resolve())
                tailored += 1
        except Exception as e:
            errors += 1
            print(f"[resume_selector] {i}/{len(jobs)} FAILED on '{job.title}': {e}")
            continue

        session.commit()
        print(f"[resume_selector] {i}/{len(jobs)} done — '{job.title}' -> {job.resume_track} (ATS {job.ats_score})")

    session.close()
    return {"processed": len(jobs), "as_is": as_is, "tailored": tailored, "errors": errors}


if __name__ == "__main__":
    print(run_resume_selector())
