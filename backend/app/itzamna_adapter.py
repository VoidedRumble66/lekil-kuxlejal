"""Adaptación local de Itzamná, sin modificar ni copiar el motor proporcionado.

Itzamná aporta dependencias, simulación, fitness y Pareto. DOMO VITAL añade
entradas energéticas por periodo y validación física explícita. No se importan
los verificadores experimentales de auditoria_2026 ni plantillas de cultivos.
"""

from hashlib import sha256
from importlib import import_module
from itertools import product
from pathlib import Path
import sys

import numpy as np

from .decision_schemas import ScenarioInput

REFERENCE = Path(__file__).resolve().parents[2] / "referencias" / "itzamna_motor"
# Ruta al paquete local exacto, no al repositorio externo ni a su API/frontend.
if str(REFERENCE.parent) not in sys.path:
    sys.path.insert(0, str(REFERENCE.parent))
_core = "itzamna_motor.core"
_previous_bytecode = sys.dont_write_bytecode
try:
    sys.dont_write_bytecode = True  # La referencia se conserva incluso sin cachés generadas.
    DynamicTemplate = import_module(f"{_core}.schemas").DynamicTemplate
    validate_dependency_graph = import_module(f"{_core}.dependencies").validate_dependency_graph
    build_gene_mapping = import_module(f"{_core}.genetic_algorithm").build_gene_mapping
    simulate_fixed_allocations = import_module(f"{_core}.simulation").simulate_fixed_allocations
    evaluate_population = import_module(f"{_core}.fitness").evaluate_population
    pareto_front = import_module(f"{_core}.pareto").pareto_front
finally:
    sys.dont_write_bytecode = _previous_bytecode

EPSILON = 1e-8
ADAPTER_VERSION = "domo-vital-2b-v1"


def engine_fingerprint() -> str:
    digest = sha256(ADAPTER_VERSION.encode())
    for path in sorted((REFERENCE / "core").glob("*.py")):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def validate_allocations(parameters: ScenarioInput, allocations: dict[str, float]) -> None:
    """Rechazo previo: el motor normaliza excesos y no debe ocultar solicitudes inválidas."""
    scale = parameters.period_hours / 24
    expected = {s.key for s in parameters.services}
    if set(allocations) != expected:
        raise ValueError("Las asignaciones deben corresponder exactamente a los servicios declarados.")
    for service in parameters.services:
        amount = allocations[service.key]
        if not np.isfinite(amount) or amount < 0 or amount > service.target_daily_kwh * scale + EPSILON:
            raise ValueError("Asignación negativa, no finita o superior al objetivo del servicio.")
        if service.minimum_daily_kwh is not None and amount + EPSILON < service.minimum_daily_kwh * scale:
            raise ValueError("La asignación no cubre un mínimo declarado.")
    if sum(allocations.values()) > parameters.module_daily_limit_kwh * scale + EPSILON:
        raise ValueError("Los hijos exceden el límite energético del módulo padre.")


def evaluate_plan(parameters: ScenarioInput, allocations: dict[str, float]) -> dict:
    validate_allocations(parameters, allocations)
    scale = parameters.period_hours / 24
    inventory = parameters.initial_energy_kwh
    consumed = sum(allocations.values())
    periods = []
    fitness = 0.0
    for index, daily_generation in enumerate(parameters.generation_daily_kwh, 1):
        gross = daily_generation * scale
        generation = gross * (1 - parameters.generation_reduction)
        uncapped = inventory + generation
        curtailed = max(0.0, uncapped - parameters.storage_capacity_kwh)
        available = uncapped - curtailed
        if consumed > available - parameters.protected_reserve_kwh + EPSILON:
            raise ValueError(f"Energía o reserva insuficiente en el periodo {index}.")
        template = DynamicTemplate(
            template_id="domo-vital-hipotetico", name="Supuestos energéticos", description=ADAPTER_VERSION,
            max_periods=1, resources={"ENERGIA": {"value": available}},
            # El recorte ya se aplicó a generación; nunca al inventario ni al motor.
            crisis_factors={},
            benefit_values={"ENERGIA": {"unit_value": 0, "minimum_reserve": parameters.protected_reserve_kwh,
                                         "storage_capacity": parameters.storage_capacity_kwh}},
            consumers={"modulo": {
                "priority_weight": 1,
                "requirements": {"ENERGIA": {"value": parameters.module_daily_limit_kwh * scale}},
                "subconsumers": {s.key: {
                    "priority_weight": s.priority,
                    "requirements": {"ENERGIA": {"value": s.target_daily_kwh * scale}},
                } for s in parameters.services},
            }},
        )
        validate_dependency_graph(template)
        absolute = {"modulo.ENERGIA": consumed, **{
            f"modulo.{key}.ENERGIA": amount for key, amount in allocations.items()
        }}
        simulation = simulate_fixed_allocations(template, absolute)
        mapping = build_gene_mapping(template)
        matrix = np.array([[absolute[f"{path}.{resource}"] for path, resource in mapping]])
        scores, feasible = evaluate_population(matrix, template, mapping)
        ending = float(simulation.periods[0]["ending_inventory"]["ENERGIA"][0])
        engine_consumed = float(simulation.total_consumed["ENERGIA"][0])
        if (not feasible[0] or simulation.infeasible[0] or ending < -EPSILON
                or ending > parameters.storage_capacity_kwh + EPSILON
                or ending + EPSILON < parameters.protected_reserve_kwh
                or abs(engine_consumed - consumed) > EPSILON
                or abs(inventory + generation - curtailed - consumed - ending) > EPSILON):
            raise ValueError(f"Balance físico o jerarquía inválida en el periodo {index}.")
        periods.append({
            "period": index, "hours": parameters.period_hours, "initial_kwh": inventory,
            "gross_generation_kwh": gross, "reduced_generation_kwh": generation,
            "generation_cut_kwh": gross - generation, "curtailed_kwh": curtailed,
            "available_kwh": available, "consumption_kwh": consumed, "ending_kwh": ending,
            "protected_reserve_kwh": parameters.protected_reserve_kwh, "allocations_kwh": allocations,
        })
        inventory = ending
        fitness += float(scores[0])
    return {"allocations_kwh": allocations, "periods": periods, "fitness": fitness / parameters.periods,
            "total_consumption_kwh": consumed * parameters.periods,
            "total_curtailed_kwh": sum(p["curtailed_kwh"] for p in periods), "ending_kwh": inventory}


def compare(parameters: ScenarioInput) -> dict:
    scale = parameters.period_hours / 24
    # Malla reproducible acotada: mínimos exactos y tres niveles hasta el objetivo.
    levels = [sorted(set(float(x) * scale for x in np.linspace(
        s.minimum_daily_kwh or 0, s.target_daily_kwh, 4))) for s in parameters.services]
    feasible, rejected = [], {}
    for values in product(*levels):
        allocations = dict(zip((s.key for s in parameters.services), values))
        try:
            feasible.append(evaluate_plan(parameters, allocations))
        except ValueError as error:
            message = str(error)
            rejected[message] = rejected.get(message, 0) + 1
    complete_minima = all(s.minimum_daily_kwh is not None for s in parameters.services)
    result = {
        "status": "feasible" if feasible else "infeasible", "source": "hypothetical", "unit": "kWh",
        "attribution": "Itzamná · núcleo local proporcionado; adaptación energética DOMO VITAL",
        "adapter_version": ADAPTER_VERSION,
        "agricultural_status": ("Mínimos declarados cubiertos; sin validación agronómica" if feasible
                                else "Sin alternativa que cubra los mínimos declarados; sin validación agronómica")
                               if complete_minima else "Factibilidad agrícola no evaluada",
        "search": {"evaluated": len(feasible) + sum(rejected.values()), "feasible": len(feasible),
                   "pareto": 0, "method": "Malla determinista: 4 niveles por servicio, incluidos mínimo y objetivo."},
        "constraints": [
            "Factibilidad energética respecto de supuestos; no demuestra supervivencia ni rendimiento agrícola.",
            "Generación diaria × horas/24 × (1 − recorte), acreditada al inicio de cada periodo.",
            "El almacenamiento limita la entrada; el excedente se registra como vertido, no como energía almacenada.",
            "Consumo de hijos ≤ límite del módulo; no se cuenta dos veces el consumo padre/hijos.",
            "Reserva protegida en cada cierre; no hay potencia instantánea, horario solar ni pérdidas de conversión modeladas.",
            "Asignación constante por periodo; búsqueda acotada, sin garantía de óptimo continuo.",
        ],
        "rejections": [{"reason": message, "count": count} for message, count in sorted(rejected.items())],
        "alternatives": [],
    }
    if not feasible:
        return result
    # Pareto maximiza cobertura de cada servicio y saldo final: compromisos explícitos.
    objectives = np.array([[*(plan["allocations_kwh"][s.key] / (s.target_daily_kwh * scale)
                             if s.target_daily_kwh else 1 for s in parameters.services),
                            plan["ending_kwh"] / max(parameters.storage_capacity_kwh, 1)] for plan in feasible])
    front = np.flatnonzero(pareto_front(objectives)).tolist()
    result["search"]["pareto"] = len(front)
    selected = [max(front, key=lambda i: feasible[i]["fitness"])]
    while len(selected) < min(3, len(front)):
        others = [i for i in front if i not in selected]
        # Diversidad entre alternativas reales de la frontera, sin relleno ficticio.
        selected.append(max(others, key=lambda i: min(float(np.linalg.norm(objectives[i] - objectives[j])) for j in selected)))
    for number, index in enumerate(selected, 1):
        plan = feasible[index]
        plan.update({"id": f"alternativa_{number}", "label": f"Alternativa {number}", "feasible": True,
                     "justification": "No dominada en cobertura de servicios y reserva final. "
                     + ("Mayor fitness Itzamná entre los candidatos factibles." if number == 1 else "Compromiso distinto de cobertura y reserva frente a las otras alternativas."),
                     "unmet_target_kwh": {s.key: max(0.0, s.target_daily_kwh * scale - plan["allocations_kwh"][s.key])
                                          for s in parameters.services}})
        result["alternatives"].append(plan)
    return result
