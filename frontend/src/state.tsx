import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { api } from './api'
import type { Device, Health, Telemetry, Zone } from './api'

export interface Resource<T> {
  data: T | undefined
  loading: boolean
  error: string | null
  reload: (background?: boolean) => Promise<void>
}

function useResource<T>(loader: () => Promise<T>): Resource<T> {
  const [state, setState] = useState<{ data: T | undefined; loading: boolean; error: string | null }>({ data: undefined, loading: true, error: null })
  const sequence = useRef(0)
  const reload = useCallback(async (background = false) => {
    const current = ++sequence.current
    setState(previous => background && previous.data !== undefined
      ? previous : { data: undefined, loading: true, error: null })
    try {
      const data = await loader()
      if (current === sequence.current) setState({ data, loading: false, error: null })
    } catch (error) {
      if (current === sequence.current) setState({ data: undefined, loading: false, error: error instanceof Error ? error.message : 'No se pudo consultar la información.' })
    }
  }, [loader])
  useEffect(() => {
    void reload()
    return () => { sequence.current += 1 }
  }, [reload])
  return { ...state, reload }
}

interface AppState {
  health: Resource<Health>
  zones: Resource<Zone[]>
  devices: Resource<Device[]>
  telemetry: Resource<Telemetry>
  connected: boolean
  refresh: () => Promise<void>
}

const Context = createContext<AppState | null>(null)

export function DataProvider({ children }: { children: ReactNode }) {
  const health = useResource(api.health)
  const zones = useResource(api.zones)
  const devices = useResource(api.devices)
  const telemetry = useResource(api.telemetry)
  const connected = health.data?.status === 'ok' && health.data.database === 'connected' && health.data.control_enabled === false && health.data.mode === 'observation'
  const refresh = async () => { await Promise.allSettled([health.reload(), zones.reload(), devices.reload(), telemetry.reload()]) }
  return <Context.Provider value={{ health, zones, devices, telemetry, connected, refresh }}>{children}</Context.Provider>
}

export function useData() {
  const context = useContext(Context)
  if (!context) throw new Error('DataProvider no disponible')
  return context
}

export function formatDate(value: string | undefined) {
  if (!value || Number.isNaN(new Date(value).getTime())) return 'Fecha no disponible'
  return new Intl.DateTimeFormat('es-MX', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}
