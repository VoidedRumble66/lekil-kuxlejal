"""Compare exact global evaluations against evolution's score contract."""
import numpy as np
import pytest

from core.fitness import evaluate_fixed_preferences, evaluate_population
from core.genetic_algorithm import build_gene_mapping, decode_to_absolute
from core.templates import get_templates
from core.schemas import DynamicTemplate


def production_chain(periods=3):
    return DynamicTemplate(
        template_id="production-chain",
        name="Planta y cultivo",
        description="",
        max_periods=periods,
        resources={"WATER": {"value": 10}, "ENERGY": {"value": 0}, "FOOD": {"value": 0}},
        benefit_values={
            "WATER": {"unit_value": 0},
            "ENERGY": {"unit_value": 0},
            "FOOD": {"unit_value": 1, "target_demand": 2, "critical": True},
        },
        consumers={
            "POWER_PLANT": {
                "priority_weight": 1,
                "requirements": {"WATER": {"value": 10}},
                "outputs": {"ENERGY": {"amount_per_unit": 10, "efficiency": 0.5}},
            },
            "POTATO_CROP": {
                "priority_weight": 1,
                "requirements": {"ENERGY": {"value": 5}},
                "outputs": {"FOOD": {"amount_per_unit": 2}},
            },
        },
    )


def _compare(template, preferences):
    mapping = build_gene_mapping(template)
    genes = np.array([[preferences.get(f"{p}.{r}", 0.0) for p, r in mapping]])
    decoded = decode_to_absolute(genes, template, mapping)
    evol_scores, evol_viable = evaluate_population(decoded, template, mapping, gene_population=genes)
    global_score, global_viable, details = evaluate_fixed_preferences(template, preferences)
    assert global_score == pytest.approx(float(evol_scores[0]), abs=1e-9)
    assert global_viable == bool(evol_viable[0])
    return global_score, global_viable, details


def test_agricultural_template_has_identical_global_and_local_fitness():
    template = next(t for t in get_templates() if t.template_id == "domo_bioagricola_inteligente")
    mapping = build_gene_mapping(template)
    score, feasible, details = _compare(template, {f"{p}.{r}": 0.5 for p, r in mapping})
    assert feasible
    assert score == pytest.approx(146.67611028529905)
    assert len(details["periods"]) == template.max_periods


def test_critical_target_failure_matches_feasibility_and_penalty():
    template = production_chain(periods=2)
    score, feasible, details = _compare(template, {"POWER_PLANT.WATER": 1.0, "POTATO_CROP.ENERGY": 1.0})
    assert not feasible
    assert score <= -1_000_000
    assert details["critical_deficits"]["FOOD"] == pytest.approx(2)


def test_feasible_production_chain_matches_both_routes():
    template = production_chain(periods=3)
    score, feasible, details = _compare(template, {"POWER_PLANT.WATER": 1.0, "POTATO_CROP.ENERGY": 1.0})
    assert feasible
    assert score > 0
    assert details["useful_benefits"]["FOOD"] == pytest.approx(2)
