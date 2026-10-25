import numpy as np
from core.schemas import EvolutionParams
from core.pareto import extract_archetypes, pareto_front
from core.fitness import get_objectives

def test_pareto_front_extracts_three_archetypes():
    params = EvolutionParams(
        water_total_liters=1000.0,
        energy_total_kwh=100.0,
        num_inhabitants=10,
        cultivable_area_m2=20.0
    )
    pop = np.array([
        [500.0, 30.0, 40.0, 40.0],
        [250.0, 60.0, 40.0, 40.0],
        [400.0, 48.0, 40.0, 40.0],
    ])
    fitness = np.array([0.8, 0.7, 0.9])
    objs = get_objectives(pop, params)
    archetypes = extract_archetypes(pop, fitness, objs)
    
    assert len(archetypes) == 3
    ids = [a.scenario_id for a in archetypes]
    assert "human_priority" in ids
    assert "crop_viability" in ids
    assert "balanced" in ids

def test_degenerate_front_returns_unavailable():
    params = EvolutionParams(
        water_total_liters=1000.0,
        energy_total_kwh=100.0,
        num_inhabitants=10,
        cultivable_area_m2=20.0
    )
    pop = np.array([
        [500.0, 60.0, 40.0, 40.0],
    ])
    fitness = np.array([0.8])
    objs = get_objectives(pop, params)
    archetypes = extract_archetypes(pop, fitness, objs)
    
    assert len(archetypes) == 3
    assert archetypes[0].scenario_id == "unavailable"
    assert archetypes[1].scenario_id == "unavailable"
    assert archetypes[2].scenario_id == "unavailable"
