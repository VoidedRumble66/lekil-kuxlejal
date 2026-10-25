from collections import defaultdict
from typing import Dict, Iterable, List, Set, Tuple

from .schemas import ConsumerDef, DynamicTemplate


class DependencyValidationError(ValueError):
    """Raised when a production template cannot be evaluated safely."""

    def __init__(self, message: str, code: str = "invalid_dependency"):
        super().__init__(message)
        self.code = code


def _walk_consumers(
    consumers: Dict[str, ConsumerDef],
    parent_path: str = "",
) -> Iterable[Tuple[str, ConsumerDef]]:
    for name, consumer in consumers.items():
        path = f"{parent_path}.{name}" if parent_path else name
        yield path, consumer
        yield from _walk_consumers(consumer.subconsumers, path)


def validate_dependency_graph(template: DynamicTemplate) -> None:
    """Validate resource production dependencies before starting optimization."""
    nodes = dict(_walk_consumers(template.consumers))
    producers: Dict[str, List[str]] = defaultdict(list)

    for path, consumer in nodes.items():
        for resource_name in consumer.requirements:
            if resource_name not in template.resources:
                raise DependencyValidationError(
                    f"El nodo {path.replace('_', ' ').title()} consume el recurso inexistente {resource_name.replace('_', ' ').title()}.",
                    "unknown_input_resource",
                )

        for resource_name in consumer.outputs:
            if resource_name not in template.resources:
                raise DependencyValidationError(
                    f"El nodo {path.replace('_', ' ').title()} produce el recurso inexistente {resource_name.replace('_', ' ').title()}.",
                    "unknown_output_resource",
                )
            if resource_name not in template.benefit_values:
                raise DependencyValidationError(
                    f"El output {resource_name.replace('_', ' ').title()} del nodo {path.replace('_', ' ').title()} no tiene una valoración definida.",
                    "missing_benefit_value",
                )
            producers[resource_name].append(path)

    for resource_name in template.benefit_values:
        if resource_name not in template.resources:
            raise DependencyValidationError(
                f"La valoración referencia el recurso inexistente {resource_name.replace('_', ' ').title()}.",
                "unknown_benefit_resource",
            )
        benefit = template.benefit_values[resource_name]
        if benefit.minimum_reserve > template.resources[resource_name].value:
            raise DependencyValidationError(
                f"La reserva mínima de {resource_name.replace('_', ' ').title()} supera el inventario inicial.",
                "invalid_reserve",
            )
        if benefit.storage_capacity is not None and benefit.storage_capacity < benefit.minimum_reserve:
            raise DependencyValidationError(
                f"La capacidad de almacenamiento de {resource_name.replace('_', ' ').title()} es menor que su reserva mínima.",
                "invalid_reserve",
            )

    graph: Dict[str, Set[str]] = defaultdict(set)
    for consumer_path, consumer in nodes.items():
        for resource_name in consumer.requirements:
            for producer_path in producers.get(resource_name, []):
                graph[producer_path].add(consumer_path)

    visiting: Set[str] = set()
    visited: Set[str] = set()

    def visit(path: str, trail: List[str]) -> None:
        if path in visiting:
            cycle_start = trail.index(path)
            cycle = trail[cycle_start:] + [path]
            raise DependencyValidationError(
                "Dependencia circular detectada: " + " -> ".join(cycle),
                "dependency_cycle",
            )
        if path in visited:
            return

        visiting.add(path)
        for child_path in sorted(graph.get(path, set())):
            visit(child_path, trail + [path])
        visiting.remove(path)
        visited.add(path)

    for path in nodes:
        visit(path, [])
