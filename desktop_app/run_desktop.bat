@echo off
cd /d "%~dp0"

echo.
echo =========================================
echo        ARVIS Desktop - Interfaz HUD
echo =========================================
echo.

if not exist ".venv" (
    echo [ARVIS] No se encontro .venv. Creando entorno virtual local...
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo [ERROR] No se pudo crear el entorno virtual.
        echo Verifica que Python este instalado y disponible en PATH.
        goto error
    )
) else (
    echo [ARVIS] Entorno virtual existente detectado.
)

call .venv\Scripts\activate
if errorlevel 1 (
    echo.
    echo [ERROR] No se pudo activar .venv.
    goto error
)

echo [ARVIS] Actualizando pip...
python -m pip install --upgrade pip
if errorlevel 1 goto error

echo [ARVIS] Instalando dependencias de escritorio...
pip install -r requirements.txt
if errorlevel 1 goto error

echo.
echo [ARVIS] Iniciando interfaz de escritorio...
python main.py
if errorlevel 1 goto error

goto end

:error
echo.
echo [ARVIS] La interfaz no pudo iniciar. Revisa el mensaje anterior.
echo.
pause
exit /b 1

:end
pause
