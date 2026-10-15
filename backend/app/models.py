"""Entidades persistentes mínimas; sin sensores ni control físico en Fase 1."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Column
from sqlmodel import Field, SQLModel

from .database import UTCDateTime, utc_now


class Zone(SQLModel, table=True):
    __tablename__ = "zones"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=80)
    purpose: str = Field(max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(UTCDateTime(), nullable=False))


class Device(SQLModel, table=True):
    __tablename__ = "devices"
    __table_args__ = (
        CheckConstraint("kind = 'esp32-s3'", name="ck_devices_kind"),
        CheckConstraint("status = 'not_configured'", name="ck_devices_phase1_status"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=80)
    kind: str = Field(default="esp32-s3", max_length=32)
    model: str | None = Field(default=None, max_length=120)
    serial_port: str | None = Field(default=None, max_length=128)
    status: str = Field(default="not_configured", max_length=32)
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(UTCDateTime(), nullable=False))
    last_seen_at: datetime | None = Field(default=None, sa_column=Column(UTCDateTime(), nullable=True))


class Measurement(SQLModel, table=True):
    """Reserva para mediciones físicas; no hay ruta de ingesta en esta fase.

    Los escenarios tendrán tablas independientes. Un dispositivo registrado no
    constituye evidencia de conexión ni origina mediciones automáticamente.
    """

    __tablename__ = "measurements"
    __table_args__ = (
        CheckConstraint("source = 'real'", name="ck_measurements_real_source"),
        CheckConstraint("quality IN ('valid', 'invalid', 'unverified')", name="ck_measurements_quality"),
        CheckConstraint("value >= -1.0e308 AND value <= 1.0e308", name="ck_measurements_finite_value"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    source: str = Field(default="real", max_length=16)
    zone_id: UUID = Field(foreign_key="zones.id", index=True, ondelete="RESTRICT")
    device_id: UUID = Field(foreign_key="devices.id", index=True, ondelete="RESTRICT")
    quantity: str = Field(max_length=64)
    unit: str = Field(max_length=32)
    value: float
    quality: str = Field(max_length=16)
    measured_at: datetime = Field(sa_column=Column(UTCDateTime(), nullable=False, index=True))
    recorded_at: datetime = Field(default_factory=utc_now, sa_column=Column(UTCDateTime(), nullable=False))
    observations: str | None = Field(default=None, max_length=2000)
