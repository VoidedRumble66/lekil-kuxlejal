export function DomeDiagram() {
  return <div className="dome-diagram">
    <svg viewBox="0 0 600 350" role="img" aria-labelledby="dome-title dome-description">
      <title id="dome-title">Esquema conceptual del biodomo</title>
      <desc id="dome-description">Representación de los sectores de hidroponía, sustrato seguro, semillas y servicios. No representa zonas instaladas ni lecturas reales.</desc>
      <defs>
        <linearGradient id="dome-fill" x1="300" y1="65" x2="300" y2="285" gradientUnits="userSpaceOnUse"><stop stopColor="#739b78" stopOpacity=".12" /><stop offset="1" stopColor="#739b78" stopOpacity=".015" /></linearGradient>
        <linearGradient id="dome-line" x1="120" y1="75" x2="500" y2="290" gradientUnits="userSpaceOnUse"><stop stopColor="#a1b796" stopOpacity=".8" /><stop offset="1" stopColor="#547365" stopOpacity=".3" /></linearGradient>
        <pattern id="floor-grid" width="35" height="17.5" patternUnits="userSpaceOnUse" patternTransform="skewX(-35)"><path d="M35 0H0V17.5" fill="none" stroke="#779485" strokeOpacity=".08" strokeWidth=".7" /></pattern>
      </defs>
      <ellipse cx="300" cy="268" rx="244" ry="64" fill="url(#floor-grid)" stroke="#607b6e" strokeOpacity=".18" />
      <ellipse cx="300" cy="268" rx="223" ry="49" fill="#0c1915" fillOpacity=".5" stroke="#739b78" strokeOpacity=".27" />
      <path d="M77 268C77 147 177 66 300 66s223 81 223 202" fill="url(#dome-fill)" stroke="url(#dome-line)" strokeWidth="1.5" />
      <g fill="none" stroke="url(#dome-line)" strokeWidth="1">
        <path d="M300 66c-86 54-142 132-147 231M300 66c86 54 142 132 147 231M300 66v250M123 157c98 38 256 38 354 0M82 229c118 48 319 48 436 0M123 157l30 140M123 157l109 106M123 157l84-70 25 176M207 87l93 121 93-121M300 66l-68 197 68-55 68 55-68-197M477 157l-30 140M477 157L368 263M477 157l-84-70-25 176M82 229l125-142M518 229L393 87M153 297l79-34M447 297l-79-34" />
      </g>
      <g fill="#91aa91"><circle cx="300" cy="66" r="3" /><circle cx="123" cy="157" r="2.5" /><circle cx="477" cy="157" r="2.5" /><circle cx="300" cy="208" r="2.5" /><circle cx="232" cy="263" r="2.5" /><circle cx="368" cy="263" r="2.5" /></g>
      <g stroke="#53735d" strokeWidth="1.2">
        <path d="m168 235 67-16 42 14-68 18Z" fill="#2b4231" /><path d="m168 235 41 16v10l-41-16Zm41 16 68-18v10l-68 18Z" fill="#21392a" />
        <path d="m322 233 65-17 41 15-66 18Z" fill="#304334" /><path d="m322 233 40 16v10l-40-16Zm40 16 66-18v10l-66 18Z" fill="#23382b" />
      </g>
      <g fill="none" stroke="#8dab80" strokeWidth="2" strokeLinecap="round">
        <path d="M190 238v-12m0 6c-8 0-9-5-9-5m9 9c8 0 10-6 10-6M213 232v-12m0 6c-8 0-9-5-9-5m9 9c8 0 10-6 10-6M237 226v-12m0 6c-8 0-9-5-9-5m9 9c8 0 10-6 10-6" />
        <path d="M345 236v-10m0 5-6-4m6 7 7-5M368 230v-10m0 5-6-4m6 7 7-5M391 224v-10m0 5-6-4m6 7 7-5" />
      </g>
      <g stroke="#65796a" strokeWidth="1.1"><path d="m213 282 46-12 29 10-46 13Z" fill="#314136" /><path d="m213 282 29 11v10l-29-11Zm29 11 46-13v10l-46 13Z" fill="#26362c" /><path d="m333 282 30-8 28 10-30 9Z" fill="#314136" /><path d="m333 282 28 11v10l-28-11Zm28 11 30-9v10l-30 9Z" fill="#26362c" /></g>
      <path d="m300 267 0 50" stroke="#c1a260" strokeWidth="2" strokeDasharray="3 5" opacity=".55" />
      <g fill="none" stroke="#c1a260" strokeOpacity=".6" strokeWidth="1"><path d="M149 220H78l-15-15M437 218h86l14-15M221 298l-25 29h-61M387 298l25 29h60" /><circle cx="149" cy="220" r="2" fill="#c1a260" /><circle cx="437" cy="218" r="2" fill="#c1a260" /></g>
      <g fill="#a9b7aa" fontSize="10" fontFamily="Segoe UI, sans-serif" letterSpacing="1"><text x="31" y="196">HIDROPONÍA</text><text x="466" y="194">SUSTRATO SEGURO</text><text x="79" y="331">SEMILLAS</text><text x="426" y="331">SERVICIOS</text></g>
    </svg>
    <span className="diagram-note">ESQUEMA CONCEPTUAL · SIN INSTRUMENTACIÓN</span>
  </div>
}
