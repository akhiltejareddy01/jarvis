"""SQLAlchemy 2.0 models — per Sara_Job_Arch.docx §"Database tables" + §07 of the
older JARVIS_Plan.pdf (used for the columns the locked doc doesn't spell out in
full). embedding columns are Vector(768) to match the local nomic/bge embedding
model in core/embeddings.py (not OpenAI's 1536-dim — that was an earlier, wrong
assumption from before the doc was locked).
"""

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _uuid_pk():
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


# ============================================================
# Profile Brain — Sara's RAG source. Seeded once from the real
# resumes (scripts/seed_profile.py), edited later via the frontend
# once the API layer exists.
# ============================================================


class ProfileFact(Base):
    __tablename__ = "profile_facts"
    __table_args__ = (UniqueConstraint("category", "key"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    category: Mapped[str]
    key: Mapped[str]
    value: Mapped[str]
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class ResumeVariant(Base):
    __tablename__ = "resume_variants"

    id: Mapped[uuid.UUID] = _uuid_pk()
    track: Mapped[str] = mapped_column(unique=True)
    summary: Mapped[str] = mapped_column(default="")
    file_name: Mapped[str] = mapped_column(default="")
    notes: Mapped[str] = mapped_column(default="")
    # Full text extracted from the real PDF (jarvis/agents/resume_selector.py,
    # lazily backfilled on first run) + its embedding, so Resume Selector can
    # do real ATS-style scoring instead of guessing off the one-line `notes`.
    full_text: Mapped[str] = mapped_column(default="")
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768), nullable=True)
    # Structured fields extracted once from full_text (jarvis/tools/resume_pdf.py
    # schema) — name/contact/education/dates live here as fixed facts a rewrite
    # can never touch; only summary/experience-bullets/skills are tailorable.
    structured: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class ScreeningAnswer(Base):
    __tablename__ = "screening_answers"

    id: Mapped[uuid.UUID] = _uuid_pk()
    question_key: Mapped[str] = mapped_column(unique=True)
    question_text: Mapped[str]
    answer: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


# ============================================================
# Daily intake
# ============================================================


class DailyIntake(Base):
    __tablename__ = "daily_intake"

    id: Mapped[uuid.UUID] = _uuid_pk()
    run_date: Mapped[str] = mapped_column(unique=True)  # ISO date, e.g. "2026-07-27"
    track: Mapped[str] = mapped_column(default="")
    locations: Mapped[list[str]] = mapped_column(JSON, default=list)
    remote_ok: Mapped[bool] = mapped_column(default=True)
    salary_floor: Mapped[int] = mapped_column(default=0)
    target_count: Mapped[int] = mapped_column(default=50)
    mode: Mapped[str] = mapped_column(default="semi_auto")
    focus_companies: Mapped[list[str]] = mapped_column(JSON, default=list)
    avoid_companies: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(default="pending")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


# ============================================================
# The job loop
# ============================================================


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = _uuid_pk()
    name: Mapped[str] = mapped_column(unique=True)
    category: Mapped[str] = mapped_column(default="")  # midsize | university | gov | mnc | startup
    domain: Mapped[str] = mapped_column(default="")
    ats: Mapped[str] = mapped_column(default="")  # greenhouse | lever | ashby | other
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    jobs: Mapped[list["Job"]] = relationship(back_populates="company")


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("source", "external_id"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    company_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("companies.id"))
    source: Mapped[str]  # adzuna | usajobs | greenhouse | lever | ashby
    external_id: Mapped[str]
    title: Mapped[str]
    location: Mapped[str] = mapped_column(default="")
    remote: Mapped[bool] = mapped_column(default=False)
    url: Mapped[str] = mapped_column(default="")
    jd_text: Mapped[str] = mapped_column(default="")
    jd_parsed: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768), nullable=True)
    theme_day: Mapped[str] = mapped_column(default="")
    fit_rating: Mapped[str | None] = mapped_column(nullable=True)  # strong | medium | weak
    fit_reason: Mapped[str | None] = mapped_column(nullable=True)
    # Resume Selector + Cover Letter (jarvis/agents/resume_selector.py,
    # jarvis/agents/cover_letter.py) — populated for strong/medium jobs only,
    # per the daily pipeline order (Fit Scorer filters Weak out first).
    resume_track: Mapped[str | None] = mapped_column(nullable=True)  # e.g. "AI Engineer" or "AI Engineer (tailored)"
    resume_text: Mapped[str | None] = mapped_column(nullable=True)
    ats_score: Mapped[int | None] = mapped_column(nullable=True)  # 0-100, quality bar is 70
    # Actual file to upload at Apply time. As-is picks point straight at the real
    # PDF in resumes/; tailored picks get a freshly rendered one under
    # generated_resumes/ (jarvis/tools/resume_pdf.py) — a resume_text string alone
    # isn't something any ATS upload form can take.
    resume_file_path: Mapped[str | None] = mapped_column(nullable=True)
    cover_letter: Mapped[str | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(default="new")  # new | queued | applied | skipped
    seen_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    company: Mapped["Company"] = relationship(back_populates="jobs")


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = _uuid_pk()
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id"))
    resume_variant: Mapped[str] = mapped_column(default="")
    cover_letter: Mapped[str] = mapped_column(default="")
    mode: Mapped[str] = mapped_column(default="semi_auto")
    submitted_via: Mapped[str | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(default="draft")
    approved_by_human: Mapped[bool] = mapped_column(default=False)
    submitted_at: Mapped[datetime | None] = mapped_column(nullable=True)
    # jarvis/agents/applier.py — proof screenshot per the docx ("Log: company +
    # proof screenshot saved") and the actual screening-question answers it
    # submitted, for audit purposes.
    screenshot_path: Mapped[str | None] = mapped_column(nullable=True)
    screening_answers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[uuid.UUID] = _uuid_pk()
    company_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("companies.id"))
    name: Mapped[str] = mapped_column(default="")
    role: Mapped[str] = mapped_column(default="")  # recruiter | hiring_manager | engineer | alumni
    source: Mapped[str] = mapped_column(default="")
    profile_url: Mapped[str] = mapped_column(default="")
    last_contact_at: Mapped[datetime | None] = mapped_column(nullable=True)


class DailyReport(Base):
    __tablename__ = "daily_reports"

    id: Mapped[uuid.UUID] = _uuid_pk()
    report_date: Mapped[str] = mapped_column(unique=True)
    stats: Mapped[dict] = mapped_column(JSON, default=dict)
    journal_entry: Mapped[str] = mapped_column(default="")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class ActionLog(Base):
    __tablename__ = "action_log"

    id: Mapped[uuid.UUID] = _uuid_pk()
    actor: Mapped[str]
    action: Mapped[str]
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
