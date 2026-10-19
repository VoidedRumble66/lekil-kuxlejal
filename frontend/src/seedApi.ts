import { request } from './api'

export const criteria = ['nutrition', 'resources', 'continuity', 'edible', 'culinary', 'resilience'] as const
export type Criterion = typeof criteria[number]
export type Weights = Record<Criterion, number>
export type RecordKind = 'inventory' | 'study' | 'simulation'
export type EvidenceKind = 'documentary' | 'manual' | 'instrumental' | 'calculation' | 'simulation'
export interface SeedEvidence {
  kind: EvidenceKind; subject: string; content: string; recorded_on: string; method: string; source: string
  value: number | null; unit: string | null; instrument: string | null; assumptions: string | null
}
export interface SeedTest { kind: 'germination' | 'viability'; result: string; tested_on: string | null; method: string | null; source: string }
export interface Passport {
  common_name: string; scientific_name: string | null; variety: string | null; code: string
  source_kind: 'real' | 'hypothetical'; quantity: number | null; unit: string | null
  record_kind?: RecordKind | null; evidence?: SeedEvidence[]; scenario_assumptions?: string | null
  provenance: string | null; custodian_entity: string | null
  authorization_status: 'pending' | 'authorized' | 'denied'; use_conditions: string | null; authorization_source: string | null
  received_on: string | null; storage_conditions: string | null; container: string | null; location: string | null
  tests: SeedTest[]; observations: string | null; information_source: string | null
}
export interface SeedLot extends Passport { id: string; revision: number; created_at: string; updated_at: string }
export interface WeightSnapshot {
  id: string | null; weights: Weights; responsible: string | null; reason: string; created_at: string | null
}
export interface WeightProfile extends WeightSnapshot {
  criteria: Record<Criterion, string>; scale: string
}
export interface Score { value: number; justification: string; source: string }
export type Scores = Record<Criterion, Score | null>
export interface Assessment { id: string; lot_id: string; lot_revision: number; weight_profile_id: string | null; weights: Weights; scores: Scores; total: number | null; responsible: string; created_at: string }
export interface Comparison {
  complete: boolean; comparison_hash: string; notice: string; weights: WeightSnapshot
  rows: { lot: SeedLot; assessment: Assessment | null; problems: string[]; total: number | null }[]
}
export type Action = 'conservar' | 'sembrar' | 'retirar' | 'repetir_prueba' | 'seleccionar'
export interface SeedDecision { id: string; action: Action; responsible: string; reason: string; created_at: string; snapshot: { lot: SeedLot; comparison: Comparison | null; effect: string } }
export interface SeedHistory {
  revisions: { id: string; revision: number; passport: Passport; created_at: string }[]
  assessments: Assessment[]; decisions: SeedDecision[]
}
export const emptyPassport = (): Passport => ({
  common_name: '', scientific_name: null, variety: null, code: '', source_kind: 'real', quantity: null, unit: null,
  provenance: null, custodian_entity: null, authorization_status: 'pending', use_conditions: null, authorization_source: null,
  received_on: null, storage_conditions: null, container: null, location: null, tests: [], observations: null, information_source: null,
  record_kind: null, evidence: [], scenario_assumptions: null,
})
export const passportOf = (lot: SeedLot): Passport => {
  const { id, revision, created_at, updated_at, ...passport } = lot
  void id; void revision; void created_at; void updated_at
  return passport
}
const post = <T>(path: string, data: unknown) => request<T>(path, { method: 'POST', body: JSON.stringify(data) })
export const seedApi = {
  lots: (offset = 0) => request<SeedLot[]>(`/seeds/lots?limit=100&offset=${offset}`),
  lot: (id: string) => request<SeedLot>(`/seeds/lots/${id}`),
  create: (passport: Passport) => post<SeedLot>('/seeds/lots', passport),
  update: (lot: SeedLot, passport: Passport) => request<SeedLot>(`/seeds/lots/${lot.id}`, { method: 'PUT', body: JSON.stringify({ expected_revision: lot.revision, passport }) }),
  weights: () => request<WeightProfile>('/seeds/weights'),
  saveWeights: (weights: Weights, responsible: string, reason: string) => post<WeightProfile>('/seeds/weights', { weights, responsible, reason }),
  history: (id: string) => request<SeedHistory>(`/seeds/lots/${id}/history`),
  assess: (lot: SeedLot, profile: WeightProfile, scores: Scores, responsible: string) => post<Assessment>(`/seeds/lots/${lot.id}/assessments`, { expected_revision: lot.revision, weight_profile_id: profile.id, scores, responsible }),
  compare: (lot_ids: string[]) => post<Comparison>('/seeds/compare', { lot_ids }),
  decide: (lot: SeedLot, action: Action, responsible: string, reason: string, comparison: Comparison | null) => post<SeedDecision>(`/seeds/lots/${lot.id}/decisions`, {
    expected_revision: lot.revision, action, responsible, reason,
    ...(action === 'seleccionar' && comparison ? { comparison: { lot_ids: comparison.rows.map(row => row.lot.id) }, comparison_hash: comparison.comparison_hash } : {}),
  }),
}
