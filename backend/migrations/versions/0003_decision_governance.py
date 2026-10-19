"""Comparaciones hipotéticas y revisión humana; no altera tablas físicas."""

from alembic import op
import sqlalchemy as sa

revision = "0003_decisions"
down_revision = "0002_serial"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "decision_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("engine_fingerprint", sa.String(64), nullable=False),
        sa.Column("snapshot_sha256", sa.String(64), nullable=False),
        sa.CheckConstraint("source = 'hypothetical'", name="ck_decision_runs_source"),
    )
    op.create_table(
        "decision_reviews",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("alternative_id", sa.String(20), nullable=False),
        sa.Column("decision", sa.String(10), nullable=False),
        sa.Column("responsible", sa.String(120), nullable=False),
        sa.Column("reason", sa.String(2000), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["decision_runs.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("run_id", "alternative_id", name="uq_review_alternative"),
        sa.CheckConstraint("decision IN ('approved', 'rejected')", name="ck_review_decision"),
    )
    op.create_index("ix_decision_reviews_run_id", "decision_reviews", ["run_id"])
    op.create_index("uq_review_approved_run", "decision_reviews", ["run_id"], unique=True,
                    sqlite_where=sa.text("decision = 'approved'"))


def downgrade():
    raise RuntimeError("Reversión destructiva deshabilitada: conservar decisiones e historial.")
