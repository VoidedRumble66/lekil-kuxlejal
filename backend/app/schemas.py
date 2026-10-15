"""Contratos públicos: validación estricta y estados controlados por el servidor."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
Purpose = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
Description = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
DeviceModel = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
SerialPort = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=128)]


class StrictInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ZoneCreate(StrictInput):
    name: Name
    purpose: Purpose
    description: Description | None = None


class ZoneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    purpose: str
    description: str | None
    created_at: AwareDatetime


class DeviceCreate(StrictInput):
    name: Name
    model: DeviceModel | None = None
    serial_port: SerialPort | None = None


class DeviceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    kind: Literal["esp32-s3"]
    model: str | None
    serial_port: str | None
    status: Literal["not_configured"]
    created_at: AwareDatetime
    last_seen_at: AwareDatetime | None


class MeasurementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    source: Literal["real"]
    zone_id: UUID
    device_id: UUID
    quantity: str
    unit: str
    value: float = Field(allow_inf_nan=False)
    quality: Literal["valid", "invalid", "unverified"]
    measured_at: AwareDatetime
    recorded_at: AwareDatetime
    observations: str | None


class TelemetryRead(BaseModel):
    items: list[MeasurementRead]
    total: int
    source: Literal["real"] = "real"
    queried_at: AwareDatetime


class HealthRead(BaseModel):
    status: Literal["ok", "error"]
    database: Literal["connected", "unavailable"]
    mode: Literal["observation"] = "observation"
    control_enabled: Literal[False] = False
    timestamp: AwareDatetime
