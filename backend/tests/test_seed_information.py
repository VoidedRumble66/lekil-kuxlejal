"""Investigación auténtica y compatibilidad, siempre en bases temporales."""

import json
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import create_app
from app.seed_schemas import record_group
from test_seeds import assess, create, data, decision


def evidence(kind='documentary', **changes):
    # Texto de ensayo de contrato; no afirma resultados científicos de una especie.
    return {'kind': kind, 'subject': 'Dato documental de prueba', 'content': 'Contenido de prueba temporal',
            'recorded_on': '2026-10-19', 'method': 'Revisión documental de prueba',
            'source': 'Referencia temporal de la suite, no bibliografía científica real', **changes}


def study(client, code='ESTUDIO', **changes):
    return create(client, code=code, source_kind='hypothetical', record_kind='study', **changes)


def test_documentary_research_without_inventory_or_sensors(client):
    lot = study(client, information_source='Referencia general de prueba', evidence=[evidence()])
    assert lot['record_kind'] == 'study' and record_group(lot) == 'study'
    assert lot['quantity'] is None and lot['unit'] is None and lot['received_on'] is None
    assert lot['authorization_status'] == 'pending'
    assert lot['evidence'][0]['kind'] == 'documentary'
    assert client.get('/api/telemetry').json()['items'] == []
    assert client.get('/api/devices').json() == []
    assert client.get('/api/zones').json() == []


@pytest.mark.parametrize('kind', ['documentary', 'manual', 'instrumental', 'calculation', 'simulation'])
def test_evidence_types_persist_separately_across_restart(database_url, kind):
    extra = {'instrument': 'Instrumento externo y registro de prueba'} if kind == 'instrumental' else {}
    if kind == 'simulation':
        extra['assumptions'] = 'Supuestos explícitos de una ejecución de prueba'
    item = evidence(kind, value=0, unit='unidad de prueba', **extra)
    with TestClient(create_app(database_url)) as client:
        lot = study(client, evidence=[item])
        assert lot['evidence'][0]['kind'] == kind
    with TestClient(create_app(database_url)) as client:
        saved = client.get(f'/api/seeds/lots/{lot["id"]}').json()
        assert saved == lot
        assert saved['evidence'][0]['value'] == 0
        assert client.get('/api/telemetry').json()['items'] == []


@pytest.mark.parametrize('changes', [
    {'source': ''}, {'method': ' '}, {'recorded_on': None}, {'recorded_on': 'fecha desconocida'},
    {'value': 1}, {'value': 'NaN', 'unit': 'u'}, {'kind': 'sensor_auto'},
    {'kind': 'instrumental'}, {'kind': 'simulation'},
])
def test_missing_or_misclassified_provenance_rejected(client, changes):
    response = client.post('/api/seeds/lots', json={'common_name': 'Prueba temporal', 'code': 'INVALIDO',
                           'source_kind': 'hypothetical', 'record_kind': 'study',
                           'evidence': [evidence(**changes)]})
    assert response.status_code == 422
    assert client.get('/api/seeds/lots').json() == []


def test_study_and_simulation_cannot_claim_stock_or_change_to_physical(client):
    for extra in ({'quantity': 2, 'unit': 'semillas'}, {'quantity': 0, 'unit': 'g'}, {'unit': 'g'}):
        response = client.post('/api/seeds/lots', json={'common_name': 'Temporal', 'code': 'NO-STOCK',
                               'source_kind': 'hypothetical', 'record_kind': 'study', **extra})
        assert response.status_code == 422
    lot = study(client)
    assert client.put(f'/api/seeds/lots/{lot["id"]}', json={'expected_revision': 1,
                      'passport': data(lot) | {'source_kind': 'real', 'record_kind': 'inventory'}}).status_code == 422
    assert client.put(f'/api/seeds/lots/{lot["id"]}', json={'expected_revision': 1,
                      'passport': data(lot) | {'quantity': 10, 'unit': 'g'}}).status_code == 422


def test_simulation_requires_assumptions_and_does_not_accept_documentary_facts(client):
    base = {'common_name': 'Simulación temporal', 'code': 'SIM', 'source_kind': 'hypothetical', 'record_kind': 'simulation'}
    assert client.post('/api/seeds/lots', json=base).status_code == 422
    base['scenario_assumptions'] = 'Escenario supuesto explícito de prueba'
    assert client.post('/api/seeds/lots', json=base | {'evidence': [evidence()]}).status_code == 422
    response = client.post('/api/seeds/lots', json=base | {'evidence': [evidence('simulation', assumptions='Supuestos de ejecución de prueba')]})
    assert response.status_code == 201 and response.json()['quantity'] is None
    # Un cliente previo que omite la clasificación no puede saltarse su validación.
    lot = response.json()
    incoming = data(lot) | {'evidence': [evidence()]}
    del incoming['record_kind']; del incoming['scenario_assumptions']
    assert client.put(f'/api/seeds/lots/{lot["id"]}', json={'expected_revision': 1, 'passport': incoming}).status_code == 422


def test_comparison_keeps_studies_inventory_simulation_and_legacy_apart(client):
    first, second = study(client), study(client, code='ESTUDIO-2')
    assess(client, first); assess(client, second)
    response = client.post('/api/seeds/compare', json={'lot_ids': [first['id'], second['id']]})
    assert response.status_code == 200 and response.json()['complete'] is True
    others = [create(client, code='FISICO', record_kind='inventory'),
              create(client, code='ANTERIOR', source_kind='hypothetical'),
              create(client, code='SIMULADO', source_kind='hypothetical', record_kind='simulation', scenario_assumptions='Supuestos temporales')]
    for other in others:
        assert client.post('/api/seeds/compare', json={'lot_ids': [first['id'], other['id']]}).status_code == 422


def test_legacy_json_reads_do_not_rewrite_or_promote_history(client, application):
    lot = create(client, source_kind='hypothetical', quantity=3, unit='u', authorized=True,
                 tests=[{'kind': 'germination', 'result': 'Resultado anterior de prueba', 'source': 'Fuente anterior'}])
    assess(client, lot)
    assert client.post(f'/api/seeds/lots/{lot["id"]}/decisions', json=decision(lot)).status_code == 201
    legacy = data(lot)
    for key in ('record_kind', 'evidence', 'scenario_assumptions'):
        del legacy[key]
    raw = json.dumps(legacy, ensure_ascii=False)
    with application.state.engine.begin() as connection:
        connection.execute(text('UPDATE seed_lots SET passport=:raw WHERE id=:id'), {'raw': raw, 'id': lot['id'].replace('-', '')})
        connection.execute(text('UPDATE seed_lot_revisions SET passport=:raw WHERE lot_id=:id'), {'raw': raw, 'id': lot['id'].replace('-', '')})
    before = client.get(f'/api/seeds/lots/{lot["id"]}/history').json()
    for _ in range(2):
        viewed = client.get(f'/api/seeds/lots/{lot["id"]}').json()
        assert viewed['record_kind'] is None and record_group(viewed) == 'legacy'
        assert viewed['quantity'] == 3 and viewed['tests'] == lot['tests']
        client.get('/api/seeds/lots')
    with application.state.engine.connect() as connection:
        assert connection.execute(text('SELECT passport FROM seed_lots')).scalar_one() == raw
        assert connection.execute(text('SELECT version_num FROM alembic_version')).scalar_one() == '0004_seeds'
    assert client.get(f'/api/seeds/lots/{lot["id"]}/history').json() == before
    # Revisión humana explícita: añade clasificación, conserva cantidad heredada y auditoría.
    changed = client.put(f'/api/seeds/lots/{lot["id"]}', json={'expected_revision': 1, 'passport': legacy | {'record_kind': 'study'}})
    assert changed.status_code == 200 and changed.json()['quantity'] == 3
    after = client.get(f'/api/seeds/lots/{lot["id"]}/history').json()
    assert after['assessments'] == before['assessments'] and after['decisions'] == before['decisions']
    assert after['revisions'][1:] == before['revisions']
    assert after['revisions'][0]['passport']['record_kind'] == 'study'


def test_older_client_update_preserves_new_metadata_and_permissions(client):
    lot = study(client, authorized=True, evidence=[evidence()], information_source='Fuente general documentada')
    incoming = deepcopy(data(lot))
    for key in ('record_kind', 'evidence', 'scenario_assumptions'):
        del incoming[key]
    incoming['observations'] = 'Anotación nueva del cliente anterior'
    response = client.put(f'/api/seeds/lots/{lot["id"]}', json={'expected_revision': 1, 'passport': incoming})
    assert response.status_code == 200
    saved = response.json()
    assert saved['evidence'] == lot['evidence'] and saved['record_kind'] == 'study'
    assert saved['authorization_status'] == 'authorized' and saved['authorization_source'] == lot['authorization_source']
    assert saved['code'] == lot['code'] and saved['id'] == lot['id']
