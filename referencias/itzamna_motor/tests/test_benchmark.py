import time
import numpy as np
from core.schemas import EvolutionParams
from core.genetic_algorithm import GeneticAlgorithm

def test_benchmark_sc004():
    """SC-004: 200 gen * 100 ind < 10s"""
    params = EvolutionParams(
        water_total_liters=5000.0,
        energy_total_kwh=1000.0,
        num_inhabitants=100,
        cultivable_area_m2=200.0,
        population_size=100,
        max_generations=200
    )
    
    start = time.perf_counter()
    ga = GeneticAlgorithm(params)
    ga.initialize_population()
    for _ in range(params.max_generations):
        ga.evolve_one_generation()
    end = time.perf_counter()
    
    duration = end - start
    print(f"Benchmark took {duration:.2f} seconds")
    
    assert duration < 10.0, f"Benchmark failed: took {duration}s, expected < 10s"
