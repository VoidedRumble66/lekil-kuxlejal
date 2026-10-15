import { useLocation } from 'react-router-dom'
import { PageHeading, PhaseNotice } from '../components/Shared'

const modules: Record<string, [string, string]> = {
  '/domo/semillas': ['Semillas y custodia', 'El catálogo, los lotes y los registros de germinación se incorporarán con procedencia, custodia y resultados reales.'],
  '/domo/cultivos': ['Cultivos', 'Los ciclos de cultivo, las observaciones y las cosechas se incorporarán en una etapa posterior. Una cosecha experimental no implica su liberación para consumo.'],
  '/domo/biomasa': ['Biomasa y sustratos', 'Los ensayos conservarán componentes, tratamientos, réplicas y mediciones reales. La evaluación experimental no constituye una certificación.'],
  '/domo/memoria': ['Memoria biocultural', 'Las fichas deberán conservar procedencia, consentimiento y condiciones de uso. La publicación requiere permisos explícitos.'],
  '/recursos/inventarios': ['Inventarios', 'El inventario y los movimientos de agua, nutrientes, semillas y consumibles se habilitarán en una etapa posterior. No hay reservas registradas en esta fase.'],
  '/recursos/recetas': ['Alimentos y recetas', 'Los lotes, fichas de preparación y recetas se incorporarán con procedencia cultural, cantidades y resultados disponibles. No se infieren certificaciones de inocuidad.'],
  '/recursos/historial': ['Historial y trazabilidad', 'La vista de auditoría se incorporará en una etapa posterior. Los registros actuales de zonas y dispositivos conservan su identificador y fecha en la API.'],
}

export default function FutureModule() {
  const { pathname } = useLocation()
  const module = modules[pathname]
  return <><PageHeading title={module?.[0] || 'Página no encontrada'} description={module ? 'Módulo previsto en la arquitectura del proyecto.' : 'Esta dirección no corresponde a una página del sistema.'} /><PhaseNotice title={module ? 'Este módulo aún no está disponible' : 'Vuelve al centro de observación'} description={module?.[1] || 'Usa la navegación principal para continuar.'} /></>
}
