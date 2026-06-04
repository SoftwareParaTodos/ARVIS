import platform
import socket
import sys


def get_system_info() -> dict[str, object]:
    data = {
        "os": platform.system(),
        "os_version": platform.version(),
        "python_version": sys.version.split()[0],
        "architecture": platform.machine(),
        "hostname": socket.gethostname(),
    }

    return {
        "message": "Informacion basica del sistema obtenida.",
        "status": "executed",
        "data": data,
    }
