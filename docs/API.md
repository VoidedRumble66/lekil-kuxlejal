# API local · DOMO VITAL

Base: `http://127.0.0.1:8000/api`. OpenAPI: `http://127.0.0.1:8000/openapi.json`; explorador: `http://127.0.0.1:8000/docs`.

JSON con nombres `snake_case`. Identificadores UUID. Fechas de auditoría ISO 8601 UTC con `Z` o desplazamiento explícito; fechas documentales de semillas usan `YYYY-MM-DD`. No hay autenticación de usuarios: ejecutar en la interfaz local. El contrato inicial de observación se conserva abajo como referencia histórica. Diagnóstico serial en `FASE_2A_SERIAL.md`, escenarios en `FASE_2B_ITZAMNA.md` y Semillas en `FASE_2C_A_SEMILLAS.md`. No hay comandos físicos.

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

## Banco de semillas · Fase 2C-A

Prefijo `/api/seeds`. `GET/POST /lots`, `GET/PUT /lots/{lot_id}`, `GET/POST /weights`, `POST /lots/{lot_id}/assessments`, `POST /compare`, `POST /lots/{lot_id}/decisions` y `GET /lots/{lot_id}/history`. Detalles, reglas y flujo en [FASE_2C_A_SEMILLAS.md](FASE_2C_A_SEMILLAS.md).

El pasaporte requiere nombre común, código único y `source_kind` (`real` o `hypothetical`). Los datos desconocidos son nulos, sin resultados autogenerados. Autorización `pending` de manera predeterminada; `authorized` y `denied` requieren fuente documental, y `authorized` exige condiciones de uso. No hay campos para personas custodias ni vistas de publicación.

La edición usa `{expected_revision, passport}`. Una evaluación usa `{expected_revision, weight_profile_id, scores, responsible}`; `scores` incluye los seis criterios, cada uno nulo o `{value, justification, source}`. Escala provisional 0–5; total sólo con seis puntuaciones. `weight_profile_id` nulo representa los pesos iniciales propuestos, sin precargar tablas.

Una comparación recibe `{lot_ids}` (2–20 UUID distintos del mismo tipo). Su respuesta conserva el orden consultado, no genera un ranking y contiene `complete`, filas con pendientes, pesos y `comparison_hash`. Una selección requiere decisión humana `seleccionar`, revisión esperada, responsable, motivo, los mismos `lot_ids` bajo `comparison` y el `comparison_hash` revisado. El servidor comprueba datos vigentes y autorización; no ejecuta tareas físicas.

Cambios obsoletos/código duplicado devuelven 409. Comparación incompleta o mezclada y siembra/selección sin autorización devuelven 422. CORS añade `PUT` únicamente para la edición local de lotes; no incorpora métodos de actuación ni escritura de telemetría.
