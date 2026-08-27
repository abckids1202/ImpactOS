"""Add the Response Loop commitments, updates, and priority dimensions."""

from alembic import op
import sqlalchemy as sa


revision = "0002_response_loop"
down_revision = "0001_phase1_auth_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("response_commitments"):
        op.create_table(
            "response_commitments",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("school_id", sa.String(36), sa.ForeignKey("schools.id"), nullable=False),
            sa.Column("cluster_id", sa.String(36), sa.ForeignKey("problem_clusters.id"), nullable=False),
            sa.Column("research_id", sa.String(36), sa.ForeignKey("research_projects.id"), nullable=True),
            sa.Column("project_id", sa.String(36), sa.ForeignKey("impact_projects.id"), nullable=True),
            sa.Column("title", sa.String(240), nullable=False),
            sa.Column("intended_outcome", sa.Text(), nullable=False, server_default=""),
            sa.Column("owner_role", sa.String(80), nullable=False),
            sa.Column("owner_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("assigned_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("status", sa.String(30), nullable=False, server_default="OPEN"),
            sa.Column("priority", sa.String(20), nullable=False, server_default="MEDIUM"),
            sa.Column("due_date", sa.String(30), nullable=True),
            sa.Column("next_update_date", sa.String(30), nullable=True),
            sa.Column("blocker", sa.Text(), nullable=False, server_default=""),
            sa.Column("completion_note", sa.Text(), nullable=False, server_default=""),
            sa.Column("evidence_reference", sa.Text(), nullable=False, server_default=""),
            sa.Column("visibility", sa.String(30), nullable=False, server_default="SCHOOL"),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_response_commitments_school_id", "response_commitments", ["school_id"])
        op.create_index("ix_response_commitments_cluster_id", "response_commitments", ["cluster_id"])
        op.create_index("ix_response_commitments_owner_id", "response_commitments", ["owner_id"])
        op.create_index("ix_response_commitments_status", "response_commitments", ["status"])

    if not inspector.has_table("response_commitment_updates"):
        op.create_table(
            "response_commitment_updates",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("school_id", sa.String(36), sa.ForeignKey("schools.id"), nullable=False),
            sa.Column("commitment_id", sa.String(36), sa.ForeignKey("response_commitments.id"), nullable=False),
            sa.Column("author_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("kind", sa.String(30), nullable=False, server_default="UPDATE"),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("visibility", sa.String(30), nullable=False, server_default="SCHOOL"),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_response_commitment_updates_school_id", "response_commitment_updates", ["school_id"])
        op.create_index("ix_response_commitment_updates_commitment_id", "response_commitment_updates", ["commitment_id"])

    existing = {column["name"] for column in inspector.get_columns("problem_priorities")} if inspector.has_table("problem_priorities") else set()
    additions = {
        "evidence_strength": (sa.Integer(), sa.text("0")),
        "urgency_score": (sa.Integer(), sa.text("0")),
        "reach_score": (sa.Integer(), sa.text("0")),
        "feasibility_score": (sa.Integer(), sa.text("0")),
        "reviewed_by": (sa.String(36), None),
        "reviewed_at": (sa.DateTime(), None),
        "review_date": (sa.String(30), None),
    }
    for name, (type_, default) in additions.items():
        if name not in existing:
            kwargs = {"nullable": True}
            if default is not None:
                kwargs["server_default"] = default
            with op.batch_alter_table("problem_priorities") as batch:
                batch.add_column(sa.Column(name, type_, **kwargs))

    evidence_existing = {column["name"] for column in inspector.get_columns("evidence_items")} if inspector.has_table("evidence_items") else set()
    if "report_id" not in evidence_existing:
        with op.batch_alter_table("evidence_items") as batch:
            batch.add_column(sa.Column("report_id", sa.String(36), sa.ForeignKey("problem_reports.id"), nullable=True))
    evidence_indexes = {index["name"] for index in inspector.get_indexes("evidence_items")} if inspector.has_table("evidence_items") else set()
    if "ix_evidence_items_report_id" not in evidence_indexes:
        op.create_index("ix_evidence_items_report_id", "evidence_items", ["report_id"])


def downgrade() -> None:
    op.drop_index("ix_evidence_items_report_id", table_name="evidence_items")
    with op.batch_alter_table("evidence_items") as batch:
        batch.drop_column("report_id")
    for name in ("review_date", "reviewed_at", "reviewed_by", "feasibility_score", "reach_score", "urgency_score", "evidence_strength"):
        with op.batch_alter_table("problem_priorities") as batch:
            batch.drop_column(name)
    op.drop_index("ix_response_commitment_updates_commitment_id", table_name="response_commitment_updates")
    op.drop_index("ix_response_commitment_updates_school_id", table_name="response_commitment_updates")
    op.drop_table("response_commitment_updates")
    op.drop_index("ix_response_commitments_status", table_name="response_commitments")
    op.drop_index("ix_response_commitments_owner_id", table_name="response_commitments")
    op.drop_index("ix_response_commitments_cluster_id", table_name="response_commitments")
    op.drop_index("ix_response_commitments_school_id", table_name="response_commitments")
    op.drop_table("response_commitments")
