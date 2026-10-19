"""Supuestos sintéticos: sólo SQLite temporales de pytest, sin puertos seriales."""

from copy import deepcopy
from datetime import datetime, timedelta
from uuid import uuid4

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text
from alembic import command
from alembic.config import Config

from app.decision_routes import snapshot_hash
from app.decision_schemas import ScenarioInput
from app.itzamna_adapter import compare, evaluate_plan, pareto_front, validate_allocations
from app.main import create_app
from app.database import BACKEND_DIR, build_engine, migration_connection


@pytest.fixture
def parameters():
    return {
        "name": "Supuestos de prueba aislada", "assumptions": "No son necesidades agrícolas reales.",
        "periods": 5, "period_hours": 24, "generation_reduction": 0.4,
        "initial_energy_kwh": 8, "storage_capacity_kwh": 12, "protected_reserve_kwh": 2,
        "generation_daily_kwh": [10] * 5, "module_daily_limit_kwh": 13,
        "services": [
            {"key": "a", "name": "Servicio A", "target_daily_kwh": 6, "priority": 1},
            {"key": "b", "name": "Servicio B", "target_daily_kwh": 4, "priority": 0.8},
        ],
    }


def test_temporal_balance_cut_once_capacity_and_reserve(parameters):
    scenario = ScenarioInput(**parameters)
    plan = evaluate_plan(scenario, {"a": 4, "b": 2})
    previous = 8
    for period in plan["periods"]:
        assert period["initial_kwh"] == previous
        assert period["gross_generation_kwh"] == 10
        assert period["reduced_generation_kwh"] == 6
        assert period["generation_cut_kwh"] == 4
        assert period["ending_kwh"] == pytest.approx(previous + 6 - period["curtailed_kwh"] - 6)
        assert 2 <= period["ending_kwh"] <= 12
        previous = period["ending_kwh"]
    assert plan["periods"][0]["curtailed_kwh"] == 2
    assert plan["total_consumption_kwh"] == 30  # Padres e hijos no duplican consumo.


@pytest.mark.parametrize("hours", [12, 24, 48])
def test_period_hours_scale_generation_consumption_not_initial_energy(parameters, hours):
    parameters.update(period_hours=hours, initial_energy_kwh=20, storage_capacity_kwh=100)
    scale = hours / 24
    plan = evaluate_plan(ScenarioInput(**parameters), {"a": 3 * scale, "b": 2 * scale})
    assert plan["periods"][0]["initial_kwh"] == 20
    assert plan["periods"][0]["reduced_generation_kwh"] == 6 * scale
    assert plan["ending_kwh"] == pytest.approx(20 + 5 * scale)


def test_no_future_energy_can_pay_an_earlier_period(parameters):
    parameters.update(initial_energy_kwh=2, generation_daily_kwh=[0, 100, 100, 100, 100])
    with pytest.raises(ValueError, match="periodo 1"):
        evaluate_plan(ScenarioInput(**parameters), {"a": 1, "b": 1})


@pytest.mark.parametrize("allocations", [{"a": -1, "b": 0}, {"a": 7, "b": 0}, {"a": float('nan'), "b": 0}, {"a": 1}])
def test_invalid_allocations_are_rejected_not_silently_normalized(parameters, allocations):
    with pytest.raises(ValueError):
        evaluate_plan(ScenarioInput(**parameters), allocations)


def test_hierarchy_limit_and_minimum_are_hard_constraints(parameters):
    parameters["module_daily_limit_kwh"] = 3
    with pytest.raises(ValueError, match="padre"):
        validate_allocations(ScenarioInput(**parameters), {"a": 3, "b": 1})
    parameters["services"][0].update(minimum_daily_kwh=2, minimum_basis="Supuesto de ensayo, no validado")
    with pytest.raises(ValueError, match="mínimo"):
        validate_allocations(ScenarioInput(**parameters), {"a": 1, "b": 0})


def test_missing_minima_are_not_invented_and_all_alternatives_are_feasible(parameters):
    scenario = ScenarioInput(**parameters)
    result = compare(scenario)
    assert result["agricultural_status"] == "Factibilidad agrícola no evaluada"
    assert 1 <= len(result["alternatives"]) <= 3
    assert len({tuple(a["allocations_kwh"].values()) for a in result["alternatives"]}) == len(result["alternatives"])
    for alternative in result["alternatives"]:
        assert evaluate_plan(scenario, alternative["allocations_kwh"])["periods"] == alternative["periods"]
    assert compare(scenario) == result
    assert all(s.minimum_daily_kwh is None for s in scenario.services)


def test_only_one_feasible_plan_does_not_fabricate_three(parameters):
    parameters.update(initial_energy_kwh=2, generation_daily_kwh=[0] * 5)
    result = compare(ScenarioInput(**parameters))
    assert result["search"]["feasible"] == 1
    assert len(result["alternatives"]) == 1
    assert result["alternatives"][0]["total_consumption_kwh"] == 0
    assert result["agricultural_status"] == "Factibilidad agrícola no evaluada"


@pytest.mark.parametrize("cause", ["energy", "hierarchy"])
def test_infeasible_scenarios_have_no_alternatives(parameters, cause):
    for service in parameters["services"]:
        service.update(minimum_daily_kwh=service["target_daily_kwh"], minimum_basis="Supuesto de prueba declarado")
    if cause == "hierarchy":
        parameters["module_daily_limit_kwh"] = 1
    result = compare(ScenarioInput(**parameters))
    assert result["status"] == "infeasible"
    assert result["alternatives"] == []
    assert result["rejections"]


def test_declared_minima_are_covered_without_claiming_agronomic_validation(parameters):
    for service in parameters["services"]:
        service.update(minimum_daily_kwh=1, minimum_basis="Declaración hipotética de prueba")
    result = compare(ScenarioInput(**parameters))
    assert "sin validación agronómica" in result["agricultural_status"]
    for alternative in result["alternatives"]:
        assert all(amount >= 1 for amount in alternative["allocations_kwh"].values())


@pytest.mark.parametrize("change", [
    {"initial_energy_kwh": -1}, {"initial_energy_kwh": 13}, {"protected_reserve_kwh": 9},
    {"storage_capacity_kwh": -1}, {"period_hours": 0}, {"generation_reduction": 1.1},
    {"periods": 0}, {"generation_daily_kwh": [10]}, {"generation_daily_kwh": [-1] * 5},
    {"initial_energy_kwh": float('inf')}, {"physical_command": "start"},
])
def test_bad_configuration_rejected_before_comparison(client, parameters, change):
    parameters.update(change)
    if change.get("initial_energy_kwh") == float('inf'):
        with pytest.raises(ValueError):
            ScenarioInput(**parameters)
    else:
        assert client.post("/api/decisions/runs", json=parameters).status_code == 422
    assert client.get("/api/decisions/runs").json() == []


def test_minimum_requires_provenance_and_does_not_exceed_target(client, parameters):
    parameters["services"][0]["minimum_daily_kwh"] = 1
    assert client.post("/api/decisions/runs", json=parameters).status_code == 422
    parameters["services"][0].update(minimum_daily_kwh=7, minimum_basis="Supuesto")
    assert client.post("/api/decisions/runs", json=parameters).status_code == 422


def test_human_review_persists_with_parameters_results_and_utc(database_url, parameters):
    with TestClient(create_app(database_url)) as first:
        assert first.get("/api/decisions/runs").json() == []
        response = first.post("/api/decisions/runs", json=parameters)
        assert response.status_code == 201
        run = response.json()
        assert run["reviews"] == []  # El motor no aprueba.
        verdict = {"alternative_id": "alternativa_1", "decision": "approved", "responsible": " Persona de prueba ", "reason": "Revisión de supuestos aislados"}
        review_response = first.post(f'/api/decisions/runs/{run["id"]}/reviews', json=verdict)
        assert review_response.status_code == 201
        review = review_response.json()
        assert review["responsible"] == "Persona de prueba"
        assert datetime.fromisoformat(review["created_at"].replace("Z", "+00:00")).utcoffset() == timedelta(0)
        assert first.post(f'/api/decisions/runs/{run["id"]}/reviews', json=verdict).status_code == 409
        verdict["alternative_id"] = "alternativa_2"
        assert first.post(f'/api/decisions/runs/{run["id"]}/reviews', json=verdict).status_code == 409
        verdict["decision"] = "rejected"
        assert first.post(f'/api/decisions/runs/{run["id"]}/reviews', json=verdict).status_code == 201
    with TestClient(create_app(database_url)) as second:
        saved = second.get(f'/api/decisions/runs/{run["id"]}').json()
        assert saved["parameters"] == run["parameters"]
        assert saved["result"] == run["result"]
        assert saved["snapshot_sha256"] == snapshot_hash(saved["parameters"], saved["result"], saved["engine_fingerprint"])
        assert [r["decision"] for r in saved["reviews"]] == ["approved", "rejected"]
        assert len(second.get("/api/decisions/runs").json()) == 1
        assert second.get("/api/decisions/runs?offset=1").json() == []
        assert second.get("/api/telemetry").json()["items"] == []
        assert second.get("/api/devices").json() == []
        assert second.get("/api/zones").json() == []
        assert second.post("/api/commands", json={}).status_code == 404


def test_reviews_require_actual_alternative_human_and_reason(client, parameters):
    run = client.post("/api/decisions/runs", json=parameters).json()
    verdict = {"alternative_id": "alternativa_1", "decision": "rejected", "responsible": "Persona", "reason": "Motivo"}
    for field in ("responsible", "reason"):
        invalid = deepcopy(verdict); invalid[field] = " "
        assert client.post(f'/api/decisions/runs/{run["id"]}/reviews', json=invalid).status_code == 422
    assert client.post(f"/api/decisions/runs/{uuid4()}/reviews", json=verdict).status_code == 404
    parameters.update(initial_energy_kwh=2, generation_daily_kwh=[0] * 5)
    for service in parameters["services"]:
        service.update(minimum_daily_kwh=1, minimum_basis="Supuesto de ensayo")
    bad = client.post("/api/decisions/runs", json=parameters).json()
    assert bad["result"]["status"] == "infeasible"
    assert client.post(f'/api/decisions/runs/{bad["id"]}/reviews', json=verdict).status_code == 422


def test_scenario_storage_is_separate_and_referential(client, application, parameters):
    run = client.post("/api/decisions/runs", json=parameters).json()
    inspector = inspect(application.state.engine)
    assert inspector.get_foreign_keys("decision_runs") == []
    assert {fk["referred_table"] for fk in inspector.get_foreign_keys("decision_reviews")} == {"decision_runs"}
    with application.state.engine.connect() as connection:
        for name in ("measurements", "devices", "zones", "device_events"):
            assert connection.execute(text(f"SELECT count(*) FROM {name}")).scalar_one() == 0
    assert run["source"] == "hypothetical"


def test_upgrade_preserves_existing_phase_2a_rows(database_url, parameters):
    engine = build_engine(database_url)
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    with migration_connection(engine) as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "0002_serial")
    # Copia sintética de un diagnóstico previo: únicamente en esta base temporal.
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO devices (id,name,kind,model,serial_port,status,created_at) "
                                "VALUES (:id,'Placa de prueba','esp32','ESP32-D0WD-V3','COM6','disconnected','2026-10-19 00:00:00')"), {"id": uuid4().hex})
        original = [tuple(row) for row in connection.execute(text("SELECT * FROM devices"))]
    engine.dispose()
    with TestClient(create_app(database_url)) as api:
        assert api.post("/api/decisions/runs", json=parameters).status_code == 201
        assert api.get("/api/devices").json()[0]["serial_port"] == "COM6"
        assert api.get("/api/telemetry").json()["total"] == 0
    engine = build_engine(database_url)
    with engine.connect() as connection:
        assert [tuple(row) for row in connection.execute(text("SELECT * FROM devices"))] == original
        assert connection.execute(text("PRAGMA foreign_key_check")).all() == []
    engine.dispose()


def test_reused_pareto_is_maximizing_and_order_independent():
    scores = np.array([[2., 2.], [1., 1.], [3., 0.]])
    assert pareto_front(scores).tolist() == [True, False, True]
    assert pareto_front(scores[::-1]).tolist() == [True, False, True]
