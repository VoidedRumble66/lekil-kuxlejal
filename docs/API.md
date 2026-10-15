# API local de Fase 1

Base: `http://127.0.0.1:8000/api`. OpenAPI: `http://127.0.0.1:8000/openapi.json`; explorador: `http://127.0.0.1:8000/docs`.

JSON con nombres `snake_case`. Identificadores UUID. Fechas ISO 8601 UTC con `Z` o desplazamiento explícito. No hay autenticación en esta fase: ejecutar en la interfaz local. No hay rutas de ingesta, escenarios ni comandos físicos.

## Contratos implementados

| Método y ruta | Éxito | Resultado |
| --- | --- | --- |
| `GET /api/health` | 200 | Estado de acceso a SQLite, modo y control |
| `GET /api/zones` | 200 | Lista de zonas; `[]` si no se registraron |
| `POST /api/zones` | 201 | Nueva zona de configuración |
| `GET /api/devices` | 200 | Lista de dispositivos; `[]` si no se registraron |
| `POST /api/devices` | 201 | Nuevo ESP32-S3, `not_configured` |
| `GET /api/telemetry` | 200 | Página de mediciones reales; vacía inicialmente |

### Salud

```json
{
  "status": "ok",
  "database": "connected",
  "mode": "observation",
  "control_enabled": false,
  "timestamp": "<fecha ISO 8601 UTC del servidor>"
}
```

`timestamp` se genera al consultar. Si falla el acceso a la base, health devuelve 503 con `status: "error"` y `database: "unavailable"`, manteniendo observación y control deshabilitado. Este endpoint no acredita conexión con hardware ni calidad agronómica.

### Zonas

Cuerpo de alta, ejemplo de configuración introducida deliberadamente por una persona:

```json
{
  "name": "Banco de semillas",
  "purpose": "Custodia y registro de lotes",
  "description": null
}
```

`name`: texto 1-80; `purpose`: texto 1-160; `description`: nulo u omitido, o texto 1-2000. Se recortan espacios de extremos. Respuesta: esos campos más `id` y `created_at`, asignados por servidor. La lista se ordena por creación e identificador. La API no crea automáticamente sectores físicos.

### Dispositivos

```json
{
  "name": "Controlador de banco",
  "model": null,
  "serial_port": null
}
```

`name`: texto 1-80; `model`: opcional/nulo o texto 1-120; `serial_port`: opcional/nulo o texto 1-128. El modelo exacto y el puerto quedan nulos si se desconocen. El puerto es un metadato: esta ruta no intenta abrirlo ni validar una placa conectada.

Respuesta: `id`, `name`, `kind: "esp32-s3"`, `model`, `serial_port`, `status: "not_configured"`, `created_at`, `last_seen_at: null`. El cliente no puede asignar estado, identificador ni fechas. La lista se ordena por creación e identificador.

### Telemetría

Consulta inicial, sin mediciones:

```json
{
  "items": [],
  "total": 0,
  "source": "real",
  "queried_at": "<fecha ISO 8601 UTC de la consulta>"
}
```

`source: "real"` define el conjunto consultado; una lista vacía no afirma que exista hardware activo. `total` cuenta todos los registros que cumplen filtros, antes de la paginación.

| Parámetro opcional | Regla | Predeterminado |
| --- | --- | --- |
| `limit` | Entero 1-200 | 100 |
| `offset` | Entero >= 0 | 0 |
| `zone_id` | UUID | Sin filtro |
| `device_id` | UUID | Sin filtro |

Orden: `measured_at` descendente e `id`. Un filtro válido sin coincidencias devuelve lista vacía.

Contrato de cada medición reservado para futura ingesta real: `id`, `source: "real"`, `zone_id`, `device_id`, `quantity`, `unit`, `value` finito, `quality` (`valid`, `invalid`, `unverified`), `measured_at`, `recorded_at`, `observations` nullable. No hay POST de telemetría; la Fase 1 no produce estos registros.

## Errores y límites

- **422:** cuerpo o parámetros inválidos. Los POST rechazan propiedades desconocidas, tipos incorrectos, texto vacío y exceso de longitud; FastAPI devuelve `detail` con los errores.
- **503:** acceso a base no disponible. Fuera de health, respuesta `{"detail":"La base de datos no está disponible."}`.
- **405:** métodos no implementados, por ejemplo POST de telemetría.
- Las respuestas vacías no deben convertirse en valores cero ni estados estables. El frontend presenta ausencia de datos y conserva el mensaje de error cuando no puede consultar.

El contrato está definido por los esquemas Pydantic y el OpenAPI generado por el servidor. Cualquier cambio exige revisar tipos del frontend, migraciones, pruebas y este documento.

## Configuración de almacenamiento

Sin variables de entorno, la base es `backend/data/lekil.db`. `DATABASE_URL` acepta sólo SQLite persistente: por ejemplo, `sqlite:///data/otro-banco.db` se resuelve respecto de `backend/`, mientras una ruta absoluta conserva su ubicación. No se admiten bases en memoria para la operación del servicio. Cambiar la variable elige otro archivo; no migra los datos del archivo anterior.

El inicio aplica `alembic upgrade head`. Para aplicarlo manualmente desde la raíz con el entorno del proyecto: `.\.venv\Scripts\python.exe -m alembic -c backend/alembic.ini upgrade head`. La revisión inicial es `0001_observation`. Su `downgrade` destructivo está bloqueado para preservar el historial; una recuperación exige respaldo y revisión explícita.
