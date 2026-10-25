import numpy as np
from typing import Tuple, List, Dict, Any
from .schemas import DynamicTemplate, ConsumerDef
from .simulation import SimulationResult, simulate_population


def _simulation_penalty(simulation: SimulationResult, template: DynamicTemplate) -> np.ndarray:
    penalty = np.zeros(len(simulation.utility))
    critical_demand = sum(
        value.target_demand
        for value in template.benefit_values.values()
        if value.critical
    )
    minimum_reserve = sum(
        value.minimum_reserve
        for value in template.benefit_values.values()
    )
    total_demand = sum(value.target_demand for value in template.benefit_values.values())
    if total_demand > 0:
        penalty += (simulation.demand_deficit / total_demand) * 0.5
    if critical_demand > 0:
        penalty += (simulation.critical_deficit / critical_demand) * 2.0
    if minimum_reserve > 0:
        penalty += (simulation.reserve_violation / minimum_reserve) * 2.0
    penalty += simulation.consumption_penalty
    return penalty

def _evaluate_node(
    consumers: Dict[str, ConsumerDef],
    population: np.ndarray,
    mapping: List[Tuple[str, str]],
    parent_allocations: Dict[str, np.ndarray],
    parent_path: str = "",
    inherited_priority: float = 1.0
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Dict[str, np.ndarray]]:
    """
    Returns:
    - total_fitness: np.ndarray
    - penalty: np.ndarray
    - viable_mask: np.ndarray
    - node_allocations: Dict[str, np.ndarray] of allocations at this level, to be used by parent constraint.
    """
    pop_size = len(population)
    total_fitness = np.zeros(pop_size)
    total_penalty = np.zeros(pop_size)
    viable_mask = np.ones(pop_size, dtype=bool)
    
    # Track allocations at this level for each resource to return to parent
    level_allocations = {}
    
    for c_name, consumer in consumers.items():
        current_path = f"{parent_path}.{c_name}" if parent_path else c_name
        effective_priority = inherited_priority * consumer.priority_weight
        
        c_fitness = np.ones(pop_size)
        node_res_allocations = {}
        
        for r_name, req in consumer.requirements.items():
            gene_idx = mapping.index((current_path, r_name))
            allocated = population[:, gene_idx]
            req_val = req.value
            coverage = np.minimum(1.0, allocated / req_val) if req_val > 0 else np.ones(pop_size)
            c_fitness *= coverage
            
            node_res_allocations[r_name] = allocated
            if r_name not in level_allocations:
                level_allocations[r_name] = np.zeros(pop_size)
            level_allocations[r_name] += allocated
            
        total_fitness += effective_priority * c_fitness
        
        # Evaluate children
        if consumer.subconsumers:
            child_fitness, child_penalty, child_viable, child_allocations = _evaluate_node(
                consumer.subconsumers,
                population,
                mapping,
                node_res_allocations,
                current_path,
                effective_priority
            )
            total_fitness += child_fitness
            total_penalty += child_penalty
            viable_mask &= child_viable
            
            # Constraint: child allocations sum <= parent allocation for each resource
            for r_name, c_alloc_sum in child_allocations.items():
                p_alloc = node_res_allocations.get(r_name, np.zeros(pop_size))
                excess = np.maximum(0, c_alloc_sum - p_alloc)
                # Penalize excess, weighted
                p_max = p_alloc.copy()
                p_max[p_max == 0] = 1.0 # avoid div by zero in penalty
                total_penalty += (excess / p_max) * 2.0
                viable_mask &= (c_alloc_sum <= p_alloc)

    return total_fitness, total_penalty, viable_mask, level_allocations


def evaluate_population(
    population: np.ndarray,
    template: DynamicTemplate,
    mapping: List[Tuple[str, str]],
    gene_population: np.ndarray | None = None,
) -> Tuple[np.ndarray, np.ndarray]:
    pop_size = len(population)
    
    # 1. Apply crisis factors to resources
    resource_maxes = {}
    for r_name, r_def in template.resources.items():
        base_val = r_def.value
        # Calculate impact from all active crises
        total_impact = 0.0
        for crisis in template.crisis_factors.values():
            if r_name in crisis.impact_resource:
                total_impact += crisis.intensity * crisis.impact_resource[r_name]
        
        # apply impact (e.g., -0.5 means -50% reduction)
        effective_val = base_val * (1.0 + total_impact)
        resource_maxes[r_name] = max(0.0, effective_val)
    
    # 2. Evaluate hierarchy
    total_fitness, total_penalty, viable_mask, top_level_allocations = _evaluate_node(
        template.consumers, population, mapping, {}
    )
    
    # 3. Global constraint on top level allocations
    for r_name, alloc_sum in top_level_allocations.items():
        max_val = resource_maxes.get(r_name, 0.0)
        if max_val > 0:
            excess = np.maximum(0, alloc_sum - max_val)
            total_penalty += (excess / max_val) * 2.0
            viable_mask &= (alloc_sum <= max_val)
        else:
            # If max_val is 0, any allocation > 0 is excess
            excess = alloc_sum
            total_penalty += excess * 2.0
            viable_mask &= (alloc_sum <= 0)

    if template.benefit_values:
        simulation = simulate_population(population, template, mapping, gene_population)
        total_penalty += _simulation_penalty(simulation, template)
        total_fitness += simulation.utility
        viable_mask &= ~simulation.infeasible

    fitness = total_fitness - total_penalty
    # Hard safety and critical-demand violations are never rescued by utility.
    if template.benefit_values:
        fitness = np.where(viable_mask, fitness, -1_000_000.0 - total_penalty)
    return fitness, viable_mask


def evaluate_fixed_preferences(template: DynamicTemplate, preferences: Dict[str, float]):
    """Return a single auditable score for a complete global branch."""
    from .genetic_algorithm import build_gene_mapping, decode_to_absolute

    mapping = build_gene_mapping(template)
    genes = np.zeros((1, len(mapping)))
    for index, (path, resource) in enumerate(mapping):
        genes[0, index] = min(1.0, max(0.0, preferences.get(f"{path}.{resource}", 0.0)))
    fixed = decode_to_absolute(genes, template, mapping)
    if not template.benefit_values:
        scores, feasible = evaluate_population(fixed, template, mapping)
        return float(scores[0]), bool(feasible[0]), {
            "useful_benefits": {}, "demand_deficits": {}, "critical_deficits": {}, "reserve_violations": {}, "periods": []
        }

    simulation = simulate_population(fixed, template, mapping, gene_population=genes)
    details = {
        "useful_benefits": {name: float(values[0]) for name, values in simulation.useful_benefits.items()},
        "critical_deficits": {
            name: float(values[0]) for name, values in simulation.critical_deficits_by_resource.items()
        },
        "demand_deficits": {
            name: float(values[0]) for name, values in simulation.demand_deficits_by_resource.items()
        },
        "reserve_violations": {
            name: float(values[0]) for name, values in simulation.reserve_violations_by_resource.items()
            if values[0] > 1e-8
        },
        "periods": [
            {
                "period": index,
                **{
                    field: {name: float(values[0]) for name, values in snapshot[field].items()}
                    for field in ("available_resources", "consumed_resources", "produced_resources", "useful_benefits", "critical_deficits", "ending_inventory")
                },
            }
            for index, snapshot in enumerate(simulation.periods)
        ],
    }
    # Use the same hierarchical coverage, simulation penalties, and feasibility
    # rules as the genetic evolution. A global branch must be comparable with
    # a candidate evaluated by the evolutionary algorithm.
    scores, viable = evaluate_population(fixed, template, mapping, gene_population=genes)
    return float(scores[0]), bool(viable[0]), details


def _get_objectives_node(
    consumers: Dict[str, ConsumerDef],
    population: np.ndarray,
    mapping: List[Tuple[str, str]],
    parent_path: str = "",
    inherited_priority: float = 1.0
) -> List[np.ndarray]:
    """Returns a list of objectives for consumers recursively."""
    pop_size = len(population)
    objs = []
    
    for c_name, consumer in consumers.items():
        current_path = f"{parent_path}.{c_name}" if parent_path else c_name
        effective_priority = inherited_priority * consumer.priority_weight
        
        c_fitness = np.ones(pop_size)
        for r_name, req in consumer.requirements.items():
            gene_idx = mapping.index((current_path, r_name))
            allocated = population[:, gene_idx]
            req_val = req.value
            coverage = np.minimum(1.0, allocated / req_val) if req_val > 0 else np.ones(pop_size)
            c_fitness *= coverage
            
        objs.append(effective_priority * c_fitness)
        
        if consumer.subconsumers:
            objs.extend(_get_objectives_node(
                consumer.subconsumers,
                population,
                mapping,
                current_path,
                effective_priority
            ))
            
    return objs


def get_objectives(
    population: np.ndarray,
    template: DynamicTemplate,
    mapping: List[Tuple[str, str]],
    gene_population: np.ndarray | None = None,
    feasible_mask: np.ndarray | None = None,
) -> np.ndarray:
    pop_size = len(population)
    
    # 1. Apply crisis factors to resources
    resource_maxes = {}
    for r_name, r_def in template.resources.items():
        base_val = r_def.value
        total_impact = 0.0
        for crisis in template.crisis_factors.values():
            if r_name in crisis.impact_resource:
                total_impact += crisis.intensity * crisis.impact_resource[r_name]
        resource_maxes[r_name] = max(0.0, base_val * (1.0 + total_impact))
    
    # 2. Get global penalties
    total_penalty = np.zeros(pop_size)
    _, penalty_hierarchy, _, top_level_allocations = _evaluate_node(template.consumers, population, mapping, {})
    total_penalty += penalty_hierarchy
    
    for r_name, alloc_sum in top_level_allocations.items():
        max_val = resource_maxes.get(r_name, 0.0)
        if max_val > 0:
            excess = np.maximum(0, alloc_sum - max_val)
            total_penalty += (excess / max_val) * 2.0
        else:
            total_penalty += alloc_sum * 2.0
            
    # 3. Get objectives
    objs_list = _get_objectives_node(template.consumers, population, mapping)

    if template.benefit_values:
        simulation = simulate_population(population, template, mapping, gene_population)
        for resource_name, value in template.benefit_values.items():
            if value.unit_value > 0:
                objs_list.append(
                    simulation.useful_benefits[resource_name] * value.unit_value
                )
        for resource_name, consumed in simulation.total_consumed.items():
            capacity = max(template.resources[resource_name].value * template.max_periods, 1.0)
            objs_list.append(1.0 - np.minimum(1.0, consumed / capacity))
        total_penalty += _simulation_penalty(simulation, template)
    
    if not objs_list:
        return np.zeros((pop_size, 1))
        
    objs = np.column_stack(objs_list)
    # Apply penalty to all objectives
    objs = objs - total_penalty[:, np.newaxis]
    if feasible_mask is not None:
        objs[~feasible_mask] = -1_000_000.0
    return objs
