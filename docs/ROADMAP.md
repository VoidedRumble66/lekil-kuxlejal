# Hoja de ruta

Fecha de referencia: 15 de octubre de 2026. Objetivo de entrega de software: 30 de octubre de 2026, según la especificación aportada. La presente ejecución termina en **Fase 1**; las fases siguientes requieren una nueva instrucción.

| Fase | Alcance | Puerta de avance |
| --- | --- | --- |
| 1. Base local | Arquitectura, documentación, FastAPI, SQLite/Alembic, zonas/dispositivos, consulta real vacía, Inicio React | API conectada, persistencia comprobada, cero mediciones inventadas, pruebas y build documentados |
| 2. Instrumentación real | Identificar ESP32-S3, puerto y sensores; protocolo serial; adaptadores, ingesta, calibración, calidad/vigencia, desconexión y alertas | Lecturas físicas trazables y pruebas de pérdida de conexión, datos imposibles y reinicio; control sigue deshabilitado |
| 3. Recursos y gobernanza | Movimientos reales, balances, mínimos aprobados, motor determinista, alternativas, autorizaciones y auditoría | Casos factibles/inviables explicados, permisos comprobados e historial conservado |
| 4. Cadena productiva y memoria | Semillas, ciclos, biomasa, alimentos, recetas y fichas culturales con procedencia/consentimiento | Trazabilidad por lote, separación de laboratorio, liberación documentada y controles de acceso |
| 5. Integración física y demostración | Hardware probado, actuación acotada sólo tras revisión, tareas con usuarios y presentación | Comandos reversibles autorizados, confirmación, cancelación, recuperación y evidencia de pruebas |

## Preparación de la segunda fase

1. Identificar fabricante y modelo exacto de la placa ESP32-S3; aportar ficha técnica y diagrama comprobado.
2. Inventariar sensores realmente disponibles, magnitud, unidad, alimentación, interfaz y calibración.
3. Confirmar sectores reales y propósito; acordar identificadores de dispositivo/sensor/zona y un contrato serial versionado.
4. Añadir migraciones aditivas de sensores, calibraciones y estados; validar UTC, valores finitos, unidades y fuentes antes de persistir.
5. Probar con hardware, sin insertar ejemplos en la base operativa. Mantener fixtures en bases temporales.
6. Incorporar reglas de alerta por fuente/cultivo cuando sus límites estén justificados. Una desconexión no demuestra una emergencia agrícola.

Los escenarios hipotéticos se habilitarán como una línea separada de la ingesta real. Sus seis casos provienen del expediente p. 47. Nunca escribirán en mediciones ni enviarán comandos.

## Alcance de la fecha límite

La fecha del 30 de octubre no sustituye criterios de seguridad o evidencia. Si faltan hardware, calibraciones, permisos, análisis o tiempo de validación, la presentación debe declarar la limitación. El cronograma del expediente (p. 50) plantea un banco terrestre progresivo durante meses; no se transforma en una promesa de madurez física para la fecha de entrega del software.

Las pruebas alimentarias, de estructura, presión, descontaminación, vida útil y revisión comunitaria son trabajos independientes. No se acreditan con una pantalla, un simulador ni un build aprobado (expediente, pp. 47-51 y 57).
