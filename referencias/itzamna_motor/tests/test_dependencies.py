import pytest

from core.dependencies import DependencyValidationError, validate_dependency_graph
from core.schemas import DynamicTemplate


def make_template(consumers):
    return DynamicTemplate(
        template_id="dependency-test",
        name="Dependency test",
        description="",
        resources={"WATER": {"value": 100}, "ENERGY": {"value": 100}, "FOOD": {"value": 100}},
        benefit_values={
            "WATER": {"unit_value": 1},
            "ENERGY": {"unit_value": 1},
            "FOOD": {"unit_value": 1},
        },
        consumers=consumers,
    )


def test_legacy_template_without_outputs_is_valid():
    template = make_template({
        "CROP": {
            "priority_weight": 1.0,
            "requirements": {"WATER": {"value": 10}},
            "subconsumers": {},
        }
    })

    validate_dependency_graph(template)


def test_acyclic_production_chain_is_valid():
    template = make_template({
        "POWER": {
            "priority_weight": 1.0,
            "requirements": {"WATER": {"value": 10}},
            "outputs": {"ENERGY": {"amount_per_unit": 20}},
            "subconsumers": {},
        },
        "CROP": {
            "priority_weight": 1.0,
            "requirements": {"ENERGY": {"value": 10}},
            "outputs": {"FOOD": {"amount_per_unit": 5}},
            "subconsumers": {},
        },
    })

    validate_dependency_graph(template)


def test_circular_production_chain_is_rejected():
    template = make_template({
        "POWER": {
            "priority_weight": 1.0,
            "requirements": {"WATER": {"value": 10}},
            "outputs": {"ENERGY": {"amount_per_unit": 20}},
            "subconsumers": {},
        },
        "CROP": {
            "priority_weight": 1.0,
            "requirements": {"ENERGY": {"value": 10}},
            "outputs": {"WATER": {"amount_per_unit": 5}},
            "subconsumers": {},
        },
    })

    with pytest.raises(DependencyValidationError, match="Dependencia circular"):
        validate_dependency_graph(template)


def test_output_must_have_a_resource_and_benefit_value():
    template = make_template({
        "POWER": {
            "priority_weight": 1.0,
            "requirements": {},
            "outputs": {"UNKNOWN": {"amount_per_unit": 20}},
            "subconsumers": {},
        }
    })

    with pytest.raises(DependencyValidationError, match="recurso inexistente"):
        validate_dependency_graph(template)


def test_reserve_cannot_exceed_initial_inventory():
    template = make_template({})
    template.benefit_values["WATER"].minimum_reserve = 101

    with pytest.raises(DependencyValidationError) as error:
        validate_dependency_graph(template)

    assert error.value.code == "invalid_reserve"
