"""Sync SQLAlchemy engine/session. Agents run as scheduled scripts, not a
high-concurrency server, so sync is simpler and sufficient — the FastAPI
layer (a later build step) can wrap calls in a threadpool if needed."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from jarvis.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


def get_session() -> Session:
    return SessionLocal()
