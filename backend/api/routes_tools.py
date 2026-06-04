from fastapi import APIRouter


router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("")
def list_tools() -> list[dict[str, object]]:
    return [
        {
            "name": "open_program",
            "description": "Abre programas permitidos por lista blanca.",
            "permission_level": "safe",
            "examples": ["abrir calculadora", "abrir bloc de notas"],
        },
        {
            "name": "open_folder",
            "description": "Abre carpetas permitidas por lista blanca.",
            "permission_level": "safe",
            "examples": ["abrir descargas"],
        },
        {
            "name": "notes",
            "description": "Crea notas simples en la carpeta autorizada de ARVIS.",
            "permission_level": "safe",
            "examples": ["crear nota comprar leche", "guardar nota llamar manana"],
        },
        {
            "name": "system_info",
            "description": "Devuelve informacion basica del sistema.",
            "permission_level": "safe",
            "examples": ["info del sistema", "informacion del sistema"],
        },
        {
            "name": "ai_chat",
            "description": "Capacidad conversacional con Ollama cuando esta disponible. No ejecuta herramientas directamente.",
            "permission_level": "safe",
            "examples": ["hola arvis", "explicame como funciona el backend"],
        },
        {
            "name": "settings",
            "description": "Capacidad del backend para leer y actualizar configuracion segura.",
            "permission_level": "safe",
            "examples": ["GET /settings", "PATCH /settings"],
        },
        {
            "name": "ai_models",
            "description": "Capacidad del backend para listar modelos locales y seleccionar el modelo activo.",
            "permission_level": "safe",
            "examples": ["GET /ai/models", "POST /ai/model"],
        },
        {
            "name": "pending_actions",
            "description": "Lista acciones riesgosas pendientes de confirmacion.",
            "permission_level": "safe",
            "examples": ["GET /actions/pending"],
        },
        {
            "name": "confirm_action",
            "description": "Confirma una accion pendiente sin saltarse permisos ni listas blancas.",
            "permission_level": "confirmation_required",
            "examples": ["confirmar accion 3", "POST /actions/3/confirm"],
        },
        {
            "name": "cancel_action",
            "description": "Cancela una accion pendiente.",
            "permission_level": "safe",
            "examples": ["cancelar accion 3", "POST /actions/3/cancel"],
        },
        {
            "name": "voice_stt",
            "description": "Transcribe audio a texto. La transcripcion no evita permisos ni confirmaciones.",
            "permission_level": "safe",
            "examples": ["POST /voice/stt"],
        },
        {
            "name": "voice_tts",
            "description": "Genera audio desde texto si TTS esta disponible.",
            "permission_level": "safe",
            "examples": ["POST /voice/tts"],
        },
        {
            "name": "voice_chat",
            "description": "Transcribe audio, pasa el texto por brain.py y devuelve respuesta segura.",
            "permission_level": "safe",
            "examples": ["POST /voice/chat"],
        },
        {
            "name": "microphone_status",
            "description": "Consulta estado del microfono. No inicia grabacion.",
            "permission_level": "safe",
            "examples": ["GET /voice/mic/status", "GET /voice/mic/devices"],
        },
        {
            "name": "microphone_record",
            "description": "Graba microfono por una duracion limitada y explicita.",
            "permission_level": "safe",
            "examples": ["POST /voice/mic/record"],
        },
        {
            "name": "microphone_chat",
            "description": "Graba, transcribe y procesa por brain.py. No evita permisos ni confirmaciones.",
            "permission_level": "safe",
            "examples": ["POST /voice/mic/chat"],
        },
    ]
