# Roadmap de ARVIS

## v0.1.0 backend minimo seguro creado

- Backend con FastAPI.
- Endpoint de salud.
- Endpoint de chat.
- Router simple de intenciones.
- Permisos basicos.
- Herramientas seguras iniciales.
- Memoria SQLite.

## v0.1.1 pruebas, arranque facil y diagnostico

- Scripts de instalacion y arranque para Windows.
- Diagnostico extendido en `/health`.
- Listado detallado en `/tools`.
- Lectura reciente de memoria en `/memory/recent`.
- Contrato consistente para `/chat`.
- Pruebas basicas con pytest.

## v0.2.0 integracion inicial con Ollama

- Integracion opcional con Ollama.
- Endpoint `/ai/status`.
- Prompt base de ARVIS.
- Fallback si Ollama no esta disponible.
- La IA solo responde texto; las herramientas siguen pasando por permisos.

## v0.2.1 configuracion de IA y modelo

- Configuracion persistente en `backend/storage/settings.json`.
- Endpoints `/settings`, `/ai/models` y `/ai/model`.
- Seleccion simple de modelo sin descargas automaticas.
- Historial conversacional corto opcional.
- Comando local de ayuda.

## v0.2.2 confirmaciones, acciones pendientes y auditoria basica

- Acciones pendientes persistidas en SQLite.
- Endpoints `/actions/pending`, `/actions/{id}/confirm`, `/actions/{id}/cancel`.
- Expiracion configurable de acciones pendientes.
- Confirmacion con revalidacion de permisos.
- Auditoria basica en memoria.

## v0.3.0 voz basica STT/TTS

- Endpoints `/voice/status`, `/voice/stt`, `/voice/tts` y `/voice/chat`.
- STT opcional con `faster-whisper`.
- TTS opcional con `pyttsx3`.
- La voz pasa por `brain.py`, permisos y confirmaciones.
- Sin escucha continua y sin wake word.

## v0.3.1 captura de microfono controlada

- Endpoints `/voice/mic/status`, `/voice/mic/devices`, `/voice/mic/record` y `/voice/mic/chat`.
- Captura de microfono limitada por segundos.
- Dependencias opcionales `sounddevice` y `numpy`.
- Sin escucha continua y sin wake word.

## v0.4.0 interfaz de escritorio minima

- Captura manual desde boton o accion explicita.
- Panel basico de estado del backend.
- Integracion visual con chat, voz y acciones pendientes.

## v0.4.1 integracion robusta escritorio-backend

- Cliente API centralizado para la app de escritorio.
- Deteccion de backend conectado/desconectado.
- Chat real contra `POST /chat`.
- Paneles de estado para backend, Ollama, modelo, STT, TTS, microfono y pendientes.
- Confirmacion/cancelacion de acciones pendientes desde la UI pasando por el backend.
- Logs visuales y botones seguros para Swagger, proyecto y storage.

## v0.4.2 pulido controlado de escritorio

- Tema visual centralizado.
- Mensajes de error y estados mas claros.
- Chat y paneles mas legibles.
- Botones para limpiar chat visual y copiar ultima respuesta.

## v0.4.3 modo compacto, bandeja y HUD liviano

- Modo compacto/flotante.
- Minimizar a bandeja de Windows con menu.
- Control de siempre visible y pantalla completa.
- Logs visuales con limite de eventos.
- Configuracion desktop extendida.

## v0.4.4 panel de configuracion y diagnostico desde escritorio

- Panel `Configuracion y diagnostico`.
- Diagnostico completo copiable.
- Configuracion desktop editable desde UI.
- Settings backend seguros editables con `PATCH /settings`.
- Diagnostico de IA, voz, microfono, pendientes, rutas y logs.

## v0.4.x mejoras de escritorio

- Interfaz para PC.
- Historial de conversaciones.
- Panel de permisos.

## v0.5 app Android

- Cliente movil.
- Conexion con backend local o remoto.

## v1.0 primera version publica

- Instalacion documentada.
- Seguridad revisada.
- Sistema de plugins inicial.
