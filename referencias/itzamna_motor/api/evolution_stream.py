import asyncio
from fastapi import APIRouter, Request, HTTPException
from sse_starlette.sse import EventSourceResponse
from core.schemas import DynamicTemplate, PlanEvaluationRequest, SSEPayload
from core.dependencies import DependencyValidationError, validate_dependency_graph
from core.genetic_algorithm import GeneticAlgorithm
from core.pareto import extract_archetypes
from core.fitness import get_objectives
from core.genetic_algorithm import decode_to_absolute
from core.simulation import simulate_population
from core.fitness import evaluate_fixed_preferences
from core.templates import get_templates

router = APIRouter()

# Global state for active template
active_template: DynamicTemplate = get_templates()[0]


def _walk_for_status(template: DynamicTemplate):
    def walk(consumers, prefix=""):
        for name, consumer in consumers.items():
            path = f"{prefix}.{name}" if prefix else name
            yield path, consumer
            yield from walk(consumer.subconsumers, path)
    return walk(template.consumers)

@router.post("/scenarios/active")
async def set_active_template(template: DynamicTemplate):
    global active_template
    try:
        validate_dependency_graph(template)
    except DependencyValidationError as error:
        raise HTTPException(
            status_code=422,
            detail={"code": error.code, "message": str(error)},
        ) from error
    active_template = template
    return {"status": "ok", "template_id": active_template.template_id}

@router.get("/scenarios/templates")
async def list_templates():
    return [t.model_dump() for t in get_templates()]


@router.post("/scenarios/evaluate")
def evaluate_complete_plan(payload: PlanEvaluationRequest):
    """Re-score a complete/partial beam branch using the whole tree."""
    try:
        template = payload.template
        preferences = payload.preferences
        validate_dependency_graph(template)
        from core.genetic_algorithm import build_gene_mapping
        valid_preferences = {f"{path}.{resource}" for path, resource in build_gene_mapping(template)}
        unknown = set(preferences) - valid_preferences
        if unknown:
            raise ValueError("Preferencias de nodos/recurso desconocidas: " + ", ".join(sorted(unknown)))
        fitness, feasible, details = evaluate_fixed_preferences(template, preferences)
        return {
            "fitness_score": fitness,
            "feasible": feasible,
            "useful_benefits": details["useful_benefits"],
            "demand_deficits": details["demand_deficits"],
            "critical_deficits": details["critical_deficits"],
            "reserve_violations": details["reserve_violations"],
            "periods": details["periods"],
        }
    except DependencyValidationError as error:
        raise HTTPException(422, detail={"code": error.code, "message": str(error)}) from error
    except Exception as error:
        raise HTTPException(422, detail={"code": "invalid_plan", "message": str(error)}) from error

async def evolution_generator(request: Request, template: DynamicTemplate):
    ga = GeneticAlgorithm(template)
    ga.initialize_population()
    
    try:
        for generation in range(template.max_generations):
            if await request.is_disconnected():
                break
                
            ga.evolve_one_generation()
            
            is_final = (generation == template.max_generations - 1)
            
            if generation % template.emit_every_n == 0 or is_final:
                abs_population = decode_to_absolute(ga.population, template, ga.mapping)
                production_enabled = bool(template.benefit_values)
                objs = get_objectives(
                    abs_population, template, ga.mapping,
                    gene_population=ga.population,
                    feasible_mask=ga.viable_mask if production_enabled else None,
                )
                simulation = simulate_population(
                    ga.population, template, ga.mapping, gene_population=ga.population
                ) if production_enabled else None
                top3 = extract_archetypes(
                    ga.population, ga.fitness, objs, template, ga.mapping,
                    feasible_mask=ga.viable_mask if production_enabled else None,
                    simulation=simulation,
                )
                best_index = int(ga.fitness.argmax())
                last_period = simulation.periods[-1] if simulation and simulation.periods else {}

                payload = SSEPayload(
                    generation=generation,
                    avg_fitness=ga.get_avg_fitness(),
                    max_fitness=ga.get_max_fitness(),
                    top3=top3,
                    is_final=is_final,
                    viable_count=ga.get_viable_count(),
                    weights_normalized=(generation == 0),
                    period=max(0, len(simulation.periods) - 1) if simulation else None,
                    available_resources={
                        key: float(value[best_index])
                        for key, value in last_period.get("available_resources", {}).items()
                    },
                    consumed_resources={
                        key: float(value[best_index])
                        for key, value in last_period.get("consumed_resources", {}).items()
                    },
                    produced_resources={
                        key: float(value[best_index])
                        for key, value in last_period.get("produced_resources", {}).items()
                    },
                    useful_benefits={
                        key: float(value[best_index])
                        for key, value in (simulation.useful_benefits.items() if simulation else [])
                    },
                    demand_deficits={
                        key: float(value[best_index])
                        for key, value in (simulation.demand_deficits_by_resource.items() if simulation else [])
                        if value[best_index] > 1e-8
                    },
                    critical_deficits={
                        key: float(value[best_index])
                        for key, value in (simulation.critical_deficits_by_resource.items() if simulation else [])
                    },
                    reserve_violations={
                        key: float(value[best_index])
                        for key, value in (simulation.reserve_violations_by_resource.items() if simulation else [])
                        if value[best_index] > 1e-8
                    },
                    dependency_status={
                        path: "programado" for path, consumer in _walk_for_status(template)
                        if consumer.outputs
                    },
                )
                
                yield {"data": payload.model_dump_json()}
                
            await asyncio.sleep(0.02)  # Yield control to event loop, slight delay for visualization
            
    except asyncio.CancelledError:
        pass

@router.get("/evolution-stream")
async def sse_endpoint(request: Request):
    global active_template
    # Re-instantiate the GA using the current active template
    return EventSourceResponse(
        evolution_generator(request, active_template),
        headers={"X-Accel-Buffering": "no"}
    )
