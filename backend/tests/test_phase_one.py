from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError, OperationalError, StatementError
from sqlmodel import Session

from app.main import create_app
from app.models import Device, Measurement, Zone


def assert_utc(value):
    timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    assert timestamp.utcoffset() == timedelta(0)


def add_test_measurement(application, **overrides):
    """Fixture sintético exclusivamente en el SQLite temporal de pytest."""
    with Session(application.state.engine) as session:
        zone = Zone(name="Zona de prueba", purpose="Ensayo aislado")
        device = Device(name="Dispositivo de prueba")
        session.add(zone)
        session.add(device)
        session.commit()
        session.refresh(zone)
        session.refresh(device)
        values = {
            "zone_id": zone.id,
            "device_id": device.id,
            "quantity": "air_temperature",
            "unit": "°C",
            "value": 22.25,
            "quality": "unverified",
            "measured_at": datetime(2026, 10, 15, 10, 0, tzinfo=timezone(timedelta(hours=-6))),
        }
        values.update(overrides)
        measurement = Measurement(**values)
        session.add(measurement)
        session.commit()
        session.refresh(measurement)
        return measurement.id, zone.id, device.id


def test_first_start_migrates_without_seeding_data(client, application):
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json() | {"timestamp": "time"} == {
        "status": "ok",
        "database": "connected",
        "mode": "observation",
        "control_enabled": False,
        "timestamp": "time",
    }
    assert_utc(health.json()["timestamp"])
    assert client.get("/api/zones").json() == []
    assert client.get("/api/devices").json() == []
    telemetry = client.get("/api/telemetry").json()
    assert telemetry["items"] == []
    assert telemetry["total"] == 0
    assert telemetry["source"] == "real"
    assert_utc(telemetry["queried_at"])
    with application.state.engine.connect() as connection:
        assert connection.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "0002_serial"
        assert connection.execute(text("SELECT count(*) FROM measurements")).scalar_one() == 0


def test_configuration_persists_across_application_restarts(database_url):
    first_app = create_app(database_url)
    with TestClient(first_app) as first:
        zone_response = first.post("/api/zones", json={"name": " Banco de semillas ", "purpose": "Conservación"})
        device_response = first.post("/api/devices", json={"name": "ESP de campo", "model": None, "serial_port": None})
        assert zone_response.status_code == 201
        assert device_response.status_code == 201
        zone = zone_response.json()
        device = device_response.json()
        UUID(zone["id"])
        UUID(device["id"])
        assert zone["name"] == "Banco de semillas"
        assert zone["description"] is None
        assert device["kind"] == "esp32"
        assert device["status"] == "not_configured"
        assert device["last_seen_at"] is None
        assert_utc(zone["created_at"])
        assert_utc(device["created_at"])

    with TestClient(create_app(database_url)) as second:
        assert second.get("/api/zones").json() == [zone]
        assert second.get("/api/devices").json() == [device]
        assert second.get("/api/telemetry").json()["items"] == []


@pytest.mark.parametrize(
    "path,payload",
    [
        ("/api/zones", {"name": " ", "purpose": "Producción"}),
        ("/api/zones", {"name": "A", "purpose": None}),
        ("/api/zones", {"name": "A", "purpose": " "}),
        ("/api/zones", {"name": "A" * 81, "purpose": "Producción"}),
        ("/api/zones", {"name": "A", "purpose": "P" * 161}),
        ("/api/zones", {"name": "A", "purpose": "Producción", "description": "X" * 2001}),
        ("/api/zones", {"name": 10, "purpose": "Producción"}),
        ("/api/zones", {"name": "A", "purpose": "Producción", "id": str(uuid4())}),
        ("/api/devices", {"name": " "}),
        ("/api/devices", {"name": "A" * 81}),
        ("/api/devices", {"name": "ESP", "model": "M" * 121}),
        ("/api/devices", {"name": "ESP", "serial_port": "C" * 129}),
        ("/api/devices", {"name": "ESP", "serial_port": " "}),
        ("/api/devices", {"name": "ESP", "status": "connected"}),
        ("/api/devices", {"name": "ESP", "kind": "esp32-s3"}),
        ("/api/devices", {"name": "ESP", "last_seen_at": "2026-10-15T00:00:00Z"}),
    ],
)
def test_invalid_configuration_cannot_create_rows(client, path, payload):
    assert client.post(path, json=payload).status_code == 422
    assert client.get(path).json() == []


def test_configuration_accepts_documented_length_boundaries(client):
    zone = client.post("/api/zones", json={"name": "A" * 80, "purpose": "P" * 160, "description": "D" * 2000})
    device = client.post("/api/devices", json={"name": "E" * 80, "model": "M" * 120, "serial_port": "C" * 128})
    assert zone.status_code == 201
    assert device.status_code == 201
    assert device.json()["status"] == "not_configured"


@pytest.mark.parametrize("query", ["limit=0", "limit=201", "offset=-1", "zone_id=bad", "device_id=bad"])
def test_telemetry_rejects_invalid_queries(client, query):
    assert client.get(f"/api/telemetry?{query}").status_code == 422


def test_telemetry_preserves_provenance_units_nulls_and_utc(client, application):
    measurement_id, zone_id, device_id = add_test_measurement(application)
    result = client.get(f"/api/telemetry?zone_id={zone_id}&device_id={device_id}&limit=1").json()
    assert result["total"] == 1
    item = result["items"][0]
    assert item["id"] == str(measurement_id)
    assert item["zone_id"] == str(zone_id)
    assert item["device_id"] == str(device_id)
    assert item["source"] == "real"
    assert item["unit"] == "°C"
    assert item["quantity"] == "air_temperature"
    assert item["value"] == 22.25
    assert item["quality"] == "unverified"
    assert item["observations"] is None
    assert datetime.fromisoformat(item["measured_at"].replace("Z", "+00:00")) == datetime(2026, 10, 15, 16, 0, tzinfo=timezone.utc)
    assert_utc(item["recorded_at"])
    assert client.get("/api/telemetry?offset=1").json()["items"] == []
    assert client.get(f"/api/telemetry?zone_id={uuid4()}").json()["total"] == 0


def test_database_rejects_hypothetical_measurements_and_naive_timestamps(client, application):
    with pytest.raises(IntegrityError):
        add_test_measurement(application, source="hypothetical")
    with pytest.raises(StatementError):
        add_test_measurement(application, measured_at=datetime(2026, 10, 15))
    with pytest.raises(IntegrityError):
        add_test_measurement(application, value=float("inf"))
    assert client.get("/api/telemetry").json()["total"] == 0


def test_foreign_keys_reject_orphans_and_protect_history(client, application):
    measurement_id, zone_id, device_id = add_test_measurement(application)
    inspector = inspect(application.state.engine)
    assert {key["referred_table"] for key in inspector.get_foreign_keys("measurements")} == {"zones", "devices"}
    with application.state.engine.begin() as connection:
        with pytest.raises(IntegrityError):
            connection.execute(text("DELETE FROM zones WHERE id = :id"), {"id": zone_id.hex})
        with pytest.raises(IntegrityError):
            connection.execute(text("DELETE FROM devices WHERE id = :id"), {"id": device_id.hex})
    with pytest.raises(IntegrityError):
        add_test_measurement(application, device_id=uuid4())
    assert client.get("/api/telemetry").json()["total"] == 1


def test_database_failure_is_not_reported_as_healthy(client, application, monkeypatch):
    def fail_to_connect(*args, **kwargs):
        raise OperationalError("SELECT 1", {}, Exception("isolated test: unavailable"))

    monkeypatch.setattr(application.state.engine, "connect", fail_to_connect)
    health = client.get("/api/health")
    assert health.status_code == 503
    assert health.json()["status"] == "error"
    assert health.json()["database"] == "unavailable"
    assert health.json()["control_enabled"] is False
    assert client.get("/api/zones").status_code == 503


def test_no_ingestion_actuation_or_destructive_endpoints(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert set(paths) == {"/api/health", "/api/zones", "/api/devices", "/api/telemetry", "/api/devices/{device_id}/events", "/api/internal/serial-events"}
    assert set(paths["/api/telemetry"]) == {"get"}
    assert client.post("/api/telemetry", json={}).status_code == 405
    assert client.delete("/api/zones").status_code == 405
    assert client.patch("/api/devices", json={}).status_code == 405
    assert client.post("/api/commands", json={}).status_code == 404


def test_cors_allows_only_documented_local_frontends(client):
    trusted = client.options(
        "/api/zones",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"},
    )
    assert trusted.status_code == 200
    assert trusted.headers["access-control-allow-origin"] == "http://localhost:5173"
    untrusted = client.options(
        "/api/zones",
        headers={"Origin": "https://example.com", "Access-Control-Request-Method": "POST"},
    )
    assert untrusted.status_code == 400
    assert "access-control-allow-origin" not in untrusted.headers
