"""Pasaportes y valoraciones humanas; no son telemetría ni validación agronómica."""

from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
Criterion = Literal['nutrition', 'resources', 'continuity', 'edible', 'culinary', 'resilience']
CRITERIA = {
    'nutrition': ('Nutrición', 25),
    'resources': ('Agua, energía y volumen', 20),
    'continuity': ('Duración y continuidad', 15),
    'edible': ('Fracción comestible y residuos', 15),
    'culinary': ('Valor culinario y emocional', 15),
    'resilience': ('Resiliencia y mantenimiento', 10),
}
DEFAULT_WEIGHTS = {key: value[1] for key, value in CRITERIA.items()}


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


class SeedTest(Input):
    kind: Literal['germination', 'viability']
    result: Text
    tested_on: date | None = None
    method: Text | None = None
    source: Text


class Passport(Input):
    common_name: Name
    scientific_name: Name | None = None
    variety: Name | None = None
    code: Name
    source_kind: Literal['real', 'hypothetical']
    quantity: float | None = Field(default=None, ge=0, le=1_000_000_000)
    unit: Name | None = None
    provenance: Text | None = None
    custodian_entity: Text | None = None
    authorization_status: Literal['pending', 'authorized', 'denied'] = 'pending'
    use_conditions: Text | None = None
    authorization_source: Text | None = None
    received_on: date | None = None
    storage_conditions: Text | None = None
    container: Text | None = None
    location: Text | None = None
    tests: list[SeedTest] = Field(default_factory=list, max_length=100)
    observations: Text | None = None
    information_source: Text | None = None

    @model_validator(mode='after')
    def check_evidence(self):
        if self.quantity is not None and self.unit is None:
            raise ValueError('Una cantidad necesita una unidad documentada.')
        if self.authorization_status != 'pending' and not self.authorization_source:
            raise ValueError('Indica la fuente documental de la autorización o denegación.')
        if self.authorization_status == 'authorized' and not self.use_conditions:
            raise ValueError('Registra las condiciones del uso autorizado.')
        return self


class LotUpdate(Input):
    expected_revision: int = Field(ge=1)
    passport: Passport


class LotRead(Passport):
    id: UUID
    revision: int
    created_at: datetime
    updated_at: datetime


class WeightsInput(Input):
    weights: dict[Criterion, Annotated[float, Field(ge=0, le=100)]]
    responsible: Name
    reason: Text

    @model_validator(mode='after')
    def check_weights(self):
        if set(self.weights) != set(CRITERIA) or abs(sum(self.weights.values()) - 100) > 1e-7:
            raise ValueError('Deben estar los seis criterios y sus pesos deben sumar 100 %.')
        return self


class Score(Input):
    value: float = Field(ge=0, le=5)
    justification: Text
    source: Text


class AssessmentInput(Input):
    expected_revision: int = Field(ge=1)
    weight_profile_id: UUID | None = None
    scores: dict[Criterion, Score | None]
    responsible: Name

    @model_validator(mode='after')
    def all_criteria(self):
        if set(self.scores) != set(CRITERIA):
            raise ValueError('Incluye los seis criterios; usa null para los pendientes.')
        return self


class CompareInput(Input):
    lot_ids: list[UUID] = Field(min_length=2, max_length=20)

    @model_validator(mode='after')
    def unique_lots(self):
        if len(set(self.lot_ids)) != len(self.lot_ids):
            raise ValueError('Cada lote debe aparecer una sola vez.')
        return self


class SeedDecisionInput(Input):
    expected_revision: int = Field(ge=1)
    action: Literal['conservar', 'sembrar', 'retirar', 'repetir_prueba', 'seleccionar']
    responsible: Name
    reason: Text
    comparison: CompareInput | None = None
    comparison_hash: str | None = Field(default=None, pattern=r'^[a-f0-9]{64}$')

    @model_validator(mode='after')
    def selection_context(self):
        if self.action == 'seleccionar':
            if self.comparison is None or self.comparison_hash is None:
                raise ValueError('La selección humana necesita una comparación revisada.')
        elif self.comparison is not None or self.comparison_hash is not None:
            raise ValueError('La comparación corresponde únicamente a una selección humana.')
        return self
