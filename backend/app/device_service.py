"""Persistencia y vigencia de diagnóstico. Sólo el backend escribe SQLite."""

import os
import secrets
from datetime import datetime, timezone
from pathlib import Path

from sqlmodel import Session, select

from .database import utc_now
from .models import Device, DeviceEvent
from .schemas import DeviceRead
from .serial_protocol import HEARTBEAT_TTL_SECONDS, SerialEventInput


def load_ingest_token(database_path: str) -> str:
    configured = os.environ.get("SERIAL_INGEST_TOKEN")
    if configured:
        if len(configured) < 24:
            raise ValueError("SERIAL_INGEST_TOKEN debe contener al menos 24 caracteres.")
        return configured
    path = Path(database_path).parent / "serial.token"
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        token = path.read_text(encoding="utf-8").strip()
    else:
        token = secrets.token_urlsafe(32)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(token)
    if len(token) < 24:
        raise ValueError("Token serial vacío/inválido; revisar el archivo local serial.token.")
    return token


def device_view(device: Device, now: datetime | None = None) -> DeviceRead:
    result = DeviceRead.model_validate(device)
    if device.hardware_id is None or device.status == "disconnected":
        return result
    age = None if device.last_heartbeat_at is None else ((now or utc_now()) - device.last_heartbeat_at).total_seconds()
    current = "connected" if age is not None and 0 <= age <= HEARTBEAT_TTL_SECONDS else "stale"
    return result.model_copy(update={"status": current})


def ingest_event(session: Session, event: SerialEventInput) -> dict:
    if session.get(DeviceEvent, event.event_id) is not None:
        return {"accepted": False, "reason": "duplicate"}
    received = event.received_at.astimezone(timezone.utc)
    device = None
    message = event.message
    if message is not None:
        device = session.exec(select(Device).where(Device.hardware_id == message.device_id)).first()
        if device is not None:
            duplicate = session.exec(select(DeviceEvent.id).where(
                DeviceEvent.device_id == device.id, DeviceEvent.boot_id == message.boot_id,
                DeviceEvent.sequence == message.sequence,
            )).first()
            if duplicate is not None:
                return {"accepted": False, "reason": "duplicate"}
            if device.boot_id == message.boot_id:
                if message.sequence <= (device.last_sequence if device.last_sequence is not None else -1):
                    return {"accepted": False, "reason": "out_of_order"}
                if device.uptime_ms is not None and message.uptime_ms < device.uptime_ms:
                    return {"accepted": False, "reason": "uptime_regressed"}
            elif session.exec(select(DeviceEvent.id).where(
                DeviceEvent.device_id == device.id, DeviceEvent.boot_id == message.boot_id,
            )).first() is not None:
                return {"accepted": False, "reason": "retired_boot"}
            if device.last_seen_at is not None and received < device.last_seen_at:
                return {"accepted": False, "reason": "old_reception"}
        else:
            # Reuse a single manually configured placeholder on this port.
            candidates = session.exec(select(Device).where(
                Device.hardware_id.is_(None), Device.serial_port == event.port,
            )).all()
            device = candidates[0] if len(candidates) == 1 else Device(name="ESP32 principal")
        if device.boot_id != message.boot_id:
            device.last_heartbeat_at = None
        device.kind = "esp32"
        device.hardware_id = message.device_id
        device.model = message.chip_model
        device.serial_port = event.port
        device.firmware_version = message.firmware_version
        device.boot_id = message.boot_id
        device.last_sequence = message.sequence
        device.uptime_ms = message.uptime_ms
        device.last_seen_at = received
        if message.type == "heartbeat":
            device.last_heartbeat_at = received
        if device.connection_updated_at is None or received >= device.connection_updated_at:
            device.status = "connected"
            device.connection_updated_at = received
        session.add(device)
        session.flush()
    elif event.kind in ("disconnected", "reader_stopped"):
        devices = session.exec(select(Device).where(Device.serial_port == event.port, Device.hardware_id.is_not(None))).all()
        for target in devices:
            if target.connection_updated_at is None or received >= target.connection_updated_at:
                target.status = "disconnected"
                target.connection_updated_at = received
                session.add(target)
        if len(devices) == 1:
            device = devices[0]
    diagnostic = DeviceEvent(
        id=event.event_id, device_id=None if device is None else device.id,
        port=event.port, baud_rate=event.baud_rate,
        kind=message.type if message else event.kind,
        boot_id=message.boot_id if message else None,
        sequence=message.sequence if message else None,
        received_at=received,
        payload=message.model_dump() if message else {"detail": event.detail},
    )
    session.add(diagnostic)
    session.commit()
    return {"accepted": True, "device_id": None if device is None else str(device.id)}
