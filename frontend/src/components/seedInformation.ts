import type { EvidenceKind, Passport } from '../seedApi'

export const recordLabels = {
  inventory: 'Semillas disponibles', study: 'Cultivos en estudio', simulation: 'Simulación',
  legacy: 'Ficha anterior · por revisar',
} as const
export function recordGroup(passport: Pick<Passport, 'record_kind' | 'source_kind'>) {
  return passport.record_kind ?? (passport.source_kind === 'real' ? 'inventory' : 'legacy')
}
export const recordLabel = (passport: Pick<Passport, 'record_kind' | 'source_kind'>) => recordLabels[recordGroup(passport)]
export const evidenceLabels: Record<EvidenceKind, string> = {
  documentary: 'Información documental', manual: 'Observación manual', instrumental: 'Medición instrumental transcrita',
  calculation: 'Cálculo', simulation: 'Simulación',
}
export const evidenceHelp: Record<EvidenceKind, string> = {
  documentary: 'Información de un artículo, libro, etiqueta u otra fuente identificable. Fecha de consulta y método de revisión; no afirma que tengas semillas.',
  manual: 'Un hecho observado por una persona. Indica la fecha del hecho y cómo se observó.',
  instrumental: 'Transcripción de un registro instrumental existente. Identifica instrumento, fecha, método y fuente. No crea sensores ni telemetría en DOMO VITAL.',
  calculation: 'Un resultado derivado. Escribe la fórmula o procedimiento y la procedencia de los datos de entrada. No es una medición física.',
  simulation: 'Sólo un resultado generado por un escenario supuesto. Identifica la ejecución o modelo y sus supuestos. No es un hecho observado.',
}
