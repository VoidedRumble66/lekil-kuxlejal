import type { DecisionRun } from '../decisionApi'

export interface DecisionMapNode {
  id: string
  parentId: string | null
  title: string
  kind: 'module' | 'service'
  target: number | null
  allocation: number | null
  deficit: number | null
  priority: number | null
  unit: string
  moduleLimit?: number | null
}

export interface MapLayout {
  width: number
  height: number
  positions: Record<string, { x: number; y: number }>
  compact: boolean
}

const ROOT = 'domo'
const finite = (value: unknown): number | null => typeof value === 'number' && Number.isFinite(value) ? value : null
const sumKnown = (values: (number | null)[]) => values.every(value => value !== null)
  ? (values as number[]).reduce((sum, value) => sum + value, 0) : null

/** Proyección de una instantánea de la API. No usa el formulario ni calcula planes. */
export function buildMapNodes(run: DecisionRun, alternativeId: string): DecisionMapNode[] {
  const alternative = run.result.alternatives.find(item => item.id === alternativeId && item.feasible)
  if (!alternative) return []
  const hours = finite(run.parameters.period_hours)
  const scale = hours === null ? null : hours / 24
  const children: DecisionMapNode[] = run.parameters.services.map(service => ({
    id: `servicio:${service.key}`, parentId: ROOT, title: service.name, kind: 'service',
    target: scale === null || finite(service.target_daily_kwh) === null ? null : service.target_daily_kwh * scale,
    allocation: finite(alternative.allocations_kwh[service.key]),
    deficit: finite(alternative.unmet_target_kwh[service.key]),
    priority: finite(service.priority), unit: run.result.unit,
  }))
  return [{
    id: ROOT, parentId: null, title: 'Domo agrícola', kind: 'module',
    target: sumKnown(children.map(node => node.target)),
    allocation: finite(alternative.periods[0]?.consumption_kwh),
    deficit: sumKnown(children.map(node => node.deficit)),
    // El contrato público no declara prioridad para la raíz. No se inventa.
    priority: null, unit: run.result.unit,
    moduleLimit: scale === null || finite(run.parameters.module_daily_limit_kwh) === null
      ? null : run.parameters.module_daily_limit_kwh * scale,
  }, ...children]
}

/** Separación explícita de círculos y etiquetas; sin dependencias D3 adicionales. */
export function layoutMap(nodes: DecisionMapNode[], compact: boolean): MapLayout {
  const children = nodes.filter(node => node.parentId !== null)
  const width = compact ? 440 : Math.max(660, children.length * 220)
  const height = compact ? Math.max(470, children.length * 150 + 40) : 400
  const positions: MapLayout['positions'] = {}
  if (nodes[0]) positions[nodes[0].id] = compact ? { x: 90, y: height / 2 - 25 } : { x: width / 2, y: 75 }
  children.forEach((node, index) => {
    positions[node.id] = compact
      ? { x: 320, y: 65 + index * 150 }
      : { x: width / children.length * (index + 0.5), y: 260 }
  })
  return { width, height, positions, compact }
}

/** Navegación de árbol WAI-ARIA: padre, hijos y hermanos, sin modificar datos. */
export function adjacentNode(nodes: DecisionMapNode[], activeId: string, key: string): string | null {
  const index = nodes.findIndex(node => node.id === activeId)
  if (index < 0) return null
  if (key === 'Home') return nodes[0].id
  if (key === 'End') return nodes.at(-1)!.id
  if (key === 'ArrowDown') return nodes[Math.min(index + 1, nodes.length - 1)].id
  if (key === 'ArrowUp') return nodes[Math.max(index - 1, 0)].id
  if (key === 'ArrowLeft') return nodes[index].parentId
  if (key === 'ArrowRight') return nodes.find(node => node.parentId === activeId)?.id ?? null
  return null
}
