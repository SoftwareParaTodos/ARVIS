ARVIS v0.3.0 - Interfaz HUD inicial

Contenido:
- desktop_app/main.py
- desktop_app/run_desktop.bat
- desktop_app/requirements.txt
- desktop_app/ui/theme.py
- desktop_app/ui/hud_core.py
- desktop_app/ui/panels.py
- desktop_app/ui/arvis_window.py

Cómo instalar:
1. Descomprimir este ZIP.
2. Copiar la carpeta desktop_app dentro de C:\ARVIS.
   Debe quedar así:
   C:\ARVIS\desktop_app

Cómo ejecutar:
1. Abrir PowerShell o el Explorador.
2. Entrar en:
   C:\ARVIS\desktop_app
3. Ejecutar:
   run_desktop.bat

Atajos:
- F11: pantalla completa.
- ESC: salir de pantalla completa.

Notas:
- La interfaz funciona aunque el backend no esté encendido.
- Si el backend de ARVIS está corriendo en http://127.0.0.1:8000, el chat intenta usar /chat.
- Esta versión es visual/funcional inicial. Todavía no trae voz real completa.
