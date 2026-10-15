"""JSON Lines de diagnóstico compartido por API y lector; no contiene sensores."""

import json
from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints, model_validator

MAX_LINE_BYTES = 2048
HEARTBEAT_TTL_SECONDS = 10
Text = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=120)]
Counter = Annotated[int, Field(strict=True, ge=0, le=9223372036854775807)]


class SerialMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    protocol_version: Annotated[int, Field(strict=True, ge=1, le=1)]
    type: Literal["hello", "heartbeat"]
    device_id: Annotated[str, StringConstraints(pattern=r"^esp32-[0-9a-f]{12}$")]
    chip_model: Text
    firmware_version: Text
    boot_id: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{16}$")]
    uptime_ms: Counter
    sequence: Counter

    @model_validator(mode="after")
    def check_sequence(self):
        if (self.type == "hello" and self.sequence != 0) or (self.type == "heartbeat" and self.sequence == 0):
            raise ValueError("hello requiere secuencia 0 y heartbeat una secuencia positiva.")
        if not self.chip_model.startswith("ESP32") or "S3" in self.chip_model.upper():
            raise ValueError("Este protocolo está destinado al ESP32 clásico identificado.")
        return self


class SerialEventInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: Annotated[str, StringConstraints(strict=True, pattern=r"^[0-9a-f]{32}$")]
    port: Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=128)]
    baud_rate: Literal[115200] = 115200
    received_at: AwareDatetime
    kind: Literal["message", "disconnected", "protocol_error", "reader_stopped"]
    message: SerialMessage | None = None
    detail: Annotated[str, StringConstraints(strict=True, max_length=240)] | None = None

    @model_validator(mode="after")
    def check_event(self):
        if (self.kind == "message") != (self.message is not None):
            raise ValueError("Sólo un evento message debe contener un mensaje validado.")
        if self.received_at.timestamp() > datetime.now(timezone.utc).timestamp() + 5:
            raise ValueError("La recepción no puede estar en el futuro.")
        return self


def parse_line(line: bytes) -> SerialMessage:
    if not line.endswith(b"\n"):
        raise ValueError("Línea incompleta: falta el salto de línea.")
    if len(line) > MAX_LINE_BYTES:
        raise ValueError("Línea demasiado larga.")

    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Clave JSON repetida.")
            result[key] = value
        return result

    value = json.loads(line.decode("utf-8"), object_pairs_hook=unique_keys)
    return SerialMessage.model_validate(value)
