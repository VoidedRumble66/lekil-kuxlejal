"""Deterministic, period-based evaluation of resource production plans."""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

import numpy as np

from .schemas import ConsumerDef, DynamicTemplate


@dataclass
class SimulationResult:
    useful_benefits: Dict[str, np.ndarray]
    produced_benefits: Dict[str, np.ndarray]
    utility: np.ndarray
    demand_deficit: np.ndarray
    critical_deficit: np.ndarray
    reserve_violation: np.ndarray
    infeasible: np.ndarray
    critical_deficits_by_resource: Dict[str, np.ndarray]
    demand_deficits_by_resource: Dict[str, np.ndarray]
    reserve_violations_by_resource: Dict[str, np.ndarray]
    periods: List[Dict[str, Dict[str, np.ndarray]]]
    total_consumed: Dict[str, np.ndarray]
    consumption_penalty: np.ndarray


def _walk_consumers(
    consumers: Dict[str, ConsumerDef], parent_path: str = ""
) -> List[Tuple[str, ConsumerDef]]:
    nodes: List[Tuple[str, ConsumerDef]] = []
    for name, consumer in consumers.items():
        path = f"{parent_path}.{name}" if parent_path else name
        nodes.append((path, consumer))
        nodes.extend(_walk_consumers(consumer.subconsumers, path))
    return nodes


def _effective_resources(template: DynamicTemplate) -> Dict[str, float]:
    values: Dict[str, float] = {}
    for name, resource in template.resources.items():
        impact = sum(
            crisis.intensity * crisis.impact_resource.get(name, 0.0)
            for crisis in template.crisis_factors.values()
        )
        values[name] = max(0.0, resource.value * (1.0 + impact))
    return values


def _decode_fixed_allocations(
    requests: Dict[str, float],
    template: DynamicTemplate,
    mapping: List[Tuple[str, str]],
    pools: Dict[str, np.ndarray],
) -> np.ndarray:
    mapping_indices = {entry: index for index, entry in enumerate(mapping)}
    result = np.zeros((1, len(mapping)))

    def distribute(consumers: Dict[str, ConsumerDef], available: Dict[str, np.ndarray], prefix: str = ""):
        child_pools = {name: {} for name in consumers}
        for resource_name, pool in available.items():
            direct = []
            for name, consumer in consumers.items():
                if resource_name in consumer.requirements:
                    path = f"{prefix}.{name}" if prefix else name
                    direct.append((path, consumer))
            if not direct:
                continue
            desired = np.array([
                max(0.0, requests.get(f"{path}.{resource_name}", 0.0))
                for path, _ in direct
            ])
            total = float(desired.sum())
            factor = min(1.0, float(pool[0]) / total) if total > 0 else 0.0
            for index, (path, _) in enumerate(direct):
                amount = np.array([desired[index] * factor])
                gene_index = mapping_indices[(path, resource_name)]
                result[0, gene_index] = amount[0]
                child_name = path.rsplit(".", 1)[-1]
                child_pools[child_name][resource_name] = amount
        for name, consumer in consumers.items():
            if consumer.subconsumers and child_pools[name]:
                path = f"{prefix}.{name}" if prefix else name
                distribute(consumer.subconsumers, child_pools[name], path)

    distribute(template.consumers, pools)
    return result


def _simulate(
    template: DynamicTemplate,
    mapping: List[Tuple[str, str]],
    gene_population: Optional[np.ndarray] = None,
    fixed_allocations: Optional[Dict[str, float]] = None,
    fixed_preferences: Optional[Dict[str, float]] = None,
    fixed_matrix: Optional[np.ndarray] = None,
) -> SimulationResult:
    """Run one or more plans. Outputs are visible no earlier than the next period."""
    from .genetic_algorithm import decode_to_absolute

    if gene_population is None and fixed_allocations is None and fixed_preferences is None and fixed_matrix is None:
        raise ValueError("Se requiere una población genética o asignaciones fijas.")

    if fixed_preferences is not None:
        gene_population = np.array([[
            min(1.0, max(0.0, fixed_preferences.get(f"{path}.{resource}", 0.0)))
            for path, resource in mapping
        ]])
    pop_size = len(gene_population) if gene_population is not None else (len(fixed_matrix) if fixed_matrix is not None else 1)
    resources = _effective_resources(template)
    inventory = {name: np.full(pop_size, value) for name, value in resources.items()}
    produced = {name: np.zeros(pop_size) for name in template.resources}
    useful = {name: np.zeros(pop_size) for name in template.resources}
    remaining_demand = {
        name: np.full(pop_size, benefit.target_demand)
        for name, benefit in template.benefit_values.items()
    }
    reserve_violation = np.zeros(pop_size)
    reserve_by_resource = {name: np.zeros(pop_size) for name in template.benefit_values}
    utility = np.zeros(pop_size)
    total_consumed = {name: np.zeros(pop_size) for name in template.resources}
    scheduled: Dict[int, Dict[str, np.ndarray]] = {}
    snapshots: List[Dict[str, Dict[str, np.ndarray]]] = []
    mapping_indices = {entry: index for index, entry in enumerate(mapping)}
    nodes = _walk_consumers(template.consumers)
    max_periods = template.max_periods

    for name, benefit in template.benefit_values.items():
        reserve_by_resource[name] += np.maximum(0.0, benefit.minimum_reserve - inventory.get(name, 0.0))

    for period in range(max_periods):
        arrivals = scheduled.pop(period, {})
        for name, amount in arrivals.items():
            inventory[name] = inventory.get(name, np.zeros(pop_size)) + amount
        available_at_start = {name: values.copy() for name, values in inventory.items()}
        operational_pools = {
            name: np.maximum(0.0, values - template.benefit_values.get(name, _ZERO_BENEFIT).minimum_reserve)
            for name, values in inventory.items()
        }

        if gene_population is not None:
            period_allocations = decode_to_absolute(
                gene_population, template, mapping, available_resources=operational_pools
            )
        elif fixed_matrix is not None:
            period_allocations = fixed_matrix.copy()
        else:
            period_allocations = _decode_fixed_allocations(
                fixed_allocations or {}, template, mapping, operational_pools
            )

        root_consumption = {name: np.zeros(pop_size) for name in template.resources}
        period_production = {name: arrivals.get(name, np.zeros(pop_size)).copy() for name in template.resources}
        for path, consumer in nodes:
            operation_level = np.ones(pop_size)
            for resource_name, requirement in consumer.requirements.items():
                gene_index = mapping_indices.get((path, resource_name))
                if gene_index is None:
                    continue
                allocation = period_allocations[:, gene_index]
                if requirement.value > 0:
                    operation_level = np.minimum(operation_level, allocation / requirement.value)
                if "." not in path:
                    root_consumption[resource_name] += allocation
            operation_level = np.clip(operation_level, 0.0, 1.0)

            for resource_name, output in consumer.outputs.items():
                amount = output.amount_per_unit * output.efficiency * operation_level
                if output.max_output is not None:
                    amount = np.minimum(amount, output.max_output)
                produced[resource_name] += amount
                ready_period = period + max(1, output.available_after_periods)
                scheduled.setdefault(ready_period, {}).setdefault(
                    resource_name, np.zeros(pop_size)
                )[:] += amount
        for name, values in root_consumption.items():
            total_consumed[name] += values

        if fixed_allocations is not None:
            for name in template.resources:
                requested = sum(
                    max(0.0, fixed_allocations.get(f"{node_name}.{name}", 0.0))
                    for node_name in template.consumers
                    if name in template.consumers[node_name].requirements
                )
                overdraw = np.maximum(0.0, requested - operational_pools[name])
                reserve_by_resource.setdefault(name, np.zeros(pop_size))[:] += overdraw
        if fixed_allocations is not None:
            for path, consumer in nodes:
                for resource_name in consumer.requirements:
                    direct_children = [
                        (child_path, child)
                        for child_path, child in nodes
                        if child_path.rsplit(".", 1)[0] == path and "." in child_path
                        and resource_name in child.requirements
                    ]
                    child_requested = sum(
                        max(0.0, fixed_allocations.get(f"{child_path}.{resource_name}", 0.0))
                        for child_path, _ in direct_children
                    )
                    parent_requested = max(0.0, fixed_allocations.get(f"{path}.{resource_name}", 0.0))
                    excess = np.full(pop_size, max(0.0, child_requested - parent_requested))
                    reserve_by_resource.setdefault(f"jerarquia:{path}:{resource_name}", np.zeros(pop_size))[:] += excess

        for resource_name, benefit in template.benefit_values.items():
            amount = period_production.get(resource_name, np.zeros(pop_size))
            useful_amount = np.minimum(amount, remaining_demand[resource_name])
            useful[resource_name] += useful_amount
            remaining_demand[resource_name] -= useful_amount
            utility += useful_amount * benefit.unit_value

        next_inventory = {
            name: np.maximum(0.0, inventory[name] - root_consumption[name])
            for name in inventory
        }
        # A declared storage limit caps carry-over stock; with no capacity, only
        # production scheduled for this period is carried to its consumer window.
        for name, benefit in template.benefit_values.items():
            if benefit.storage_capacity is not None:
                next_inventory[name] = np.minimum(next_inventory.get(name, 0.0), benefit.storage_capacity)
            else:
                next_inventory[name] = np.minimum(
                    next_inventory.get(name, 0.0), benefit.minimum_reserve
                )
        inventory = next_inventory

        critical_deficits = {
            name: remaining_demand[name].copy()
            for name, benefit in template.benefit_values.items()
            if benefit.critical
        }
        snapshots.append({
            "available_resources": available_at_start,
            "consumed_resources": root_consumption,
            "produced_resources": period_production,
            "useful_benefits": {name: useful[name].copy() for name in useful},
            "critical_deficits": critical_deficits,
            "ending_inventory": {name: values.copy() for name, values in inventory.items()},
        })

    critical_deficit = np.zeros(pop_size)
    demand_deficit = np.zeros(pop_size)
    critical_by_resource: Dict[str, np.ndarray] = {}
    deficits_by_resource: Dict[str, np.ndarray] = {}
    for name, benefit in template.benefit_values.items():
        demand_deficit += remaining_demand[name]
        deficits_by_resource[name] = remaining_demand[name].copy()
        if benefit.critical:
            critical_by_resource[name] = remaining_demand[name].copy()
            critical_deficit += remaining_demand[name]
    for values in reserve_by_resource.values():
        reserve_violation += values
    consumption_penalty = np.zeros(pop_size)
    for name, amount in total_consumed.items():
        consumption_penalty += 0.1 * amount / max(resources[name], 1.0)
    infeasible = (reserve_violation > 1e-8) | (critical_deficit > 1e-8)
    return SimulationResult(
        useful_benefits=useful,
        produced_benefits=produced,
        utility=utility,
        demand_deficit=demand_deficit,
        critical_deficit=critical_deficit,
        reserve_violation=reserve_violation,
        infeasible=infeasible,
        critical_deficits_by_resource=critical_by_resource,
        demand_deficits_by_resource=deficits_by_resource,
        reserve_violations_by_resource=reserve_by_resource,
        periods=snapshots,
        total_consumed=total_consumed,
        consumption_penalty=consumption_penalty,
    )


class _ZeroBenefit:
    minimum_reserve = 0.0


_ZERO_BENEFIT = _ZeroBenefit()


def simulate_population(
    population: np.ndarray,
    template: DynamicTemplate,
    mapping: List[Tuple[str, str]],
    gene_population: Optional[np.ndarray] = None,
) -> SimulationResult:
    if gene_population is None:
        return _simulate(template, mapping, fixed_matrix=population)
    return _simulate(template, mapping, gene_population=gene_population)


def simulate_fixed_allocations(
    template: DynamicTemplate, allocations: Dict[str, float]
) -> SimulationResult:
    from .genetic_algorithm import build_gene_mapping

    return _simulate(template, build_gene_mapping(template), fixed_allocations=allocations)


def simulate_preferences(
    template: DynamicTemplate, preferences: Dict[str, float]
) -> SimulationResult:
    from .genetic_algorithm import build_gene_mapping

    return _simulate(template, build_gene_mapping(template), fixed_preferences=preferences)
