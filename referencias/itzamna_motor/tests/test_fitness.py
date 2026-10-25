import numpy as np
from core.schemas import EvolutionParams
from core.fitness import evaluate_population

def test_inviable_individual_gets_zero_fitness():
    params = EvolutionParams(
        water_total_liters=100.0,
        energy_total_kwh=100.0,
        num_inhabitants=10,
        cultivable_area_m2=20.0
    )
    # water_human + water_irrigation > 100
    pop = np.array([
        [60.0, 50.0, 10.0, 10.0],
    ])
    fitness = evaluate_population(pop, params)
    assert fitness[0] == 0.0

def test_water_overflow_gives_zero():
    params = EvolutionParams(
        water_total_liters=100.0,
        energy_total_kwh=100.0,
        num_inhabitants=10,
        cultivable_area_m2=20.0
    )
    pop = np.array([[101.0, 0.0, 10.0, 10.0]])
    fitness = evaluate_population(pop, params)
    assert fitness[0] == 0.0

def test_energy_overflow_gives_zero():
    params = EvolutionParams(
        water_total_liters=100.0,
        energy_total_kwh=100.0,
        num_inhabitants=10,
        cultivable_area_m2=20.0
    )
    pop = np.array([[10.0, 10.0, 50.0, 60.0]])
    fitness = evaluate_population(pop, params)
    assert fitness[0] == 0.0

def test_viable_individual_gets_positive_fitness():
    params = EvolutionParams(
        water_total_liters=1000.0,
        energy_total_kwh=100.0,
        num_inhabitants=10,
        cultivable_area_m2=20.0
    )
    pop = np.array([[500.0, 60.0, 40.0, 40.0]])
    fitness = evaluate_population(pop, params)
    assert fitness[0] > 0.0

def test_fitness_is_between_zero_and_one():
    params = EvolutionParams(
        water_total_liters=1000.0,
        energy_total_kwh=100.0,
        num_inhabitants=10,
        cultivable_area_m2=20.0
    )
    pop = np.random.uniform(0, 50, (100, 4))
    fitness = evaluate_population(pop, params)
    assert np.all(fitness >= 0.0)
    assert np.all(fitness <= 1.0)
