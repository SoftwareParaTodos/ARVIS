import os
import subprocess
import sys

from config import ALLOWED_FOLDERS


def open_allowed_folder(folder_key: str) -> dict[str, str]:
    folder = ALLOWED_FOLDERS.get(folder_key)
    if folder is None:
        return {
            "message": "Carpeta bloqueada: no esta en la lista blanca.",
            "status": "blocked",
        }

    folder.mkdir(parents=True, exist_ok=True)

    try:
        if sys.platform.startswith("win"):
            os.startfile(folder)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(folder)], shell=False)
        else:
            subprocess.Popen(["xdg-open", str(folder)], shell=False)
    except OSError as error:
        return {
            "message": f"No se pudo abrir la carpeta permitida: {error}",
            "status": "error",
        }

    return {
        "message": f"Accion ejecutada: se abrio la carpeta {folder}.",
        "status": "executed",
    }
