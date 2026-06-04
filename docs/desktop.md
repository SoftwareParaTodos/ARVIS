# ARVIS Desktop

ARVIS Desktop es la interfaz HUD local del proyecto. En v0.4.4 no ejecuta comandos ni herramientas por su cuenta: todo pasa por el backend FastAPI.

## Iniciar backend

Desde `C:\ARVIS`:

```bat
run_backend.bat
```

Tambien se puede iniciar manualmente:

```bat
cd C:\ARVIS\backend
uvicorn main:app --reload
```

## Iniciar desktop

Desde `C:\ARVIS\desktop_app`:

```bat
run_desktop.bat
```

El script crea el entorno virtual del escritorio si no existe e instala `desktop_app\requirements.txt`.

## Backend apagado

La app puede abrir sin backend. Si `http://127.0.0.1:8000` no responde, muestra que el backend esta desconectado, deshabilita acciones que dependen del backend y permite usar el boton `Reintentar conexion`.

La configuracion local esta en:

```text
C:\ARVIS\desktop_app\config\desktop_settings.json
```

Valores principales:

- `backend_base_url`
- `request_timeout_seconds`
- `auto_refresh_status`
- `auto_refresh_interval_seconds`
- `compact_mode_enabled`
- `always_on_top`
- `minimize_to_tray`
- `ui_mode`

## Modo compacto

El modo compacto reduce la ventana para dejar visible el nucleo HUD, estado general, chat y controles minimos. No pierde el historial visual al alternar.

Usar el boton `Modo compacto` para entrar o `Normal` para volver. La preferencia se guarda en `desktop_settings.json`.

## Bandeja de Windows

Si el sistema soporta bandeja, ARVIS crea un icono simple generado localmente. El menu de bandeja permite:

- Mostrar ARVIS.
- Alternar modo compacto.
- Actualizar estados.
- Abrir Swagger.
- Minimizar a bandeja.
- Salir.

Con `minimize_to_tray=true`, cerrar o minimizar oculta la ventana en la bandeja. Para salir realmente, usar `Salir` desde el menu de bandeja o desactivar esa opcion en configuracion.

## Controles de ventana

La interfaz incluye:

- Pantalla completa/restaurar con boton o `F11`.
- Siempre visible.
- Minimizar a bandeja.
- Limpiar chat visual, sin borrar memoria del backend.
- Copiar ultima respuesta.

## Modo facil / avanzado

`ui_mode` acepta `easy` o `advanced`.

- `easy`: prioriza nucleo, chat, estado y pendientes.
- `advanced`: muestra paneles completos, logs, herramientas, IA y voz.

## Configuracion y diagnostico

El boton `Configuracion` abre el panel `Configuracion y diagnostico`.

Desde ahi se puede:

- Probar o reintentar conexion con backend.
- Abrir Swagger.
- Copiar estado del backend.
- Copiar diagnostico completo.
- Ver IA local, modelo actual y modelos instalados si Ollama responde.
- Cambiar modelo con `POST /ai/model`, sin descargar modelos.
- Ver estado de voz, STT, TTS y microfono.
- Probar TTS con un texto corto si el backend lo permite.
- Listar dispositivos de microfono sin grabar automaticamente.
- Ver y actualizar acciones pendientes.
- Abrir carpetas fijas del proyecto y storage.
- Editar configuracion desktop segura.
- Editar settings backend permitidos por `PATCH /settings`.

Colores:

- Azul/celeste o verde: conectado/OK.
- Naranja: advertencia o dependencia faltante.
- Rojo: error o bloqueo.
- Gris: no disponible.

El diagnostico incluye versiones, URL, estados, rutas y ultimos eventos visuales. No incluye el contenido completo del chat.

## Probar chat

Con backend encendido, escribir:

```text
info del sistema
```

La app envia `POST /chat` y muestra el estado devuelto por el backend: `executed`, `blocked`, `confirmation_required`, `response` o `error`.

Para probar una accion peligrosa sin ejecutar nada:

```text
borrar archivos
```

ARVIS debe responder `blocked` o `confirmation_required` segun la politica vigente, pero no borra archivos.

## Estados

El escritorio consulta:

- `GET /health`
- `GET /settings`
- `GET /ai/status`
- `GET /voice/status`
- `GET /voice/mic/status`
- `GET /actions/pending`

Tambien permite listar modelos con `GET /ai/models` y guardar el modelo activo con `POST /ai/model`. No descarga modelos automaticamente.

## Acciones pendientes

El panel de pendientes lista acciones desde `GET /actions/pending`.

Confirmar llama a:

```text
POST /actions/{id}/confirm
```

Cancelar llama a:

```text
POST /actions/{id}/cancel
```

La UI no salta permisos. El backend revalida la accion.

## Voz

Los botones de voz consultan `GET /voice/status` y `GET /voice/mic/status`. El boton `Grabar 5s` llama a `POST /voice/mic/chat` con duracion limitada.

No hay escucha continua y no hay wake word.

## Limites actuales

- Ollama es opcional.
- STT/TTS/microfono dependen de paquetes opcionales.
- No hay automatizaciones avanzadas.
- No hay app Android.
- No hay ejecucion libre de comandos desde desktop.
