"""Scout — job sources -> jobs table with dedup. First of the "next" build-order
steps in Sara_Job_Arch.docx.

Weekly theme pattern (from JARVIS_Plan.pdf §05 — the locked doc says "weekly
theme sets the category" without redefining it, so this fills that in exactly
as the older doc specified, kept consistent with the frontend's mock data):
    Mon midsize · Tue university · Wed gov · Thu mnc · Fri+ startup/custom

Dedup, per docx §"Frozen decisions": "pgvector embedding similarity against
past jobs." Hard dedup on (source, external_id) happens first (cheap); soft
dedup via cosine similarity catches the same posting re-listed under a
different external_id (common with Adzuna aggregating multiple boards).
"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from jarvis.core.embeddings import embed
from jarvis.db.models import Company, Job, ProfileFact
from jarvis.db.session import get_session
from jarvis.tools.job_sources import fetch_adzuna, fetch_curated_boards, fetch_usajobs

WEEKLY_THEME = {
    0: "midsize",     # Monday
    1: "university",  # Tuesday
    2: "gov",         # Wednesday
    3: "mnc",         # Thursday
    4: "startup",     # Friday
    5: "startup",     # Saturday
    6: "startup",     # Sunday
}

DUPLICATE_SIMILARITY_THRESHOLD = 0.95  # cosine similarity above this = same job


def todays_theme() -> str:
    return WEEKLY_THEME[date.today().weekday()]


def _profile_value(session, category: str, key: str, default: str = "") -> str:
    fact = session.scalar(
        select(ProfileFact).where(ProfileFact.category == category, ProfileFact.key == key)
    )
    return fact.value if fact else default


def _get_or_create_company(session, name: str, category: str) -> Company:
    company = session.scalar(select(Company).where(Company.name == name))
    if company:
        return company
    company = Company(name=name, category=category)
    session.add(company)
    session.flush()
    return company


def _is_near_duplicate(session, embedding: list[float]) -> bool:
    """Cosine distance in pgvector is 1 - cosine_similarity, so distance below
    (1 - threshold) means similarity above threshold."""
    max_distance = 1 - DUPLICATE_SIMILARITY_THRESHOLD
    match = session.scalar(
        select(Job.id)
        .where(Job.embedding.is_not(None))
        .order_by(Job.embedding.cosine_distance(embedding))
        .limit(1)
    )
    if match is None:
        return False
    distance = session.scalar(
        select(Job.embedding.cosine_distance(embedding)).where(Job.id == match)
    )
    return distance is not None and distance <= max_distance


def run_scout() -> dict:
    session = get_session()
    theme = todays_theme()

    target_roles = [
        r.strip()
        for r in _profile_value(session, "preferences", "target_roles").split(",")
        if r.strip()
    ]
    locations = [
        l.strip()
        for l in _profile_value(session, "preferences", "locations").split(",")
        if l.strip()
    ]
    primary_location = locations[0] if locations else ""

    raw_jobs = []
    for role in target_roles:
        raw_jobs.extend(fetch_adzuna(role, primary_location))

    if theme == "gov":
        for role in target_roles:
            raw_jobs.extend(fetch_usajobs(role))

    raw_jobs.extend(fetch_curated_boards(category=theme))

    seen_count = len(raw_jobs)
    inserted = 0
    hard_duplicates = 0
    soft_duplicates = 0

    for raw in raw_jobs:
        exists = session.scalar(
            select(Job.id).where(Job.source == raw["source"], Job.external_id == raw["external_id"])
        )
        if exists:
            hard_duplicates += 1
            continue

        text_for_embedding = f"{raw['title']} at {raw['company_name']}. {raw['jd_text'][:1000]}"
        vector = embed(text_for_embedding)

        if _is_near_duplicate(session, vector):
            soft_duplicates += 1
            continue

        company = _get_or_create_company(
            session, raw["company_name"] or "Unknown", raw.get("company_category", "")
        )

        stmt = pg_insert(Job).values(
            company_id=company.id,
            source=raw["source"],
            external_id=raw["external_id"],
            title=raw["title"],
            location=raw["location"],
            remote=raw["remote"],
            url=raw["url"],
            jd_text=raw["jd_text"],
            embedding=vector,
            theme_day=theme,
            status="new",
        ).on_conflict_do_nothing(index_elements=["source", "external_id"])
        session.execute(stmt)
        inserted += 1

    session.commit()
    session.close()

    return {
        "theme": theme,
        "target_roles": target_roles,
        "fetched": seen_count,
        "inserted": inserted,
        "hard_duplicates": hard_duplicates,
        "soft_duplicates": soft_duplicates,
    }


if __name__ == "__main__":
    result = run_scout()
    print(result)
