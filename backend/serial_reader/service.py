"""UART de sólo lectura -> cola acotada -> interfaz HTTP local autenticada."""

from collections import deque
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import secrets
import signal
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

import serial

from app.serial_protocol import MAX_LINE_BYTES, SerialEventInput, parse_line

LOGGER = logging.getLogger("lekil.serial")


class PermanentRejection(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class BackendClient:
    def __init__(self, base_url: str, token_file: Path):
        url = urlsplit(base_url)
        if (url.scheme != "http" or url.hostname not in ("127.0.0.1", "localhost", "::1")
                or url.username or url.password or url.query or url.fragment or url.path not in ("", "/")):
            raise ValueError("El backend serial debe ser HTTP local, sin ruta ni credenciales en la URL.")
        self.url = base_url.rstrip("/") + "/api/internal/serial-events"
        self.token_file = token_file
        self.opener = build_opener(ProxyHandler({}), NoRedirect())

    def __call__(self, event: SerialEventInput):
        token = os.environ.get("SERIAL_INGEST_TOKEN") or self.token_file.read_text(encoding="utf-8").strip()
        if len(token) < 24:
            raise OSError("Token serial no disponible; inicia primero el backend.")
        request = Request(self.url, data=event.model_dump_json().encode("utf-8"), method="POST",
                          headers={"Content-Type": "application/json", "X-Serial-Token": token})
        try:
            with self.opener.open(request, timeout=2) as response:
                result = json.loads(response.read(4096))
                if not isinstance(result, dict) or not isinstance(result.get("accepted"), bool):
                    raise OSError("Confirmación inválida de la API local.")
                return result
        except HTTPError as error:
            if 400 <= error.code < 500 and error.code not in (403, 429):
                raise PermanentRejection(f"API rechazó el evento: HTTP {error.code}") from error
            raise


class SerialReader:
    def __init__(self, port, deliver, *, serial_factory=serial.Serial, stop=None,
                 clock=time.monotonic, now=None, queue_limit=128):
        self.port_name = port
        self.deliver = deliver
        self.serial_factory = serial_factory
        self.stop = stop if stop is not None else threading.Event()
        self.clock = clock
        self.now = now or (lambda: datetime.now(timezone.utc))
        self.queue = deque()
        self.queue_limit = queue_limit
        self.port = None
        self.buffer = bytearray()
        self.discarding = False
        self.partial_since = None
        self.next_open = 0.0
        self.next_delivery = 0.0
        self.backoff = 1.0
        self.disconnect_reported = False
        self.last_protocol_report = float("-inf")
        self.seen = set()
        self.seen_order = deque()

    def enqueue(self, kind, *, message=None, detail=None):
        event = SerialEventInput(event_id=secrets.token_hex(16), port=self.port_name,
                                 received_at=self.now(), kind=kind, message=message, detail=detail)
        if len(self.queue) >= self.queue_limit:
            self.queue.popleft()
            LOGGER.error("Cola llena: se descarta el evento más antiguo, sin inventar datos.")
        self.queue.append(event)

    def flush(self):
        if self.clock() < self.next_delivery:
            return
        for _ in range(min(32, len(self.queue))):
            try:
                result = self.deliver(self.queue[0])
            except PermanentRejection as error:
                LOGGER.error("%s", error)
                self.queue.popleft()
                continue
            except (OSError, URLError, ValueError, TimeoutError) as error:
                LOGGER.warning("API no disponible (%s); se reintentará sin cambiar la recepción UTC.", type(error).__name__)
                self.next_delivery = self.clock() + 2
                return
            self.queue.popleft()
            if result and result.get("accepted"):
                LOGGER.info("Diagnóstico confirmado por backend.")

    def close_port(self):
        if self.port is not None:
            try:
                self.port.close()
            except (OSError, serial.SerialException):
                LOGGER.warning("El puerto ya no estaba disponible al cerrarlo.")
            finally:
                self.port = None
        self.buffer.clear()
        self.discarding = False
        self.partial_since = None

    def disconnected(self, error):
        LOGGER.warning("Puerto %s no disponible (%s). Reintento en %.0f s.", self.port_name, type(error).__name__, self.backoff)
        if not self.disconnect_reported:
            self.enqueue("disconnected", detail=f"Puerto no disponible: {type(error).__name__}")
            self.disconnect_reported = True
        self.close_port()
        self.next_open = self.clock() + self.backoff
        self.backoff = min(self.backoff * 2, 15)

    def protocol_error(self, detail):
        LOGGER.warning("Mensaje rechazado: %s", detail)
        if self.clock() - self.last_protocol_report >= 10:
            self.enqueue("protocol_error", detail=detail[:240])
            self.last_protocol_report = self.clock()

    def feed(self, data):
        # Byte framing also handles partial reads, oversized frames and resync.
        for byte in data:
            if self.discarding:
                if byte == 10:
                    self.discarding = False
                continue
            if not self.buffer:
                self.partial_since = self.clock()
            self.buffer.append(byte)
            if len(self.buffer) > MAX_LINE_BYTES:
                self.protocol_error("Línea demasiado larga.")
                self.buffer.clear()
                self.discarding = byte != 10
                self.partial_since = None
            elif byte == 10:
                line = bytes(self.buffer)
                self.buffer.clear()
                self.partial_since = None
                try:
                    message = parse_line(line)
                except (ValueError, UnicodeError):
                    self.protocol_error("JSON o protocolo no válido; se descartó la línea.")
                else:
                    key = (message.device_id, message.boot_id, message.sequence)
                    if key in self.seen:
                        continue
                    if len(self.seen_order) >= 256:
                        self.seen.discard(self.seen_order.popleft())
                    self.seen.add(key)
                    self.seen_order.append(key)
                    self.enqueue("message", message=message)
                    self.disconnect_reported = False
                    self.backoff = 1

    def step(self):
        if self.port is None and self.clock() >= self.next_open:
            try:
                self.port = self.serial_factory(port=None, baudrate=115200, timeout=0.5)
                self.port.dtr = False
                self.port.rts = False
                self.port.port = self.port_name
                self.port.open()
                LOGGER.info("Puerto %s abierto a 115200; esperando JSON Lines.", self.port_name)
            except (OSError, serial.SerialException) as error:
                self.disconnected(error)
        if self.port is not None:
            try:
                data = self.port.read(256)
                if data:
                    self.feed(data)
                if self.partial_since is not None and self.clock() - self.partial_since > 2:
                    self.protocol_error("Línea incompleta: no terminó en 2 segundos.")
                    self.buffer.clear()
                    self.partial_since = None
                    self.discarding = True
            except (OSError, serial.SerialException) as error:
                self.disconnected(error)
        self.flush()

    def run(self):
        try:
            while not self.stop.is_set():
                self.step()
                if self.port is None:
                    self.stop.wait(0.1)
        finally:
            self.close_port()
            self.enqueue("reader_stopped", detail="Lector finalizado; puerto cerrado.")
            self.next_delivery = 0
            self.flush()
            if self.queue:
                LOGGER.warning("Quedan %d diagnósticos sin confirmar; el heartbeat caducará en la API.", len(self.queue))


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Lector real de diagnóstico ESP32; sin escritura serial ni SQLite.")
    parser.add_argument("--port", default=os.environ.get("SERIAL_PORT", "COM6"))
    parser.add_argument("--backend-url", default=os.environ.get("SERIAL_BACKEND_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--token-file", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "serial.token")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        deliver = BackendClient(args.backend_url, args.token_file)
    except ValueError as error:
        parser.error(str(error))
    stop = threading.Event()
    def shutdown(signum, frame):
        stop.set()
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    try:
        SerialReader(args.port, deliver, stop=stop).run()
    except KeyboardInterrupt:
        stop.set()


if __name__ == "__main__":
    main()
