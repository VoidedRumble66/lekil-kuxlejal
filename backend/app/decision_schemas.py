"""Contratos de supuestos hipotéticos, separados de la instrumentación."""

from typing import Annotated, Literal
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
Energy = Annotated[float, Field(ge=0, le=1_000_000, allow_inf_nan=False)]


class StrictInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class ServiceAssumption(StrictInput):
    key: str = Field(pattern=r"^[a-z][a-z0-9_]{0,31}$")
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
    target_daily_kwh: Energy
    priority: float = Field(ge=0, le=1)
    minimum_daily_kwh: Energy | None = None
    minimum_basis: Text | None = None

    @model_validator(mode="after")
    def check_minimum(self):
        if self.minimum_daily_kwh is not None:
            if self.minimum_daily_kwh > self.target_daily_kwh:
                raise ValueError("El mínimo declarado no puede superar el objetivo del servicio.")
            if not self.minimum_basis:
                raise ValueError("Todo mínimo declarado necesita procedencia y contexto agrícola.")
        elif self.minimum_basis is not None:
            raise ValueError("La procedencia requiere un mínimo declarado.")
        return self


class ScenarioInput(StrictInput):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
    assumptions: Text
    periods: int = Field(default=5, ge=1, le=30)
    period_hours: float = Field(default=24, gt=0, le=168)
    generation_reduction: float = Field(default=0.4, ge=0, le=1)
    initial_energy_kwh: Energy
    storage_capacity_kwh: Energy
    protected_reserve_kwh: Energy
    generation_daily_kwh: list[Energy] = Field(min_length=1, max_length=30)
    module_daily_limit_kwh: Energy
    services: list[ServiceAssumption] = Field(min_length=1, max_length=4)

    @model_validator(mode="after")
    def check_scenario(self):
        if len(self.generation_daily_kwh) != self.periods:
            raise ValueError("Indica una generación diaria hipotética para cada periodo.")
        if not self.protected_reserve_kwh <= self.initial_energy_kwh <= self.storage_capacity_kwh:
            raise ValueError("Se requiere reserva ≤ energía inicial ≤ capacidad de almacenamiento.")
        if len({s.key for s in self.services}) != len(self.services):
            raise ValueError("Las claves de los servicios deben ser únicas.")
        return self


class ReviewInput(StrictInput):
    alternative_id: str = Field(pattern=r"^alternativa_[1-3]$")
    decision: Literal["approved", "rejected"]
    responsible: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
    reason: Text


class ReviewRead(ReviewInput):
    id: UUID
    run_id: UUID
    created_at: datetime


class RunRead(BaseModel):
    id: UUID
    created_at: datetime
    source: Literal["hypothetical"]
    parameters: ScenarioInput
    result: dict
    engine_fingerprint: str
    snapshot_sha256: str
    reviews: list[ReviewRead]


class RunSummary(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    status: str
    alternative_count: int
