# Seguridad de ARVIS

ARVIS v0.3.1 usa un sistema simple de permisos para evitar acciones peligrosas durante la etapa inicial del proyecto.

## Niveles de permisos

- `safe`: acciones permitidas sin confirmacion porque estan limitadas por listas blancas.
- `confirmation_required`: acciones potencialmente sensibles que no deben ejecutarse sin aprobacion explicita.
- `blocked`: acciones peligrosas que no se ejecutan.

## Acciones permitidas

Las acciones permitidas en esta version son:

- Abrir Bloc de notas en Windows mediante `notepad.exe`.
- Abrir Calculadora en Windows mediante `calc.exe`.
- Abrir la carpeta Descargas del usuario.
- Crear notas simples dentro de `backend/storage/notes/`.
- Consultar informacion basica del sistema.

## Lista blanca

Las herramientas no aceptan comandos arbitrarios. `open_program.py` solo abre programas definidos en `config.py`. `open_folder.py` solo abre carpetas definidas en `config.py`.

## Acciones peligrosas

ARVIS bloquea o requiere confirmacion para:

- Borrar archivos.
- Mover archivos.
- Ejecutar comandos libres del sistema.
- Instalar programas.
- Cerrar aplicaciones.
- Modificar configuraciones sensibles.

## Por que no se ejecutan comandos libres

Ejecutar comandos libres permitiria borrar datos, instalar software no deseado o modificar el sistema sin controles suficientes. En esta etapa, ARVIS solo debe actuar mediante herramientas pequenas, auditables y limitadas por lista blanca.

## IA local con Ollama

Ollama solo responde texto en ARVIS v0.3.1. La IA no puede ejecutar herramientas directamente, no puede ejecutar comandos arbitrarios y no modifica el sistema.

Las acciones del sistema siguen pasando por:

- `assistant/router.py`
- `assistant/permissions.py`
- herramientas seguras en `backend/tools/`

Las herramientas continuan limitadas por lista blanca. Aunque la IA sugiera una accion, ARVIS no la ejecuta si no existe una herramienta segura y un permiso compatible.

Cambiar el modelo activo con `/ai/model` solo escribe configuracion local en `backend/storage/settings.json`. No ejecuta comandos, no descarga modelos y no instala software automaticamente.

Si Ollama no esta instalado, ARVIS conserva el backend, las herramientas seguras y el fallback conversacional.

## Confirmaciones

Confirmar una accion no significa permiso total. Una accion confirmada vuelve a pasar por `permissions.py` y solo se ejecuta si existe una herramienta segura implementada.

En v0.2.2, pedidos como borrar archivos, mover archivos o enviar mensajes pueden generar una accion pendiente, pero no se ejecutan porque no existen herramientas seguras implementadas para esas operaciones.

ARVIS no ejecuta comandos libres aunque el usuario confirme. Tampoco descarga modelos automaticamente ni instala programas.

## Voz

Las ordenes por voz son tratadas igual que texto. Toda transcripcion pasa por `assistant/brain.py`, el router, permisos, herramientas seguras y acciones pendientes si corresponde.

Las acciones riesgosas siguen requiriendo confirmacion aunque hayan llegado por audio.

En v0.3.1:

- No hay escucha continua.
- No hay wake word.
- No se accede al microfono automaticamente.
- El microfono solo se activa cuando se llama explicitamente a `/voice/mic/record` o `/voice/mic/chat`.
- No se ejecutan comandos libres.
- Los audios subidos se guardan localmente si `voice_storage_keep_files=true`.
- Los audios grabados del microfono se guardan localmente si `mic_save_recordings=true`.

Debe existir limpieza futura de grabaciones y audios de forma mas granular.
