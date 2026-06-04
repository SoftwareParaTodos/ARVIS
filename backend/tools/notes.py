import re
from datetime import datetime

from config import NOTES_DIR


def _safe_filename(text: str) -> str:
    base = text.lower().strip()
    base = re.sub(r"^crear nota\s*", "", base)
    base = re.sub(r"[^a-z0-9]+", "-", base)
    base = base.strip("-")[:50]
    return base or "nota"


def _extract_note_content(message: str) -> str:
    content = re.sub(r"^crear nota\s*", "", message, flags=re.IGNORECASE).strip()
    return content or "Nota creada desde ARVIS."


def create_note(message: str) -> dict[str, str]:
    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    content = _extract_note_content(message)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{timestamp}-{_safe_filename(content)}.txt"
    note_path = NOTES_DIR / filename

    counter = 1
    while note_path.exists():
        note_path = NOTES_DIR / f"{timestamp}-{_safe_filename(content)}-{counter}.txt"
        counter += 1

    note_path.write_text(content + "\n", encoding="utf-8")

    return {
        "message": f"Accion ejecutada: nota creada en {note_path}.",
        "status": "executed",
    }
