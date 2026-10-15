import { BellRing, ShieldCheck } from 'lucide-react'
import { PageHeading, PhaseNotice } from '../components/Shared'

export default function Alerts() {
  return <>
    <PageHeading title="Alertas" description="Una alerta necesita una lectura válida, un límite justificado y un contexto." />
    <div className="info-strip"><ShieldCheck size={21} /><p><strong>Estado: sin evaluar.</strong> La ausencia de alertas generadas no confirma condiciones estables ni ausencia de riesgos.</p></div>
    <PhaseNotice icon={BellRing} title="El motor de alertas aún no está habilitado" description="La siguiente fase integrará la telemetría real, la vigencia de lecturas y los estados de conexión. Los límites se configurarán por cultivo y fuente; no se utiliza un rango universal." />
  </>
}
