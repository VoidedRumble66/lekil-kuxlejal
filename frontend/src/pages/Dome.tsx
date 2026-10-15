import { ArrowRight, Archive, Beaker, BookOpen, FlaskConical, Plus, Sprout } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useData } from '../state'
import { PageHeading, ResourceState, RouteCard } from '../components/Shared'

export default function Dome() {
  const { zones } = useData()
  return <>
    <PageHeading title="Mapa del domo" description="Zonas con un propósito definido. Producción e investigación, con límites claros." action={<Link className="button button-gold" to="/configuracion"><Plus size={17} />Registrar zona</Link>} />
    <section className="panel section-panel"><div className="panel-heading"><div><div className="eyebrow">CONFIGURACIÓN REAL</div><h2>Zonas registradas</h2></div><span className="tag">SIN INSTRUMENTACIÓN</span></div>
      <ResourceState resource={zones}>{items => items.length ? <div className="zone-grid">{items.map(zone => <article className="zone-card" key={zone.id}><div className="zone-card-top"><Sprout size={23} /><span className="status-pill neutral">Sin datos</span></div><h3>{zone.name}</h3><span className="zone-purpose">{zone.purpose}</span>{zone.description && <p>{zone.description}</p>}<div className="zone-card-footer">Sensor no configurado</div></article>)}</div> : <div className="empty-inline"><div className="empty-icon"><Sprout size={30} strokeWidth={1.4} /></div><h3>El mapa comienza con tus zonas</h3><p>Registra las áreas que existen en tu instalación. Los sectores conceptuales no se crean como zonas operativas automáticamente.</p><Link className="text-link" to="/configuracion">Definir la primera zona<ArrowRight size={16} /></Link></div>}</ResourceState>
    </section>
    <div className="section-title"><div><div className="eyebrow">UN SISTEMA CON IDENTIDAD</div><h2>Explorar el módulo</h2></div><span className="subtle-note">Módulos previstos · aún no operativos</span></div>
    <div className="route-grid"><RouteCard icon={Archive} title="Semillas y custodia" description="Lotes, procedencia y viabilidad" to="/domo/semillas" /><RouteCard icon={Sprout} title="Cultivos" description="Ciclos, observaciones y cosechas" to="/domo/cultivos" /><RouteCard icon={Beaker} title="Biomasa y sustratos" description="Ensayos y evidencia experimental" to="/domo/biomasa" /><RouteCard icon={BookOpen} title="Memoria biocultural" description="Procedencia, consentimiento y revisión" to="/domo/memoria" /></div>
    <div className="info-strip"><FlaskConical size={20} /><p>El laboratorio confinado debe permanecer separado de la producción alimentaria. El propósito de cada zona se define durante su registro.</p></div>
  </>
}
