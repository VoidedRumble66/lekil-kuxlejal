import { Archive, BookOpen, Droplets, History, LockKeyhole, Zap } from 'lucide-react'
import { PageHeading, RouteCard, SourceLabel } from '../components/Shared'

export default function Resources() {
  return <>
    <PageHeading title="Recursos del domo" description="Para decidir con cuidado, primero necesitamos medir." />
    <div className="resources-grid">
      <section className="panel resource-panel water"><span className="resource-icon"><Droplets size={28} strokeWidth={1.5} /></span><SourceLabel>LECTURA NO DISPONIBLE</SourceLabel><h2>Agua agrícola</h2><div className="resource-value">Sin datos<span>L</span></div><p>El volumen del depósito requiere instrumentación y validación. No hay una reserva medida.</p><div className="metric-footer"><span className="small-dot" />Sensor no configurado</div></section>
      <section className="panel resource-panel energy"><span className="resource-icon"><Zap size={28} strokeWidth={1.5} /></span><SourceLabel>MEDICIÓN PENDIENTE</SourceLabel><h2>Energía eléctrica</h2><div className="resource-value">Sin datos<span>Wh</span></div><p>Una medición requiere un medidor eléctrico. El estado de un interruptor no permite determinar el consumo.</p><div className="metric-footer"><span className="small-dot" />Consumo no medido</div></section>
    </div>
    <div className="info-strip"><LockKeyhole size={20} /><p>Los balances, movimientos de inventario y cálculos de consumo se habilitarán en una etapa posterior, con datos, unidades y supuestos trazables.</p></div>
    <div className="section-title"><div><div className="eyebrow">TRAZABILIDAD DEL SISTEMA</div><h2>Más allá de la medición</h2></div></div>
    <div className="route-grid"><RouteCard icon={Archive} title="Inventarios" description="Reservas y movimientos · etapa posterior" to="/recursos/inventarios" /><RouteCard icon={BookOpen} title="Alimentos y recetas" description="Preparación, lotes y evidencia" to="/recursos/recetas" /><RouteCard icon={History} title="Historial y trazabilidad" description="Conservar el origen de cada registro" to="/recursos/historial" /></div>
    <section className="scenario-disabled"><div><div className="eyebrow">ESCENARIOS HIPOTÉTICOS</div><h3>Explorar posibilidades, conservar la evidencia</h3><p>Los escenarios tendrán sus propios datos e historial, separados de las mediciones reales.</p></div><button className="button button-outline" disabled><LockKeyhole size={16} />Disponible en otra etapa</button></section>
  </>
}
