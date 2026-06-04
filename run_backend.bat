@echo off
setlocal

cd /d "%~dp0backend"
if errorlevel 1 goto error

if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
) else (
    echo No se encontro el entorno virtual backend\.venv.
    echo Para crearlo, ejecuta setup_backend.bat desde la carpeta principal de ARVIS.
    echo Se intentara usar uvicorn disponible en el sistema.
)

uvicorn main:app --reload
if errorlevel 1 goto error

goto end

:error
echo.
echo Ocurrio un error al iniciar el backend de ARVIS.
pause

:end
endlocal
