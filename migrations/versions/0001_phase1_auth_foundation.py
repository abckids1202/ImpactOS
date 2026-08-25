"""Add the Phase 1 identity, role, invitation, session, and audit foundation.

Revision ID: 0001_phase1_auth_foundation
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_phase1_auth_foundation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    # The local project historically bootstrapped its complete schema with
    # SQLAlchemy metadata. Keep that zero-setup behavior available to staging,
    # then add the Phase 1 columns for databases that predate this revision.
    from app.db import Base
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=bind)
    inspector = sa.inspect(bind)
    additions = {
        "schools": [("is_active", sa.Boolean(), sa.text("1")), ("updated_at", sa.DateTime(), None)],
        "users": [("status", sa.String(20), sa.text("'ACTIVE'")), ("last_login_at", sa.DateTime(), None), ("updated_at", sa.DateTime(), None)],
        "invitations": [("status", sa.String(20), sa.text("'PENDING'")), ("invited_by", sa.String(36), None), ("used_by", sa.String(36), None)],
        "audit_logs": [("actor_user_id", sa.String(36), None), ("request_id", sa.String(80), None)],
    }
    for table, columns in additions.items():
        if not inspector.has_table(table):
            continue
        existing = {column["name"] for column in inspector.get_columns(table)}
        for name, type_, default in columns:
            if name in existing:
                continue
            kwargs = {"nullable": True}
            if default is not None:
                kwargs["server_default"] = default
            with op.batch_alter_table(table) as batch:
                batch.add_column(sa.Column(name, type_, **kwargs))


def downgrade() -> None:
    # New installations and legacy installations both receive the same model
    # tables; only remove the additive Phase 1 columns on downgrade.
    for table, columns in {
        "audit_logs": ("request_id", "actor_user_id"),
        "invitations": ("used_by", "invited_by", "status"),
        "users": ("updated_at", "last_login_at", "status"),
        "schools": ("updated_at", "is_active"),
    }.items():
        with op.batch_alter_table(table) as batch:
            for column in columns:
                batch.drop_column(column)
