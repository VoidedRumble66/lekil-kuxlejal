import { agriculturalMessage } from '../components/decisionLanguage'
import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { CheckCheck, History, Play, Scale, X } from 'lucide-react'
import { PageHeading } from '../components/Shared'
import DecisionMap from '../components/DecisionMap'
import { decisionApi } from '../decisionApi'
import type { Alternative, DecisionRun, ReviewInput, RunSummary, ScenarioInput } from '../decisionApi'

const example: ScenarioInput = {
  name: 'Recorte energético hipotético',
  assumptions: 'Ejemplo hipotético editable. No procede de sensores ni define necesidades agrícolas reales.',
  periods: 5, period_hours: 24, generation_reduction: 0.4,
  initial_energy_kwh: 8, storage_capacity_kwh: 12, protected_reserve_kwh: 2,
  generation_daily_kwh: [10, 10, 10, 10, 10], module_daily_limit_kwh: 13,
  services: [
    { key: 'circulacion', name: 'Circulación', target_daily_kwh: 6, priority: 1, minimum_daily_kwh: null, minimum_basis: null },
    { key: 'iluminacion', name: 'Iluminación', target_daily_kwh: 4, priority: 0.8, minimum_daily_kwh: null, minimum_basis: null },
    { key: 'ambiente', name: 'Ambiente', target_daily_kwh: 3, priority: 0.6, minimum_daily_kwh: null, minimum_basis: null },
  ],
}
const number = (value: number) => value.toLocaleString('es-MX', { maximumFractionDigits: 3 })
const date = (value: string) => new Date(value).toLocaleString('es-MX')
const message = (error: unknown) => error instanceof Error ? error.message : 'No se pudo completar la operación.'

function Numeric({ label, value, onChange, min = 0, max = 1_000_000, step = 'any' }: {
  label: string; value: number; onChange: (value: number) => void; min?: number; max?: number; step?: string
}) {
  return <label>{label}<input type="number" required min={min} max={max} step={step} value={value} onChange={e => onChange(Number(e.target.value))} /></label>
}

function AlternativeDetail({ alternative, run }: { alternative: Alternative; run: DecisionRun }) {
  return <>
    <p>{alternative.justification}</p>
    <div className="decision-totals"><span>Consumo total <strong>{number(alternative.total_consumption_kwh)} kWh</strong></span><span>Vertido total <strong>{number(alternative.total_curtailed_kwh)} kWh</strong></span><span>Saldo final <strong>{number(alternative.ending_kwh)} kWh</strong></span><span>Fitness Itzamná <strong>{number(alternative.fitness)}</strong></span></div>
    <div className="decision-table" role="region" aria-label={`Asignaciones ${alternative.label}`} tabIndex={0}><table><caption>Asignaciones hipotéticas por periodo ({number(run.parameters.period_hours)} h)</caption><thead><tr><th>Servicio</th><th>Asignado (kWh)</th><th>Objetivo no cubierto (kWh)</th><th>Mínimo declarado (kWh/24 h)</th></tr></thead><tbody>{run.parameters.services.map(service => <tr key={service.key}><th>{service.name}</th><td>{number(alternative.allocations_kwh[service.key])}</td><td>{number(alternative.unmet_target_kwh[service.key])}</td><td>{service.minimum_daily_kwh === null ? 'Sin declarar' : number(service.minimum_daily_kwh)}</td></tr>)}</tbody></table></div>
    <div className="decision-table" role="region" aria-label={`Balance ${alternative.label}`} tabIndex={0}><table><caption>Balance temporal · kWh. La reserva está incluida en el saldo.</caption><thead><tr><th>Periodo</th><th>Inicial</th><th>Generación bruta</th><th>Tras recorte</th><th>Pérdida por recorte</th><th>Vertido</th><th>Consumo</th><th>Saldo</th><th>Reserva protegida</th></tr></thead><tbody>{alternative.periods.map(period => <tr key={period.period}><th>{period.period}</th><td>{number(period.initial_kwh)}</td><td>{number(period.gross_generation_kwh)}</td><td>{number(period.reduced_generation_kwh)}</td><td>{number(period.generation_cut_kwh)}</td><td>{number(period.curtailed_kwh)}</td><td>{number(period.consumption_kwh)}</td><td>{number(period.ending_kwh)}</td><td>{number(period.protected_reserve_kwh)}</td></tr>)}</tbody></table></div>
  </>
}

export default function Decisions() {
  const [parameters, setParameters] = useState<ScenarioInput>(example)
  const [run, setRun] = useState<DecisionRun | null>(null)
  const [history, setHistory] = useState<RunSummary[]>([])
  const [hasMore, setHasMore] = useState(false)
  const [historyError, setHistoryError] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)
  const [review, setReview] = useState<ReviewInput | null>(null)
  const update = <K extends keyof ScenarioInput>(key: K, value: ScenarioInput[K]) => setParameters(current => ({ ...current, [key]: value }))

  async function loadHistory(more = false) {
    setHistoryError('')
    try {
      const items = await decisionApi.history(more ? history.length : 0)
      setHistory(current => more ? [...current, ...items] : items)
      setHasMore(items.length === 30)
    } catch (cause) { setHistoryError(message(cause)) }
  }
  useEffect(() => { void loadHistory() }, [])
  useEffect(() => {
    if (run) document.getElementById('decision-results')?.scrollIntoView({ block: 'start' })
  }, [run?.id])
  useEffect(() => {
    if (review) document.getElementById('decision-review')?.scrollIntoView({ block: 'center' })
  }, [review?.alternative_id, review?.decision])

  async function compare(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError(''); setNotice(''); setReview(null)
    try { setRun(await decisionApi.compare(parameters)); await loadHistory() }
    catch (cause) { setError(message(cause)) }
    finally { setBusy(false) }
  }
  async function openRun(id: string) {
    setBusy(true); setError(''); setNotice(''); setReview(null)
    try { setRun(await decisionApi.run(id)) }
    catch (cause) { setError(message(cause)) }
    finally { setBusy(false) }
  }
  async function saveReview(event: FormEvent) {
    event.preventDefault()
    if (!run || !review) return
    setBusy(true); setError(''); setNotice('')
    try {
      const saved = await decisionApi.review(run.id, review)
      setRun({ ...run, reviews: [...run.reviews, saved] }); setReview(null)
      setNotice('Revisión humana registrada. No se ejecutó ninguna acción física.')
    } catch (cause) { setError(message(cause)) }
    finally { setBusy(false) }
  }

  return <>
    <PageHeading title="Decisiones" description="Gobernanza agrícola con Itzamná. Compara supuestos energéticos y registra la revisión humana." />
    <div className="info-strip"><Scale size={22} /><p><strong>Escenario de prueba — valores hipotéticos</strong><br />Las cifras son cálculos del escenario, no mediciones físicas. Todos los números del formulario son supuestos configurables. Las alternativas son factibles energéticamente bajo esos supuestos; no certifican viabilidad agrícola. La persona responsable decide. Sin conexión con el control físico.</p></div>
    {error && <div className="error-notice" role="alert"><p>{error}</p></div>}
    {notice && <div className="success-notice" role="status"><CheckCheck size={18} />{notice}</div>}

    <form className="panel decision-form" onSubmit={event => void compare(event)}>
      <fieldset disabled={busy}><legend>1. Configurar supuestos hipotéticos</legend>
        <div className="decision-fields"><label>Nombre del escenario<input required maxLength={120} value={parameters.name} onChange={e => update('name', e.target.value)} /></label><label>Procedencia y límites de los supuestos<textarea required maxLength={2000} value={parameters.assumptions} onChange={e => update('assumptions', e.target.value)} /></label></div>
        <div className="decision-fields">
          <Numeric label="Número de periodos" value={parameters.periods} min={1} max={30} step="1" onChange={value => {
            if (!Number.isInteger(value) || value < 1 || value > 30) return
            setParameters(current => ({ ...current, periods: value, generation_daily_kwh: Array.from({ length: value }, (_, i) => current.generation_daily_kwh[i] ?? current.generation_daily_kwh.at(-1) ?? 0) }))
          }} />
          <Numeric label="Horas por periodo" value={parameters.period_hours} min={0.001} max={168} onChange={value => update('period_hours', value)} />
          <Numeric label="Recorte de generación (%)" value={parameters.generation_reduction * 100} max={100} onChange={value => update('generation_reduction', value / 100)} />
          <Numeric label="Energía inicial (kWh)" value={parameters.initial_energy_kwh} onChange={value => update('initial_energy_kwh', value)} />
          <Numeric label="Capacidad de almacenamiento (kWh)" value={parameters.storage_capacity_kwh} onChange={value => update('storage_capacity_kwh', value)} />
          <Numeric label="Reserva protegida (kWh)" value={parameters.protected_reserve_kwh} onChange={value => update('protected_reserve_kwh', value)} />
          <Numeric label="Límite del módulo padre (kWh/24 h)" value={parameters.module_daily_limit_kwh} onChange={value => update('module_daily_limit_kwh', value)} />
        </div>
        <details open><summary>Generación antes del recorte · supuestos en kWh/24 h</summary><p>Se escala a las horas del periodo y se aplica el recorte una sola vez. Entra al almacenamiento antes del consumo; el exceso se vierte.</p><div className="decision-fields">{parameters.generation_daily_kwh.map((value, index) => <Numeric key={index} label={`Generación periodo ${index + 1}`} value={value} onChange={newValue => update('generation_daily_kwh', parameters.generation_daily_kwh.map((old, i) => i === index ? newValue : old))} />)}</div></details>
        <details><summary>Servicios, prioridades y mínimos opcionales · todos hipotéticos</summary><p>El objetivo es un límite de asignación configurable, no una necesidad de supervivencia. Sin mínimos y procedencia para todos los servicios: «Aún no sabemos si estos recursos bastan para los cultivos».</p>{parameters.services.map((service, index) => <div className="decision-service" key={service.key}><h3>Servicio hipotético {index + 1}</h3><div className="decision-fields">
          <label>Nombre del servicio<input required maxLength={80} value={service.name} onChange={e => update('services', parameters.services.map((old, i) => i === index ? { ...old, name: e.target.value } : old))} /></label>
          <Numeric label={`Objetivo ${service.name} (kWh/24 h)`} value={service.target_daily_kwh} onChange={value => update('services', parameters.services.map((old, i) => i === index ? { ...old, target_daily_kwh: value } : old))} />
          <Numeric label={`Prioridad ${service.name} (0–1)`} value={service.priority} max={1} onChange={value => update('services', parameters.services.map((old, i) => i === index ? { ...old, priority: value } : old))} />
          <label>Mínimo declarado (kWh/24 h, opcional)<input type="number" min={0} max={service.target_daily_kwh} step="any" placeholder="Sin declarar" value={service.minimum_daily_kwh ?? ''} onChange={e => update('services', parameters.services.map((old, i) => i === index ? { ...old, minimum_daily_kwh: e.target.value === '' ? null : Number(e.target.value), minimum_basis: e.target.value === '' ? null : old.minimum_basis } : old))} /></label>
          {service.minimum_daily_kwh !== null && <label>Procedencia y contexto agrícola del mínimo<input required maxLength={2000} value={service.minimum_basis ?? ''} onChange={e => update('services', parameters.services.map((old, i) => i === index ? { ...old, minimum_basis: e.target.value } : old))} /></label>}
        </div></div>)}</details>
        <button className="button button-gold" type="submit"><Play size={15} />{busy ? 'Procesando…' : 'Ejecutar comparación y guardar'}</button>
      </fieldset>
    </form>

    {run && <section id="decision-results" className="decision-results" aria-label="Resultado de comparación">
      <div className="section-title"><h2>2. {run.parameters.name}</h2><span className="tag">SUPUESTOS HIPOTÉTICOS · kWh</span></div>
      <p className="decision-note">Guardado {date(run.created_at)} · {run.parameters.periods} periodos de {number(run.parameters.period_hours)} h · Recorte {number(run.parameters.generation_reduction * 100)} %</p>
      <p className="decision-warning" role="status">{agriculturalMessage(run.result.agricultural_status)}</p>
      <DecisionMap key={run.id} run={run} />
      <details className="panel decision-details"><summary>Parámetros guardados y restricciones</summary><p>{run.parameters.assumptions}</p><p>Inicial: {number(run.parameters.initial_energy_kwh)} kWh · Capacidad: {number(run.parameters.storage_capacity_kwh)} kWh · Reserva: {number(run.parameters.protected_reserve_kwh)} kWh · Límite del módulo: {number(run.parameters.module_daily_limit_kwh)} kWh/24 h.</p><p>Generación bruta por periodo (kWh/24 h): {run.parameters.generation_daily_kwh.map(number).join(' · ')}.</p>{run.parameters.services.map(service => <p key={service.key}>{service.name}: objetivo {number(service.target_daily_kwh)} kWh/24 h; prioridad {number(service.priority)}; mínimo {service.minimum_daily_kwh === null ? 'sin declarar' : `${number(service.minimum_daily_kwh)} kWh/24 h`}. {service.minimum_basis}</p>)}<ul>{run.result.constraints.map(constraint => <li key={constraint}>{constraint}</li>)}</ul><p>{run.result.search.method} Evaluados: {run.result.search.evaluated}; factibles: {run.result.search.feasible}; en frontera: {run.result.search.pareto}.</p>{run.result.rejections.length > 0 && <><h3>Restricciones que descartaron candidatos</h3><ul>{run.result.rejections.map(item => <li key={item.reason}>{item.reason} ({item.count})</li>)}</ul></>}<p>{run.result.attribution}</p><p className="decision-trace">Registro: {run.id}<br />SHA-256 de parámetros, resultado y versión: {run.snapshot_sha256}<br />Huella del motor y versión de adaptación: {run.engine_fingerprint}</p></details>
      {run.result.status === 'infeasible' && <div className="error-notice" role="alert"><p>No hay alternativas factibles con estos supuestos. Revisa energía, reserva, límites y mínimos declarados. No se puede aprobar una alternativa inexistente.</p></div>}
      {run.result.alternatives.map(alternative => {
        const saved = run.reviews.find(item => item.alternative_id === alternative.id)
        return <article key={alternative.id} className="panel decision-alternative"><div className="decision-alternative-heading"><h3>{alternative.label}</h3><span className="tag">FACTIBLE ENERGÉTICAMENTE</span></div><AlternativeDetail alternative={alternative} run={run} />
          {saved ? <div className="decision-review-saved"><strong>{saved.decision === 'approved' ? 'Aprobada' : 'Rechazada'} por {saved.responsible}</strong><p>{saved.reason}</p><time dateTime={saved.created_at}>{date(saved.created_at)} · {saved.created_at}</time></div> : <div className="decision-actions"><button className="button button-gold" disabled={busy || run.reviews.some(item => item.decision === 'approved')} onClick={() => { setReview({ alternative_id: alternative.id, decision: 'approved', responsible: '', reason: '' }); setNotice('') }}><CheckCheck size={15} />Aprobar {alternative.label.toLowerCase()}</button><button className="button button-outline" disabled={busy} onClick={() => { setReview({ alternative_id: alternative.id, decision: 'rejected', responsible: '', reason: '' }); setNotice('') }}><X size={15} />Rechazar {alternative.label.toLowerCase()}</button></div>}
        </article>
      })}
      {review && <form id="decision-review" className="panel decision-form" onSubmit={event => void saveReview(event)} aria-label="Revisión humana"><fieldset disabled={busy}><legend>3. Registrar {review.decision === 'approved' ? 'aprobación' : 'rechazo'} · {review.alternative_id.replace('_', ' ')}</legend><p>La revisión es definitiva para esta alternativa. Sólo se admite una aprobación por comparación. No acciona equipos.</p><label>Responsable<input required maxLength={120} value={review.responsible} onChange={e => setReview({ ...review, responsible: e.target.value })} /></label><label>Motivo de la decisión<textarea required maxLength={2000} value={review.reason} onChange={e => setReview({ ...review, reason: e.target.value })} /></label><div className="decision-actions"><button className="button button-gold" type="submit">Guardar revisión humana</button><button className="button button-quiet" type="button" onClick={() => setReview(null)}>Cancelar</button></div></fieldset></form>}
    </section>}

    <section className="panel decision-history"><h2><History size={18} />Historial de escenarios hipotéticos</h2><p>Las comparaciones y revisiones se conservan en SQLite, separadas de los datos físicos.</p>{historyError ? <div className="error-notice" role="alert"><p>{historyError}</p><button className="button button-quiet" onClick={() => void loadHistory()}>Reintentar historial</button></div> : history.length === 0 ? <p>Sin comparaciones registradas.</p> : <ul>{history.map(item => <li key={item.id}><button className="button button-outline" disabled={busy} onClick={() => void openRun(item.id)}>{item.name}<small>{date(item.created_at)} · {item.alternative_count} alternativas · {item.status === 'infeasible' ? 'Infactible' : 'Factible energéticamente'}</small></button></li>)}</ul>}{hasMore && <button disabled={busy} className="button button-quiet" onClick={() => void loadHistory(true)}>Cargar más comparaciones</button>}</section>
  </>
}
