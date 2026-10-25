from pydantic import BaseModel, Field, field_validator
from typing import Any, Dict, List, Optional

class ResourceDef(BaseModel):
    value: float = Field(..., ge=0.0)

class RequirementDef(BaseModel):
    value: float = Field(..., ge=0.0)

class OutputDef(BaseModel):
    amount_per_unit: float = Field(..., ge=0.0)
    efficiency: float = Field(1.0, ge=0.0, le=1.0)
    max_output: Optional[float] = Field(None, ge=0.0)
    available_after_periods: int = Field(1, ge=0)

class BenefitValueDef(BaseModel):
    unit_value: float = Field(..., ge=0.0)
    target_demand: float = Field(0.0, ge=0.0)
    critical: bool = False
    minimum_reserve: float = Field(0.0, ge=0.0)
    storage_capacity: Optional[float] = Field(None, ge=0.0)

class ConsumerDef(BaseModel):
    requirements: Dict[str, RequirementDef] = Field(default_factory=dict)
    priority_weight: float = Field(..., ge=0.0, le=1.0)
    outputs: Dict[str, OutputDef] = Field(default_factory=dict)
    subconsumers: Dict[str, 'ConsumerDef'] = Field(default_factory=dict)

class CrisisDef(BaseModel):
    name: str
    description: str
    intensity: float = Field(0.0, ge=0.0, le=1.0)
    impact_resource: Dict[str, float] = Field(default_factory=dict) # e.g. "OXIGENO_L": -0.5 meaning -50% at full intensity

class DynamicTemplate(BaseModel):
    template_id: str
    name: str
    description: str
    crisis_factors: Dict[str, CrisisDef] = Field(default_factory=dict)
    resources: Dict[str, ResourceDef]
    consumers: Dict[str, ConsumerDef]
    benefit_values: Dict[str, BenefitValueDef] = Field(default_factory=dict)
    max_periods: int = Field(5, ge=1, le=100)
    
    population_size: int = Field(100, ge=10)
    max_generations: int = Field(200, ge=1)
    emit_every_n: int = Field(5, ge=1)
    mutation_rate: float = Field(0.1, ge=0.0, le=1.0)
    mutation_strength: float = Field(0.1, ge=0.0, le=1.0)
    crossover_rate: float = Field(1.0, ge=0.0, le=1.0)
    elitism_count: int = Field(1, ge=1)
    tournament_size: int = Field(2, ge=2)


class PlanEvaluationRequest(BaseModel):
    template: DynamicTemplate
    preferences: Dict[str, float] = Field(default_factory=dict)

    @field_validator("preferences")
    @classmethod
    def validate_preferences(cls, preferences):
        if any(not 0.0 <= value <= 1.0 for value in preferences.values()):
            raise ValueError("Las preferencias de asignación deben estar entre 0 y 1.")
        return preferences

class ParetoScenario(BaseModel):
    scenario_id: str
    label: str
    allocations: Dict[str, float] # Changed to a single flat dict for simplicity or keep hierarchical
    allocation_preferences: Dict[str, float] = Field(default_factory=dict)
    fitness_score: float
    pareto_rank: int
    feasible: bool = True
    useful_benefits: Dict[str, float] = Field(default_factory=dict)
    demand_deficits: Dict[str, float] = Field(default_factory=dict)
    critical_deficits: Dict[str, float] = Field(default_factory=dict)
    reserve_violations: Dict[str, float] = Field(default_factory=dict)
    periods: List[Dict[str, Any]] = Field(default_factory=list)

class SSEPayload(BaseModel):
    generation: int
    avg_fitness: float
    max_fitness: float
    top3: List[ParetoScenario]
    is_final: bool
    viable_count: int
    weights_normalized: bool = False
    period: Optional[int] = None
    available_resources: Dict[str, float] = Field(default_factory=dict)
    consumed_resources: Dict[str, float] = Field(default_factory=dict)
    produced_resources: Dict[str, float] = Field(default_factory=dict)
    useful_benefits: Dict[str, float] = Field(default_factory=dict)
    demand_deficits: Dict[str, float] = Field(default_factory=dict)
    critical_deficits: Dict[str, float] = Field(default_factory=dict)
    reserve_violations: Dict[str, float] = Field(default_factory=dict)
    dependency_status: Dict[str, str] = Field(default_factory=dict)
