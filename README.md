# ARVIS

ARVIS es un asistente open source para PC y celular. En esta etapa el proyecto incluye un backend minimo en Python, con FastAPI, SQLite, Pydantic, Uvicorn, configuracion persistente, integracion opcional con IA local mediante Ollama y una interfaz de escritorio conectada al backend local.

## Objetivo

Construir una base estable, modular y segura antes de agregar automatizaciones avanzadas, wake word o app movil.

## Instalacion inicial

Requisitos:

- Python 3.11 o superior.
- Windows recomendado para las herramientas `notepad.exe` y `calc.exe`.

Instalacion automatica en Windows:

```bat
setup_backend.bat
```

Este script crea `backend\.venv`, actualiza `pip` e instala `backend\requirements.txt`.

Instalacion manual:

```bash
cd backend
pip install -r requirements.txt
```

## Ejecutar backend

Arranque recomendado en Windows:

```bat
run_backend.bat
```

Arranque manual:

```bash
cd backend
uvicorn main:app --reload
```

El backend queda disponible en:

```text
http://127.0.0.1:8000
```

Swagger queda disponible en:

```text
http://127.0.0.1:8000/docs
```

## Ejecutar interfaz de escritorio

La app de escritorio vive en `desktop_app` y se inicia con:

```bat
cd C:\ARVIS\desktop_app
run_desktop.bat
```

La interfaz puede abrir aunque el backend este apagado. En ese caso muestra:

```text
Backend de ARVIS no disponible. Inicia run_backend.bat o revisa la conexion local.
```

Cuando el backend esta corriendo, el escritorio muestra version, URL, estado de Ollama, modelo activo, STT, TTS, microfono y acciones pendientes. El chat envia mensajes reales a `POST /chat`; la UI no ejecuta acciones por su cuenta.

Botones utiles:

- Abrir Swagger: `http://127.0.0.1:8000/docs`
- Abrir proyecto: `C:\ARVIS`
- Abrir storage: `C:\ARVIS\backend\storage`
- Reintentar conexion.
- Actualizar estados.

## Voz basica

ARVIS v0.3.1 agrega endpoints de voz opcionales y captura de microfono controlada. No hay escucha continua, no hay wake word y ARVIS no accede al microfono automaticamente.

Instalacion opcional de dependencias de voz:

```bat
cd C:\ARVIS\backend
.venv\Scripts\activate
pip install -r requirements-voice.txt
```

Instalacion opcional de dependencias de microfono:

```bat
cd C:\ARVIS\backend
.venv\Scripts\activate
pip install -r requirements-mic.txt
```

Endpoints:

- `GET /voice/status`
- `POST /voice/stt`
- `POST /voice/tts`
- `POST /voice/chat`
- `GET /voice/mic/status`
- `GET /voice/mic/devices`
- `POST /voice/mic/record`
- `POST /voice/mic/chat`

Ejemplo TTS:

```json
{
  "text": "Hola, soy ARVIS.",
  "speak_now": false
}
```

La voz es solo otra entrada/salida. Toda orden transcripta pasa por `brain.py`, permisos, herramientas seguras y acciones pendientes si corresponde.

Ejemplo para grabar microfono:

```json
{
  "duration_seconds": 5
}
```

Ejemplo para chat por microfono:

```json
{
  "duration_seconds": 5,
  "speak_response": false
}
```

## Endpoints disponibles

### GET /health

Devuelve el estado del backend y datos de diagnostico.

Respuesta esperada:

```json
{
  "status": "OK",
  "app": "ARVIS",
  "version": "0.4.4",
  "backend": "running",
  "storage_path": "C:\\ARVIS\\backend\\storage",
  "database_exists": true,
  "settings_exists": true,
  "pending_actions_count": 0,
  "ai_enabled": true,
  "ai_available": false,
  "ai_model": "llama3.2",
  "voice_enabled": true,
  "stt_available": false,
  "tts_available": false,
  "mic_enabled": true,
  "mic_available": false
}
```

### POST /chat

Recibe un mensaje del usuario.

Ejemplo:

```json
{
  "message": "abrir calculadora"
}
```

Otros ejemplos:

```json
{
  "message": "info del sistema"
}
```

```json
{
  "message": "borrar archivos"
}
```

La respuesta mantiene este formato:

```json
{
  "status": "executed",
  "message": "Accion ejecutada.",
  "intent": "open_calculator",
  "tool": "open_program",
  "requires_confirmation": false,
  "risk_level": "safe",
  "details": {}
}
```

### GET /tools

Lista herramientas disponibles con nombre, descripcion, nivel de permiso y ejemplos.

### GET /ai/status

Devuelve el estado de la integracion local con Ollama.

Ejemplo:

```json
{
  "enabled": true,
  "available": false,
  "base_url": "http://127.0.0.1:11434",
  "model": "llama3.2",
  "timeout_seconds": 30,
  "error": "Timeout al consultar Ollama."
}
```

### GET /ai/models

Lista modelos instalados en Ollama si Ollama responde.

```text
http://127.0.0.1:8000/ai/models
```

Si Ollama no esta instalado o no responde, devuelve `available: false`, `models: []` y un error claro.

### POST /ai/model

Cambia el modelo activo guardado en `backend/storage/settings.json`. No descarga modelos automaticamente.

Body:

```json
{
  "model": "qwen2.5"
}
```

Si Ollama esta disponible y el modelo no aparece instalado, ARVIS devuelve una advertencia en `details`. Si Ollama no esta disponible, guarda el modelo igual e indica que no pudo verificarlo.

### GET /settings

Devuelve la configuracion segura actual.

```json
{
  "ollama_enabled": true,
  "ollama_base_url": "http://127.0.0.1:11434",
  "ollama_model": "llama3.2",
  "ollama_timeout_seconds": 30,
  "conversation_history_enabled": true,
  "conversation_history_limit": 6
}
```

### PATCH /settings

Actualiza parcialmente la configuracion.

```json
{
  "ollama_model": "qwen2.5",
  "ollama_timeout_seconds": 45
}
```

### POST /settings/reset

Restaura la configuracion por defecto.

### GET /settings/permissions

Lista niveles de permisos configurados.

### GET /memory/recent

Devuelve las ultimas interacciones guardadas en SQLite.

Ejemplo:

```text
http://127.0.0.1:8000/memory/recent?limit=5
```

### GET /voice/status

Devuelve estado de STT, TTS y almacenamiento local de voz.

### POST /voice/stt

Recibe un archivo de audio como `multipart/form-data` y devuelve transcripcion si STT esta disponible.

### POST /voice/tts

Genera audio desde texto si TTS esta disponible.

### POST /voice/chat

Recibe audio, lo transcribe, envia el texto a `brain.py` y devuelve la respuesta. Opcionalmente puede generar audio de respuesta.

### GET /voice/mic/status

Devuelve estado de configuracion y disponibilidad del microfono.

### GET /voice/mic/devices

Lista dispositivos de entrada disponibles si `sounddevice` esta instalado.

### POST /voice/mic/record

Graba audio del microfono por una duracion limitada y explicita.

### POST /voice/mic/chat

Graba audio, transcribe, envia el texto a `brain.py` y devuelve la respuesta segura.

### GET /actions/pending

Lista acciones pendientes de confirmacion.

```text
http://127.0.0.1:8000/actions/pending
```

### POST /actions/{action_id}/confirm

Confirma una accion pendiente por ID. La accion vuelve a pasar por permisos y solo se ejecuta si existe una herramienta segura implementada.

```text
http://127.0.0.1:8000/actions/3/confirm
```

### POST /actions/{action_id}/cancel

Cancela una accion pendiente.

```text
http://127.0.0.1:8000/actions/3/cancel
```

### POST /actions/clear-resolved

Limpia acciones resueltas: `confirmed`, `cancelled`, `expired` y `blocked`. No borra acciones `pending`.

## Confirmaciones

ARVIS v0.2.2 agrega acciones pendientes para pedidos riesgosos. Ejemplos de confirmacion:

```text
confirmo
confirmar accion 3
ejecutar accion pendiente 3
```

Ejemplos de cancelacion:

```text
cancelar
cancelar accion 3
cancelar pendiente 3
```

Todavia no hay herramientas peligrosas reales implementadas para borrar, mover, enviar mensajes o ejecutar comandos. Si una accion se confirma pero no existe herramienta segura, ARVIS responde con error controlado y no ejecuta nada.

## IA local con Ollama

Ollama es opcional en ARVIS v0.4.4. Si no esta instalado, no esta corriendo o no responde, el backend sigue funcionando con el router basico y las herramientas seguras.

Modelo configurado por defecto:

```text
llama3.2
```

Para verificar si Ollama esta corriendo, se puede abrir:

```text
http://127.0.0.1:11434/api/tags
```

Tambien se puede consultar desde ARVIS:

```text
http://127.0.0.1:8000/ai/status
```

Cuando Ollama esta disponible, `POST /chat` usa IA local para mensajes que no sean ordenes conocidas. Cuando no esta disponible, ARVIS responde con un fallback claro y conserva las herramientas basicas.

Ejemplo de fallback:

```text
Todavia no tengo IA local disponible. Puedo ayudarte con herramientas basicas como info del sistema, abrir calculadora, abrir descargas o crear notas.
```

Si Ollama no esta instalado, no hace falta cambiar nada para que el backend funcione. Se puede dejar apagado desde `PATCH /settings` con:

```json
{
  "ollama_enabled": false
}
```

## Seguridad

ARVIS no ejecuta comandos libres del sistema. Las herramientas iniciales usan listas blancas y solo permiten acciones concretas: abrir Bloc de notas, abrir Calculadora, abrir Descargas, crear notas en una carpeta autorizada y consultar informacion basica del sistema.

Ollama solo genera respuestas de texto en v0.4.4. La IA no ejecuta herramientas directamente.

Acciones como borrar archivos, mover archivos, instalar programas, cerrar aplicaciones o modificar configuraciones sensibles quedan bloqueadas o requieren confirmacion. Confirmar una accion no significa permiso total: vuelve a pasar por permisos y listas blancas.

## Roadmap corto

- v0.1.0 backend minimo seguro creado.
- v0.1.1 pruebas, arranque facil y diagnostico.
- v0.2.0 integracion inicial con Ollama.
- v0.2.1 configuracion de IA y modelo.
- v0.2.2 confirmaciones, acciones pendientes y auditoria basica.
- v0.3.0 voz basica STT/TTS.
- v0.3.1 captura de microfono controlada.
- v0.4.0 interfaz escritorio minima.
- v0.4.1 integracion robusta escritorio-backend.
- v0.4.2 pulido controlado de escritorio.
- v0.4.3 modo compacto, bandeja y HUD liviano.
- v0.4.4 panel de configuracion y diagnostico desde escritorio.
- v0.5 app Android.
- v1.0 primera version publica.
