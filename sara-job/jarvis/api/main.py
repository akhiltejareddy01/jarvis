"""FastAPI REST layer — per Sara_Job_Arch.docx: "Frontend never touches agents
or the DB directly — everything goes through the FastAPI REST layer."

This is a minimal first slice (just /api/jobs) built ahead of the doc's build
order at Akhil's request, to get the real Scout/JD-Parser/Fit-Scorer output
into the dashboard now rather than waiting for the full FastAPI+scheduler
milestone. Extend this file as more agents/tables come online — don't create
a second API app.

Run:  uvicorn jarvis.api.main:app --reload --port 8000
"""

import threading
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import select

from jarvis.agents.applier import reopen_application
from jarvis.db.models import Application, Company, Job
from jarvis.db.session import get_session

app = FastAPI(title="Sara Job API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_FIT_ORDER = {"strong": 0, "medium": 1, "weak": 2, None: 3}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/jobs")
def list_jobs(status: str | None = None):
    session = get_session()
    try:
        stmt = select(Job, Company.name, Company.category).join(Company, isouter=True)
        if status:
            stmt = stmt.where(Job.status == status)
        rows = session.execute(stmt).all()

        jobs = [
            {
                "id": str(job.id),
                "company": company_name or "Unknown",
                "companyCategory": company_category or "",
                "title": job.title,
                "location": job.location,
                "remote": job.remote,
                "url": job.url,
                "themeDay": job.theme_day,
                "fitRating": job.fit_rating,
                "fitReason": job.fit_reason,
                "status": job.status,
                "seenAt": job.seen_at.isoformat() if job.seen_at else None,
                "resumeUsed": job.resume_track,
                "atsScore": job.ats_score,
                "coverLetterPreview": job.cover_letter,
            }
            for job, company_name, company_category in rows
        ]
        jobs.sort(key=lambda j: (_FIT_ORDER.get(j["fitRating"], 3), j["seenAt"] or ""))
        return jobs
    finally:
        session.close()


@app.post("/api/jobs/{job_id}/approve")
def approve_job(job_id: str):
    session = get_session()
    try:
        job = session.get(Job, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="job not found")
        job.status = "approved"
        session.commit()
        return {"id": job_id, "status": "approved"}
    finally:
        session.close()


@app.post("/api/jobs/{job_id}/skip")
def skip_job(job_id: str):
    session = get_session()
    try:
        job = session.get(Job, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="job not found")
        job.status = "skipped"
        session.commit()
        return {"id": job_id, "status": "skipped"}
    finally:
        session.close()


@app.get("/api/applications")
def list_applications():
    session = get_session()
    try:
        rows = session.execute(
            select(Application, Job.title, Job.url, Company.name)
            .join(Job, Application.job_id == Job.id)
            .join(Company, isouter=True)
            .order_by(Application.created_at.desc())
        ).all()

        return [
            {
                "id": str(app_row.id),
                "jobId": str(app_row.job_id),
                "company": company_name or "Unknown",
                "title": job_title,
                "jobUrl": job_url,
                "resumeVariant": app_row.resume_variant,
                "submittedVia": app_row.submitted_via,
                "status": app_row.status,
                "proofScreenshotUrl": f"/api/applications/{app_row.id}/screenshot" if app_row.screenshot_path else None,
                "submittedAt": app_row.submitted_at.isoformat() if app_row.submitted_at else None,
                "lastEventAt": app_row.created_at.isoformat(),
            }
            for app_row, job_title, job_url, company_name in rows
        ]
    finally:
        session.close()


@app.get("/api/applications/{application_id}/screenshot")
def get_application_screenshot(application_id: str):
    session = get_session()
    try:
        application = session.get(Application, application_id)
        if not application or not application.screenshot_path or not Path(application.screenshot_path).exists():
            raise HTTPException(status_code=404, detail="screenshot not found")
        return FileResponse(application.screenshot_path, media_type="image/png")
    finally:
        session.close()


@app.post("/api/applications/{application_id}/open")
def open_application(application_id: str):
    """Opens a real, visible browser window right now with the application
    already filled in (reusing answers a background prep pass already
    drafted — see jarvis/agents/applier.py) so clicking this in the
    dashboard gets you straight to "just click Submit". Runs in a background
    thread so the request returns immediately instead of blocking for
    however long the browser window stays open."""
    session = get_session()
    try:
        if not session.get(Application, application_id):
            raise HTTPException(status_code=404, detail="application not found")
    finally:
        session.close()

    def run():
        try:
            reopen_application(application_id)
        except Exception as e:
            print(f"[api] reopen_application({application_id}) failed: {e}")

    threading.Thread(target=run, daemon=True).start()
    return {"id": application_id, "status": "opening"}


@app.post("/api/applications/{application_id}/confirm-submitted")
def confirm_application_submitted(application_id: str):
    """The Applier fills the form and hands off to a human to click Submit
    (Ashby's anti-bot detection rejects an automated click, confirmed on a
    real posting 2026-07-27) — there's no way for the automation to observe
    that a human click happened, so the human confirms it here instead."""
    session = get_session()
    try:
        application = session.get(Application, application_id)
        if not application:
            raise HTTPException(status_code=404, detail="application not found")
        application.status = "submitted"
        application.submitted_at = datetime.utcnow()
        job = session.get(Job, application.job_id)
        if job:
            job.status = "applied"
        session.commit()
        return {"id": application_id, "status": "submitted", "submittedAt": application.submitted_at.isoformat()}
    finally:
        session.close()


@app.post("/api/applications/{application_id}/mark-not-submitted")
def mark_application_not_submitted(application_id: str):
    session = get_session()
    try:
        application = session.get(Application, application_id)
        if not application:
            raise HTTPException(status_code=404, detail="application not found")
        application.status = "not_submitted"
        application.submitted_at = None
        session.commit()
        return {"id": application_id, "status": "not_submitted"}
    finally:
        session.close()
