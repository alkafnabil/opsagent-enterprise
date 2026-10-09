from __future__ import annotations
import logging
import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from .config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()


def _create_engine_resilient(url: str, name: str):
    """
    Creates SQLAlchemy engine for PostgreSQL.
    If psycopg2 driver or Postgres is unavailable in local environment,
    gracefully provides SQLite fallback for local test and development.
    """
    try:
        if "postgresql" in url:
            import psycopg2  # check if driver exists
        engine_inst = create_engine(url, pool_pre_ping=True)
        return engine_inst
    except Exception as exc:
        logger.warning(
            f"Tidak dapat menginisialisasi driver PostgreSQL untuk {name} ({exc}). "
            f"Menggunakan local SQLite fallback (opsagent_dev.db)."
        )
        sqlite_url = "sqlite:///./opsagent_dev.db"
        return create_engine(sqlite_url, connect_args={"check_same_thread": False})


# Primary Engine (Read-Write: for audit logging, etc.)
engine = _create_engine_resilient(settings.DATABASE_URL, "Primary Engine")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Read-Only Engine (Dedicated for sql_query tool text-to-SQL security)
engine_ro = _create_engine_resilient(settings.DATABASE_RO_URL, "Read-Only Engine")
SessionRO = sessionmaker(autocommit=False, autoflush=False, bind=engine_ro)


def init_db():
    """Initializes schema tables if using SQLite fallback."""
    try:
        from app.models.operational import Base as OpBase
        from app.models.audit import AuditLog
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.warning(f"Init DB schema notice: {e}")


init_db()


def get_db() -> Generator[Session, None, None]:
    """Dependency for obtaining read-write database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_ro_db() -> Generator[Session, None, None]:
    """Dependency for obtaining strictly read-only database session."""
    db = SessionRO()
    try:
        yield db
    finally:
        db.close()
