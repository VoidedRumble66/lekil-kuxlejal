"""Entidades persistentes mínimas; sin sensores ni control físico en Fase 1."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, CheckConstraint, Column, JSON, UniqueConstraint
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
        CheckConstraint("kind IN ('esp32', 'esp32-s3')", name="ck_devices_kind"),
        CheckConstraint("status IN ('not_configured', 'connected', 'disconnected')", name="ck_devices_status"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=80)
    kind: str = Field(default="esp32", max_length=32)
    model: str | None = Field(default=None, max_length=120)
    serial_port: str | None = Field(default=None, max_length=128)
    status: str = Field(default="not_configured", max_length=32)
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(UTCDateTime(), nullable=False))
    last_seen_at: datetime | None = Field(default=None, sa_column=Column(UTCDateTime(), nullable=True))
    hardware_id: str | None = Field(default=None, max_length=64, index=True, unique=True)
    firmware_version: str | None = Field(default=None, max_length=120)
    boot_id: str | None = Field(default=None, max_length=16)
    last_sequence: int | None = Field(default=None, sa_type=BigInteger)
    uptime_ms: int | None = Field(default=None, sa_type=BigInteger)
    last_heartbeat_at: datetime | None = Field(default=None, sa_column=Column(UTCDateTime(), nullable=True))
    connection_updated_at: datetime | None = Field(default=None, sa_column=Column(UTCDateTime(), nullable=True))


class DeviceEvent(SQLModel, table=True):
    __tablename__ = "device_events"
    __table_args__ = (
        UniqueConstraint("device_id", "boot_id", "sequence", name="uq_device_events_message"),
        CheckConstraint("kind IN ('hello', 'heartbeat', 'disconnected', 'protocol_error', 'reader_stopped')", name="ck_device_events_kind"),
    )
    id: str = Field(primary_key=True, max_length=32)
    device_id: UUID | None = Field(default=None, foreign_key="devices.id", ondelete="RESTRICT", index=True)
    port: str = Field(max_length=128)
    baud_rate: int = 115200
    kind: str = Field(max_length=32)
    boot_id: str | None = Field(default=None, max_length=16)
    sequence: int | None = Field(default=None, sa_type=BigInteger)
    received_at: datetime = Field(sa_column=Column(UTCDateTime(), nullable=False, index=True))
    recorded_at: datetime = Field(default_factory=utc_now, sa_column=Column(UTCDateTime(), nullable=False))
    payload: dict = Field(sa_column=Column(JSON, nullable=False))


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
