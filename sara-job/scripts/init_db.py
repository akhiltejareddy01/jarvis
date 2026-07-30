"""Create the pgvector extension and all tables. Safe to re-run.

Usage:  python scripts/init_db.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from jarvis.db.models import Base
from jarvis.db.session import engine


# create_all() only creates tables that don't exist yet — it never ALTERs an
# existing table, so columns added to models.py after the first run need to be
# added here explicitly. No Alembic in this project; keep this list append-only
# and idempotent (IF NOT EXISTS) rather than reaching for a migration tool.
COLUMN_MIGRATIONS = [
    "ALTER TABLE resume_variants ADD COLUMN IF NOT EXISTS full_text TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE resume_variants ADD COLUMN IF NOT EXISTS embedding vector(768)",
    "ALTER TABLE resume_variants ADD COLUMN IF NOT EXISTS structured JSONB",
    "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS resume_track TEXT",
    "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS resume_text TEXT",
    "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS ats_score INTEGER",
    "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS resume_file_path TEXT",
    "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS cover_letter TEXT",
    "ALTER TABLE applications ADD COLUMN IF NOT EXISTS screenshot_path TEXT",
    "ALTER TABLE applications ADD COLUMN IF NOT EXISTS screening_answers JSONB",
]


def main() -> None:
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        for stmt in COLUMN_MIGRATIONS:
            conn.execute(text(stmt))
    print("Schema applied:", ", ".join(sorted(Base.metadata.tables.keys())))


if __name__ == "__main__":
    main()
