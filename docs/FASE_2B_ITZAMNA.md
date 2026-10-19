# Fase 2B · Gobernanza agrícola con Itzamná

Entrega local del 19 de octubre de 2026. Alcance: configurar una crisis hipotética de generación, comparar alternativas energéticas y registrar decisiones humanas. No modifica firmware, lector serial, COM6, dispositivos, zonas ni mediciones. Los informes de Fases 1 y 2A se conservan.

## Inicio y demostración en Windows

Desde `C:\Users\mende\Documents\lekil-kuxlejal`, con el entorno existente:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt -c backend\constraints-lock.txt
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-backend.ps1
```

La instalación de NumPy necesita acceso al registro de paquetes una sola vez; después la ejecución no requiere internet. Debe existir la referencia proporcionada `referencias/itzamna_motor/core/`; se consume directamente sin copiarla ni añadirla al commit. En otra terminal:

```powershell
Set-Location 'C:\Users\mende\Documents\lekil-kuxlejal'
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-frontend.ps1
```

1. Abrir [Decisiones](http://127.0.0.1:5173/decisiones).
2. Examinar los supuestos editables: cinco periodos de 24 horas; recorte 40 %; energía inicial 8 kWh, capacidad 12 kWh, reserva 2 kWh; generación antes del recorte 10 kWh/24 h por periodo. Son ejemplos hipotéticos, no medidas. Servicios genéricos: circulación, iluminación y ambiente; no corresponden a dispositivos o zonas físicos.
3. Abrir la sección de servicios para ajustar objetivos, prioridades o mínimos opcionales con su procedencia. No se precargan mínimos agrícolas.
4. Pulsar **Ejecutar comparación y guardar**. Examinar asignaciones, objetivos no cubiertos, balances, restricciones y justificación de hasta tres alternativas distintas. Sin mínimos completos aparece **Factibilidad agrícola no evaluada**.
5. Pulsar **Aprobar alternativa…** o **Rechazar alternativa…**, indicar responsable y motivo y pulsar **Guardar revisión humana**. La fecha UTC la registra el servidor. Hay una revisión definitiva por alternativa y como máximo una aprobación por comparación; un nuevo análisis crea otro registro, sin reescribir el anterior.
6. Recargar o reiniciar API e interfaz y abrir la comparación en **Historial de escenarios hipotéticos**. Parámetros, resultados y revisiones permanecen en SQLite.
7. Para comprobar un escenario infactible, declarar mínimos iguales a los objetivos de los tres servicios, con procedencia explícita «Supuesto hipotético de demostración, sin validación agrícola», y mantener el resto del ejemplo. La energía es insuficiente para sostenerlos durante cinco periodos: no se ofrecen alternativas ni aprobación. Estos valores no son necesidades de cultivos.

No hace falta iniciar el lector serial para utilizar Decisiones. Si se usa el diagnóstico existente, su script y COM6 permanecen iguales; iniciarlo después de la API. Detener los procesos con `Ctrl+C`.

## Reutilización y atribución

`backend/app/itzamna_adapter.py` importa el paquete exacto `itzamna_motor.core` de la referencia local. Atribución: **Itzamná, núcleo local proporcionado por el usuario; adaptación energética DOMO VITAL**. No se usa el repositorio externo, la API SSE, las plantillas de cultivos ni el frontend Next.js. No se ha deducido una licencia de redistribución ni publicado la referencia; se conserva como archivo local suministrado.

Funciones reutilizadas: `validate_dependency_graph`, `build_gene_mapping`, `simulate_fixed_allocations`, `evaluate_population` y `pareto_front`. No se reemplazan estas funciones ni se modifica la carpeta de referencia, incluidas sus pruebas. La adaptación impide generar cachés de Python en ella.

El motor original parte de inventario y producción diferida; no acredita generación solar diaria externa. Los verificadores `auditoria_2026` son experimentales independientes y **no se importan** ni se atribuyen como reglas del algoritmo. La adaptación añade el balance temporal por fuera y llama a la simulación y fitness comprobados para un periodo a la vez. No requiere refactorizar el núcleo. No usa evolución aleatoria: explora cuatro niveles por servicio entre mínimo declarado y objetivo, incluidos los extremos (máximo cuatro servicios y 256 candidatos). Sin mínimo declarado, el cero es únicamente el extremo numérico de búsqueda, nunca un mínimo agrícola supuesto.

Se descartan candidatos infactibles antes de Pareto. La frontera maximiza cobertura de cada servicio y saldo final. Se elige primero el mayor fitness Itzamná y después alternativas de la frontera con separación de objetivos; nunca se rellenan plazas con resultados no disponibles. Las prioridades afectan al fitness; no son votos ni certificaciones agronómicas. El resultado es determinista, con asignaciones constantes por periodo; no asegura un óptimo continuo ni evalúa todos los horarios posibles.

## Modelo energético explícito

Todas las energías usan kWh. Generación y objetivos introducidos en kWh/24 h se multiplican por `period_hours / 24`. Duración y recorte son configurables; valores iniciales: cinco periodos, 24 h y 40 %.

Por periodo:

```text
generación_bruta = supuesto_diario × horas / 24
generación_reducida = generación_bruta × (1 − recorte)
vertido = máximo(0, saldo_inicial + generación_reducida − capacidad)
disponible = saldo_inicial + generación_reducida − vertido
saldo_final = disponible − consumo
```

La crisis se aplica **sólo a generación**, una vez. No recorta inventario inicial, objetivos, capacidad o reserva. La generación se acredita al inicio; el modelo supone almacenamiento antes de atender consumos. El vertido es generación no almacenada y se hace visible; no se permite que el inventario almacenado exceda la capacidad. No se simula consumo solar directo, potencia instantánea, horas de oscuridad, eficiencia de baterías ni pérdidas de conversión. La pérdida por recorte y el vertido se muestran separados.

Se exige `0 ≤ reserva ≤ inicial ≤ capacidad`, entradas finitas no negativas, asignaciones no negativas dentro del objetivo y suma de hijos no superior al límite padre. La reserva se protege cada periodo. El consumo se cuenta en la raíz una sola vez; los hijos distribuyen ese presupuesto. El saldo final de un periodo es exactamente el inicial del siguiente. Nunca se usa energía futura para salvar un déficit previo ni se normaliza silenciosamente una asignación inválida.

Los mínimos opcionales son declaraciones del usuario en kWh/24 h con procedencia/contexto; deben ser no negativos y no superar el objetivo. Cubrirlos sólo verifica aritmética de supuestos, no supervivencia, productividad, agua, nutrición, temperatura o etapa de un cultivo. Sin todos los mínimos se informa **Factibilidad agrícola no evaluada**, incluso si una asignación nula es energéticamente factible.

## Persistencia y API

Migración Alembic aditiva `0003_decisions`, posterior a `0002_serial`; no usa `create_all`. Crea `decision_runs` y `decision_reviews`, sin claves a telemetría, zonas o dispositivos. Una instalación nueva no contiene escenarios precargados. Sólo una ejecución solicitada en Decisiones registra supuestos; no se insertan fixtures en la base operativa.

| Ruta local | Función |
|---|---|
| `POST /api/decisions/runs` | Valida, compara y conserva parámetros y resultado, incluso infactible |
| `GET /api/decisions/runs?limit=30&offset=0` | Historial paginado |
| `GET /api/decisions/runs/{id}` | Parámetros, resultado y revisiones |
| `POST /api/decisions/runs/{id}/reviews` | Aprobación/rechazo con responsable y motivo obligatorios |

Fuente fija `hypothetical`, unidad `kWh`, procedencia de supuestos, identificadores UUID, fechas UTC conscientes de zona, instantánea de parámetros/resultados y huellas SHA-256 del núcleo/versión e instantánea. No hay endpoints de edición o borrado. Las restricciones SQLite aseguran relación con la comparación, una revisión por alternativa y una aprobación por comparación, incluso ante peticiones concurrentes. Una revisión de alternativa inexistente devuelve 422; conflictos definitivos, 409. Aprobar guarda un registro: no cambia la operación física.

La API continúa limitada a `127.0.0.1`. Los responsables son declarados manualmente: no hay autenticación de identidad, firma digital ni protección contra un administrador que edite SQLite. Las huellas son trazabilidad de versiones y contenido, no una garantía criptográfica contra manipulación por el dueño de los archivos. El esquema no presupone módulos futuros de semillas, hidroponía, biomasa o alimentos.

## Verificación

Archivos de esta entrega:

| Área | Archivos |
|---|---|
| Adaptación y API | `backend/app/itzamna_adapter.py`, `decision_schemas.py`, `decision_models.py`, `decision_routes.py`, `main.py` |
| Migraciones | `backend/migrations/versions/0003_decision_governance.py`, `backend/migrations/env.py` |
| Dependencia requerida | `backend/requirements.txt`, `backend/constraints-lock.txt` (NumPy 2.2.6) |
| Interfaz existente | `frontend/src/pages/Decisions.tsx`, `frontend/src/decisionApi.ts`, `frontend/src/styles.css` |
| Pruebas | `backend/tests/test_decisions.py`, `backend/tests/test_phase_one.py` (contrato de rutas y revisión Alembic) |
| Alcance y uso | `AGENTS.md`, `README.md`, `docs/FASE_2B_ITZAMNA.md` |

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check.ps1
```

El script ejecuta pytest en bases temporales bajo `.run/checks/` y luego `npm run build`. Las pruebas focalizadas están en `backend/tests/test_decisions.py`: balance temporal, recorte único, escala de horas, reservas, capacidad/vertido, jerarquía, entradas inválidas, mínimos ausentes/declarados, escenarios infactibles, cantidad real de alternativas, determinismo, Pareto, revisión humana, persistencia, trazabilidad, separación física y actualización desde Fase 2A.

Resultados verificados el 19/10/2026, Windows, CPython 3.12.14 y Node.js 24.22.0:

- `scripts/check.ps1`: **89 pruebas pasaron** (14,13 s) y **build TypeScript/Vite correcto**. Avisos sin fallos: deprecación de AnyIO en Starlette y permiso de renombrado de caché pytest; bases temporales y pruebas completadas.
- Núcleo de referencia, sin modificarlo: **17 pruebas pasaron** (1,08 s) en `test_pareto_regression_2026.py`, `test_simulation.py`, `test_dependencies.py` y `test_fitness_consistency_2026.py`. Se usaron `PYTHONDONTWRITEBYTECODE=1`, `PYTHONPATH=referencias/itzamna_motor` y caché/temporales propios bajo `.run/phase2b/`.
- Verificación SHA-256 antes/después: **31 archivos de referencia, cero cambios**, sin directorios `__pycache__` añadidos.
- Navegador en `127.0.0.1`, API conectada a `.run/phase2b/browser.db`: ejemplo de 40 % y cinco periodos produjo tres alternativas. La primera consumió 33,333 kWh en total, con 2 kWh de vertido y saldo final 2,667 kWh. Se comprobó el paso de generación bruta 10 a 6 kWh y el arrastre de saldos.
- Aprobación y rechazo manuales de prueba persistieron tras recargar y reabrir el historial. Los responsables registrados son de prueba, exclusivamente en la base temporal.
- Mínimos hipotéticos iguales a objetivos produjeron cero alternativas y cero botones de aprobación. La interfaz distinguió la ausencia de factibilidad energética de la ausencia de validación agrícola.
- Evidencia visual local: `output/qa/fase2b-decisiones.png` (no se añade a Git). No se arrancó el lector serial ni se modificó la base operativa durante estas comprobaciones.

Los números de resultados anteriores pertenecen únicamente al ejemplo de prueba; no son datos físicos del domo. La ejecución operativa continúa sin sensores ni consumo medido.

## Mejora visual · mapa jerárquico de sólo lectura

El 19/10/2026 se añadió el mapa en Decisiones, conservando tablas, balances, aprobación/rechazo e historial. La referencia visual es `referencias/itzamna_visual/PreziViewer.tsx`, de **Itzamná**: se adaptaron el árbol descendente, las curvas de conexión, el enfoque de nodos, la cámara y el historial de navegación. No se copia la aplicación Next.js ni se adapta la edición de `PriorityDial.tsx`. Ambas referencias se conservan intactas. React, SVG, CSS y Lucide existentes cubren la visualización: **ninguna dependencia nueva**.

La raíz «Domo agrícola» muestra los servicios guardados por la API; el ejemplo inicial tiene Circulación, Iluminación y Ambiente. El selector del mapa cambia exclusivamente la alternativa visualizada. Los nodos se obtienen de `run.parameters` y de la alternativa factible seleccionada en `run.result.alternatives`; no leen el formulario que aún se está editando, sensores, valores precargados ni otro plan. Las asignaciones y déficits se presentan tal como los devolvió la API. Únicamente se escala el objetivo guardado de kWh/24 h a horas del periodo, como en el balance existente.

En la raíz, objetivo y déficit son sumas de los servicios, y la asignación es el consumo por periodo del resultado. El límite del módulo se presenta por separado. La prioridad de la raíz no está declarada en el contrato público y se muestra «No declarada en la API». Una ausencia de valor aparece como «Sin datos»; no se transforma en cero. Sin alternativa factible no se construye un árbol de ejemplo.

El panel presenta objetivo, asignación, déficit, prioridad y unidad. Los anillos de los servicios representan prioridades guardadas; los clics sólo seleccionan y enfocan. La selección utiliza dorado y los demás nodos tonos neutros/violeta; **ningún color significa seguridad ni viabilidad agrícola**. Se conservan las etiquetas «Escenario hipotético» y el estado de factibilidad agrícola de la API.

Controles: selector de alternativa, acercar/alejar, encajar, atrás y volver a la raíz. Se puede desplazar arrastrando el lienzo. Con teclado: Tab recorre controles y llega al árbol; las flechas navegan entre raíz, hijos y hermanos; Inicio vuelve a la raíz, Fin llega al último servicio y Enter/espacio seleccionan. En el lienzo enfocado, las flechas desplazan y +/− cambian el zoom; Escape restablece la raíz. Los nodos tienen semántica de árbol, nivel, selección y foco visible; el panel anuncia la selección. Los títulos largos se limitan a dos líneas en el árbol y se muestran completos en el panel. En ancho reducido, los servicios se distribuyen en columna y el detalle pasa debajo del mapa.

Archivos de esta mejora:

- `frontend/src/components/DecisionMap.tsx`: cámara, controles y panel de inspección.
- `frontend/src/components/decisionMapModel.ts`: proyección inmutable de la respuesta API, distribución y navegación.
- `frontend/src/pages/Decisions.tsx`: inserción del mapa, sin alterar el flujo anterior.
- `frontend/src/styles.css`: estilos acotados y adaptación a pantallas pequeñas.
- `frontend/tests/decision-map.test.mjs`: pruebas focalizadas en memoria.
- `frontend/package.json`: comando `npm run test:map`, usando Node.js 24 existente.
- `docs/FASE_2B_ITZAMNA.md`: atribución, uso y verificación de la mejora.

Verificación final:

- `npm.cmd run test:map`, desde `frontend/`: **8 pruebas pasaron**. Comprueban procedencia por alternativa, campos y unidad, escala de objetivo, ausencia de valores, alternativas infactibles, inmutabilidad, navegación y separación de hasta cuatro servicios en escritorio/móvil.
- `scripts/check.ps1`: **89 pruebas del backend pasaron** (8,23 s); aviso de deprecación existente en Starlette/AnyIO, sin fallos. Usa bases temporales propias.
- `npm.cmd run build`, después de los últimos ajustes CSS: **TypeScript y Vite correctos** (14,90 s de build Vite).
- Navegador con la API local existente: se abrió una comparación ya guardada (ocho periodos, recorte 40 %) y se contrastaron los datos del mapa con las tablas. Se verificaron cambio de alternativa, selección de hijos mediante flechas, prioridad y déficit en el panel, zoom, atrás y regreso a la raíz. Las seis tablas de las tres alternativas conservaron su contenido; cero errores de consola.
- Vista móvil a **390 × 844 px**: sin desbordamiento horizontal del documento ni superposición entre los cuatro nodos. Se restauró el tamaño normal del navegador al terminar.
- **53 archivos protegidos de backend, migraciones, firmware y referencias sin cambios**, comprobados por SHA-256. La mejora no modifica el algoritmo, contratos de API, esquema SQLite, firmware ni COM6. La comprobación visual sólo leyó comparaciones existentes y no registró decisiones nuevas; no se detuvieron los servidores que ya estaban en ejecución.
- Captura del mapa con Alternativa 1 seleccionada: `output/qa/fase2b-mapa.jpg`, excluida de Git.
