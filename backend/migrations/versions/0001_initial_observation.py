"""Zonas, dispositivos y reserva vacía de telemetría física.

Revision ID: 0001_observation
Revises: None
"""

import sqlalchemy as sa
from alembic import op

revision = "0001_observation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "zones",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("purpose", sa.String(160), nullable=False),
        sa.Column("description", sa.String(2000), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "devices",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("model", sa.String(120), nullable=True),
        sa.Column("serial_port", sa.String(128), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("kind = 'esp32-s3'", name="ck_devices_kind"),
        sa.CheckConstraint("status = 'not_configured'", name="ck_devices_phase1_status"),
    )
    op.create_table(
        "measurements",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("zone_id", sa.Uuid(), nullable=False),
        sa.Column("device_id", sa.Uuid(), nullable=False),
        sa.Column("quantity", sa.String(64), nullable=False),
        sa.Column("unit", sa.String(32), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("quality", sa.String(16), nullable=False),
        sa.Column("measured_at", sa.DateTime(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.Column("observations", sa.String(2000), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["zone_id"], ["zones.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("source = 'real'", name="ck_measurements_real_source"),
        sa.CheckConstraint("quality IN ('valid', 'invalid', 'unverified')", name="ck_measurements_quality"),
        sa.CheckConstraint("value >= -1.0e308 AND value <= 1.0e308", name="ck_measurements_finite_value"),
    )
    op.create_index("ix_measurements_zone_id", "measurements", ["zone_id"])
    op.create_index("ix_measurements_device_id", "measurements", ["device_id"])
    op.create_index("ix_measurements_measured_at", "measurements", ["measured_at"])


def downgrade() -> None:
    raise RuntimeError(
        "La reversión destructiva está deshabilitada: respalde y revise el historial antes de migrar."
    )
