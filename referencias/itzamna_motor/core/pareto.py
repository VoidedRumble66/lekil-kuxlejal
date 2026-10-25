import numpy as np
from typing import List, Dict, Tuple
from .schemas import ParetoScenario, DynamicTemplate

def pareto_front(objectives: np.ndarray) -> np.ndarray:
    """Return the non-dominated candidates for objectives to MAXIMIZE.

    A candidate is dominated when another is at least as good in every
    objective and strictly better in at least one. Ties are non-dominated.
    This calculation must not depend on the order of candidates.
    """
    scores = np.asarray(objectives, dtype=float)
    if scores.ndim != 2:
        raise ValueError("Los objetivos de Pareto deben formar una matriz bidimensional.")
    if not np.isfinite(scores).all():
        raise ValueError("Los objetivos de Pareto deben ser finitos.")

    non_dominated = np.ones(len(scores), dtype=bool)
    for i in range(len(scores)):
        better_or_equal = np.all(scores >= scores[i], axis=1)
        strictly_better = np.any(scores > scores[i], axis=1)
        non_dominated[i] = not np.any(better_or_equal & strictly_better)
    return non_dominated

def extract_archetypes(
    population: np.ndarray,
    fitness: np.ndarray,
    objectives: np.ndarray,
    template: DynamicTemplate,
    mapping: List[Tuple[str, str]],
    feasible_mask: np.ndarray | None = None,
    simulation=None,
) -> List[ParetoScenario]:
    eligible = np.arange(len(population)) if feasible_mask is None else np.flatnonzero(feasible_mask)
    if len(eligible) == 0:
        return _unavailable_scenarios(template, mapping)
    eligible_objectives = objectives[eligible]
    front_mask = pareto_front(eligible_objectives)
    front_indices = eligible[front_mask]
    front_objectives = eligible_objectives[front_mask]

    if len(front_indices) == 0:
        return _unavailable_scenarios(template, mapping)

    # Decode genes to absolute allocations for the UI
    from .genetic_algorithm import decode_to_absolute
    abs_pop = decode_to_absolute(population, template, mapping)

    # Calculate distances to utopian point to find a balanced one
    utopian = np.max(front_objectives, axis=0)
    distances = np.linalg.norm(front_objectives - utopian, axis=1)
    
    candidates = [
        int(front_indices[np.argmax(front_objectives[:, 0])]),
        int(front_indices[np.argmax(front_objectives[:, -1])]),
        int(front_indices[np.argmin(distances)]),
    ]
    unique_indices: List[int] = []
    for index in candidates + [int(item) for item in front_indices]:
        if index not in unique_indices:
            unique_indices.append(index)
        if len(unique_indices) == 3:
            break
    
    first_label = mapping[0][0].replace('_', ' ').title() if mapping else "Producción"
    last_label = mapping[-1][0].replace('_', ' ').title() if mapping else "Producción"
    labels = ["Prioridad " + first_label,
              "Prioridad " + last_label,
              "Balance Sistémico"]

    archetypes = []
    for i in range(3):
        if i < len(unique_indices):
            idx = unique_indices[i]
            ind = abs_pop[idx] # Use absolute allocations
            fit = fitness[idx]
            
            allocations = {}
            allocation_preferences = {}
            for j, (node_path, r_name) in enumerate(mapping):
                allocations[f"{node_path}.{r_name}"] = float(ind[j])
                allocation_preferences[f"{node_path}.{r_name}"] = float(population[idx, j])
                
            archetypes.append(ParetoScenario(
                scenario_id=f"escenario_{i}",
                label=labels[i] if i < len(labels) else f"Variante {i}",
                allocations=allocations,
                allocation_preferences=allocation_preferences,
                fitness_score=float(fit),
                pareto_rank=1,
                feasible=True,
                useful_benefits={
                    name: float(values[idx])
                    for name, values in (simulation.useful_benefits.items() if simulation else [])
                },
                demand_deficits={
                    name: float(values[idx])
                    for name, values in (simulation.demand_deficits_by_resource.items() if simulation else [])
                    if values[idx] > 1e-8
                },
                critical_deficits={
                    name: float(values[idx])
                    for name, values in (simulation.critical_deficits_by_resource.items() if simulation else [])
                },
                reserve_violations={
                    name: float(values[idx])
                    for name, values in (simulation.reserve_violations_by_resource.items() if simulation else [])
                    if values[idx] > 1e-8
                },
                periods=[
                    {
                        "period": period_index,
                        **{
                            field: {name: float(values[idx]) for name, values in snapshot[field].items()}
                            for field in ("available_resources", "consumed_resources", "produced_resources", "useful_benefits", "critical_deficits", "ending_inventory")
                        },
                    }
                    for period_index, snapshot in enumerate(simulation.periods)
                ] if simulation else [],
            ))
        else:
            archetypes.append(_unavailable_scenario(template, mapping))
            
    return archetypes

def _unavailable_scenario(template: DynamicTemplate, mapping: List[Tuple[str, str]]) -> ParetoScenario:
    allocations = {}
    for node_path, r_name in mapping:
        allocations[f"{node_path}.{r_name}"] = 0.0
        
    return ParetoScenario(
        scenario_id="unavailable",
        label="No disponible",
        allocations=allocations,
        fitness_score=0.0,
        pareto_rank=0,
        feasible=False,
    )

def _unavailable_scenarios(template: DynamicTemplate, mapping: List[Tuple[str, str]]) -> List[ParetoScenario]:
    return [_unavailable_scenario(template, mapping) for _ in range(3)]
