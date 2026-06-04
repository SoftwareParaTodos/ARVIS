# Arquitectura de ARVIS

ARVIS v0.4.4 contiene un backend minimo en Python con configuracion persistente, acciones pendientes, integracion opcional de IA local mediante Ollama, voz STT/TTS, captura de microfono controlada y una interfaz de escritorio conectada al backend local. La arquitectura esta pensada para crecer sin mezclar UI, decisiones, permisos, IA, voz y herramientas en un unico archivo.

## Flujo principal

1. El usuario envia un mensaje al backend con `POST /chat`.
2. FastAPI recibe la solicitud en `api/routes_chat.py`.
3. `assistant/brain.py` coordina la respuesta.
4. `assistant/router.py` detecta la intencion basica del texto.
5. Si la intencion es una accion conocida, `assistant/permissions.py` clasifica la accion como `safe`, `confirmation_required` o `blocked`.
6. Si el riesgo es `safe`, `brain.py` llama una herramienta segura dentro de `tools/`.
7. Si el riesgo es `confirmation_required`, `assistant/pending_actions.py` crea una accion pendiente y no ejecuta nada.
8. Si el riesgo es `blocked`, ARVIS bloquea la accion y registra auditoria.
9. Si no hay accion conocida, `assistant/local_ai.py` consulta Ollama para generar solo texto.
10. Si el historial corto esta habilitado en `assistant/settings.py`, `brain.py` agrega contexto reciente.
11. Si Ollama no esta disponible, `brain.py` devuelve un fallback basico.
12. `assistant/memory.py` guarda la interaccion en SQLite.
13. El backend devuelve una respuesta con intencion, permiso, herramienta y estado.

## Flujo de voz

```text
Audio del usuario
-> /voice/chat
-> voice/speech_to_text.py
-> assistant/brain.py
-> router/permissions/tools o pending_actions
-> voice/text_to_speech.py opcional
-> respuesta
```

La voz no ejecuta acciones por fuera del flujo seguro existente.

## Flujo de microfono

```text
Microfono
-> /voice/mic/chat
-> voice/microphone_capture.py
-> archivo WAV local
-> voice/speech_to_text.py
-> assistant/brain.py
-> router/permissions/tools o pending_actions
-> voice/text_to_speech.py opcional
-> respuesta
```

El microfono solo se activa durante una llamada explicita al endpoint y por una duracion limitada.

## Flujo escritorio-backend

```text
desktop_app/ui/arvis_window.py
-> desktop_app/services/api_client.py
-> backend FastAPI local
-> rutas /health, /chat, /settings, /ai, /voice, /actions
-> respuesta normalizada en la UI
```

La interfaz usa workers de Qt para llamar al backend sin congelar la ventana. Si el backend esta apagado, el escritorio sigue abierto, muestra un error claro y deshabilita las acciones que dependen del backend. El modo compacto, la bandeja de Windows, los controles de ventana y el panel de configuracion/diagnostico son capa visual o llamadas a endpoints seguros: no ejecutan herramientas ni saltean permisos.

## Endpoints

- `GET /health`: estado del backend, version, ruta de almacenamiento y existencia de base SQLite.
- `POST /chat`: entrada principal del asistente.
- `GET /actions/pending`: lista acciones pendientes.
- `POST /actions/{action_id}/confirm`: confirma accion pendiente con revalidacion de permisos.
- `POST /actions/{action_id}/cancel`: cancela accion pendiente.
- `POST /actions/clear-resolved`: limpia acciones resueltas.
- `GET /voice/status`: estado de voz, STT, TTS y almacenamiento.
- `POST /voice/stt`: transcripcion de audio subido.
- `POST /voice/tts`: generacion de audio desde texto.
- `POST /voice/chat`: audio a texto, brain y TTS opcional.
- `GET /voice/mic/status`: estado del microfono.
- `GET /voice/mic/devices`: dispositivos de entrada disponibles.
- `POST /voice/mic/record`: grabacion limitada de microfono.
- `POST /voice/mic/chat`: grabacion, STT, brain y TTS opcional.
- `GET /ai/status`: estado de Ollama, modelo configurado y error si corresponde.
- `GET /ai/models`: modelos instalados en Ollama si esta disponible.
- `POST /ai/model`: cambia el modelo activo en configuracion sin descargar modelos.
- `GET /tools`: lista de herramientas disponibles con descripcion, permiso y ejemplos.
- `GET /memory/recent`: ultimas interacciones guardadas en SQLite. Acepta `limit`, por defecto `10`.
- `GET /settings`: configuracion actual segura.
- `PATCH /settings`: actualizacion parcial de configuracion.
- `POST /settings/reset`: restaurar configuracion por defecto.
- `GET /settings/permissions`: niveles de permisos configurados.

## Estructura de carpetas

- `backend/main.py`: crea la aplicacion FastAPI y registra rutas.
- `backend/config.py`: rutas, almacenamiento y listas blancas.
- `backend/api/`: endpoints HTTP.
- `backend/assistant/`: logica central del asistente, router, permisos, memoria, prompts e IA local.
- `backend/assistant/local_ai.py`: integracion opcional con Ollama para respuestas de texto.
- `backend/assistant/pending_actions.py`: persistencia y estado de acciones pendientes.
- `backend/assistant/settings.py`: configuracion persistente en `backend/storage/settings.json`.
- `backend/voice/`: servicios de STT, TTS, almacenamiento de audio y voice chat.
- `backend/voice/microphone_capture.py`: captura controlada de microfono con `sounddevice` opcional.
- `backend/tools/`: herramientas seguras y limitadas.
- `backend/storage/`: base SQLite y notas locales.
- `backend/tests/`: pruebas basicas con pytest.
- `desktop_app/main.py`: arranque de la interfaz de escritorio.
- `desktop_app/ui/`: ventana HUD, paneles y tema visual.
- `desktop_app/services/api_client.py`: cliente HTTP centralizado para el backend.
- `desktop_app/services/diagnostics.py`: construccion de reportes de diagnostico sin incluir chat completo.
- `desktop_app/config/desktop_settings.json`: URL del backend, timeout e intervalo de actualizacion.
- `desktop_app/tests/`: pruebas livianas del cliente API y configuracion de escritorio.
- `docs/`: documentacion tecnica.
- `plugins/`: espacio reservado para futuras extensiones.

## Principio de diseno

El backend no ejecuta comandos libres. Toda accion de sistema debe pasar por una herramienta explicita, con lista blanca y permisos revisables.

Ollama no ejecuta herramientas directamente en v0.4.4. La IA local solo genera texto; las acciones siguen controladas por `router.py`, `permissions.py`, `pending_actions.py` y los modulos dentro de `tools/`. La interfaz de escritorio tampoco ejecuta herramientas directamente: todas las acciones pasan por el backend.
