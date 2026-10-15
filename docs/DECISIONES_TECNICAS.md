# Decisiones técnicas

Estado: decisiones de la Fase 1, 15 de octubre de 2026.

| Decisión | Motivo y consecuencia |
| --- | --- |
| Un monorepositorio y un backend | Comparte contratos y evita modelos de negocio duplicados. Frontend y firmware no acceden directamente a SQLite |
| React/TypeScript/Vite | Sigue el stack explícito del usuario. La ruta Next.js sugerida en el expediente p. 41 es una posibilidad conceptual |
| FastAPI, Pydantic y SQLModel | Contratos tipados, validación de entrada y persistencia con un esquema común |
| SQLite local y Alembic | Arranque sin nube; integridad referencial y evolución versionada. No usar `create_all` como sistema de migraciones |
| Base inicial sin datos de ejemplo | Los valores de los mockups son demostrativos (pp. 40-41). La ausencia de instrumentación debe quedar visible |
| Alta manual de zonas/dispositivos | Permite comprobar configuración y persistencia antes de tener sensores. No equivale a instalar, conectar o medir |
| Tabla de mediciones reservada | Hace explícita la consulta real y las claves de procedencia; permanece vacía y no tiene ruta de escritura en esta fase |
| Modo observación fijo | No hay control físico, reglas de actuación ni órdenes eléctricas; la autorización de configuración no autoriza automatización |
| Sin seed de cuatro sectores | El PDF p. 31 define funciones conceptuales; no evidencia cuatro zonas reales productivas ni su instalación |
| UTC en almacenamiento | Evita ambigüedad al unir mediciones, decisiones e historial. API siempre devuelve fechas con zona |
| Sin endpoints de borrado | La primera entrega conserva registros y evita comprometer trazabilidad; se diseñarán correcciones explícitas más adelante |
| Servicio sólo local | No se implementaron usuarios/roles en Fase 1. CORS no sustituye autenticación; acceso de red requiere una fase adicional |
| Sin motor de IA ni ML | El futuro motor será determinista primero; faltan datos físicos y evaluación para justificar entrenamiento |
| Sin gráficos con series inventadas | Recharts está preparado en dependencias; las visualizaciones de mediciones esperan series reales |
| Referencias locales sin publicación | Se preservan archivos aportados para revisión, con sus restricciones; no se presume permiso de difusión |

## Separaciones que deben conservarse

Datos medidos, registros manuales, estimaciones y escenarios tendrán fuente y tratamiento propios. La tabla real sólo admite `source=real`; los escenarios tendrán tablas distintas. Los registros bioculturales enlazarán evidencia técnica sin sustituir permisos ni contexto. La producción alimentaria y el laboratorio confinado mantienen barreras y trazabilidad (expediente, pp. 20, 24, 36-38 y 53).

## Límites del entorno

El objetivo indicado por el usuario es Python 3.13 y Node.js 24 LTS. El runtime disponible para las pruebas de esta ejecución es Python 3.12.14 y Node.js 24.22.0. Se documenta esta diferencia; no se declara verificación en Python 3.13 sin ejecutarla. Los resultados definitivos están en `VERIFICACION_FASE_1.md`.

## Registro de cambios futuro

Antes de cambiar un contrato, revisar frontend, backend, tests y documentos. Las futuras tablas deben incorporarse por migración aditiva y mantener identificadores e historial. Cualquier cambio de modo físico requerirá hardware probado, reglas preaprobadas, límites de alcance/tiempo, cancelación manual y revisión de seguridad. La fecha límite no habilita excepciones tácitas.
