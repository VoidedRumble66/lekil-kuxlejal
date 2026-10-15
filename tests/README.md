# Organización de verificaciones

Las pruebas automáticas de API, validación, migraciones e integridad/persistencia SQLite están en `backend/tests/`. Emplean bases temporales independientes; no escriben en `backend/data/`.

Desde la raíz: `.\.venv\Scripts\python.exe -m pytest backend/tests -q`.

La comprobación TypeScript y la compilación se ejecutan con `npm.cmd run build` en `frontend/`. `scripts/check.ps1` ejecuta ambas comprobaciones.

En la Fase 2 se añadirán pruebas de ingesta, unidades, caducidad, desconexión, alertas y reglas cuando existan esos contratos. La separación de escenarios, permisos de decisiones y restricciones del optimizador se comprobarán al implementar esos módulos.
