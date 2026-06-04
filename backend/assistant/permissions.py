from enum import Enum


class PermissionLevel(str, Enum):
    SAFE = "safe"
    CONFIRMATION_REQUIRED = "confirmation_required"
    BLOCKED = "blocked"


SAFE_INTENTS = {
    "open_notepad",
    "open_calculator",
    "open_downloads",
    "create_note",
    "system_info",
}

CONFIRMATION_REQUIRED_KEYWORDS = (
    "borrar archivo",
    "borrar archivos",
    "eliminar archivo",
    "eliminar archivos",
    "mover archivo",
    "mover archivos",
    "sobrescribir documento",
    "sobrescribir documentos",
    "enviar mensaje",
    "enviar mensajes",
    "ejecutar comando del sistema",
    "ejecutar comandos del sistema",
    "instalar programa",
    "instalar programas",
    "cerrar aplicacion",
    "cerrar aplicaciones",
    "cerrar programa",
    "cerrar programas",
    "modificar configuracion",
    "modificar configuraciones",
    "cambiar configuracion",
    "configuracion sensible",
    "acceder a carpeta",
    "acceder a carpetas",
    "carpeta no autorizada",
    "subir informacion",
    "subir datos",
)

BLOCKED_KEYWORDS = (
    "comando libre",
    "ejecutar comando libre",
    "ejecutar comandos libres",
    "borrar masivo",
    "eliminar masivo",
    "formatear disco",
    "formatear unidad",
    "desactivar seguridad",
    "deshabilitar seguridad",
    "acceder a credenciales",
    "robar credenciales",
    "exfiltrar datos",
    "extraer datos",
    "cmd",
    "powershell",
)


def classify_permission(intent: str | None, message: str) -> PermissionLevel:
    normalized = message.lower().strip()

    if any(keyword in normalized for keyword in BLOCKED_KEYWORDS):
        return PermissionLevel.BLOCKED

    if any(keyword in normalized for keyword in CONFIRMATION_REQUIRED_KEYWORDS):
        return PermissionLevel.CONFIRMATION_REQUIRED

    if intent in SAFE_INTENTS:
        return PermissionLevel.SAFE

    return PermissionLevel.SAFE
