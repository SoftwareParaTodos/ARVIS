# Voz en ARVIS

ARVIS v0.3.1 agrega una capa basica de voz al backend:

- STT: convertir audio a texto.
- TTS: convertir texto a audio.
- Voice chat: recibir audio, transcribirlo, pasarlo por `brain.py` y devolver respuesta.
- Captura de microfono controlada por endpoint, con duracion limitada.

La voz es opcional. El backend sigue funcionando aunque `faster-whisper` o `pyttsx3` no esten instalados.

## Instalacion opcional

Desde Windows:

```bat
cd C:\ARVIS\backend
.venv\Scripts\activate
pip install -r requirements-voice.txt
```

`python-multipart` esta en `requirements.txt` porque FastAPI lo necesita para recibir archivos. Los motores STT/TTS viven en `requirements-voice.txt`.

Dependencias opcionales de microfono:

```bat
cd C:\ARVIS\backend
.venv\Scripts\activate
pip install -r requirements-mic.txt
```

## STT

El modulo `backend/voice/speech_to_text.py` usa `faster-whisper` si esta instalado.

Formatos permitidos:

- `.wav`
- `.mp3`
- `.m4a`
- `.mp4`
- `.webm`
- `.flac`

Nota: `faster-whisper` puede necesitar FFmpeg y modelos locales. Si el modelo no esta disponible, el motor puede intentar obtenerlo segun su configuracion interna. ARVIS no implementa descargas automaticas propias en v0.3.1.

## TTS

El modulo `backend/voice/text_to_speech.py` usa `pyttsx3` si esta instalado.

Por defecto, los endpoints generan archivos `.wav` en:

```text
backend/storage/voice/tts/
```

`speak_now` existe, pero los endpoints prefieren generar archivo antes que hablar directamente desde el servidor.

## Endpoints

### GET /voice/status

Devuelve estado de voz, STT, TTS y almacenamiento.

### POST /voice/stt

Recibe audio por `multipart/form-data` con campo `file` y devuelve transcripcion.

### POST /voice/tts

Body:

```json
{
  "text": "Hola, soy ARVIS.",
  "speak_now": false
}
```

### POST /voice/chat

Recibe audio por `multipart/form-data` con:

- `file`: archivo de audio.
- `speak_response`: `true` o `false`.

Flujo:

```text
audio -> STT -> brain.py -> router/permisos/herramientas -> TTS opcional -> respuesta
```

### GET /voice/mic/status

Devuelve estado del microfono sin grabar audio.

### GET /voice/mic/devices

Lista dispositivos de entrada disponibles si `sounddevice` esta instalado.

### POST /voice/mic/record

Body:

```json
{
  "duration_seconds": 5
}
```

Graba un WAV local durante una duracion limitada por configuracion.

### POST /voice/mic/chat

Body:

```json
{
  "duration_seconds": 5,
  "speak_response": false
}
```

Flujo:

```text
microfono -> WAV local -> STT -> brain.py -> permisos/herramientas/pendientes -> TTS opcional -> respuesta
```

## Subir audio vs grabar microfono

`/voice/stt` y `/voice/chat` reciben un archivo subido por el usuario. `/voice/mic/record` y `/voice/mic/chat` activan el microfono solo durante la llamada al endpoint y solo por la duracion indicada.

No hay escucha continua. No hay wake word. No se graba en segundo plano.

## Probar con Swagger

1. Ejecutar `run_backend.bat`.
2. Abrir `http://127.0.0.1:8000/docs`.
3. Usar los endpoints bajo la seccion `voice`.

## Seguridad

La voz no evita permisos ni confirmaciones. Toda transcripcion se trata igual que texto y pasa por `brain.py`.

No hay escucha continua en v0.3.1. No hay wake word. ARVIS no accede al microfono automaticamente.

## Limitaciones de v0.3.1

- No hay wake word.
- No hay escucha continua.
- STT/TTS dependen de paquetes opcionales.
- Captura de microfono depende de `sounddevice` y `numpy`.
- La duracion de grabacion esta limitada por configuracion.
- No hay limpieza automatica avanzada de audios.

## Proximo paso sugerido

v0.4.0: interfaz de escritorio minima con captura de microfono controlada desde un boton o accion explicita.
