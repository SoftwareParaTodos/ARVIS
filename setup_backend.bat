@echo off
setlocal

cd /d "%~dp0backend"
if errorlevel 1 goto error

if not exist ".venv\Scripts\activate.bat" (
    echo Creando entorno virtual en backend\.venv...
    python -m venv .venv
    if errorlevel 1 goto error
) else (
    echo Entorno virtual existente detectado.
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 goto error

python -m pip install --upgrade pip
if errorlevel 1 goto error

pip install -r requirements.txt
if errorlevel 1 goto error

echo.
echo Instalacion completada.
echo Para iniciar ARVIS ejecuta run_backend.bat desde C:\ARVIS.
goto end

:error
echo.
echo Ocurrio un error durante la instalacion del backend de ARVIS.
pause

:end
endlocal
