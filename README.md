# LEKIL KUXLEJAL MARTE · DOMO VITAL

Sistema local de observación y registro para el módulo agrícola. **Entrega actual: Fase 2A**, integración serial real del ESP32 clásico por COM6. Configuración muestra identificación, heartbeat, uptime y firmware desde la API. Protocolo, comandos y resultados en [docs/FASE_2A_SERIAL.md](docs/FASE_2A_SERIAL.md).

Una instalación nueva comienza vacía. El lector identifica la placa mediante mensajes físicos válidos; esta entrega conserva un dispositivo real y sus diagnósticos. No hay sensores ni generador de telemetría: las mediciones ambientales siguen vacías. Estar conectado requiere un heartbeat de no más de 10 segundos. El control físico está deshabilitado.

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

Terminal 3, lector serial, después del backend y de cerrar cualquier monitor que use COM6:

```powershell
Set-Location 'C:\Users\mende\Documents\lekil-kuxlejal'
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-serial.ps1 -Port COM6
```

Orden: backend, frontend, lector. Abre [Configuración](http://127.0.0.1:5173/configuracion). La API está en [salud](http://127.0.0.1:8000/api/health) y los contratos en [OpenAPI](http://127.0.0.1:8000/docs). Detén cada proceso con `Ctrl+C`, primero el lector. Los servidores escuchan en `127.0.0.1`. La interfaz interna serial requiere token local; las rutas públicas todavía no incluyen usuarios ni roles.

## Qué se puede hacer

- Consultar salud, zonas, dispositivos y telemetría real vacía.
- Registrar zonas y placas ESP32; la identidad física se registra automáticamente por serial y persiste tras reiniciar la API.
- Consultar conectado, desconectado o comunicación caducada, última comunicación, chip, firmware y uptime del último mensaje.
- Navegar por Inicio, Domo, Recursos, Decisiones y Alertas. Los módulos posteriores se identifican como pendientes.
- Reintentar una consulta cuando la API falla. La interfaz muestra el fallo en lugar de presentar valores de demostración.

SQLite se crea en `backend/data/lekil.db`. Al iniciar, Alembic aplica las migraciones pendientes sin introducir registros. La ubicación se puede cambiar con `DATABASE_URL`; consulta `docs/API.md` y `docs/ARQUITECTURA.md`. No borres la base para actualizar: utiliza migraciones y conserva copias de seguridad.

Vite envía `/api` a `http://127.0.0.1:8000` en desarrollo. El bundle construido necesita el mismo encaminamiento si se sirve mediante otro servidor; `vite preview` está preparado para la verificación local. Un origen alternativo se configura antes de compilar con `frontend/.env.example`. Ningún servicio externo es necesario para operar.

## Verificación

```powershell
Set-Location 'C:\Users\mende\Documents\lekil-kuxlejal'
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check.ps1
```

El script crea temporales aislados bajo `.run/checks/`, ejecuta las pruebas y compila el frontend. Evita reutilizar carpetas de pytest creadas por otra cuenta de Windows. Para compilar solamente la interfaz:

```powershell
Set-Location frontend
npm.cmd run build
```

Las pruebas usan bases temporales. Los resultados y las limitaciones observadas están en `docs/VERIFICACION_FASE_1.md`.

## Estructura y documentación

```text
frontend/             React, TypeScript, Vite, Tailwind y navegación
backend/app/          API, contratos tipados y persistencia SQLModel
backend/serial_reader/ Lector independiente de sólo lectura -> HTTP local
backend/migrations/   Revisiones Alembic
backend/tests/        Pruebas aisladas de la base operativa
firmware/             ESP32 clásico: hello y heartbeat, sin actuadores
hardware/             Identificación de instrumentación pendiente
docs/referencias/     Copias locales de las fuentes recibidas
docs/                 Plan, arquitectura, requisitos, datos y roadmap
scripts/              Instalación, inicio y comprobación en Windows
tests/                Guía de organización de verificaciones
```

Empieza por `docs/PLAN_TECNICO.md` y `docs/ROADMAP.md`. Los documentos fuente y las bases operativas se excluyen de Git para evitar publicación accidental de material privado. Las copias locales de las referencias están disponibles en `docs/referencias/`; no se recibieron otros documentos de Mars Challenge.

## Límites de la entrega y siguiente fase

Están implementados identificación serial, heartbeat, reconexión y vigencia de comunicación. Continúan pendientes sensores ambientales, calibración, alertas agronómicas, recursos medidos, gobernanza, escenarios, cultivos, alimentos y cultura. No se dibujan curvas ficticias ni se habilitan modos asistido o automático.

La Fase 2A termina con diagnóstico de la placa sin sensores. No se iniciará Fase 2B sin nueva autorización del usuario.
