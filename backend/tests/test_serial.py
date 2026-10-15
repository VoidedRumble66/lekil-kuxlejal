"""Datos y puertos sintéticos exclusivamente en estas pruebas y bases temporales."""

from datetime import datetime, timedelta, timezone
import json
import secrets
import threading

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
import pytest
import serial

from app.database import BACKEND_DIR, build_engine, migration_connection
from app.main import create_app
from app.serial_protocol import parse_line
from serial_reader.service import BackendClient, SerialReader


def packet(**changes):
    result = dict(protocol_version=1, type="heartbeat", device_id="esp32-001122334455",
                  chip_model="ESP32-D0WD-V3", firmware_version="0.2.0",
                  boot_id="0123456789abcdef", uptime_ms=3000, sequence=1)
    result.update(changes)
    return result


def line(**changes):
    return (json.dumps(packet(**changes)) + "\n").encode()


def envelope(message=None, *, kind="message", at=None):
    return dict(event_id=secrets.token_hex(16), port="COM6", baud_rate=115200,
                received_at=(at or datetime.now(timezone.utc)).isoformat(), kind=kind, message=message)


def post(client, body):
    return client.post("/api/internal/serial-events", json=body,
                       headers={"X-Serial-Token": client.app.state.serial_token})


@pytest.fixture
def serial_client(application):
    with TestClient(application, client=("127.0.0.1", 50000)) as client:
        yield client


@pytest.mark.parametrize("changes", [{}, {"type": "hello", "sequence": 0, "uptime_ms": 250}])
def test_valid_hello_and_heartbeat(changes):
    message = parse_line(line(**changes))
    assert message.device_id == "esp32-001122334455"
    assert message.model_dump() == packet(**changes)


@pytest.mark.parametrize("raw", [
    b"not json\n", b'{"type":', line()[:-1], line(temperature=22),
    line(protocol_version=True), line(sequence=-1), line(type="hello", sequence=1),
    line(uptime_ms=float("nan")), b"x" * 2049 + b"\n",
    line().replace(b'"protocol_version": 1', b'"protocol_version": 1, "protocol_version": 1'),
])
def test_invalid_or_incomplete_messages_rejected(raw):
    with pytest.raises(ValueError):
        parse_line(raw)


def test_identity_freshness_no_sensors_and_duplicate_does_not_refresh(serial_client, monkeypatch):
    client = serial_client
    received = datetime.now(timezone.utc) - timedelta(seconds=1)
    assert post(client, envelope(packet(type="hello", sequence=0, uptime_ms=250), at=received)).json()["accepted"]
    assert client.get("/api/devices").json()[0]["status"] == "stale"  # hello is not a heartbeat
    event = envelope(packet(), at=received)
    assert post(client, event).json()["accepted"]
    first = client.get("/api/devices").json()[0]
    assert first["name"] == "ESP32 principal"
    assert first["kind"] == "esp32"
    assert first["model"] == "ESP32-D0WD-V3"
    assert first["serial_port"] == "COM6"
    assert first["status"] == "connected"
    assert first["uptime_ms"] == 3000
    assert first["firmware_version"] == "0.2.0"
    assert post(client, event).json() == {"accepted": False, "reason": "duplicate"}
    assert post(client, envelope(packet())).json()["reason"] == "duplicate"
    from app import device_service
    monkeypatch.setattr(device_service, "utc_now", lambda: received + timedelta(seconds=11))
    stale = client.get("/api/devices").json()[0]
    assert stale["status"] == "stale"
    assert stale["last_seen_at"] == first["last_seen_at"]
    assert client.get("/api/telemetry").json()["items"] == []
    assert client.get("/api/zones").json() == []
    assert len(client.get(f'/api/devices/{first["id"]}/events').json()) == 2


def test_reboot_old_boot_replay_out_of_order_and_manual_adoption(serial_client):
    client = serial_client
    manual = client.post("/api/devices", json={"name": "Mi placa", "serial_port": "COM6"}).json()
    assert post(client, envelope(packet())).json()["accepted"]
    assert client.get("/api/devices").json()[0]["id"] == manual["id"]
    assert post(client, envelope(packet(sequence=2, uptime_ms=100))).json()["reason"] == "uptime_regressed"
    assert post(client, envelope(packet(boot_id="aaaaaaaaaaaaaaaa", type="hello", sequence=0, uptime_ms=10))).json()["accepted"]
    assert post(client, envelope(packet(sequence=3, uptime_ms=9000))).json()["reason"] == "retired_boot"
    assert post(client, envelope(packet(boot_id="aaaaaaaaaaaaaaaa", sequence=2, uptime_ms=6000))).json()["accepted"]
    assert post(client, envelope(packet(boot_id="aaaaaaaaaaaaaaaa", sequence=1, uptime_ms=3000))).json()["reason"] == "out_of_order"
    result = client.get("/api/devices").json()
    assert len(result) == 1 and result[0]["status"] == "connected"
    assert result[0]["boot_id"] == "aaaaaaaaaaaaaaaa"


def test_disconnect_reconnect_and_old_disconnect_cannot_override_heartbeat(serial_client):
    client = serial_client
    now = datetime.now(timezone.utc)
    assert post(client, envelope(packet(), at=now - timedelta(seconds=3))).status_code == 200
    assert post(client, envelope(kind="disconnected", at=now - timedelta(seconds=2))).json()["accepted"]
    assert client.get("/api/devices").json()[0]["status"] == "disconnected"
    assert post(client, envelope(packet(sequence=2, uptime_ms=6000), at=now)).json()["accepted"]
    assert post(client, envelope(kind="reader_stopped", at=now - timedelta(seconds=1))).json()["accepted"]
    assert client.get("/api/devices").json()[0]["status"] == "connected"


def test_backend_restart_keeps_identity_and_deduplication(database_url):
    event = envelope(packet())
    with TestClient(create_app(database_url), client=("127.0.0.1", 50000)) as first:
        post(first, event)
        device = first.get("/api/devices").json()[0]
    with TestClient(create_app(database_url), client=("127.0.0.1", 50000)) as second:
        assert post(second, event).json()["reason"] == "duplicate"
        assert second.get("/api/devices").json()[0]["id"] == device["id"]
        assert second.get("/api/telemetry").json()["total"] == 0


def test_internal_interface_requires_local_token_and_no_browser_origin(serial_client):
    client = serial_client
    event = envelope(packet())
    assert client.post("/api/internal/serial-events", json=event).status_code == 403
    assert client.post("/api/internal/serial-events", json=event, headers={
        "X-Serial-Token": client.app.state.serial_token, "Origin": "http://localhost:5173",
    }).status_code == 403
    with TestClient(client.app, client=("192.0.2.1", 50000)) as remote:
        assert post(remote, event).status_code == 403
    assert client.get("/api/devices").json() == []
    assert post(client, envelope(packet(), at=datetime.now(timezone.utc) + timedelta(minutes=1))).status_code == 422


class FakePort:
    def __init__(self, chunks, stop=None):
        self.chunks = iter(chunks)
        self.closed = False
        self.stop = stop

    def open(self):
        pass

    def read(self, size):
        item = next(self.chunks, b"")
        if isinstance(item, Exception):
            raise item
        if self.stop is not None:
            self.stop.set()
        return item

    def close(self):
        self.closed = True

    def write(self, value):
        raise AssertionError("El lector nunca debe escribir al puerto")


def test_serial_port_disconnect_reconnect_and_fragmented_lines():
    now = [0.0]
    events = []
    first = FakePort([serial.SerialException("test-only unplug")])
    raw = line()
    second = FakePort([raw[:15], raw[15:]])
    ports = iter([first, second])
    reader = SerialReader("TEST_ONLY", lambda event: events.append(event),
                          serial_factory=lambda **kwargs: next(ports), clock=lambda: now[0])
    reader.step()
    assert first.closed and events[0].kind == "disconnected"
    now[0] = 1
    reader.step()
    assert not any(event.kind == "message" for event in events)
    reader.step()
    assert events[-1].message.sequence == 1
    reader.close_port()
    assert second.closed


def test_partial_timeout_oversized_frame_and_resynchronization():
    now = [0.0]
    events = []
    port = FakePort([b'{"unfinished":', b"", b"\n" + b"x" * 2050 + b"\n" + line()])
    reader = SerialReader("TEST_ONLY", lambda event: events.append(event),
                          serial_factory=lambda **kwargs: port, clock=lambda: now[0])
    reader.step()
    now[0] = 3
    reader.step()
    reader.step()
    assert any(event.kind == "protocol_error" for event in events)
    assert [event.message.sequence for event in events if event.message] == [1]
    reader.close_port()


def test_backend_outage_retries_same_event_and_queue_is_bounded():
    now = [0.0]
    delivered = []
    def deliver(event):
        delivered.append(event)
        if len(delivered) == 1:
            raise OSError("test-only backend down")
    reader = SerialReader("TEST_ONLY", deliver, clock=lambda: now[0], queue_limit=2)
    reader.feed(line())
    reader.flush()
    now[0] = 2
    reader.flush()
    assert delivered[0].event_id == delivered[1].event_id
    assert delivered[0].received_at == delivered[1].received_at
    for _ in range(3):
        reader.enqueue("protocol_error", detail="isolated test")
    assert len(reader.queue) == 2


def test_reader_closes_on_shutdown():
    stop = threading.Event()
    port = FakePort([line()], stop)
    events = []
    SerialReader("TEST_ONLY", lambda event: events.append(event), serial_factory=lambda **kwargs: port, stop=stop).run()
    assert port.closed and events[-1].kind == "reader_stopped"


def test_reader_filters_duplicates_before_delivery():
    events = []
    reader = SerialReader("TEST_ONLY", lambda event: events.append(event))
    reader.feed(line() + line())
    reader.flush()
    assert len(events) == 1


@pytest.mark.parametrize("url", ["https://example.com", "http://192.0.2.1", "http://localhost/path", "http://a:b@localhost"])
def test_reader_refuses_remote_backend(url, tmp_path):
    with pytest.raises(ValueError):
        BackendClient(url, tmp_path / "unused.token")


def test_migration_preserves_phase_one_measurement_history(database_url):
    engine = build_engine(database_url)
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    with migration_connection(engine) as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "0001_observation")
        connection.exec_driver_sql("INSERT INTO zones VALUES (?, ?, ?, ?, ?)",
                                   ("1" * 32, "Zona test", "Prueba aislada", None, "2026-10-15 00:00:00"))
        connection.exec_driver_sql("INSERT INTO devices VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                   ("2" * 32, "Legacy", "esp32-s3", None, None, "not_configured", "2026-10-15 00:00:00", None))
        connection.exec_driver_sql("INSERT INTO measurements VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                   ("3" * 32, "real", "1" * 32, "2" * 32, "test_only", "test", 1.0, "unverified", "2026-10-15 00:00:00", "2026-10-15 00:00:00", None))
    engine.dispose()
    with TestClient(create_app(database_url)) as client:
        assert client.get("/api/telemetry").json()["total"] == 1
        assert client.get("/api/devices").json()[0]["kind"] == "esp32-s3"
        with client.app.state.engine.connect() as connection:
            assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
            assert connection.exec_driver_sql("PRAGMA foreign_key_check").fetchall() == []
