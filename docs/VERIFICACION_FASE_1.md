# Verificación de la Fase 1

Fecha: 15 de octubre de 2026, America/Mexico_City. Alcance completado: infraestructura local, configuración persistente, consulta real vacía e Inicio. No se inició la Fase 2.

## Entorno comprobado

Windows, Windows PowerShell 5.1, Node.js 24.22.0, npm 11.19.1 y CPython 3.12.14 del runtime de Codex. Python 3.13 es la versión objetivo de la especificación, pero no se encontró en PATH ni en las ubicaciones consultadas y **no se verificó con esa versión**. El entorno `.venv` usa 3.12.14.

Se instalaron los paquetes Python y Node; las versiones están recogidas en `backend/constraints-lock.txt` y `frontend/package-lock.json`. `pip check` devolvió «No broken requirements found». La instalación inicial requiere internet; no se incorporan fuentes, llamadas de IA, telemetría externa ni servicios de nube al funcionamiento principal.

## Comprobaciones ejecutadas

| Comprobación | Resultado |
| --- | --- |
| `scripts/check.ps1` ejecutado con Windows PowerShell 5.1 | 30 pruebas aprobadas y compilación terminada, código 0 |
| API y migración inicial | Arranque real con `scripts/start-backend.ps1`, SQLite disponible y revisión `0001_observation` |
| Alembic CLI, base temporal | `upgrade head`, `check` sin diferencias y `current` en head |
| Persistencia automatizada | Misma configuración recuperada por una nueva instancia de aplicación |
| Integridad referencial | Claves foráneas activas; rechazo de huérfanos y borrado de entidades referenciadas |
| Validación | Rechazo de nulos obligatorios, textos vacíos, longitudes inválidas, tipos incorrectos y campos controlados por servidor |
| Telemetría | Procedencia, unidad, calidad y UTC conservados en fixtures temporales; rechazo de valores no finitos, fecha sin zona y fuente hipotética |
| Estados y superficies | Health 503 ante fallo de base; sin ingesta, control físico, edición ni borrado por API |
| Frontend | TypeScript y Vite 6.4.4: 1603 módulos; bundle JS 316.98 kB, CSS 33.68 kB |
| Conexión desde Vite | HTML 200 y `/api/health` 200 a través del proxy hacia FastAPI |
| Formularios en navegador | Alta de una zona y un dispositivo en `tmp/browser-qa.db`, exclusivamente temporal; opcionales desconocidos nulos |
| Reinicio y recuperación | Mismos identificadores de configuración tras reiniciar el proceso; consulta recuperada desde Inicio |
| Caída de API | Al detener el backend y actualizar, errores visibles, «API sin verificar», sin conservar afirmaciones de disponibilidad |
| Navegación | Inicio, Domo, Recursos, Decisiones, Alertas y Configuración accesibles; módulos futuros explícitos |
| Teclado | Nombre recibe foco al abrir el diálogo; Escape cierra y devuelve foco a «Registrar zona» |
| Diseño adaptable | Navegador a 390×844 y 1440×1000; anchos de documento 375 y 1425 px, respectivamente, sin desbordamiento horizontal; menú móvil/lateral adecuados |

La suite se encuentra en `backend/tests/test_phase_one.py`; sus datos sintéticos se restringen a SQLite temporal. Antes de esta entrega no había código ni pruebas existentes en la carpeta inicial.

## Base operativa entregada

Se inició también la API contra **`backend/data/lekil.db`**, separada de las pruebas. Comprobación de sólo lectura posterior al QA:

```text
zones: 0
devices: 0
measurements: 0
PRAGMA integrity_check: ok
alembic_version: 0001_observation
```

La consulta real por el proxy devolvió `items: []`, `total: 0`, `source: real` y fecha UTC. Los cuatro indicadores muestran «Sin datos». Ningún registro de prueba se trasladó a la base operativa. No se enviaron comandos físicos.

La captura local de Inicio con esta base vacía está en `output/qa/inicio-escritorio.jpg`, excluida de Git. Las referencias recibidas permanecen en `docs/referencias/`, también excluidas de publicación automática.

## Problemas encontrados y correcciones

- El sandbox bloqueó descargas de pip/npm y el acceso de esbuild a directorios de configuración. Se solicitaron los permisos de ejecución correspondientes y las instalaciones, compilación y vista local funcionaron con la cuenta del usuario.
- Windows PowerShell 5.1 eliminaba comillas internas en las comprobaciones de versiones. Se sustituyeron por expresiones sin comillas internas y se ejecutaron correctamente con esa versión de PowerShell.
- La primera comprobación conjunta encontró permisos incompatibles en los temporales globales/caché de pytest creados por otra cuenta. `check.ps1` ahora crea una ruta nueva y verificada bajo `.run/checks/` para cada ejecución; la repetición aprobó las 30 pruebas y el build. No se modificaron permisos de carpetas temporales del usuario.
- Se alinearon los límites de los formularios: nombres 80 caracteres y puerto 128.
- El diálogo perdía el foco al cerrarse. Se conserva el botón de apertura, se libera el estado modal y se restaura el foco después del desmontaje; Escape fue comprobado en navegador.
- Git se inicializó localmente. Se corrigió la propiedad de la carpeta `.git` creada por el sandbox para que la cuenta del usuario pueda operar normalmente, sin añadir excepciones globales de seguridad. No hay remoto ni publicación.

## Limitaciones pendientes

- Una advertencia de depreciación de Starlette/AnyIO aparece en las pruebas; no causa fallos. No se ocultó.
- No se verificó Python 3.13, un navegador distinto del integrado de Codex, ni un dispositivo físico.
- No hay autenticación: los scripts escuchan sólo en `127.0.0.1`.
- USB serial, sensores, calibración, caducidad, alertas, balances, decisiones, escenarios, cultivos, biomasa, alimentos y cultura continúan pendientes según el roadmap.
- No se aportaron la rúbrica independiente de Mars Challenge ni otros archivos externos citados por el expediente; están inventariados como ausentes.

## Uso y siguiente entrega

Los comandos exactos para instalar e iniciar en dos terminales están en el README raíz. Los servidores utilizados para QA se detienen al terminar la comprobación; la captura permite revisar la entrega sin mantener procesos de pruebas abiertos.

La Fase 2 requiere una nueva instrucción: identificar placa/sensores, definir contrato serial, asociar instrumentación, validar unidades y calidad, implementar ingesta, heartbeat, vigencia y alertas basadas en evidencia. No comenzar automatización física por iniciativa propia.
