import subprocess

from config import ALLOWED_PROGRAMS


def open_allowed_program(program_key: str) -> dict[str, str]:
    program = ALLOWED_PROGRAMS.get(program_key)
    if program is None:
        return {
            "message": "Programa bloqueado: no esta en la lista blanca.",
            "status": "blocked",
        }

    try:
        subprocess.Popen([program], shell=False)
    except OSError as error:
        return {
            "message": f"No se pudo abrir el programa permitido: {error}",
            "status": "error",
        }

    return {
        "message": f"Accion ejecutada: se abrio {program}.",
        "status": "executed",
    }
