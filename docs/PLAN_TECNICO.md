# Plan técnico de LEKIL KUXLEJAL CONTROL

Fecha de planificación: 15 de octubre de 2026. Entrega solicitada: **únicamente Fase 1**. La fecha objetivo del proyecto es el 30 de octubre de 2026; no implica que las validaciones físicas, alimentarias o culturales del expediente estén realizadas.

## Fuentes y alcance

Se revisaron el expediente local, versión oficial 1.1, de 62 páginas, la especificación maestra aportada por el usuario y las ocho capturas de DOMO VITAL. El inventario y las páginas verificadas están en [referencias/README.md](referencias/README.md). El PDF aporta requisitos de dominio; sus propuestas y cálculos no constituyen órdenes ejecutables ni resultados físicos. La especificación limita esta ejecución a la primera fase.

LEKIL KUXLEJAL MARTE identifica el sistema completo; DOMO VITAL identifica su módulo agrícola. El primer despliegue es terrestre, educativo y local. El biodomo no sustituye el soporte vital humano (expediente, pp. 3, 10 y 20).

## Secuencia de la primera entrega

1. Inventariar las fuentes y registrar discrepancias, ausencias y límites de evidencia.
2. Definir contratos comunes y preparar el monorepositorio, reglas de colaboración y documentación.
3. Configurar un único servicio FastAPI con Pydantic, SQLModel, SQLite persistente y migraciones Alembic.
4. Registrar zonas y dispositivos manualmente, sin inventar sectores instalados, sensores, lecturas o conexiones.
5. Consultar salud, configuración y telemetría real a través de `/api`; la base de mediciones empieza vacía y no hay ingesta en esta fase.
6. Construir Inicio en React, TypeScript, Vite y Tailwind, con la identidad de los mockups, navegación real y estados de ausencia de datos.
7. Verificar contratos, validación, persistencia y build. Probar con bases temporales; comprobar que la base operativa conserva cero mediciones.
8. Documentar resultados y comandos Windows en el README raíz y en `VERIFICACION_FASE_1.md`.

## Puerta de aceptación

| Resultado comprobable | Evidencia prevista |
| --- | --- |
| API local y SQLite accesibles | `GET /api/health`, con modo `observation` y `control_enabled: false` |
| Configuración persistente | Crear zona/dispositivo; cerrar y abrir conexión; recuperar los mismos registros |
| Ausencia de datos inventados | Consulta vacía de `measurements`; no seed, generador ni tarea de simulación |
| Frontend conectado | Peticiones HTTP a FastAPI y estados distintos para API inaccesible y ausencia de lecturas |
| Indicadores honestos | «Sin datos», «Sensor no configurado» y «Consumo no medido» |
| Control deshabilitado | Ningún endpoint, adaptador o botón envía órdenes físicas |
| Código comprobable | Pruebas backend y compilación TypeScript/Vite; revisión visual cuando esté disponible |

## Entorno y decisiones

Windows y Node.js 24 LTS son el objetivo. La especificación solicita Python 3.13; el entorno disponible para esta ejecución contiene Python 3.12.14 en el runtime de Codex. La verificación con 3.12 no acredita ejecución con 3.13. No se sustituye ni instala silenciosamente el Python del usuario.

Las dependencias se instalan una vez; el funcionamiento principal es local. SQLite reside por defecto en `backend/data/lekil.db`, fuera de los archivos de código versionados. El backend escucha en `127.0.0.1`; esta entrega no incorpora autenticación y no debe exponerse a una red.

## Riesgos y pendientes

- No se identificó el modelo físico exacto de la placa ESP32-S3, sensores instalados, puerto, pinout ni calibraciones. Se pueden guardar metadatos sin afirmar conexión.
- No se aportaron otros documentos independientes de Mars Challenge. La rúbrica mencionada por el PDF no está disponible como archivo.
- El índice del PDF se desfasa respecto a algunas páginas reales; los documentos del repositorio citan la numeración de las páginas comprobadas.
- USB serial, ingesta, evaluación de calidad, alertas, escenarios y gobernanza quedan para fases futuras. Cada avance requiere una nueva instrucción y su propia evidencia.

Los resultados ejecutados, fallos de entorno y limitaciones deben registrarse en `VERIFICACION_FASE_1.md`; este plan no declara pruebas aprobadas por adelantado.
