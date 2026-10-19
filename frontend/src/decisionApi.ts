import { request } from './api'

export interface ServiceAssumption {
  key: string; name: string; target_daily_kwh: number; priority: number
  minimum_daily_kwh: number | null; minimum_basis: string | null
}
export interface ScenarioInput {
  name: string; assumptions: string; periods: number; period_hours: number; generation_reduction: number
  initial_energy_kwh: number; storage_capacity_kwh: number; protected_reserve_kwh: number
  generation_daily_kwh: number[]; module_daily_limit_kwh: number; services: ServiceAssumption[]
}
export interface EnergyPeriod {
  period: number; hours: number; initial_kwh: number; gross_generation_kwh: number
  reduced_generation_kwh: number; generation_cut_kwh: number; curtailed_kwh: number
  available_kwh: number; consumption_kwh: number; ending_kwh: number; protected_reserve_kwh: number
  allocations_kwh: Record<string, number>
}
export interface Alternative {
  id: string; label: string; feasible: boolean; allocations_kwh: Record<string, number>; periods: EnergyPeriod[]
  fitness: number; total_consumption_kwh: number; total_curtailed_kwh: number; ending_kwh: number
  justification: string; unmet_target_kwh: Record<string, number>
}
export interface ReviewInput {
  alternative_id: string; decision: 'approved' | 'rejected'; responsible: string; reason: string
}
export interface Review extends ReviewInput { id: string; run_id: string; created_at: string }
export interface DecisionRun {
  id: string; created_at: string; source: 'hypothetical'; parameters: ScenarioInput
  engine_fingerprint: string; snapshot_sha256: string; reviews: Review[]
  result: {
    status: 'feasible' | 'infeasible'; source: 'hypothetical'; unit: 'kWh'; attribution: string
    agricultural_status: string; constraints: string[]
    search: { evaluated: number; feasible: number; pareto: number; method: string }
    rejections: { reason: string; count: number }[]; alternatives: Alternative[]
  }
}
export interface RunSummary { id: string; name: string; created_at: string; status: string; alternative_count: number }

export const decisionApi = {
  compare: (value: ScenarioInput) => request<DecisionRun>('/decisions/runs', { method: 'POST', body: JSON.stringify(value) }),
  history: (offset = 0) => request<RunSummary[]>(`/decisions/runs?limit=30&offset=${offset}`),
  run: (id: string) => request<DecisionRun>(`/decisions/runs/${id}`),
  review: (id: string, value: ReviewInput) => request<Review>(`/decisions/runs/${id}/reviews`, { method: 'POST', body: JSON.stringify(value) }),
}
