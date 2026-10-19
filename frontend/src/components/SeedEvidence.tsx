import type { Passport, SeedEvidence } from '../seedApi'
import { evidenceHelp, evidenceLabels, recordGroup } from './seedInformation'

export function EvidenceOverview({ passport }: { passport: Passport }) {
  const evidence = passport.evidence ?? []
  const group = recordGroup(passport)
  return <section className="seed-evidence-overview" aria-label="Procedencia de la información">
    <h3>Información y respaldo</h3>
    <p>{group === 'study' ? 'Cultivo candidato: puede contener información científica auténtica. Esta ficha no registra existencias físicas.'
      : group === 'simulation' ? 'Resultados de un escenario supuesto; no son existencias ni hechos observados.'
      : group === 'legacy' ? 'La clasificación anterior no distinguía investigación documental de ejemplos supuestos. Revisa su procedencia y clasifícala explícitamente al editar; no se convierte en inventario.'
      : 'Inventario registrado por una persona. La calidad y procedencia de cada dato se documentan por separado.'}</p>
    <p>Fuente general: {passport.information_source ?? 'Sin datos · pendiente de documentar'}. Una referencia registrada no equivale a validación científica automática.</p>
    {passport.scenario_assumptions && <p>Supuestos del escenario: {passport.scenario_assumptions}</p>}
    <p>{passport.scientific_name ? `Nombre científico registrado: ${passport.scientific_name}.` : 'Nombre científico: Sin datos.'} {evidence.length === 0 ? 'Sin evidencias clasificadas por dato; la información anterior se conserva sin asignarle una procedencia nueva.' : `${evidence.length} ${evidence.length === 1 ? 'registro' : 'registros'} con fecha, método y fuente declarados.`}</p>
    {(Object.keys(evidenceLabels) as (keyof typeof evidenceLabels)[]).map(kind => {
      const items = evidence.filter(item => item.kind === kind)
      if (!items.length) return null
      return <details className="seed-form-section" key={kind}><summary>{evidenceLabels[kind]} ({items.length})</summary><p>{evidenceHelp[kind]}</p>{items.map((item, index) => <article className="seed-test" key={index}>
        <h4>{item.subject}</h4><p>{item.content}</p>{item.value !== null && <p>Valor documentado: {item.value} {item.unit}</p>}
        <p>Fecha: {item.recorded_on} · Método: {item.method}</p><p>Fuente: {item.source}</p>
        {item.instrument && <p>Instrumento y registro: {item.instrument}</p>}{item.assumptions && <p>Supuestos: {item.assumptions}</p>}
      </article>)}</details>
    })}
  </section>
}

export function EvidenceEditor({ passport, open = false, change }: { passport: Passport; open?: boolean; change: (value: SeedEvidence[]) => void }) {
  const evidence = passport.evidence ?? []
  const set = <K extends keyof SeedEvidence>(index: number, key: K, value: SeedEvidence[K]) => change(evidence.map((item, i) => i === index ? { ...item, [key]: value } : item))
  return <details className="seed-form-section" open={open || undefined}><summary>Pruebas y observaciones · información con fuente</summary>
    <p>Separa lo que documentaste, observaste, mediste, calculaste o simulaste. Para registrar un dato necesitas fecha, método y fuente. Si faltan, conserva la nota en «Observaciones» como pendiente; no inventes esos datos.</p>
    {evidence.map((item, index) => <fieldset className="seed-test" key={index}><legend>Dato {index + 1}</legend><div className="seed-fields">
      <label>Tipo de información<select value={item.kind} onChange={e => set(index, 'kind', e.target.value as SeedEvidence['kind'])}>{Object.entries(evidenceLabels).filter(([key]) => passport.record_kind !== 'simulation' || key === 'simulation').map(([key, title]) => <option key={key} value={key}>{title}</option>)}</select></label>
      <label>Qué estás documentando *<input required maxLength={120} value={item.subject} onChange={e => set(index, 'subject', e.target.value)} /></label>
      <label>Información o resultado *<textarea required maxLength={2000} value={item.content} onChange={e => set(index, 'content', e.target.value)} /></label>
      <label>{item.kind === 'documentary' ? 'Fecha de consulta *' : 'Fecha del hecho o resultado *'}<input required type="date" value={item.recorded_on} onInput={e => set(index, 'recorded_on', e.currentTarget.value)} onChange={e => set(index, 'recorded_on', e.target.value)} /></label>
      <label>Método o procedimiento *<textarea required maxLength={2000} value={item.method} onChange={e => set(index, 'method', e.target.value)} /></label>
      <label>Fuente del dato *<textarea required maxLength={2000} placeholder="Referencia, DOI, página o registro de origen" value={item.source} onChange={e => set(index, 'source', e.target.value)} /></label>
      <label>Valor numérico (si corresponde)<input type="number" step="any" value={item.value ?? ''} onChange={e => set(index, 'value', e.target.value === '' ? null : Number(e.target.value))} /></label>
      <label>Unidad{item.value !== null ? ' *' : ''}<input required={item.value !== null} maxLength={120} value={item.unit ?? ''} onChange={e => set(index, 'unit', e.target.value || null)} /></label>
      {(item.kind === 'instrumental' || item.instrument) && <label>Instrumento y referencia del registro{item.kind === 'instrumental' ? ' *' : ''}<textarea required={item.kind === 'instrumental'} maxLength={2000} value={item.instrument ?? ''} onChange={e => set(index, 'instrument', e.target.value || null)} /></label>}
      {(item.kind === 'simulation' || item.assumptions) && <label>Supuestos del escenario{item.kind === 'simulation' ? ' *' : ''}<textarea required={item.kind === 'simulation'} maxLength={2000} value={item.assumptions ?? ''} onChange={e => set(index, 'assumptions', e.target.value || null)} /></label>}
    </div><p>{evidenceHelp[item.kind]}</p><button type="button" className="button button-quiet" onClick={() => change(evidence.filter((_, i) => i !== index))}>Quitar dato {index + 1} de esta edición</button></fieldset>)}
    <button type="button" className="button button-outline" disabled={evidence.length >= 200} onClick={() => change([...evidence, {
      kind: passport.record_kind === 'simulation' ? 'simulation' : 'documentary', subject: '', content: '', recorded_on: '',
      method: '', source: '', value: null, unit: null, instrument: null, assumptions: null,
    }])}>Añadir información con fuente</button>
  </details>
}
