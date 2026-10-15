# LEKIL KUXLEJAL MARTE · DOMO VITAL

Sistema local de observación y registro para el módulo agrícola. **Entrega actual: Fase 1**, conforme a la especificación maestra. La pantalla Inicio toma como referencia los mockups DOMO VITAL y consulta una API real; SQLite conserva únicamente registros introducidos de forma explícita.

La base comienza sin zonas, dispositivos ni mediciones. No hay generador de telemetría. Registrar una placa no significa que esté conectada: los indicadores permanecen en «Sin datos» / «Sensor no configurado» y la energía en «Consumo no medido». El control físico está deshabilitado.

## Inicio en Windows / PowerShell

Requisitos: Node.js 24 LTS y Python 3.13 como versión objetivo. También se admite Python 3.12; esta entrega se verifica con el intérprete realmente disponible (ver `docs/VERIFICACION_FASE_1.md`). La primera instalación necesita internet; la operación posterior es local. No se requiere activar el entorno virtual.

Desde la carpeta del proyecto:

```powershell
Set-Location 'C:\Users\mende\Documents\lekil-kuxlejal'
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

Si Python no está en el PATH, proporciona su ejecutable. En el equipo de esta entrega está disponible el intérprete incluido con Codex:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1 -PythonExe 'C:\Users\mende\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
```

El script reutiliza `.venv` si existe. Para verificar con otro intérprete, crea un entorno independiente y conserva el existente hasta finalizar la comprobación.

`backend/constraints-lock.txt` fija las versiones transitivas verificadas en Windows; `frontend/package-lock.json` fija las dependencias de Node. Los scripts usan esas versiones para instalaciones reproducibles.

Terminal 1, API:

```powershell
Set-Location 'C:\Users\mende\Documents\lekil-kuxlejal'
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-backend.ps1
```

Terminal 2, interfaz:

```powershell
Set-Location 'C:\Users\mende\Documents\lekil-kuxlejal'
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-frontend.ps1
```

Abre [DOMO VITAL](http://127.0.0.1:5173). La API está en [salud](http://127.0.0.1:8000/api/health) y los contratos interactivos en [OpenAPI](http://127.0.0.1:8000/docs). Detén cada servidor con `Ctrl+C`. Ambos escuchan en `127.0.0.1`; esta fase no incluye autenticación ni exposición a la red.

## Qué se puede hacer

- Consultar salud, zonas, dispositivos y telemetría real vacía.
- Registrar zonas y placas ESP32-S3 desde Configuración; los cambios persisten tras reiniciar la API.
- Navegar por Inicio, Domo, Recursos, Decisiones y Alertas. Los módulos posteriores se identifican como pendientes.
- Reintentar una consulta cuando la API falla. La interfaz muestra el fallo en lugar de presentar valores de demostración.

SQLite se crea en `backend/data/lekil.db`. Al iniciar, Alembic aplica las migraciones pendientes sin introducir registros. La ubicación se puede cambiar con `DATABASE_URL`; consulta `docs/API.md` y `docs/ARQUITECTURA.md`. No borres la base para actualizar: utiliza migraciones y conserva copias de seguridad.

Vite envía `/api` a `http://127.0.0.1:8000` en desarrollo. El bundle construido necesita el mismo encaminamiento si se sirve mediante otro servidor; `vite preview` está preparado para la verificación local. Un origen alternativo se configura antes de compilar con `frontend/.env.example`. Ningún servicio externo es necesario para operar.

## Verificación

```powershell
Set-Location 'C:\Users\mende\Documents\lekil-kuxlejal'
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check.ps1
```

El script crea temporales aislados bajo `.run/checks/`, ejecuta las 30 pruebas y compila el frontend. Evita reutilizar carpetas de pytest creadas por otra cuenta de Windows. Para compilar solamente la interfaz:

```powershell
Set-Location frontend
npm.cmd run build
```

Las pruebas usan bases temporales. Los resultados y las limitaciones observadas están en `docs/VERIFICACION_FASE_1.md`.

## Estructura y documentación

```text
frontend/             React, TypeScript, Vite, Tailwind y navegación
backend/app/          API, contratos tipados y persistencia SQLModel
backend/migrations/   Revisiones Alembic
backend/tests/        Pruebas aisladas de la base operativa
firmware/             Alcance futuro ESP32-S3; sin código de control
hardware/             Identificación de instrumentación pendiente
docs/referencias/     Copias locales de las fuentes recibidas
docs/                 Plan, arquitectura, requisitos, datos y roadmap
scripts/              Instalación, inicio y comprobación en Windows
tests/                Guía de organización de verificaciones
```

Empieza por `docs/PLAN_TECNICO.md` y `docs/ROADMAP.md`. Los documentos fuente y las bases operativas se excluyen de Git para evitar publicación accidental de material privado. Las copias locales de las referencias están disponibles en `docs/referencias/`; no se recibieron otros documentos de Mars Challenge.

## Límites de la entrega y siguiente fase

No están implementadas la comunicación USB, ingestión de sensores, calibración, caducidad, motor de alertas, recursos medidos, gobernanza, escenarios, cultivo, alimentos o memoria biocultural. Recharts está disponible como dependencia para futuras series reales; no se dibujan curvas ficticias. Los modos asistido y automático no están habilitados.

La Fase 2 requiere identificar placa y sensores, acordar el contrato serial y las unidades, validar/calibrar el hardware e implementar ingesta, heartbeat, calidad, vigencia y alertas comprobables. Se iniciará únicamente por una nueva instrucción del usuario.
