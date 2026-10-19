"""Todos los pasaportes y ejemplos de esta suite se crean en SQLite temporal."""

from copy import deepcopy
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from alembic import command
from alembic.config import Config

from app.database import BACKEND_DIR, build_engine, migration_connection
from app.main import create_app
from app.seed_schemas import CRITERIA, DEFAULT_WEIGHTS


def passport(code='PRUEBA-01', authorized=False, **changes):
    result = {'common_name': 'Lote de prueba temporal', 'code': code, 'source_kind': 'real'}
    if authorized:
        result.update(authorization_status='authorized', use_conditions='Uso limitado al ensayo temporal',
                      authorization_source='Documento de prueba en base temporal')
    return result | changes


def create(client, **kw):
    response = client.post('/api/seeds/lots', json=passport(**kw))
    assert response.status_code == 201, response.text
    return response.json()


def data(lot):
    return {k: v for k, v in lot.items() if k not in ('id', 'revision', 'created_at', 'updated_at')}


def assess(client, lot, complete=True, score=4, profile_id=None):
    payload = {'expected_revision': lot['revision'], 'weight_profile_id': profile_id,
               'responsible': 'Rol de prueba', 'scores': {key: {'value': score, 'justification': 'Valoración de ensayo',
                        'source': 'Fuente temporal explícita'} for key in CRITERIA}}
    if not complete:
        payload['scores']['nutrition'] = None
    response = client.post(f'/api/seeds/lots/{lot["id"]}/assessments', json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def compare(client, lots):
    response = client.post('/api/seeds/compare', json={'lot_ids': [lot['id'] for lot in lots]})
    assert response.status_code == 200, response.text
    return response.json()


def decision(lot, action='conservar'):
    return {'expected_revision': lot['revision'], 'action': action, 'responsible': 'Responsable de prueba',
            'reason': 'Revisión humana documentada del lote'}


def test_empty_bank_and_no_physical_changes(client, application):
    assert client.get('/api/seeds/lots').json() == []
    profile = client.get('/api/seeds/weights').json()
    assert profile['id'] is None and profile['weights'] == DEFAULT_WEIGHTS
    lot = create(client)
    assert lot['quantity'] is None and lot['received_on'] is None and lot['tests'] == []
    assert lot['authorization_status'] == 'pending'
    for path in ('zones', 'devices', 'decisions/runs'):
        assert client.get('/api/' + path).json() == []
    assert client.get('/api/telemetry').json()['total'] == 0
    with application.state.engine.connect() as connection:
        assert connection.execute(text('PRAGMA foreign_keys')).scalar_one() == 1
        assert connection.execute(text('SELECT count(*) FROM seed_weight_profiles')).scalar_one() == 0


def test_create_edit_restart_and_revision_history(database_url):
    with TestClient(create_app(database_url)) as client:
        lot = create(client, quantity=0, unit='semillas', custodian_entity='Entidad de prueba',
                     tests=[{'kind': 'germination', 'result': 'Resultado de ensayo temporal', 'source': 'Registro de prueba'}])
        changed = data(lot) | {'quantity': 12.5, 'unit': 'g', 'received_on': '2026-10-19',
                               'storage_conditions': 'Condiciones documentadas de ensayo'}
        response = client.put(f'/api/seeds/lots/{lot["id"]}', json={'expected_revision': 1, 'passport': changed})
        assert response.status_code == 200
        assert response.json()['revision'] == 2
        assert client.put(f'/api/seeds/lots/{lot["id"]}', json={'expected_revision': 1, 'passport': changed}).status_code == 409
    with TestClient(create_app(database_url)) as reopened:
        saved = reopened.get(f'/api/seeds/lots/{lot["id"]}').json()
        assert saved['quantity'] == 12.5 and saved['tests'][0]['method'] is None
        assert saved['updated_at'].endswith('Z')
        history = reopened.get(f'/api/seeds/lots/{lot["id"]}/history').json()
        assert [r['revision'] for r in history['revisions']] == [2, 1]
        assert history['revisions'][1]['passport']['quantity'] == 0


@pytest.mark.parametrize('changes', [
    {'quantity': -1, 'unit': 'g'}, {'quantity': 1}, {'common_name': '  '}, {'code': ' '},
    {'authorization_status': 'authorized'}, {'authorization_status': 'denied'},
    {'authorization_status': 'authorized', 'authorization_source': 'Fuente sin condiciones'},
    {'source_kind': 'sensor'}, {'received_on': '2026-02-30'}, {'custodian_person': 'Dato personal'},
    {'tests': [{'kind': 'germination', 'result': 'Sin fuente'}]},
])
def test_invalid_or_unsupported_data_rejected(client, changes):
    assert client.post('/api/seeds/lots', json=passport(**changes)).status_code == 422
    assert client.get('/api/seeds/lots').json() == []


def test_identity_duplicate_and_type_separation(client):
    lot = create(client)
    assert client.post('/api/seeds/lots', json=passport()).status_code == 409
    assert client.put(f'/api/seeds/lots/{lot["id"]}', json={'expected_revision': 1,
                     'passport': data(lot) | {'source_kind': 'hypothetical'}}).status_code == 422
    example = create(client, code='EJEMPLO', source_kind='hypothetical')
    assert client.post('/api/seeds/compare', json={'lot_ids': [lot['id'], example['id']]}).status_code == 422
    assert len(client.get('/api/seeds/lots?source_kind=real').json()) == 1
    assert len(client.get('/api/seeds/lots?source_kind=hypothetical').json()) == 1
    assert client.get('/api/seeds/lots?source_kind=inventado').status_code == 422


@pytest.mark.parametrize('status', ['pending', 'denied'])
def test_pending_or_denied_authorization_does_not_become_permission(client, status):
    lot = create(client, authorization_status=status,
                 **({'authorization_source': 'Denegación temporal'} if status == 'denied' else {}))
    for action in ('conservar', 'retirar', 'repetir_prueba'):
        response = client.post(f'/api/seeds/lots/{lot["id"]}/decisions', json=decision(lot, action))
        assert response.status_code == 201
    assert client.post(f'/api/seeds/lots/{lot["id"]}/decisions', json=decision(lot, 'sembrar')).status_code == 422
    assert client.get(f'/api/seeds/lots/{lot["id"]}').json()['authorization_status'] == status


def test_incomplete_assessment_never_creates_global_ranking(client):
    first, second = create(client), create(client, code='DOS')
    saved = assess(client, first, complete=False)
    assert saved['total'] is None and saved['scores']['nutrition'] is None
    result = compare(client, [first, second])
    assert result['complete'] is False and all(row['total'] is None for row in result['rows'])
    assert result['rows'][1]['assessment'] is None
    assert 'ranking' not in result


def test_scores_need_all_keys_finite_range_and_evidence(client):
    lot = create(client)
    payload = {'expected_revision': 1, 'responsible': 'Rol', 'scores': {key: None for key in CRITERIA}}
    for score in ({'value': 6, 'justification': 'a', 'source': 'b'}, {'value': -1, 'justification': 'a', 'source': 'b'},
                  {'value': 3, 'justification': ' ', 'source': 'b'}, {'value': 3, 'justification': 'a'},
                  {'value': 'NaN', 'justification': 'a', 'source': 'b'}):
        invalid = deepcopy(payload); invalid['scores']['nutrition'] = score
        assert client.post(f'/api/seeds/lots/{lot["id"]}/assessments', json=invalid).status_code == 422
    del payload['scores']['nutrition']
    assert client.post(f'/api/seeds/lots/{lot["id"]}/assessments', json=payload).status_code == 422


def test_weighted_calculation_zero_and_full_scores(client):
    first, second = create(client), create(client, code='DOS')
    zero = assess(client, first, score=0)
    assert zero['total'] == 0
    payload = {'expected_revision': 1, 'responsible': 'Rol', 'scores': {key: {'value': i, 'justification': 'a', 'source': 'b'} for i, key in enumerate(CRITERIA)}}
    response = client.post(f'/api/seeds/lots/{second["id"]}/assessments', json=payload)
    assert response.status_code == 201 and response.json()['total'] == pytest.approx(2.05)
    result = compare(client, [first, second])
    assert result['complete'] is True
    assert [row['lot']['id'] for row in result['rows']] == [first['id'], second['id']]  # no ranking automático


def test_weight_revisions_do_not_rewrite_evidence(client):
    first, second = create(client), create(client, code='DOS')
    saved = assess(client, first)
    assess(client, second)
    weights = dict(DEFAULT_WEIGHTS, nutrition=30, resources=15)
    response = client.post('/api/seeds/weights', json={'weights': weights, 'responsible': 'Rol', 'reason': 'Revisión de sensibilidad'})
    assert response.status_code == 201
    profile = response.json()
    assert compare(client, [first, second])['complete'] is False
    assert client.get(f'/api/seeds/lots/{first["id"]}/history').json()['assessments'][0] == saved
    assess(client, first, profile_id=profile['id']); assess(client, second, profile_id=profile['id'])
    assert compare(client, [first, second])['complete'] is True
    for invalid in (dict(weights, nutrition=31), {'nutrition': 100}, dict(weights, resilience=-10)):
        assert client.post('/api/seeds/weights', json={'weights': invalid, 'responsible': 'Rol', 'reason': 'Motivo'}).status_code == 422


def test_manual_selection_snapshot_persists_and_detects_stale_comparison(database_url):
    with TestClient(create_app(database_url)) as client:
        first, second = create(client, authorized=True), create(client, code='DOS', authorized=True)
        assess(client, first); assess(client, second, score=5)
        compared = compare(client, [first, second])
        payload = decision(first, 'seleccionar') | {'comparison': {'lot_ids': [first['id'], second['id']]},
                                                    'comparison_hash': compared['comparison_hash']}
        assert client.get(f'/api/seeds/lots/{first["id"]}/history').json()['decisions'] == []
        # La persona puede elegir el de menor puntuación con motivo explícito.
        selected = client.post(f'/api/seeds/lots/{first["id"]}/decisions', json=payload)
        assert selected.status_code == 201
        assert selected.json()['snapshot']['comparison'] == compared
        update = client.put(f'/api/seeds/lots/{second["id"]}', json={'expected_revision': 1,
                              'passport': data(second) | {'observations': 'Nueva evidencia'}})
        assert update.status_code == 200
        assert client.post(f'/api/seeds/lots/{first["id"]}/decisions', json=payload).status_code == 422
        assess(client, update.json())
        assert client.post(f'/api/seeds/lots/{first["id"]}/decisions', json=payload).status_code == 409
    with TestClient(create_app(database_url)) as client:
        history = client.get(f'/api/seeds/lots/{first["id"]}/history').json()
        assert len(history['decisions']) == 1
        assert history['decisions'][0] == selected.json()
        assert client.get('/api/seeds/weights').json()['weights'] == DEFAULT_WEIGHTS
        assert client.get('/api/telemetry').json()['items'] == []


def test_decisions_require_human_reason_and_valid_context(client):
    lot = create(client, authorized=True)
    endpoint = f'/api/seeds/lots/{lot["id"]}/decisions'
    for invalid in (decision(lot) | {'reason': ' '}, decision(lot) | {'responsible': ''}, decision(lot, 'seleccionar'),
                    decision(lot) | {'action': 'automatico'}):
        assert client.post(endpoint, json=invalid).status_code == 422
    assert client.post(endpoint, json=decision(lot) | {'expected_revision': 99}).status_code == 409
    assert client.post(endpoint, json=decision(lot, 'sembrar')).status_code == 201
    assert client.post('/api/seeds/compare', json={'lot_ids': [lot['id'], lot['id']]}).status_code == 422
    assert client.get(f'/api/seeds/lots/{uuid4()}').status_code == 404


def test_migration_preserves_prior_decision_history(database_url):
    config = Config(str(BACKEND_DIR / 'alembic.ini'))
    config.set_main_option('script_location', str(BACKEND_DIR / 'migrations'))
    engine = build_engine(database_url)
    identifier = uuid4().hex
    with migration_connection(engine) as connection:
        config.attributes['connection'] = connection
        command.upgrade(config, '0003_decisions')
        connection.execute(text("INSERT INTO decision_runs (id,created_at,source,parameters,result,engine_fingerprint,snapshot_sha256) VALUES (:id,'2026-10-19','hypothetical','{}','{}',:fingerprint,:hash)"),
                           {'id': identifier, 'fingerprint': 'a' * 64, 'hash': 'b' * 64})
    engine.dispose()
    with TestClient(create_app(database_url)) as client:
        assert client.get('/api/seeds/lots').json() == []
        with client.app.state.engine.connect() as connection:
            row = connection.execute(text('SELECT id,snapshot_sha256 FROM decision_runs')).one()
            assert row == (identifier, 'b' * 64)
            assert connection.execute(text('PRAGMA foreign_key_check')).all() == []


def test_assessment_must_reference_an_existing_passport_revision(client, application):
    lot = create(client)
    with pytest.raises(IntegrityError), application.state.engine.begin() as connection:
        connection.execute(text("INSERT INTO seed_assessments (id,lot_id,lot_revision,weights,scores,responsible,created_at) VALUES (:id,:lot,99,'{}','{}','Rol temporal','2026-10-19')"),
                           {'id': uuid4().hex, 'lot': UUID(lot['id']).hex})


def test_selection_cannot_promote_pending_authorization(client):
    first, second = create(client), create(client, code='DOS')
    assess(client, first); assess(client, second)
    compared = compare(client, [first, second])
    assert compared['complete'] is True
    payload = decision(first, 'seleccionar') | {'comparison': {'lot_ids': [first['id'], second['id']]},
                                                'comparison_hash': compared['comparison_hash']}
    assert client.post(f'/api/seeds/lots/{first["id"]}/decisions', json=payload).status_code == 422
    assert client.get(f'/api/seeds/lots/{first["id"]}/history').json()['decisions'] == []


def test_weight_profiles_persist_and_reject_stale_assessment(database_url):
    with TestClient(create_app(database_url)) as client:
        lot = create(client)
        old = assess(client, lot)
        weights = dict(DEFAULT_WEIGHTS, nutrition=26, resources=19)
        profile = client.post('/api/seeds/weights', json={'weights': weights, 'responsible': 'Rol temporal',
                                                        'reason': 'Revisión documentada'}).json()
        payload = {'expected_revision': 1, 'responsible': 'Rol temporal', 'scores': old['scores']}
        assert client.post(f'/api/seeds/lots/{lot["id"]}/assessments', json=payload).status_code == 409
        updated = assess(client, lot, profile_id=profile['id'])
    with TestClient(create_app(database_url)) as client:
        assert client.get('/api/seeds/weights').json() == profile
        history = client.get(f'/api/seeds/lots/{lot["id"]}/history').json()
        assert history['assessments'] == [updated, old]
