import { useId, useState } from 'react'
import type { FormEvent } from 'react'
import { criteria, emptyPassport, passportOf } from '../seedApi'
import type { Assessment, Criterion, Passport, RecordKind, Scores, SeedLot, WeightProfile, Weights } from '../seedApi'
import { suggestSeedIdentifier } from './seedRegistration'
import { recordGroup, recordLabel, recordLabels } from './seedInformation'
import { EvidenceEditor } from './SeedEvidence'

export const passportLabels = {
  scientific_name: 'Nombre científico', variety: 'Variedad', provenance: 'Procedencia documentada',
  custodian_entity: 'Entidad o comunidad custodiante', use_conditions: 'Condiciones de uso',
  authorization_source: 'Fuente documental de la autorización', received_on: 'Fecha de ingreso',
  storage_conditions: 'Condiciones conocidas de conservación', container: 'Envase', location: 'Ubicación',
  observations: 'Observaciones', information_source: 'Fuente de la información',
} as const satisfies Partial<Record<keyof Passport, string>>
export const authLabels = { pending: 'Pendiente de comprobar', authorized: 'Uso autorizado documentado', denied: 'Uso denegado documentado' }
export const display = (value: unknown) => value === null || value === undefined || value === '' ? 'Sin datos' : String(value)

const fieldHelp: Partial<Record<keyof Passport, string>> = {
  scientific_name: 'El nombre usado en ciencia, si se conoce. Puedes consultarlo en una etiqueta o documento; no lo adivines.',
  variety: 'El nombre de la variedad, si está documentado. No siempre coincide con el nombre común.',
  provenance: 'De dónde vienen las semillas o la información. Por ejemplo, una etiqueta o una ficha de entrega.',
  custodian_entity: 'La comunidad o institución que cuida las semillas, si está documentada. Evita datos personales.',
  authorization_source: 'Referencia del documento o acuerdo que respalda el permiso o la denegación.',
  use_conditions: 'Para qué se permite usar las semillas y qué límites deben respetarse, según el acuerdo.',
  received_on: 'Fecha de recepción, si se conoce. En una ficha de estudio puede quedar sin datos.',
  storage_conditions: 'Sólo las condiciones conocidas, por ejemplo las indicadas en la etiqueta. No se recomiendan valores automáticamente.',
  information_source: 'De dónde salió la información: documento, etiqueta o registro de prueba, por ejemplo.',
}

export function LotEditor({ lot, initialKind = 'real', initialRecordKind, existingCodes, showTests = false, busy, save, cancel }: {
  lot: SeedLot | null; initialKind?: Passport['source_kind']; initialRecordKind?: RecordKind; existingCodes: string[]; showTests?: boolean
  busy: boolean; save: (value: Passport) => void; cancel: () => void
}) {
  const [value, setValue] = useState<Passport>(() => lot ? passportOf(lot) : {
    ...emptyPassport(), source_kind: initialKind, record_kind: initialRecordKind ?? (initialKind === 'real' ? 'inventory' : 'study'), code: suggestSeedIdentifier(initialKind, existingCodes),
  })
  const helpId = useId()
  const change = <K extends keyof Passport>(key: K, next: Passport[K]) => setValue(previous => ({ ...previous, [key]: next }))
  const field = (key: keyof typeof passportLabels, multiline = false) => {
    const required = key === 'authorization_source' ? value.authorization_status !== 'pending'
      : key === 'use_conditions' && value.authorization_status === 'authorized'
    const props = { required, 'aria-describedby': fieldHelp[key] ? `${helpId}-${key}` : undefined,
      placeholder: 'Sin datos', value: String(value[key] ?? ''), onChange: (e: { target: { value: string } }) => change(key, e.target.value || null) }
    return <div key={key}><label>{passportLabels[key]}{required ? ' *' : ''}{multiline
      ? <textarea maxLength={2000} {...props} />
      : <input type={key === 'received_on' ? 'date' : 'text'} maxLength={key === 'scientific_name' || key === 'variety' ? 120 : 2000} {...props} />}</label>
      {fieldHelp[key] && <small className="seed-field-help" id={`${helpId}-${key}`}>{fieldHelp[key]}</small>}</div>
  }
  function submit(event: FormEvent) { event.preventDefault(); save(value) }
  return <form className="panel seed-panel seed-form" onSubmit={submit} onInvalidCapture={event => {
    // Permite enfocar un campo obligatorio aunque su sección esté cerrada.
    for (let parent = (event.target as HTMLElement).parentElement; parent; parent = parent.parentElement) {
      if (parent instanceof HTMLDetailsElement) parent.open = true
    }
  }} aria-label={lot ? 'Editar semillas' : 'Agregar semillas'}><fieldset disabled={busy}>
    <legend>{lot ? `Editar ficha · ${lot.code}` : recordLabel(value)}</legend>
    <p>{recordGroup(value) === 'inventory' ? 'Registra grupos de semillas recibidos o conservados físicamente. Una cantidad desconocida permanece sin datos.' : recordGroup(value) === 'study' ? 'Registra investigación documental auténtica sobre una especie candidata. No declara semillas físicas ni convierte la información en simulación.' : recordGroup(value) === 'simulation' ? 'Registra exclusivamente resultados ya generados por un escenario supuesto, con sus fuentes y supuestos.' : 'Ficha anterior: revisa la información y elige su clasificación. No se ha convertido en inventario ni se ha supuesto que sea simulación.'}</p>
    <div className="seed-fields seed-essential-fields"><label>Nombre de las semillas *<input required maxLength={120} placeholder="El nombre con el que las conoces" value={value.common_name} onChange={e => change('common_name', e.target.value)} /></label>
      <div><label>Tipo de registro *<select value={recordGroup(value)} disabled={!!lot && (lot.record_kind != null || lot.source_kind === 'real')} onChange={e => {
        const next = e.target.value as RecordKind
        setValue(previous => ({ ...previous, record_kind: next, source_kind: lot ? previous.source_kind : next === 'inventory' ? 'real' : 'hypothetical' }))
      }}>{recordGroup(value) === 'legacy' && <option value="legacy">Ficha anterior · por revisar</option>}{Object.entries(recordLabels).filter(([key]) => key !== 'legacy' && (!lot || key !== 'inventory' || lot.source_kind === 'real')).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label>{lot && <small className="seed-field-help">{lot.record_kind == null && lot.source_kind === 'hypothetical' ? 'Clasificar esta ficha antigua crea una revisión; no genera inventario.' : 'La clasificación se conserva al editar. La evidencia y sus fuentes se registran por separado.'}</small>}</div>
      <div><label>Identificador *<input required maxLength={120} aria-describedby={`${helpId}-code`} value={value.code} onChange={e => change('code', e.target.value)} /></label><small className="seed-field-help" id={`${helpId}-code`}>Código para distinguir esta ficha y seguir su historia. {lot ? 'Se conserva el identificador existente; puedes editarlo.' : 'Sugerimos uno único; puedes editarlo.'}</small></div>
    </div>
    {value.record_kind === 'simulation' && <label>Supuestos del escenario *<textarea required maxLength={2000} value={value.scenario_assumptions ?? ''} onChange={e => change('scenario_assumptions', e.target.value || null)} /></label>}
    <details className="seed-form-section"><summary>Origen y uso responsable</summary><p>Completa sólo lo documentado. Los datos desconocidos permanecen como «Sin datos»; el permiso sigue pendiente hasta que se documente.</p><div className="seed-fields">{field('provenance')}{field('custodian_entity')}
      <label>Estado de autorización<select value={value.authorization_status} onChange={e => change('authorization_status', e.target.value as Passport['authorization_status'])}>{Object.entries(authLabels).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label>
      {field('authorization_source', true)}{field('use_conditions', true)}
    </div><p>Registrar información no concede permiso de uso. Evita nombres, teléfonos y otros datos personales de custodios o informantes.</p></details>
    <details className="seed-form-section"><summary>Cómo se conservan</summary><div className="seed-fields">{field('storage_conditions', true)}{field('container')}{field('location')}</div></details>
    <details className="seed-form-section" open={showTests || undefined}><summary>Más información</summary><div className="seed-fields">{field('variety')}{field('scientific_name')}{field('received_on')}
      {(value.source_kind === 'real' || value.quantity !== null || value.unit !== null) && <>
      <div><label>{value.source_kind === 'real' ? 'Cantidad disponible (opcional)' : 'Cantidad anterior · no es inventario'}<input readOnly={value.source_kind !== 'real'} type="number" min="0" max="1000000000" step="any" placeholder="Sin datos" value={value.quantity ?? ''} onChange={e => change('quantity', e.target.value === '' ? null : Number(e.target.value))} /></label><small className="seed-field-help">{value.source_kind === 'real' ? 'Anota sólo cantidades conocidas. Dejarla vacía no significa cero.' : 'Se conserva este dato anterior sin reinterpretarlo. Documenta los valores nuevos con su tipo de evidencia, fuente y unidad.'}</small></div>
      <label>Unidad{value.quantity !== null ? ' *' : ''}<input readOnly={value.source_kind !== 'real'} required={value.quantity !== null} maxLength={120} placeholder="Ej.: semillas o g" value={value.unit ?? ''} onChange={e => change('unit', e.target.value || null)} /></label>
      </>}
      {field('observations', true)}{field('information_source', true)}
    </div>
    {lot && value.tests.length > 0 && <details className="seed-form-section" open={showTests || undefined}><summary>Pruebas anteriores · germinación y viabilidad</summary><p>Germinación: comprobar si las semillas brotan. Viabilidad: estudiar si pueden seguir vivas y germinar. Registra el resultado real de una prueba, su fuente y, cuando se conozcan, fecha y método; por ejemplo, el protocolo que se siguió. No se estiman resultados.</p>
    {value.tests.map((test, index) => <fieldset className="seed-test" key={index}><legend>Prueba {index + 1}</legend><div className="seed-fields">
      <label>Tipo de prueba<select value={test.kind} onChange={e => change('tests', value.tests.map((item, i) => i === index ? { ...item, kind: e.target.value as typeof test.kind } : item))}><option value="germination">Germinación</option><option value="viability">Viabilidad</option></select></label>
      {(['result', 'tested_on', 'method', 'source'] as const).map(key => <label key={key}>{{ result: 'Resultado documentado *', tested_on: 'Fecha de prueba', method: 'Método de prueba', source: 'Fuente de la prueba *' }[key]}<input type={key === 'tested_on' ? 'date' : 'text'} required={key === 'result' || key === 'source'} maxLength={2000} value={test[key] ?? ''} placeholder="Sin datos" onChange={e => change('tests', value.tests.map((item, i) => i === index ? { ...item, [key]: e.target.value || (key === 'result' || key === 'source' ? '' : null) } : item))} /></label>)}
    </div><button className="button button-quiet" type="button" onClick={() => change('tests', value.tests.filter((_, i) => i !== index))}>Quitar prueba {index + 1} de esta edición</button></fieldset>)}
    <p>Estos registros anteriores se conservan sin asignarles automáticamente un tipo de evidencia. Para una nueva prueba, usa «Pruebas y observaciones» e indica su procedencia.</p>
    </details>}
    </details>
    {lot && <EvidenceEditor passport={value} open={showTests} change={items => change('evidence', items)} />}
    {!lot && <p className="seed-field-help">Después de guardar podrás añadir información documental, pruebas y observaciones con fecha, método y fuente; evaluar la ficha y consultar su historial.</p>}
    <div className="decision-actions"><button className="button button-gold" type="submit">{busy ? 'Guardando…' : 'Guardar ficha'}</button><button className="button button-quiet" type="button" onClick={cancel}>Cancelar edición</button></div>
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
    <p>Evaluar es revisar varios aspectos de estas semillas con la información disponible. El peso indica cuánto cuenta cada aspecto en la comparación; por ejemplo, 25 % significa una cuarta parte del resultado. Debes explicar cada nota e indicar de dónde salió la información.</p>
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
