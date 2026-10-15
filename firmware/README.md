# Firmware ESP32 · Fase 2A

Placa real: ESP32 clásico de 30 pines, ESP32-D0WD-V3 y CH340. Se conserva `platformio.ini`: `board=esp32dev`, `framework=arduino`, COM6 y 115200 baudios. No es un ESP32-S3.

`src/main.cpp` envía JSON Lines: hello al arrancar y heartbeat cada 3000 ms. Campos: protocolo, tipo, ID estable de eFuse, modelo obtenido del chip, firmware, ID de arranque, secuencia y uptime real en milisegundos. La aleatoriedad del ID de arranque no genera mediciones. No se declaran pines, sensores ni actuadores.

Desde la raíz, compilar con `& "$env:USERPROFILE\.platformio\penv\Scripts\platformio.exe" run --project-dir .\firmware`. Para cargar, añadir `--target upload --upload-port COM6`, después de cerrar cualquier monitor y detener el lector serial.

El firmware ya fue compilado y cargado físicamente en esta entrega. Protocolo y resultados: `docs/FASE_2A_SERIAL.md`.
