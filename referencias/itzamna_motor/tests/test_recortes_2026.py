"""Pruebas de balances en escenarios hipoteticos de escasez del 40 %."""

import numpy as np
import pytest
from core.genetic_algorithm import build_gene_mapping, decode_to_absolute
from core.schemas import CrisisDef
from core.simulation import simulate_population
from core.templates import get_templates


@pytest.mark.parametrize("resource", ["AGUA_L", "ENERGIA_KWH"])
def test_crisis_40_percent_preserves_root_and_period_balances(resource):
    template = next(t.model_copy(deep=True) for t in get_templates()
                    if t.template_id == "domo_bioagricola_inteligente")
    template.crisis_factors = {"ENSAYO": CrisisDef(
        name="Recorte hipotetico 40 por ciento", description="Solo prueba",
        intensity=1.0, impact_resource={resource: -0.4})}
    mapping = build_gene_mapping(template)
    genes = np.full((4, len(mapping)), 0.95)
    allocated = decode_to_absolute(genes, template, mapping)
    initial = template.resources[resource].value * 0.6
    root_indices = [i for i, (path, name) in enumerate(mapping)
                    if "." not in path and name == resource]
    assert np.all(allocated[:, root_indices].sum(axis=1) <= initial + 1e-7)

    # Cada nodo hijo debe permanecer dentro del presupuesto entregado a su padre.
    for path, name in mapping:
        immediate_children = [i for i, (other, other_resource) in enumerate(mapping)
                              if other_resource == name and other.rsplit(".", 1)[0] == path
                              and "." in other]
        if immediate_children:
            parent_index = mapping.index((path, name))
            assert np.all(allocated[:, immediate_children].sum(axis=1)
                          <= allocated[:, parent_index] + 1e-7)

    simulation = simulate_population(allocated, template, mapping, gene_population=genes)
    for period in simulation.periods:
        available = period["available_resources"][resource]
        consumed = period["consumed_resources"][resource]
        assert np.all(consumed <= available + 1e-7)
        assert np.all(period["ending_inventory"][resource] >= -1e-7)
