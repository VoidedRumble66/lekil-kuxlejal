/** Adaptación de cámara, árbol y conexiones de PreziViewer de Itzamná.
 * Referencia local: referencias/itzamna_visual/PreziViewer.tsx.
 * Prioridades sólo textuales/gráficas: no se adapta la edición de PriorityDial.
 */
import { useEffect, useId, useMemo, useRef, useState } from 'react'
import type { KeyboardEvent, PointerEvent } from 'react'
import { ArrowLeft, Focus, Home, Minus, Plus } from 'lucide-react'
import type { DecisionRun } from '../decisionApi'
import { adjacentNode, buildMapNodes, layoutMap } from './decisionMapModel'
import type { DecisionMapNode } from './decisionMapModel'

const format = (value: number | null) => value === null ? 'Sin datos' : value.toLocaleString('es-MX', { maximumFractionDigits: 3 })
const clampZoom = (value: number) => Math.max(0.25, Math.min(2.5, value))
type Camera = { x: number; y: number; scale: number }

export default function DecisionMap({ run }: { run: DecisionRun }) {
  const alternatives = run.result.alternatives.filter(item => item.feasible)
  const [alternativeId, setAlternativeId] = useState(alternatives[0]?.id ?? '')
  const nodes = useMemo(() => buildMapNodes(run, alternativeId), [run, alternativeId])
  const [activeId, setActiveId] = useState('domo')
  const [history, setHistory] = useState<string[]>([])
  const [size, setSize] = useState({ width: 660, height: 440 })
  const [camera, setCamera] = useState<Camera>({ x: 330, y: 200, scale: 1 })
  const stageRef = useRef<HTMLDivElement>(null)
  const buttons = useRef<Record<string, HTMLButtonElement | null>>({})
  const drag = useRef<{ x: number; y: number; camera: Camera } | null>(null)
  const instructionsId = useId()
  const layout = useMemo(() => layoutMap(nodes, size.width < 600), [nodes, size.width])
  const active = nodes.find(node => node.id === activeId) ?? nodes[0]
  const alternative = alternatives.find(item => item.id === alternativeId)
  const fitScale = clampZoom(Math.min(size.width / layout.width, size.height / layout.height) * 0.94)

  useEffect(() => {
    const stage = stageRef.current
    if (!stage) return
    const observer = new ResizeObserver(([entry]) => {
      setSize({ width: entry.contentRect.width, height: entry.contentRect.height })
    })
    observer.observe(stage)
    return () => observer.disconnect()
  }, [nodes.length > 0])

  useEffect(() => {
    setCamera({ x: layout.width / 2, y: layout.height / 2, scale: fitScale })
  }, [layout.width, layout.height, fitScale, alternativeId])

  function fit() {
    setCamera({ x: layout.width / 2, y: layout.height / 2, scale: fitScale })
  }
  function selectNode(id: string, focus = false, remember = true) {
    const point = layout.positions[id]
    if (!point) return
    if (remember && id !== activeId) setHistory(previous => [...previous, activeId])
    setActiveId(id)
    if (id === 'domo') fit()
    else setCamera({ ...point, scale: clampZoom(Math.max(fitScale, 1)) })
    if (focus) requestAnimationFrame(() => buttons.current[id]?.focus({ preventScroll: true }))
  }
  function goRoot(focus = false) {
    setHistory([])
    selectNode('domo', focus, false)
  }
  function goBack() {
    const previous = history.at(-1)
    if (!previous) return
    setHistory(values => values.slice(0, -1))
    selectNode(previous, false, false)
  }
  function onNodeKey(event: KeyboardEvent<HTMLButtonElement>, node: DecisionMapNode) {
    event.stopPropagation()
    const next = adjacentNode(nodes, node.id, event.key)
    if (next) { event.preventDefault(); selectNode(next, true) }
    else if (event.key === 'Escape') { event.preventDefault(); goRoot(true) }
    else if (event.key === '+' || event.key === '=') { event.preventDefault(); setCamera(value => ({ ...value, scale: clampZoom(value.scale + 0.15) })) }
    else if (event.key === '-') { event.preventDefault(); setCamera(value => ({ ...value, scale: clampZoom(value.scale - 0.15) })) }
  }
  function onStageKey(event: KeyboardEvent<HTMLDivElement>) {
    if (event.target !== event.currentTarget) return
    const moves: Record<string, [number, number]> = { ArrowLeft: [-50, 0], ArrowRight: [50, 0], ArrowUp: [0, -50], ArrowDown: [0, 50] }
    if (moves[event.key]) {
      event.preventDefault()
      const [x, y] = moves[event.key]
      setCamera(value => ({ ...value, x: value.x + x / value.scale, y: value.y + y / value.scale }))
    } else if (event.key === 'Home' || event.key === 'Escape') { event.preventDefault(); goRoot() }
    else if (event.key === '+' || event.key === '=') { event.preventDefault(); setCamera(value => ({ ...value, scale: clampZoom(value.scale + 0.15) })) }
    else if (event.key === '-') { event.preventDefault(); setCamera(value => ({ ...value, scale: clampZoom(value.scale - 0.15) })) }
  }
  function startPan(event: PointerEvent<HTMLDivElement>) {
    if (event.button !== 0 || (event.target as Element).closest('button')) return
    event.currentTarget.focus({ preventScroll: true })
    event.currentTarget.setPointerCapture(event.pointerId)
    drag.current = { x: event.clientX, y: event.clientY, camera }
  }
  function movePan(event: PointerEvent<HTMLDivElement>) {
    if (!drag.current) return
    const origin = drag.current
    setCamera({ ...origin.camera, x: origin.camera.x - (event.clientX - origin.x) / origin.camera.scale,
      y: origin.camera.y - (event.clientY - origin.y) / origin.camera.scale })
  }

  return <section className="panel decision-map" aria-label="Mapa jerárquico de la alternativa">
    <div className="decision-map-heading"><div><span className="eyebrow">ESCENARIO HIPOTÉTICO · SÓLO LECTURA</span><h3>Mapa del domo</h3></div>
      {alternatives.length > 0 && <label>Alternativa del mapa<select value={alternativeId} onChange={event => {
        setAlternativeId(event.target.value); setActiveId('domo'); setHistory([])
      }}>{alternatives.map(item => <option key={item.id} value={item.id}>{item.label}</option>)}</select></label>}
    </div>
    {!active || !alternative ? <p className="decision-map-empty">Sin alternativa factible para visualizar. El mapa se alimenta únicamente de una comparación devuelta por la API.</p> : <>
      <p className="decision-map-context">{alternative.label} · Asignaciones por periodo de {format(run.parameters.period_hours)} h · {run.parameters.periods} periodos. Objetivos y prioridades: parámetros guardados en esta comparación.</p>
      <div className="decision-map-toolbar" role="group" aria-label="Navegación del mapa">
        <button type="button" className="button button-quiet" onClick={() => goRoot()}><Home size={15} />Volver a la raíz</button>
        <button type="button" className="button button-quiet" disabled={history.length === 0} onClick={goBack}><ArrowLeft size={15} />Atrás</button>
        <button type="button" className="button button-quiet" onClick={fit}><Focus size={15} />Encajar mapa</button>
        <button type="button" className="button button-quiet" aria-label="Alejar mapa" disabled={camera.scale <= 0.25} onClick={() => setCamera(value => ({ ...value, scale: clampZoom(value.scale - 0.15) }))}><Minus size={16} /></button>
        <output aria-label="Nivel de zoom">{Math.round(camera.scale * 100)} %</output>
        <button type="button" className="button button-quiet" aria-label="Acercar mapa" disabled={camera.scale >= 2.5} onClick={() => setCamera(value => ({ ...value, scale: clampZoom(value.scale + 0.15) }))}><Plus size={16} /></button>
      </div>
      <div className="decision-map-layout">
        <div ref={stageRef} className={`decision-map-stage${layout.compact ? ' compact' : ''}`} role="group" tabIndex={0}
          aria-label="Lienzo del mapa; flechas para desplazar, más y menos para zoom" aria-describedby={instructionsId}
          onKeyDown={onStageKey} onPointerDown={startPan} onPointerMove={movePan}
          onPointerUp={() => { drag.current = null }} onPointerCancel={() => { drag.current = null }}>
          <div className="decision-map-camera" style={{ transform: `translate(${size.width / 2}px, ${size.height / 2}px) scale(${camera.scale}) translate(${-camera.x}px, ${-camera.y}px)` }}>
            <svg className="decision-map-links" width={layout.width} height={layout.height} aria-hidden="true">
              {nodes.filter(node => node.parentId !== null).map(node => {
                const source = layout.positions[node.parentId!], target = layout.positions[node.id]
                const middle = layout.compact ? (source.x + target.x) / 2 : (source.y + target.y) / 2
                return <path key={node.id} d={layout.compact
                  ? `M${source.x},${source.y} C${middle},${source.y} ${middle},${target.y} ${target.x},${target.y}`
                  : `M${source.x},${source.y} C${source.x},${middle} ${target.x},${middle} ${target.x},${target.y}`} />
              })}
            </svg>
            <div role="tree" aria-label={`Jerarquía de ${alternative.label}`}>
              {nodes.map(node => <button key={node.id} type="button" role="treeitem" aria-level={node.parentId === null ? 1 : 2}
                aria-expanded={node.parentId === null ? true : undefined} aria-selected={node.id === active.id}
                aria-label={`${node.title}, asignación ${format(node.allocation)} ${node.unit}, sólo lectura`}
                tabIndex={node.id === active.id ? 0 : -1} ref={element => { buttons.current[node.id] = element }}
                className={`decision-map-node ${node.kind}${node.id === active.id ? ' selected' : ''}`}
                style={{ left: layout.positions[node.id].x, top: layout.positions[node.id].y }}
                onKeyDown={event => onNodeKey(event, node)} onClick={() => selectNode(node.id)}>
                <span className="decision-map-orb"><svg viewBox="0 0 80 80" aria-hidden="true"><circle cx="40" cy="40" r="34" />{node.priority !== null && <circle className="decision-map-priority" cx="40" cy="40" r="34" pathLength="100" strokeDasharray={`${node.priority * 100} 100`} transform="rotate(-90 40 40)" />}</svg><span>{node.parentId === null ? 'D' : node.title.slice(0, 2).toLocaleUpperCase('es')}</span></span>
                <strong>{node.title}</strong><small>{format(node.allocation)} {node.unit} asignados</small>
              </button>)}
            </div>
          </div>
        </div>
        <aside className="decision-map-inspector" aria-label="Detalle del nodo seleccionado" aria-live="polite" aria-atomic="true">
          <span className="eyebrow">{active.kind === 'module' ? 'RAÍZ · SUMA DE SERVICIOS' : 'SERVICIO · HIJO DEL DOMO'}</span><h4>{active.title}</h4>
          <dl><div><dt>Objetivo por periodo</dt><dd>{format(active.target)} {active.unit}</dd></div>
            <div><dt>Asignación por periodo</dt><dd>{format(active.allocation)} {active.unit}</dd></div>
            <div><dt>Déficit frente al objetivo</dt><dd>{format(active.deficit)} {active.unit}</dd></div>
            <div><dt>Prioridad declarada (0–1)</dt><dd>{active.priority === null ? 'No declarada en la API' : format(active.priority)}</dd></div>
            {active.moduleLimit !== undefined && <div><dt>Límite del módulo por periodo</dt><dd>{format(active.moduleLimit)} {active.unit}</dd></div>}
          </dl>
          <p>El déficit corresponde al objetivo hipotético, no a necesidades de supervivencia.</p><p>{run.result.agricultural_status}</p>
          {active.parentId !== null && <button type="button" className="button button-outline" onClick={() => goRoot(true)}><Home size={15} />Ir al domo agrícola</button>}
        </aside>
      </div>
      <p id={instructionsId} className="decision-map-help">Selecciona un nodo para examinarlo. En los nodos: flechas para navegar; Inicio para la raíz; Enter o espacio para seleccionar. En el lienzo: arrastra o usa flechas para desplazar; + y − para zoom. Los anillos representan prioridades guardadas y no se pueden editar.</p>
      <p className="decision-map-disclaimer">Los colores distinguen selección y jerarquía; no indican seguridad ni viabilidad agrícola. Escenario hipotético, sin sensores simulados.</p>
    </>}
    <footer className="decision-map-attribution">Adaptación visual inspirada en PreziViewer de Itzamná · API local · Sólo lectura.</footer>
  </section>
}
