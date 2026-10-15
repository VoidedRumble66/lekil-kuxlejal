# Inventario de referencias locales

Inspección: 15 de octubre de 2026. Al iniciar el trabajo no existía `docs/referencias/`; se creó y se copiaron los archivos aportados desde Downloads y el adjunto de texto. Las copias son para trabajo local; no se presume autorización de publicación o redistribución.

## Archivos disponibles

| Archivo local | Procedencia y función |
| --- | --- |
| `LekilKuxlejal.pdf` | PDF aportado, fuente principal de requisitos de dominio |
| `ESPECIFICACION_MAESTRA.txt` | Copia íntegra de «Texto pegado.txt» del adjunto del usuario; define el encargo y limita esta ejecución a Fase 1 |
| `Prototipo aplicación DOMO VITAL.png` | Inicio en estado normal, referencia visual |
| `Prototipo aplicación DOMO VITAL-1.png` | Inicio, tormenta de polvo |
| `Prototipo aplicación DOMO VITAL-2.png` | Inicio, falla de sensor |
| `Prototipo aplicación DOMO VITAL-3.png` | Inicio, reducción de agua |
| `Prototipo aplicación DOMO VITAL-4.png` | Inicio, recuperación |
| `Prototipo aplicación DOMO VITAL-5.png` | Mapa del domo |
| `Prototipo aplicación DOMO VITAL-6.png` | Decisiones |
| `Prototipo aplicación DOMO VITAL-7.png` | Recursos |

No se encontraron otros documentos independientes de Mars Challenge entre los archivos aportados. **Falta el archivo de la «Rúbrica de evaluación 2026»**, citado en la bibliografía del expediente (p. 57, referencia 15). Los modelos Blender, simulaciones electrónicas, hojas de formulación, bitácoras y evidencias internas citados por el PDF tampoco fueron aportados como archivos independientes. Su mención en el expediente no acredita acceso a ellos.

## Identificación verificada del expediente

- Título de portada y metadatos: **LEKIL KUXLEJAL MARTE**.
- Subtítulo: Expediente técnico y biocultural para Mars Challenge 2026.
- Autor: Equipo A Marte Chiapas.
- Versión declarada en portada: oficial 1.1, 28 de septiembre de 2026.
- Extensión comprobada con `pypdf`: **62 páginas**.
- SHA-256 del PDF copiado: `9C5FFB7E09302E902A677006BA51C216264FE5D7C1BE96A6F62999892E030C3B`.
- SHA-256 de la especificación copiada: `62734BC1E8A2B7FE022A6753FF2514B24292A1091405E42D3A023C795CFE8E72`.

Se extrajo y leyó el texto completo de los capítulos 3-12 y de los anexos A/B. Se revisaron también portada, alcance, bibliografía, ética y glosario. La página 39 se renderizó con Poppler y se inspeccionó visualmente: tablas de instrumentación y autonomía legibles. Poppler emitió avisos sobre fuentes de visualización `Symbol` y `ArialUnicode`; el PDF original no se modificó.

## Localizadores de contenido comprobados

El índice del PDF tiene desfases a partir de algunos capítulos. Se citan aquí **páginas reales del archivo, coincidentes con el pie de página**, para evitar reproducir ese error.

| Sección | Páginas | Implicación para el software |
| --- | --- | --- |
| Cap. 3, arquitectura y seis funciones | 17-20 | Cadena integrada, interfaces, autorizaciones y barreras |
| Cap. 4, ciencia con identidad | 21-25 | Registro dual, procedencia, consentimiento, pregunta, prueba y devolución |
| Cap. 5, alimentación | 26-28 | Lotes y versiones; cifras de formulación pendientes de análisis |
| Cap. 6, semillas | 29-30 | Pasaporte, custodia, viabilidad y umbrales por especie |
| Cap. 7, biodomo y envolvente | 31-35 | Sectores conceptuales y cálculos paramétricos, no desempeño medido |
| Cap. 8, cultivo, agua y biomasa | 36-38 | Separar líneas, controlar ensayos y autorizar liberación de cosecha |
| Cap. 9, telemetría y gobernanza | 39-43 | Sin datos explícito, unidades, autoridad humana y auditoría |
| Cap. 10, cocina y bienestar | 44-46 | Recetas trazables, permisos y privacidad voluntaria |
| Cap. 11, evidencia y aprendizaje | 47-48 | Estado conceptual/digital y seis escenarios de prueba |
| Cap. 12, validación | 49-51 | Banco terrestre, mediciones y puertas de avance |
| Anexo A, formatos | 58-59 | Cultivo, incidente/decisión, receta y ficha de ciencia con identidad |
| Anexo B, emergencia | 60 | Confirmar antes de actuar, mínimos, revisión e historial conservado |

## Uso y discrepancias resueltas

El PDF se trata como material de referencia. La especificación del usuario autoriza el trabajo por fases. Las capturas orientan paleta, jerarquía, iconografía y navegación; los números 21 °C, 78 u y 72 % no se copian a datos operativos. La interfaz de Fase 1 presenta ausencia de datos.

El PDF p. 41 sugiere Next.js como ruta posible; se usa Vite por instrucción explícita del usuario. El modelo de fases del expediente describe la misión, y su hoja de ruta p. 50 abarca meses; no son las fases de desarrollo del encargo. La autorización futura descrita para actuadores no habilita actuación en esta entrega.

No se inventan traducciones, pinout, valores de calibración, límites universales para cultivos, resultados agronómicos ni consentimientos. Tampoco se presentan cálculos preliminares, simulaciones o procesos alimentarios como validación física.
