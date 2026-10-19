"""API local de gobernanza hipotética. Registrar una revisión no ejecuta acciones."""

from collections.abc import Generator
from hashlib import sha256
import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from .decision_models import DecisionReview, DecisionRun
from .decision_schemas import ReviewInput, ReviewRead, RunRead, RunSummary, ScenarioInput
from .itzamna_adapter import compare, engine_fingerprint

router = APIRouter(prefix="/api/decisions", tags=["Escenarios hipotéticos"])


def get_session(request: Request) -> Generator[Session, None, None]:
    with Session(request.app.state.engine) as session:
        yield session


DatabaseSession = Annotated[Session, Depends(get_session)]


def snapshot_hash(parameters: dict, result: dict, fingerprint: str) -> str:
    return sha256(json.dumps({"parameters": parameters, "result": result, "engine": fingerprint},
                             sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def read_run(session: Session, run_id: UUID) -> RunRead:
    run = session.get(DecisionRun, run_id)
    if run is None:
        raise HTTPException(404, "Comparación hipotética no encontrada.")
    reviews = session.exec(select(DecisionReview).where(DecisionReview.run_id == run_id)
                           .order_by(DecisionReview.created_at, DecisionReview.id)).all()
    return RunRead(**run.model_dump(), reviews=[ReviewRead(**r.model_dump()) for r in reviews])


@router.post("/runs", response_model=RunRead, status_code=201)
def create_run(parameters: ScenarioInput, session: DatabaseSession):
    result = compare(parameters)
    saved_parameters = parameters.model_dump(mode="json")
    fingerprint = engine_fingerprint()
    run = DecisionRun(parameters=saved_parameters, result=result, engine_fingerprint=fingerprint,
                      snapshot_sha256=snapshot_hash(saved_parameters, result, fingerprint))
    session.add(run)
    session.commit()
    session.refresh(run)
    return read_run(session, run.id)


@router.get("/runs", response_model=list[RunSummary])
def list_runs(session: DatabaseSession, limit: Annotated[int, Query(ge=1, le=100)] = 30,
              offset: Annotated[int, Query(ge=0)] = 0):
    runs = session.exec(select(DecisionRun).order_by(DecisionRun.created_at.desc(), DecisionRun.id)
                        .offset(offset).limit(limit)).all()
    return [RunSummary(id=r.id, name=r.parameters["name"], created_at=r.created_at,
                       status=r.result["status"], alternative_count=len(r.result["alternatives"])) for r in runs]


@router.get("/runs/{run_id}", response_model=RunRead)
def get_run(run_id: UUID, session: DatabaseSession):
    return read_run(session, run_id)


@router.post("/runs/{run_id}/reviews", response_model=ReviewRead, status_code=201)
def create_review(run_id: UUID, value: ReviewInput, session: DatabaseSession):
    run = read_run(session, run_id)
    if value.alternative_id not in {a["id"] for a in run.result["alternatives"] if a["feasible"]}:
        raise HTTPException(422, "La alternativa no pertenece a esta comparación factible.")
    review = DecisionReview(run_id=run_id, **value.model_dump())
    session.add(review)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "La alternativa ya fue revisada o existe otra aprobada en esta comparación.")
    session.refresh(review)
    return ReviewRead(**review.model_dump())
