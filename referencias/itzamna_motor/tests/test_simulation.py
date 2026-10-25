import numpy as np

from core.dependencies import DependencyValidationError, validate_dependency_graph
from core.fitness import evaluate_fixed_preferences
from core.schemas import DynamicTemplate
from core.simulation import simulate_preferences


def production_chain(periods=3):
    return DynamicTemplate(
        template_id="production-chain",
        name="Planta y cultivo",
        description="",
        max_periods=periods,
        resources={
            "WATER": {"value": 10},
            "ENERGY": {"value": 0},
            "FOOD": {"value": 0},
        },
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
                "subconsumers": {},
            },
            "POTATO_CROP": {
                "priority_weight": 1,
                "requirements": {"ENERGY": {"value": 5}},
                "outputs": {"FOOD": {"amount_per_unit": 2}},
                "subconsumers": {},
            },
        },
    )


def test_output_waits_until_a_later_period_and_applies_efficiency():
    template = production_chain()
    validate_dependency_graph(template)
    result = simulate_preferences(
        template,
        {"POWER_PLANT.WATER": 1, "POTATO_CROP.ENERGY": 1},
    )

    assert result.produced_benefits["ENERGY"][0] == 5
    assert result.useful_benefits["FOOD"][0] == 2
    assert result.periods[0]["consumed_resources"]["ENERGY"][0] == 0
    assert result.periods[1]["consumed_resources"]["ENERGY"][0] == 5
    assert not result.infeasible[0]


def test_future_output_cannot_cover_demand_before_it_arrives():
    template = production_chain(periods=2)
    result = simulate_preferences(
        template,
        {"POWER_PLANT.WATER": 1, "POTATO_CROP.ENERGY": 1},
    )

    assert result.useful_benefits["FOOD"][0] == 0
    assert result.critical_deficits_by_resource["FOOD"][0] == 2
    assert result.infeasible[0]


def test_fixed_preference_values_are_bounded_by_the_gene_contract():
    template = production_chain()
    result = simulate_preferences(template, {"POWER_PLANT.WATER": 5, "POTATO_CROP.ENERGY": -1})

    assert np.isfinite(result.utility[0])
    assert result.useful_benefits["FOOD"][0] == 0


def test_complete_branch_evaluation_uses_the_whole_production_chain():
    fitness, feasible, details = evaluate_fixed_preferences(
        production_chain(),
        {"POWER_PLANT.WATER": 1, "POTATO_CROP.ENERGY": 1},
    )

    assert feasible
    assert fitness > 0
    assert details["useful_benefits"]["FOOD"] == 2
    assert len(details["periods"]) == 3
