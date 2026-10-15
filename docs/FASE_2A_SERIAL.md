# Fase 2A — integración serial real

Entrega: 15/10/2026, America/Mexico_City. Exclusivamente observación de ESP32 clásico ESP32-D0WD-V3, CH340, COM6/115200, sin sensores. No se reanalizó el expediente completo ni se utilizaron agentes paralelos. No se continúa a Fase 2B.

## Archivos

- Firmware: `firmware/src/main.cpp`, README; configuración existente `platformio.ini` conservada (`esp32dev`, Arduino, 115200) y `.gitignore` de PlatformIO incorporados.
- Backend: `app/serial_protocol.py`, `device_service.py`, `models.py`, `schemas.py`, `main.py`, `database.py`; `migrations/env.py`, migración `0002_serial_diagnostics.py`.
- Lector: `backend/serial_reader/`; `scripts/start-serial.ps1`.
- Dependencia nueva: únicamente `pyserial==3.5`, añadida a requirements y constraints.
- Frontend: `api.ts`, `state.tsx`, tarjeta `components/DeviceCard.tsx` dentro de Configuración y estilos acotados; referencias de tipo/etapa actualizadas en App e Inicio. Sin páginas nuevas ni rediseño.
- Pruebas: `test_serial.py`; expectativas de revisión, tipo y rutas actualizadas en `test_phase_one.py`.
- AGENTS.md, README raíz y este informe. Los archivos locales de VS Code existentes se preservan fuera de los commits; la documentación histórica de Fase 1 se conserva.

## Protocolo y lector

JSON Lines UTF-8, terminado en `\n`, máximo 2048 bytes. Todos los mensajes contienen `protocol_version=1`, `type=hello|heartbeat`, `device_id` estable (`esp32-` + 12 hex de eFuse), `chip_model` obtenido del chip, `firmware_version`, `boot_id` (16 hex), `uptime_ms` y `sequence`. Hello usa secuencia 0; heartbeat secuencia positiva incremental cada 3000 ms. Uptime es entero real de 64 bits, independiente del wrap de millis. La aleatoriedad sólo identifica arranques; no genera lecturas. El ID usa un orden fijo de bytes de eFuse, no la presentación textual de una MAC.

Cada heartbeat permite identificar la placa aunque el lector haya perdido el hello. No se declaran pines, sensores ni actuadores. Las líneas no JSON del ROM de arranque se rechazan.

Proceso independiente: `python -m serial_reader.service`. Nunca importa SQLite ni modelos de persistencia. Puerto configurable por `--port`/`SERIAL_PORT`, predeterminado COM6; siempre 115200. URL por `--backend-url`/`SERIAL_BACKEND_URL`, sólo HTTP loopback sin redirecciones ni proxies. DTR/RTS inactivos al abrir reducen reinicios del adaptador; no se envían bytes de comando. FastAPI no abre COM6, tampoco al recargar.

Valida UTF-8, JSON, claves repetidas, versión, tipos, límites y secuencia. Descarta líneas incompletas tras 2 s o mayores de 2048 bytes, recuperando el siguiente salto. Reintenta puerto en 1, 2, 4, 8 y hasta 15 s. Registra errores de protocolo con límite de frecuencia.

Caché de 256 claves dispositivo/arranque/secuencia; cola de entrega de 128 eventos. API no disponible: reintento cada 2 s con el mismo ID y recepción UTC. Cola llena: descarta el evento más antiguo y registra error. Cola en memoria, no durable al matar el proceso; no afirma persistencia sin confirmación. Entregar tarde no rejuvenece una comunicación antigua.

## API y estado persistido

`POST /api/internal/serial-events`: sólo loopback, sin Origin de navegador y con `X-Serial-Token`. El backend crea `backend/data/serial.token`; el lector sólo lee el archivo. No llega al frontend ni a Git. Opcional: `SERIAL_INGEST_TOKEN` igual en ambos procesos, mínimo 24 caracteres. Si se configura otra base, el token queda junto a ella; indicar al lector `-TokenFile`.

Sobre: `event_id` (32 hex), `port`, `baud_rate=115200`, `received_at` ISO 8601 con zona, `kind`, `message` o `detail`. Tipos: message, disconnected, protocol_error, reader_stopped. El backend añade fecha de persistencia UTC y rechaza recepciones futuras más de 5 s. No acepta variables ambientales en mensajes.

`GET /api/devices` añade hardware_id, boot_id, firmware, secuencia, uptime, último heartbeat y vigencia. Cada consulta calcula status:

| Estado | Evidencia |
| --- | --- |
| not_configured | Registro manual sin identidad física |
| connected | Heartbeat del arranque actual recibido hace 0-10 s; sin desconexión posterior |
| stale | Sin heartbeat vigente; hello solo aparece esperando heartbeat |
| disconnected | Evento de puerto desconectado o lector finalizado más reciente |

`GET /api/devices/{id}/events?limit=50` consulta diagnósticos (máximo 200). La tarjeta se actualiza cada 3 s; muestra el uptime del último mensaje, sin extrapolarlo. Temperatura y humedad permanecen «Sin datos».

Migración `0002_serial`: amplía devices para ESP32 clásico y conserva S3 anteriores; añade identidad única y metadatos. Device_events está separado de measurements, con unicidad por evento y dispositivo/arranque/secuencia. Puede adoptar un único registro manual en el mismo puerto; luego usa identidad eFuse para evitar duplicados. Un duplicado no renueva conexión. Rechaza secuencias antiguas, uptime regresivo y arranques retirados; desconexiones retrasadas no pisan heartbeats recientes.

Para reconstruir restricciones SQLite se utiliza una transacción física antes de admitir peticiones, FK desactivadas sólo en esa conexión de mantenimiento, comprobación `foreign_key_check` antes de confirmar y restauración de FK. Se verificó la conservación de historial anterior en base temporal. El procedimiento se contrastó con la [documentación oficial de Alembic](https://alembic.sqlalchemy.org/en/latest/batch.html#dealing-with-referencing-foreign-keys).

## PowerShell y prueba de COM6

Desde `C:\Users\mende\Documents\lekil-kuxlejal`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\backend\requirements-dev.txt -c .\backend\constraints-lock.txt
# Compilar; el firmware de esta entrega ya fue cargado físicamente.
& "$env:USERPROFILE\.platformio\penv\Scripts\platformio.exe" run --project-dir .\firmware
# Cerrar monitor y lector antes de cargar.
& "$env:USERPROFILE\.platformio\penv\Scripts\platformio.exe" run --project-dir .\firmware --target upload --upload-port COM6
```

Tres terminales distintas, en este orden:

```powershell
# Terminal 1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-backend.ps1
# Terminal 2
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-frontend.ps1
# Terminal 3
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-serial.ps1 -Port COM6
```

Abrir `http://127.0.0.1:5173/configuracion`. Debe aparecer ESP32 principal conectado, chip, COM6, firmware 0.2.0 y uptime cambiante; temperatura/humedad sin datos. No mantener simultáneamente monitor de PlatformIO y lector. Para salir, Ctrl+C primero en lector, después frontend y backend. Detención abrupta: esperar más de 10 s para observar caducidad; cierre controlado: desconectado. Reabrir lector recupera comunicación conservando identidad.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check.ps1
Invoke-RestMethod http://127.0.0.1:8000/api/devices | ConvertTo-Json -Depth 5
Invoke-RestMethod http://127.0.0.1:8000/api/telemetry | ConvertTo-Json -Depth 5
```

## Resultados ejecutados

- **57 pruebas aprobadas**: 30 regresiones y nuevos casos hello, heartbeat, JSON inválido/incompleto, límites, duplicados en lector/backend, reinicio, desconexión, caducidad, reconexión, persistencia, migración con historial, ausencia de sensores y acceso interno. Datos sintéticos y puertos falsos exclusivamente en tests y bases temporales.
- TypeScript/build Vite: correcto, 1604 módulos, JS 318.12 kB y CSS 34.13 kB. Sin compilaciones repetidas sin cambios.
- Firmware compilado: RAM 21564/327680 (6.6%), flash 269569/1310720 (20.6%). **Carga física COM6 exitosa**, hashes verificados; esptool confirmó ESP32-D0WD-V3 revisión v3.1, 240 MHz.
- `start-serial.ps1` recibió y persistió **heartbeats físicos** cada ~3 s. API y navegador mostraron ESP32 principal, ESP32-D0WD-V3, COM6, firmware 0.2.0 y estado conectado. ID estable: esp32-3816ffffc9ec.
- Se observó caducidad real al detener abruptamente el lector. Se reinició el backend y reabrió COM6 sin duplicar el dispositivo; ID de base conservado `95717915-c84c-4c03-a5ac-190c8ae818c6`. Una última lectura real de 8 s con parada controlada registró reader_stopped, cerró el puerto y mostró desconectado.
- Base operativa: **1 dispositivo real, 47 diagnósticos reales, 0 zonas, 0 mediciones ambientales**. `integrity_check=ok`, `foreign_key_check=[]`.
- Evidencia: `output/qa/esp32-com6-conectado.jpg`, fuera de Git. Los procesos de QA se detienen al finalizar; iniciar los tres procesos para volver a conectar.

## Errores y pendientes

Se corrigió la restricción ESP32-S3 por migración. El sandbox bloqueó pip, PlatformIO y sockets internos de asyncio/TestClient; se solicitaron permisos y se completaron las comprobaciones con la cuenta del usuario. Una invocación manual inicial de pytest omitió crear el padre del temporal; se corrigió la invocación (check.ps1 ya lo crea).

Advertencias no fatales: depreciación Starlette/AnyIO y permisos al renombrar caché de pytest; 57 pruebas y build terminaron con código 0. La primera navegación del navegador agotó su espera, pero la misma pestaña cargó y permitió el QA.

Se probó detención/reapertura física del lector; no se retiró manualmente el cable USB. Puerto retirado/reconexión se cubrió con puertos falsos en tests. No hay sensores, control físico ni alertas agronómicas. Python efectivo 3.12.14; 3.13 sin verificar. No se inicia Fase 2B.
