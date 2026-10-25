import pytest
import numpy as np
from core.templates import get_templates
from core.genetic_algorithm import GeneticAlgorithm
from core.fitness import evaluate_population

def test_complex_template_evolution():
    templates = get_templates()
    complex_template = next(t for t in templates if t.template_id == "fuga_radiacion")
    
    ga = GeneticAlgorithm(complex_template)
    ga.initialize_population()
    
    for _ in range(10):
        ga.evolve_one_generation()
        
    # Check that not all fitness are 0 (or exactly identical flatline)
    assert np.max(ga.fitness) > -9999, "Population completely extinct or flatlined"
    
    # Ensure there is variation
    assert np.std(ga.fitness) > 0, "Fitness has no variance, population is flatlined"

def test_proportional_penalty():
    templates = get_templates()
    template = templates[0]
    
    ga = GeneticAlgorithm(template)
    
    # Create an individual that exceeds limits slightly
    ind_slight_excess = np.zeros((1, ga.num_genes))
    # Create an individual that exceeds limits massively
    ind_massive_excess = np.zeros((1, ga.num_genes))
    
    # Set all genes to slightly above max
    for i, (c_name, r_name) in enumerate(ga.mapping):
        ind_slight_excess[0, i] = template.resources[r_name].value * 1.1 / len(template.consumers)
        ind_massive_excess[0, i] = template.resources[r_name].value * 5.0 / len(template.consumers)
        
    fit_slight = evaluate_population(ind_slight_excess, template, ga.mapping)[0]
    fit_massive = evaluate_population(ind_massive_excess, template, ga.mapping)[0]
    
    # The one that exceeds massively should have a LOWER fitness (more penalty)
    assert fit_slight > fit_massive, "Proportional penalty is not working, massive excess should be penalized more."
