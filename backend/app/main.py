"""API local. Inicio: python -m uvicorn app.main:app --host 127.0.0.1."""

from collections.abc import Generator
from contextlib import asynccontextmanager
from typing import Annotated
from uuid import UUID
from ipaddress import ip_address
import hmac

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import func, text
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from .database import build_engine, migrate_database, utc_now
from .decision_routes import router as decision_router
from .models import Device, DeviceEvent, Measurement, Zone
from .schemas import DeviceCreate, DeviceRead, DeviceEventRead, HealthRead, TelemetryRead, ZoneCreate, ZoneRead
from .device_service import device_view, ingest_event, load_ingest_token
from .serial_protocol import SerialEventInput


def get_session(request: Request) -> Generator[Session, None, None]:
    with Session(request.app.state.engine) as session:
        yield session


DatabaseSession = Annotated[Session, Depends(get_session)]
router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthRead, responses={503: {"model": HealthRead}})
def health(request: Request, response: Response) -> HealthRead:
    try:
        with request.app.state.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthRead(status="error", database="unavailable", timestamp=utc_now())
    return HealthRead(status="ok", database="connected", timestamp=utc_now())


@router.get("/zones", response_model=list[ZoneRead])
def list_zones(session: DatabaseSession) -> list[Zone]:
    return list(session.exec(select(Zone).order_by(Zone.created_at, Zone.id)).all())


@router.post("/zones", response_model=ZoneRead, status_code=status.HTTP_201_CREATED)
def create_zone(payload: ZoneCreate, session: DatabaseSession) -> Zone:
    zone = Zone(**payload.model_dump())
    session.add(zone)
    session.commit()
    session.refresh(zone)
    return zone


@router.get("/devices", response_model=list[DeviceRead])
def list_devices(session: DatabaseSession) -> list[DeviceRead]:
    return [device_view(device) for device in session.exec(select(Device).order_by(Device.created_at, Device.id)).all()]


@router.post("/devices", response_model=DeviceRead, status_code=status.HTTP_201_CREATED)
def create_device(payload: DeviceCreate, session: DatabaseSession) -> DeviceRead:
    device = Device(**payload.model_dump())
    session.add(device)
    session.commit()
    session.refresh(device)
    return device_view(device)


@router.get("/devices/{device_id}/events", response_model=list[DeviceEventRead])
def device_events(device_id: UUID, session: DatabaseSession, limit: Annotated[int, Query(ge=1, le=200)] = 50):
    if session.get(Device, device_id) is None:
        raise HTTPException(404, "Dispositivo no encontrado.")
    return session.exec(select(DeviceEvent).where(DeviceEvent.device_id == device_id)
                        .order_by(DeviceEvent.received_at.desc(), DeviceEvent.id).limit(limit)).all()


@router.post("/internal/serial-events")
def receive_serial(event: SerialEventInput, request: Request, session: DatabaseSession):
    try:
        local = request.client is not None and ip_address(request.client.host).is_loopback
    except ValueError:
        local = False
    supplied = request.headers.get("X-Serial-Token", "")
    if not local or request.headers.get("origin") or not hmac.compare_digest(supplied, request.app.state.serial_token):
        raise HTTPException(403, "Interfaz reservada al lector serial local autorizado.")
    return ingest_event(session, event)


@router.get("/telemetry", response_model=TelemetryRead)
def list_telemetry(
    session: DatabaseSession,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    zone_id: UUID | None = None,
    device_id: UUID | None = None,
) -> TelemetryRead:
    filters = [Measurement.source == "real"]
    if zone_id is not None:
        filters.append(Measurement.zone_id == zone_id)
    if device_id is not None:
        filters.append(Measurement.device_id == device_id)
    query = select(Measurement).where(*filters)
    total = session.exec(select(func.count()).select_from(Measurement).where(*filters)).one()
    measurements = session.exec(
        query.order_by(Measurement.measured_at.desc(), Measurement.id).offset(offset).limit(limit)
    ).all()
    return TelemetryRead(items=list(measurements), total=total, queried_at=utc_now())


def create_app(database_url: str | None = None) -> FastAPI:
    engine = build_engine(database_url)

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        try:
            migrate_database(engine)
            application.state.serial_token = load_ingest_token(str(engine.url.database))
            yield
        finally:
            engine.dispose()

    application = FastAPI(
        title="LEKIL KUXLEJAL · DOMO VITAL",
        version="0.3.0",
        description=(
            "Fase 2A: configuración y diagnóstico serial del ESP32, sin sensores. "
            "Fase 2B: escenarios hipotéticos con Itzamná y revisión humana, separados de telemetría. "
            "Modo observación. Control físico deshabilitado. "
            "API local sin autenticación; iniciar exclusivamente en 127.0.0.1."
        ),
        lifespan=lifespan,
    )
    application.state.engine = engine
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
        ],
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

    @application.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": "La base de datos no está disponible."})

    application.include_router(router)
    application.include_router(decision_router)
    return application


app = create_app()
