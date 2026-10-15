# Requisitos y trazabilidad

Fuentes: [especificación maestra](referencias/ESPECIFICACION_MAESTRA.txt), [expediente](referencias/LekilKuxlejal.pdf) y ocho referencias visuales inventariadas en [referencias/README.md](referencias/README.md). Las páginas siguientes son las páginas reales del PDF, no las entradas de su índice.

## Entrega activa: Fase 1

| ID | Requisito | Verificación |
| --- | --- | --- |
| F1-01 | Un backend FastAPI, un frontend React/TypeScript/Vite y SQLite local con Alembic | Arranque y build documentados |
| F1-02 | `GET /api/health`, `/api/zones`, `/api/devices` y `/api/telemetry` | Pruebas de contrato y HTTP |
| F1-03 | Registrar zonas y ESP32-S3 aunque todavía no haya sensores | POST de configuración persistente; estado `not_configured` |
| F1-04 | Ninguna medición, reserva o conexión inventada al iniciar | Tabla `measurements` vacía; indicadores sin lecturas |
| F1-05 | Inicio basado en DOMO VITAL, adaptable y accesible | Revisión de navegación, textos, contraste y estados vacíos |
| F1-06 | Modo observación, control físico deshabilitado | Health constante y ausencia de rutas de control |
| F1-07 | Contratos tipados, timestamps UTC y claves foráneas activas | Pruebas y migración versionada |
| F1-08 | Instrucciones Windows y errores pendientes explícitos | README raíz y verificación de fase |

Los POST de zonas y dispositivos permiten configurar y verificar persistencia; no habilitan telemetría ni control. No se precargan las cuatro zonas de las capturas como instalaciones reales.

## Reglas transversales

| ID | Regla | Fuente del dominio |
| --- | --- | --- |
| D-01 | Biodomo agrícola, separado de la instalación habitada y del laboratorio confinado | pp. 17-20, 31, 36-38 |
| D-02 | Seis funciones enlazadas: reserva, producción/semillas, biomasa, protección/automatización, memoria y gobernanza | pp. 17-18 |
| D-03 | Procedencia, permiso, práctica, pregunta, ensayo, adaptación, resultado y devolución; registro técnico y biocultural enlazados | pp. 21-25, 44-45, 58-59 |
| D-04 | Datos medidos, estimaciones y supuestos diferenciados; sin medidor no hay consumo medido | pp. 35, 39-41 |
| D-05 | Dato ausente no equivale a emergencia física ni a depósito vacío; mostrar calidad y verificar | pp. 39, 47-49, 60 |
| D-06 | Recomendaciones explicables, mínimos protegidos, autorización humana, revisión e historial conservado | pp. 41-43, 58 y 60 |
| D-07 | No liberar cosecha sin trazabilidad, criterios de inocuidad y autorización | pp. 36-38 y 44 |
| D-08 | No atribuir descontaminación, fertilización certificada, ahorro, vida útil o nutrición completa sin ensayos | pp. 27-28, 35-38, 47-49 y 57 |
| D-09 | No publicar ni entrenar con conocimiento restringido; consentimiento específico y derecho a corrección/retiro | pp. 24-25, 46 y 53 |

Todo registro operativo futuro debe conservar identificador, fuente, fecha/hora con zona, entidad asociada, unidad y valor cuando apliquen, calidad, responsable/dispositivo y observaciones. Los fixtures sintéticos se limitan a bases temporales de pruebas. Los escenarios tendrán almacenamiento y navegación independientes, rótulo permanente «ESCENARIO HIPOTÉTICO» y ninguna capacidad de actuación.

## Requisitos diseñados para fases posteriores

| Área | Capacidad prevista | Referencia |
| --- | --- | --- |
| Instrumentación | Sensores, calibraciones, vigencia, desconexión, unidades, valores imposibles y fallas | pp. 39 y 49 |
| Sectores | Propósitos configurables: hidroponía, investigación en sustrato seguro, banco de semillas y servicios; laboratorio separado | pp. 31 y 36 |
| Semillas | Catálogos, pasaporte, lotes, custodia, almacenamiento, viabilidad y relación con ciclos | pp. 29-30 |
| Cultivos | Observaciones manuales y sensores, consumo real, fotografías, cosecha y liberación | pp. 37-38 y 58 |
| Biomasa | Lotes, composición real, tratamientos, control, réplicas, resultados y criterios de suspensión | pp. 36-37 |
| Alimentos | Lotes, inventario, versiones de receta, preparación, empaque, análisis e inocuidad | pp. 26-28 y 44-46 |
| Cultura | Ficha enlazada a ensayos y recetas con permisos y revisión de la fuente | pp. 24, 44-45 y 59 |
| Recursos | Balances con L, W, Wh/kWh y masa; fórmulas, origen, incertidumbre y reservas fuera del biodomo | pp. 35, 37-38 y 41-43 |
| Gobernanza | Reglas deterministas, alternativas factibles, explicación, autoridad y auditoría | pp. 41-43, 58 y 60 |
| Escenarios | Normalidad, polvo, sensor desconectado, 40 % menos agua, 40 % menos energía y recuperación | p. 47 |

Esta tabla es diseño de alcance, no una declaración de módulos terminados. La validación del sistema requiere tareas con usuarios, pruebas de fallas y ensayos físicos separados (pp. 47-51).
