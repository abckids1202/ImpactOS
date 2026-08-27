from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./impactos.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    ensure_schema()


def ensure_schema() -> None:
    """Apply the small additive migration needed by the zero-setup alpha.

    The project previously used ``create_all`` only. New installations get the
    complete metadata above; existing development SQLite databases receive the
    additive identity columns here so upgrading does not destroy seeded data.
    A production deployment should run the checked-in Alembic migration before
    startup rather than relying on this compatibility path.
    """
    additions = {
        "schools": {
            "is_active": "BOOLEAN NOT NULL DEFAULT 1",
            "updated_at": "DATETIME",
        },
        "users": {
            "status": "VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'",
            "last_login_at": "DATETIME",
            "updated_at": "DATETIME",
        },
        "invitations": {
            "status": "VARCHAR(20) NOT NULL DEFAULT 'PENDING'",
            "invited_by": "VARCHAR(36)",
            "used_by": "VARCHAR(36)",
        },
        "audit_logs": {
            "actor_user_id": "VARCHAR(36)",
            "request_id": "VARCHAR(80)",
        },
        "reviews": {
            "reviewed_version": "INTEGER",
        },
        "problem_priorities": {
            "evidence_strength": "INTEGER NOT NULL DEFAULT 0",
            "urgency_score": "INTEGER NOT NULL DEFAULT 0",
            "reach_score": "INTEGER NOT NULL DEFAULT 0",
            "feasibility_score": "INTEGER NOT NULL DEFAULT 0",
            "reviewed_by": "VARCHAR(36)",
            "reviewed_at": "DATETIME",
            "review_date": "VARCHAR(30)",
        },
        "evidence_items": {
            "report_id": "VARCHAR(36)",
        },
    }
    inspector = inspect(engine)
    with engine.begin() as connection:
        for table, columns in additions.items():
            if not inspector.has_table(table):
                continue
            existing = {column["name"] for column in inspector.get_columns(table)}
            for name, definition in columns.items():
                if name not in existing:
                    connection.execute(text(f'ALTER TABLE "{table}" ADD COLUMN "{name}" {definition}'))
