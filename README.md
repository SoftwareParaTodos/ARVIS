# ARVIS [☕ Donar al proyecto] [https://cafecito.app/ar_transcription]

ARVIS es un asistente inteligente open source para computadora, pensado como una base real para construir un asistente personal moderno, modular, seguro y extensible.
________
⭐ Si te gusta el proyecto, dejá una estrella en GitHub y considerá apoyar el desarrollo con una donación.

[☕ Donar al proyecto] [((https://cafecito.app/ar_transcription))]


El objetivo del proyecto es crear un sistema capaz de recibir órdenes por texto o voz, interpretarlas con inteligencia artificial, ejecutar acciones permitidas en la computadora, responder al usuario y guardar memoria local, priorizando siempre la seguridad y el control del usuario.

La primera etapa del proyecto está enfocada en Windows, con backend en Python y FastAPI, memoria local con SQLite, sistema de permisos para herramientas, acciones seguras predefinidas e integración opcional con IA local mediante Ollama.

## Objetivo

ARVIS busca ser una alternativa abierta, local y personalizable a los asistentes tradicionales, evitando depender obligatoriamente de servicios externos. La idea es que cualquier usuario pueda instalarlo, configurarlo y ampliarlo según sus necesidades.

## Características iniciales

- Backend local con Python y FastAPI.
- Endpoints básicos para salud, chat, herramientas, memoria e IA.
- Memoria local usando SQLite.
- Sistema de permisos por nivel de riesgo.
- Herramientas seguras con lista blanca.
- Integración opcional con Ollama para IA local.
- Fallback seguro si la IA local no está disponible.
- Preparado para interfaz de escritorio.
- Estructura modular para futuras herramientas y plugins.

## Principios del proyecto

1. Primero hacerlo funcionar.
2. Después hacerlo seguro.
3. Después hacerlo lindo.
4. Después hacerlo inteligente.
5. Después hacerlo automático.

## Seguridad

ARVIS no ejecuta comandos libres del sistema de forma directa.  
Las acciones pasan por un sistema de permisos y herramientas definidas, con niveles de riesgo claros:

- Acciones seguras.
- Acciones que requieren confirmación.
- Acciones bloqueadas.

El modelo de IA puede interpretar y responder, pero no debe ejecutar acciones peligrosas sin pasar por el sistema de permisos.

## Tecnologías principales

- Python
- FastAPI
- SQLite
- Ollama
- PySide6 / PyQt6 para interfaz de escritorio
- Arquitectura modular por herramientas

## Licencia

Este proyecto está publicado bajo licencia MIT.
