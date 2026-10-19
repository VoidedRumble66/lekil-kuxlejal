// Fixtures en memoria de Node; nunca escriben en SQLite ni simulan instrumentación.
import test from 'node:test'
import assert from 'node:assert/strict'
import { adjacentNode, buildMapNodes, layoutMap } from '../src/components/decisionMapModel.ts'

const fixture = () => ({
  parameters: {
    period_hours: 24, module_daily_limit_kwh: 13,
    services: [
      { key: 'circulacion', name: 'Circulación', target_daily_kwh: 6, priority: 1 },
      { key: 'iluminacion', name: 'Iluminación', target_daily_kwh: 4, priority: 0.8 },
      { key: 'ambiente', name: 'Ambiente', target_daily_kwh: 3, priority: 0.6 },
    ],
  },
  result: {
    unit: 'kWh', alternatives: [
      { id: 'alternativa_1', feasible: true, allocations_kwh: { circulacion: 2, iluminacion: 3, ambiente: 1 },
        unmet_target_kwh: { circulacion: 4, iluminacion: 1, ambiente: 2 }, periods: [{ consumption_kwh: 6 }] },
      { id: 'alternativa_2', feasible: true, allocations_kwh: { circulacion: 0, iluminacion: 0, ambiente: 0 },
        unmet_target_kwh: { circulacion: 6, iluminacion: 4, ambiente: 3 }, periods: [{ consumption_kwh: 0 }] },
    ],
  },
})

test('raíz y tres hijos usan únicamente la alternativa seleccionada de la API', () => {
  const data = fixture()
  const nodes = buildMapNodes(data, 'alternativa_1')
  assert.deepEqual(nodes.map(node => node.title), ['Domo agrícola', 'Circulación', 'Iluminación', 'Ambiente'])
  assert.equal(nodes[0].allocation, 6)
  assert.equal(nodes[0].target, 13)
  assert.equal(nodes[0].deficit, 7)
  assert.equal(nodes[0].moduleLimit, 13)
  assert.equal(nodes[0].priority, null) // El contrato no declara esta prioridad.
  assert.deepEqual(nodes.slice(1).map(node => node.parentId), ['domo', 'domo', 'domo'])
  assert.deepEqual(nodes.slice(1).map(node => [node.allocation, node.deficit, node.priority, node.unit]),
    [[2, 4, 1, 'kWh'], [3, 1, 0.8, 'kWh'], [1, 2, 0.6, 'kWh']])
  assert.deepEqual(buildMapNodes(data, 'alternativa_2').map(node => node.allocation), [0, 0, 0, 0])
})

test('escala objetivos a las horas guardadas, sin recalcular asignaciones ni déficits', () => {
  const data = fixture()
  data.parameters.period_hours = 12
  const nodes = buildMapNodes(data, 'alternativa_1')
  assert.equal(nodes[1].target, 3)
  assert.equal(nodes[0].moduleLimit, 6.5)
  assert.equal(nodes[1].allocation, 2)
  assert.equal(nodes[1].deficit, 4) // Copia el resultado API, sin reemplazar el algoritmo.
})

test('no inventa nodos ni resultados ante una alternativa inexistente o infactible', () => {
  const data = fixture()
  assert.deepEqual(buildMapNodes(data, 'inexistente'), [])
  data.result.alternatives[0].feasible = false
  assert.deepEqual(buildMapNodes(data, 'alternativa_1'), [])
  data.result.alternatives = []
  assert.deepEqual(buildMapNodes(data, 'alternativa_1'), [])
})

test('ausencia de valores no se convierte en ceros ficticios', () => {
  const data = fixture()
  delete data.result.alternatives[0].allocations_kwh.ambiente
  data.result.alternatives[0].unmet_target_kwh.ambiente = NaN
  data.result.alternatives[0].periods = []
  const nodes = buildMapNodes(data, 'alternativa_1')
  assert.equal(nodes[3].allocation, null)
  assert.equal(nodes[3].deficit, null)
  assert.equal(nodes[0].allocation, null)
  assert.equal(nodes[0].deficit, null)
})

test('proyección y navegación no mutan prioridades, asignaciones ni parámetros', () => {
  const data = fixture(), original = structuredClone(data)
  const nodes = buildMapNodes(data, 'alternativa_1')
  adjacentNode(nodes, 'domo', 'ArrowRight')
  layoutMap(nodes, true)
  layoutMap(nodes, false)
  assert.deepEqual(data, original)
})

test('flechas, Inicio y Fin recorren raíz, hijos y hermanos', () => {
  const nodes = buildMapNodes(fixture(), 'alternativa_1')
  assert.equal(adjacentNode(nodes, 'domo', 'ArrowRight'), 'servicio:circulacion')
  assert.equal(adjacentNode(nodes, 'servicio:circulacion', 'ArrowDown'), 'servicio:iluminacion')
  assert.equal(adjacentNode(nodes, 'servicio:iluminacion', 'ArrowUp'), 'servicio:circulacion')
  assert.equal(adjacentNode(nodes, 'servicio:ambiente', 'ArrowLeft'), 'domo')
  assert.equal(adjacentNode(nodes, 'servicio:ambiente', 'Home'), 'domo')
  assert.equal(adjacentNode(nodes, 'domo', 'End'), 'servicio:ambiente')
  assert.equal(adjacentNode(nodes, 'servicio:ambiente', 'ArrowDown'), 'servicio:ambiente')
  assert.equal(adjacentNode(nodes, 'domo', 'ArrowLeft'), null)
  assert.equal(adjacentNode(nodes, 'inexistente', 'Home'), null)
})

for (const compact of [false, true]) {
  test(`layout ${compact ? 'móvil' : 'escritorio'} separa nodos y etiquetas con cuatro servicios`, () => {
    const data = fixture()
    data.parameters.services.push({ key: 'extra', name: 'Nombre largo de servicio hipotético', target_daily_kwh: 0, priority: 0 })
    const nodes = buildMapNodes(data, 'alternativa_1')
    const layout = layoutMap(nodes, compact)
    const points = Object.values(layout.positions)
    for (let a = 0; a < points.length; a++) for (let b = a + 1; b < points.length; b++) {
      assert.ok(Math.abs(points[a].x - points[b].x) >= 180 || Math.abs(points[a].y - points[b].y) >= 145)
    }
    for (const point of points) {
      assert.ok(point.x - 90 >= 0 && point.x + 90 <= layout.width)
      assert.ok(point.y - 40 >= 0 && point.y + 105 <= layout.height)
    }
  })
}
