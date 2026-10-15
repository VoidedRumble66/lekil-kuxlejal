import { CheckCheck, FileText, GitBranch, LockKeyhole, Scale } from 'lucide-react'
import { PageHeading, PhaseNotice } from '../components/Shared'

export default function Decisions() {
  return <>
    <PageHeading title="Decisiones" description="Observar, explicar y revisar. Las decisiones relevantes requieren autorización humana." />
    <div className="info-strip"><Scale size={21} /><p><strong>Gobernanza con responsabilidad.</strong> El sistema está en modo observación. No recomienda, vota ni ejecuta decisiones en esta fase.</p></div>
    <PhaseNotice icon={GitBranch} title="Primero la evidencia. Después, las alternativas." description="El motor determinista de reglas y optimización se desarrollará en una etapa posterior. Hoy no hay una evaluación operativa ni recomendaciones generadas." />
    <div className="principles-grid"><div><FileText size={21} /><h3>Explicable</h3><p>Cada alternativa deberá mostrar sus datos, supuestos y consecuencias.</p></div><div><CheckCheck size={21} /><h3>Revisable</h3><p>Las decisiones relevantes deberán contar con revisión y autorización humana.</p></div><div><LockKeyhole size={21} /><h3>Controlado</h3><p>El control físico permanece deshabilitado en esta primera fase.</p></div></div>
  </>
}
