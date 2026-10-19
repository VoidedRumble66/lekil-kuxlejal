"""Registro y evaluación provisional de semillas, con decisión humana explícita."""

from collections.abc import Generator
from hashlib import sha256
import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from .database import utc_now
from .seed_models import SeedAssessment, SeedDecision, SeedLot, SeedLotRevision, SeedWeightProfile
from .seed_schemas import (AssessmentInput, CompareInput, CRITERIA, DEFAULT_WEIGHTS,
                           LotRead, LotUpdate, Passport, SeedDecisionInput, WeightsInput)

router = APIRouter(prefix='/api/seeds', tags=['Banco biocultural de semillas'])


def get_session(request: Request) -> Generator[Session, None, None]:
    with Session(request.app.state.engine) as session:
        yield session


DB = Annotated[Session, Depends(get_session)]


def lock_write(session: Session):
    # Serializa validación + escritura: no aprobar sobre pesos o pasaportes obsoletos.
    session.connection().exec_driver_sql('BEGIN IMMEDIATE')


def lot_or_404(session: Session, lot_id: UUID) -> SeedLot:
    lot = session.get(SeedLot, lot_id)
    if lot is None:
        raise HTTPException(404, 'Lote no encontrado.')
    return lot


def lot_view(lot: SeedLot) -> LotRead:
    return LotRead(**lot.passport, id=lot.id, revision=lot.revision,
                   created_at=lot.created_at, updated_at=lot.updated_at)


def check_revision(lot: SeedLot, expected: int):
    if lot.revision != expected:
        raise HTTPException(409, 'El lote cambió. Vuelve a abrirlo y revisa sus datos.')


def current_weights(session: Session) -> dict:
    profile = session.exec(select(SeedWeightProfile).order_by(
        SeedWeightProfile.created_at.desc(), SeedWeightProfile.id.desc()).limit(1)).first()
    return profile.model_dump(mode='json') if profile else {
        'id': None, 'weights': DEFAULT_WEIGHTS, 'responsible': None, 'created_at': None,
        'reason': 'Pesos iniciales propuestos en el capítulo 6.2 del expediente; sujetos a revisión humana.'}


def latest_assessment(session: Session, lot_id: UUID):
    return session.exec(select(SeedAssessment).where(SeedAssessment.lot_id == lot_id)
                        .order_by(SeedAssessment.created_at.desc(), SeedAssessment.id.desc()).limit(1)).first()


@router.get('/lots', response_model=list[LotRead])
def list_lots(session: DB, source_kind: Annotated[str | None, Query(pattern='^(real|hypothetical)$')] = None,
              offset: Annotated[int, Query(ge=0)] = 0, limit: Annotated[int, Query(ge=1, le=200)] = 100):
    query = select(SeedLot)
    if source_kind:
        query = query.where(SeedLot.source_kind == source_kind)
    return [lot_view(lot) for lot in session.exec(query.order_by(SeedLot.created_at, SeedLot.id)
                                                .offset(offset).limit(limit)).all()]


@router.post('/lots', response_model=LotRead, status_code=201)
def create_lot(value: Passport, session: DB):
    lock_write(session)
    lot = SeedLot(code=value.code, source_kind=value.source_kind, passport=value.model_dump(mode='json'))
    session.add(lot)
    try:
        session.flush()
        session.add(SeedLotRevision(lot_id=lot.id, revision=1, passport=lot.passport))
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, 'Ya existe ese código de lote. Utiliza un código único.')
    session.refresh(lot)
    return lot_view(lot)


@router.get('/lots/{lot_id}', response_model=LotRead)
def get_lot(lot_id: UUID, session: DB):
    return lot_view(lot_or_404(session, lot_id))


@router.put('/lots/{lot_id}', response_model=LotRead)
def update_lot(lot_id: UUID, value: LotUpdate, session: DB):
    lock_write(session)
    lot = lot_or_404(session, lot_id)
    check_revision(lot, value.expected_revision)
    if value.passport.source_kind != lot.source_kind:
        raise HTTPException(422, 'Un ejemplo hipotético no puede convertirse en un lote real, ni viceversa. Registra otro lote.')
    lot.code = value.passport.code
    lot.passport = value.passport.model_dump(mode='json')
    lot.revision += 1
    lot.updated_at = utc_now()
    session.add(lot)
    session.add(SeedLotRevision(lot_id=lot.id, revision=lot.revision, passport=lot.passport))
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, 'Ya existe ese código de lote. Utiliza un código único.')
    session.refresh(lot)
    return lot_view(lot)


@router.get('/weights')
def get_weights(session: DB):
    return {**current_weights(session), 'criteria': {key: value[0] for key, value in CRITERIA.items()},
            'scale': 'Escala provisional de la aplicación: 0 a 5; mayor puntuación = mayor preferencia justificada. No es validación científica.'}


@router.post('/weights', status_code=201)
def save_weights(value: WeightsInput, session: DB):
    lock_write(session)
    profile = SeedWeightProfile(**value.model_dump())
    session.add(profile)
    session.commit()
    return get_weights(session)


@router.post('/lots/{lot_id}/assessments', status_code=201)
def save_assessment(lot_id: UUID, value: AssessmentInput, session: DB):
    lock_write(session)
    lot = lot_or_404(session, lot_id)
    check_revision(lot, value.expected_revision)
    weights = current_weights(session)
    if weights['id'] != (str(value.weight_profile_id) if value.weight_profile_id else None):
        raise HTTPException(409, 'Los pesos cambiaron. Recarga y revisa la evaluación.')
    complete = all(score is not None for score in value.scores.values())
    total = round(sum(score.value * weights['weights'][key] / 100 for key, score in value.scores.items()), 6) if complete else None
    record = SeedAssessment(lot_id=lot_id, lot_revision=lot.revision,
                            weight_profile_id=value.weight_profile_id, weights=weights['weights'],
                            scores=value.model_dump(mode='json')['scores'], total=total, responsible=value.responsible)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record.model_dump(mode='json')


def comparison_view(value: CompareInput, session: Session) -> dict:
    weights = current_weights(session)
    rows = []
    kinds = set()
    for lot_id in value.lot_ids:
        lot = lot_or_404(session, lot_id)
        kinds.add(lot.source_kind)
        assessment = latest_assessment(session, lot_id)
        problems = []
        if assessment is None:
            problems.append('Sin evaluación registrada')
        else:
            if assessment.lot_revision != lot.revision:
                problems.append('El pasaporte cambió: revisar puntuaciones')
            if (str(assessment.weight_profile_id) if assessment.weight_profile_id else None) != weights['id']:
                problems.append('Los pesos cambiaron: revisar puntuaciones')
            if assessment.total is None:
                problems.append('Faltan puntuaciones justificadas')
        rows.append({'lot': lot_view(lot).model_dump(mode='json'),
                     'assessment': assessment.model_dump(mode='json') if assessment else None,
                     'problems': problems, 'total': assessment.total if assessment and not problems else None})
    if len(kinds) > 1:
        raise HTTPException(422, 'Compara lotes reales por separado de los ejemplos hipotéticos.')
    result = {'complete': all(not row['problems'] for row in rows), 'rows': rows, 'weights': weights,
              'notice': 'Comparación provisional, sin validación científica ni selección automática. Orden de consulta, no clasificación. Revisa sensibilidad a cambios de pesos antes de decidir.'}
    result['comparison_hash'] = sha256(json.dumps(result, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()
    return result


@router.post('/compare')
def compare_lots(value: CompareInput, session: DB):
    return comparison_view(value, session)


@router.post('/lots/{lot_id}/decisions', status_code=201)
def save_decision(lot_id: UUID, value: SeedDecisionInput, session: DB):
    lock_write(session)
    lot = lot_or_404(session, lot_id)
    check_revision(lot, value.expected_revision)
    if value.action in ('sembrar', 'seleccionar') and lot.passport['authorization_status'] != 'authorized':
        raise HTTPException(422, 'El uso está pendiente de comprobar o denegado. Documenta autorización y condiciones antes de sembrar o seleccionar.')
    comparison = None
    if value.action == 'seleccionar':
        comparison = comparison_view(value.comparison, session)
        if lot_id not in value.comparison.lot_ids or not comparison['complete']:
            raise HTTPException(422, 'Selecciona un lote de una comparación con todas las evaluaciones completas y vigentes.')
        if comparison['comparison_hash'] != value.comparison_hash:
            raise HTTPException(409, 'La comparación cambió. Ejecútala de nuevo antes de decidir.')
    record = SeedDecision(lot_id=lot_id, action=value.action, responsible=value.responsible, reason=value.reason,
                          snapshot={'lot': lot_view(lot).model_dump(mode='json'), 'comparison': comparison,
                                    'effect': 'Registro humano; no modifica existencias, cultivos ni equipos.'})
    session.add(record)
    session.commit()
    session.refresh(record)
    return record.model_dump(mode='json')


@router.get('/lots/{lot_id}/history')
def lot_history(lot_id: UUID, session: DB):
    lot_or_404(session, lot_id)
    def records(model):
        return [row.model_dump(mode='json') for row in session.exec(select(model).where(model.lot_id == lot_id)
                .order_by(model.created_at.desc(), model.id.desc())).all()]
    return {'revisions': records(SeedLotRevision), 'assessments': records(SeedAssessment), 'decisions': records(SeedDecision)}
