from dataclasses import dataclass
from unicodedata import combining, normalize


@dataclass(frozen=True)
class Intent:
    name: str
    tool: str | None = None


def detect_intent(message: str) -> Intent:
    normalized = _normalize_message(message)

    if normalized in {"ayuda", "que podes hacer", "que puedes hacer", "herramientas", "comandos"}:
        return Intent(name="help")

    if "abrir bloc de notas" in normalized or "abrir notepad" in normalized:
        return Intent(name="open_notepad", tool="open_program")

    if "abrir calculadora" in normalized or "abrir calc" in normalized:
        return Intent(name="open_calculator", tool="open_program")

    if "abrir descargas" in normalized or "abrir carpeta descargas" in normalized:
        return Intent(name="open_downloads", tool="open_folder")

    if "crear nota" in normalized or "guardar nota" in normalized:
        return Intent(name="create_note", tool="notes")

    if "info del sistema" in normalized or "informacion del sistema" in normalized:
        return Intent(name="system_info", tool="system_info")

    return Intent(name="chat")


def _normalize_message(message: str) -> str:
    without_accents = "".join(
        char
        for char in normalize("NFD", message.lower().strip())
        if not combining(char)
    )
    return " ".join(without_accents.split())
