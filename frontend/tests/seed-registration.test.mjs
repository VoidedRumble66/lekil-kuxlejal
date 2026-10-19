import test from 'node:test'
import assert from 'node:assert/strict'
import { suggestSeedIdentifier } from '../src/components/seedRegistration.ts'

test('la sugerencia evita identificadores existentes sin cambiar registros guardados', () => {
  const existing = ['SEM-REPETIDO', 'SEM-ANTERIOR']
  const values = ['repetido', 'nuevo']
  assert.equal(suggestSeedIdentifier('real', existing, () => values.shift()), 'SEM-NUEVO')
  assert.deepEqual(existing, ['SEM-REPETIDO', 'SEM-ANTERIOR'])
})

test('las fichas de estudio reciben un identificador diferente sin crear datos de inventario', () => {
  const existing = ['EST-REPETIDO']
  const values = ['repetido', 'candidata']
  assert.equal(suggestSeedIdentifier('hypothetical', existing, () => values.shift()), 'EST-CANDIDATA')
  assert.deepEqual(existing, ['EST-REPETIDO'])
})

test('el generador produce códigos breves y distintos sin cambiar los identificadores anteriores', () => {
  const real = suggestSeedIdentifier('real', [])
  const next = suggestSeedIdentifier('real', [real])
  assert.match(real, /^SEM-[A-F0-9]{12}$/)
  assert.notEqual(real, next)
})
