"""Identificación real y diagnósticos seriales; preserva historial de Fase 1."""

from alembic import op
import sqlalchemy as sa

revision = "0002_serial"
down_revision = "0001_observation"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("devices", recreate="always") as batch:
        batch.drop_constraint("ck_devices_kind", type_="check")
        batch.drop_constraint("ck_devices_phase1_status", type_="check")
        batch.create_check_constraint("ck_devices_kind", "kind IN ('esp32', 'esp32-s3')")
        batch.create_check_constraint("ck_devices_status", "status IN ('not_configured', 'connected', 'disconnected')")
        batch.add_column(sa.Column("hardware_id", sa.String(64), nullable=True))
        batch.add_column(sa.Column("firmware_version", sa.String(120), nullable=True))
        batch.add_column(sa.Column("boot_id", sa.String(16), nullable=True))
        batch.add_column(sa.Column("last_sequence", sa.BigInteger(), nullable=True))
        batch.add_column(sa.Column("uptime_ms", sa.BigInteger(), nullable=True))
        batch.add_column(sa.Column("last_heartbeat_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("connection_updated_at", sa.DateTime(), nullable=True))
    op.create_index("ix_devices_hardware_id", "devices", ["hardware_id"], unique=True)
    op.create_table(
        "device_events",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("device_id", sa.Uuid(), nullable=True),
        sa.Column("port", sa.String(128), nullable=False),
        sa.Column("baud_rate", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("boot_id", sa.String(16), nullable=True),
        sa.Column("sequence", sa.BigInteger(), nullable=True),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("device_id", "boot_id", "sequence", name="uq_device_events_message"),
        sa.CheckConstraint("kind IN ('hello', 'heartbeat', 'disconnected', 'protocol_error', 'reader_stopped')", name="ck_device_events_kind"),
    )
    op.create_index("ix_device_events_device_id", "device_events", ["device_id"])
    op.create_index("ix_device_events_received_at", "device_events", ["received_at"])


def downgrade():
    raise RuntimeError("Reversión destructiva deshabilitada: conservar los diagnósticos e historial.")
