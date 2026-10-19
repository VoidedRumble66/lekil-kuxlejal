import { useState } from 'react'
import type { FormEvent } from 'react'
import { criteria, emptyPassport, passportOf } from '../seedApi'
import type { Assessment, Criterion, Passport, Scores, SeedLot, WeightProfile, Weights } from '../seedApi'

export const passportLabels = {
  scientific_name: 'Nombre científico', variety: 'Variedad', provenance: 'Procedencia documentada',
  custodian_entity: 'Entidad o comunidad custodiante', use_conditions: 'Condiciones de uso',
  authorization_source: 'Fuente documental de la autorización', received_on: 'Fecha de ingreso',
  storage_conditions: 'Condiciones conocidas de conservación', container: 'Envase', location: 'Ubicación',
  observations: 'Observaciones', information_source: 'Fuente de la información',
} as const satisfies Partial<Record<keyof Passport, string>>
export const authLabels = { pending: 'Pendiente de comprobar', authorized: 'Uso autorizado documentado', denied: 'Uso denegado documentado' }
export const kindLabels = { real: 'Lote real', hypothetical: 'Ejemplo hipotético' }
export const display = (value: unknown) => value === null || value === undefined || value === '' ? 'Sin datos' : String(value)

export function LotEditor({ lot, busy, save, cancel }: { lot: SeedLot | null; busy: boolean; save: (value: Passport) => void; cancel: () => void }) {
  const [value, setValue] = useState<Passport>(() => lot ? passportOf(lot) : emptyPassport())
  const change = <K extends keyof Passport>(key: K, next: Passport[K]) => setValue(previous => ({ ...previous, [key]: next }))
  const field = (key: keyof typeof passportLabels, multiline = false) => <label key={key}>{passportLabels[key]}{multiline
    ? <textarea maxLength={2000} placeholder="Sin datos" value={String(value[key] ?? '')} onChange={e => change(key, e.target.value || null)} />
    : <input type={key === 'received_on' ? 'date' : 'text'} maxLength={key === 'scientific_name' || key === 'variety' ? 120 : 2000} placeholder="Sin datos" value={String(value[key] ?? '')} onChange={e => change(key, e.target.value || null)} />}</label>
  function submit(event: FormEvent) { event.preventDefault(); save(value) }
  return <form className="panel seed-panel seed-form" onSubmit={submit} aria-label={lot ? 'Editar lote' : 'Registrar lote'}><fieldset disabled={busy}>
    <legend>{lot ? `Editar ${lot.code}` : 'Registrar un lote'}</legend>
    <p>Registra sólo información disponible. Los espacios vacíos se conservan como «Sin datos». No incluyas nombres personales, teléfonos ni datos privados de custodios o informantes: usa la entidad o comunidad y una referencia documental local.</p>
    <div className="seed-fields"><label>Nombre común *<input required maxLength={120} value={value.common_name} onChange={e => change('common_name', e.target.value)} /></label>
      <label>Código de lote *<input required maxLength={120} value={value.code} onChange={e => change('code', e.target.value)} /></label>
      <label>Tipo de registro *<select value={value.source_kind} disabled={!!lot} onChange={e => change('source_kind', e.target.value as Passport['source_kind'])}><option value="real">Lote real</option><option value="hypothetical">Ejemplo hipotético</option></select></label>
      {field('scientific_name')}{field('variety')}{field('received_on')}
      <label>Cantidad disponible<input type="number" min="0" max="1000000000" step="any" placeholder="Sin datos" value={value.quantity ?? ''} onChange={e => change('quantity', e.target.value === '' ? null : Number(e.target.value))} /></label>
      <label>Unidad{value.quantity !== null ? ' *' : ''}<input required={value.quantity !== null} maxLength={120} placeholder="Sin datos" value={value.unit ?? ''} onChange={e => change('unit', e.target.value || null)} /></label>
    </div>
    <h3>Procedencia y permiso de uso</h3><div className="seed-fields">{field('provenance')}{field('custodian_entity')}
      <label>Estado de autorización<select value={value.authorization_status} onChange={e => change('authorization_status', e.target.value as Passport['authorization_status'])}>{Object.entries(authLabels).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label>
      {field('authorization_source', true)}{field('use_conditions', true)}
    </div><p>Para documentar autorización o denegación se requiere una fuente. El uso autorizado también necesita condiciones explícitas. La aplicación no concede permisos.</p>
    <h3>Conservación y documentación</h3><div className="seed-fields">{field('storage_conditions', true)}{field('container')}{field('location')}{field('observations', true)}{field('information_source', true)}</div>
    <h3>Pruebas de germinación y viabilidad</h3><p>Sin pruebas registradas significa «Sin datos». Fecha y método desconocidos quedarán pendientes de comprobar; no se estiman resultados.</p>
    {value.tests.map((test, index) => <fieldset className="seed-test" key={index}><legend>Prueba {index + 1}</legend><div className="seed-fields">
      <label>Tipo de prueba<select value={test.kind} onChange={e => change('tests', value.tests.map((item, i) => i === index ? { ...item, kind: e.target.value as typeof test.kind } : item))}><option value="germination">Germinación</option><option value="viability">Viabilidad</option></select></label>
      {(['result', 'tested_on', 'method', 'source'] as const).map(key => <label key={key}>{{ result: 'Resultado documentado *', tested_on: 'Fecha de prueba', method: 'Método de prueba', source: 'Fuente de la prueba *' }[key]}<input type={key === 'tested_on' ? 'date' : 'text'} required={key === 'result' || key === 'source'} maxLength={2000} value={test[key] ?? ''} placeholder="Sin datos" onChange={e => change('tests', value.tests.map((item, i) => i === index ? { ...item, [key]: e.target.value || (key === 'result' || key === 'source' ? '' : null) } : item))} /></label>)}
    </div><button className="button button-quiet" type="button" onClick={() => change('tests', value.tests.filter((_, i) => i !== index))}>Quitar prueba {index + 1} de esta edición</button></fieldset>)}
    <button className="button button-outline" type="button" disabled={value.tests.length >= 100} onClick={() => change('tests', [...value.tests, { kind: 'germination', result: '', tested_on: null, method: null, source: '' }])}>Añadir prueba documentada</button>
    <div className="decision-actions"><button className="button button-gold" type="submit">{busy ? 'Guardando…' : 'Guardar lote'}</button><button className="button button-quiet" type="button" onClick={cancel}>Cancelar edición</button></div>
  </fieldset></form>
}

type DraftScore = { value: string; justification: string; source: string }
export function AssessmentForm({ lot, profile, previous, busy, save }: { lot: SeedLot; profile: WeightProfile; previous?: Assessment; busy: boolean; save: (scores: Scores, responsible: string) => void }) {
  const [draft, setDraft] = useState(() => Object.fromEntries(criteria.map(key => [key, { value: previous?.scores[key]?.value.toString() ?? '', justification: previous?.scores[key]?.justification ?? '', source: previous?.scores[key]?.source ?? '' }])) as Record<Criterion, DraftScore>)
  const [responsible, setResponsible] = useState('')
  const change = (key: Criterion, field: keyof DraftScore, value: string) => setDraft(before => ({ ...before, [key]: { ...before[key], [field]: value } }))
  function submit(event: FormEvent) {
    event.preventDefault()
    const scores = Object.fromEntries(criteria.map(key => [key, draft[key].value === '' ? null : { ...draft[key], value: Number(draft[key].value) }])) as Scores
    save(scores, responsible)
  }
  return <form className="seed-form" onSubmit={submit} aria-label="Evaluación multicriterio"><fieldset disabled={busy}><legend>Evaluación provisional · {lot.code}</legend>
    <p>{profile.scale} Para recursos, una nota mayor expresa una preferencia por menor demanda documentada, no un consumo medido. Explica el contexto y la escala en cada justificación.</p>
    {previous && <p className="decision-warning">Se muestran las últimas puntuaciones para revisión. Guardar crea una nueva evaluación; conserva la anterior con su fecha, datos y pesos.</p>}
    <p>Deja la puntuación vacía si falta evidencia. Podrás guardar una evaluación incompleta; no tendrá puntuación global.</p>
    {criteria.map(key => <fieldset key={key} className="seed-test"><legend>{profile.criteria[key]} · {profile.weights[key]} %</legend><div className="seed-score-fields">
      <label>Puntuación: {profile.criteria[key]}<input type="number" min="0" max="5" step="any" placeholder="Pendiente" value={draft[key].value} onChange={e => change(key, 'value', e.target.value)} /></label>
      <label>Justificación: {profile.criteria[key]}<textarea maxLength={2000} required={draft[key].value !== ''} disabled={draft[key].value === ''} value={draft[key].justification} onChange={e => change(key, 'justification', e.target.value)} /></label>
      <label>Fuente: {profile.criteria[key]}<textarea maxLength={2000} required={draft[key].value !== ''} disabled={draft[key].value === ''} value={draft[key].source} onChange={e => change(key, 'source', e.target.value)} /></label>
    </div></fieldset>)}
    <label>Responsable de la evaluación (rol o identificador local) *<input required maxLength={120} value={responsible} onChange={e => setResponsible(e.target.value)} /></label>
    <div className="decision-actions"><button className="button button-gold" type="submit">Guardar evaluación provisional</button></div>
  </fieldset></form>
}

export function WeightsForm({ profile, busy, save }: { profile: WeightProfile; busy: boolean; save: (weights: Weights, responsible: string, reason: string) => void }) {
  const [weights, setWeights] = useState(profile.weights)
  const [responsible, setResponsible] = useState(''), [reason, setReason] = useState('')
  const sum = Object.values(weights).reduce((a, b) => a + b, 0)
  return <form className="seed-form" aria-label="Revisar pesos" onSubmit={e => { e.preventDefault(); save(weights, responsible, reason) }}><fieldset disabled={busy}><legend>Pesos para próximas evaluaciones</legend><p>Pesos iniciales: capítulo 6.2 del expediente. Al cambiarlos se conserva el historial y habrá que revisar las evaluaciones antes de comparar de nuevo. Comprueba si pequeños cambios de pesos alteran tu preferencia; eso indica una decisión inestable.</p>
    <div className="seed-fields">{criteria.map(key => <label key={key}>{profile.criteria[key]} (%)<input type="number" min="0" max="100" step="0.1" required value={weights[key]} onChange={e => setWeights({ ...weights, [key]: e.target.value === '' ? 0 : Number(e.target.value) })} /></label>)}</div>
    <p role="status">Suma: {sum.toLocaleString('es-MX')} % · Debe sumar 100 %.</p>
    <label>Responsable de los pesos (rol o identificador local) *<input required maxLength={120} value={responsible} onChange={e => setResponsible(e.target.value)} /></label>
    <label>Motivo de la revisión *<textarea required maxLength={2000} value={reason} onChange={e => setReason(e.target.value)} /></label>
    <button className="button button-outline" type="submit" disabled={Math.abs(sum - 100) > 1e-7}>Guardar nueva versión de pesos</button>
  </fieldset></form>
}
