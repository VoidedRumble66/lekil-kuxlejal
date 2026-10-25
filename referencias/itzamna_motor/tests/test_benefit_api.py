from fastapi.testclient import TestClient

from core.schemas import DynamicTemplate, OutputDef
from main import app
from tests.test_simulation import production_chain


client = TestClient(app)


def test_activation_rejects_a_cycle_before_streaming():
    template = production_chain()
    template.consumers["POTATO_CROP"].outputs["WATER"] = OutputDef(amount_per_unit=1)

    response = client.post("/api/scenarios/active", json=template.model_dump())

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "dependency_cycle"
    assert "POWER_PLANT" in response.json()["detail"]["message"]
    assert "POTATO_CROP" in response.json()["detail"]["message"]


def test_global_plan_endpoint_returns_temporal_explanation():
    template: DynamicTemplate = production_chain()
    response = client.post("/api/scenarios/evaluate", json={
        "template": template.model_dump(),
        "preferences": {"POWER_PLANT.WATER": 1, "POTATO_CROP.ENERGY": 1},
    })

    assert response.status_code == 200
    result = response.json()
    assert result["feasible"] is True
    assert result["useful_benefits"]["FOOD"] == 2
    assert len(result["periods"]) == 3


def test_global_plan_endpoint_rejects_out_of_range_preferences():
    template: DynamicTemplate = production_chain()
    response = client.post("/api/scenarios/evaluate", json={
        "template": template.model_dump(),
        "preferences": {"POWER_PLANT.WATER": 1.2},
    })

    assert response.status_code == 422
