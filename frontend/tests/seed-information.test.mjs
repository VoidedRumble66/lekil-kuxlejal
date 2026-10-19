import test from 'node:test'
import assert from 'node:assert/strict'
import { recordGroup, recordLabel } from '../src/components/seedInformation.ts'

test('un estudio documental explícito no se etiqueta como ficticio ni como simulación', () => {
  const study = { source_kind: 'hypothetical', record_kind: 'study' }
  assert.equal(recordGroup(study), 'study')
  assert.equal(recordLabel(study), 'Cultivos en estudio')
})

test('los registros anteriores sin clasificación no se convierten automáticamente', () => {
  const legacy = { source_kind: 'hypothetical' }
  assert.equal(recordGroup(legacy), 'legacy')
  assert.equal(recordLabel(legacy), 'Ficha anterior · por revisar')
  assert.equal(recordGroup({ ...legacy, record_kind: null }), 'legacy')
})

test('consultar etiquetas conserva identificadores, permisos y cantidades anteriores', () => {
  const previous = { source_kind: 'hypothetical', code: 'ANTERIOR', quantity: 17, authorization_status: 'pending' }
  const snapshot = structuredClone(previous)
  recordGroup(previous); recordLabel(previous)
  assert.deepEqual(previous, snapshot)
  assert.equal(recordGroup({ source_kind: 'real' }), 'inventory')
  assert.equal(recordGroup({ source_kind: 'hypothetical', record_kind: 'simulation' }), 'simulation')
})
