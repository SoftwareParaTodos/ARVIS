# Checkpoints de ARVIS

## v0.4.3 modo compacto, bandeja y HUD liviano

- Backend y desktop reportan version `0.4.3`.
- La interfaz mantiene llamadas al backend mediante `desktop_app/services/api_client.py`.
- Modo compacto alternable sin borrar el historial visual.
- Bandeja de Windows con mostrar, compacto, actualizar, Swagger y salir.
- Siempre visible, pantalla completa, limpiar chat visual y copiar ultima respuesta.
- Configuracion desktop extendida en `desktop_app/config/desktop_settings.json`.

Limitaciones vigentes:

- No hay wake word.
- No hay escucha continua.
- No hay app Android.
- No hay ejecucion libre de comandos desde la UI.

## v0.4.4 panel de configuracion y diagnostico desde escritorio

- Backend y desktop reportan version `0.4.4`.
- Boton `Configuracion` abre `Configuracion y diagnostico`.
- Diagnostico copiable sin incluir contenido completo del chat.
- Configuracion desktop editable desde UI.
- Settings backend permitidos editables via `PATCH /settings`.
- IA, voz, microfono, pendientes, rutas y logs visibles desde el panel.

## v0.4.4.1 hotfix estabilidad desktop

- Desktop reporta version `0.4.4.1`.
- Refresh automatico queda liviano y sin solapamiento.
- Diagnostico completo queda bajo demanda.
- Timeouts mas estrictos para health, modelos y dispositivos.
