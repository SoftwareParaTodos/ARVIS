import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import BinaryIO

from config import STORAGE_DIR


VOICE_STORAGE_DIR = STORAGE_DIR / "voice"
VOICE_INPUT_DIR = VOICE_STORAGE_DIR / "input"
VOICE_OUTPUT_DIR = VOICE_STORAGE_DIR / "output"
VOICE_TTS_DIR = VOICE_STORAGE_DIR / "tts"

ALLOWED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".mp4", ".webm", ".flac"}


def ensure_voice_storage() -> dict[str, Path]:
    for directory in (VOICE_INPUT_DIR, VOICE_OUTPUT_DIR, VOICE_TTS_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    return {
        "base": VOICE_STORAGE_DIR,
        "input": VOICE_INPUT_DIR,
        "output": VOICE_OUTPUT_DIR,
        "tts": VOICE_TTS_DIR,
    }


def ensure_voice_input_storage() -> Path:
    ensure_voice_storage()
    return VOICE_INPUT_DIR


def safe_audio_filename(original_name: str | None = None, extension: str = ".wav") -> str:
    extension = extension.lower()
    if extension not in ALLOWED_AUDIO_EXTENSIONS:
        extension = ".wav"

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    stem = "audio"
    if original_name:
        safe_stem = Path(original_name).stem.lower()
        safe_stem = "".join(char if char.isalnum() else "-" for char in safe_stem)
        safe_stem = "-".join(part for part in safe_stem.split("-") if part)[:40]
        stem = safe_stem or stem

    return f"{timestamp}-{stem}{extension}"


def safe_wav_filename(prefix: str = "recording") -> str:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    safe_prefix = "".join(char if char.isalnum() else "-" for char in prefix.lower())
    safe_prefix = "-".join(part for part in safe_prefix.split("-") if part)[:40]
    return f"{timestamp}-{safe_prefix or 'recording'}.wav"


def normalize_record_seconds(
    duration_seconds: int | None,
    default_seconds: int,
    max_seconds: int,
) -> int:
    if duration_seconds is None:
        return default_seconds

    if not isinstance(duration_seconds, int) or isinstance(duration_seconds, bool):
        return default_seconds

    return max(1, min(duration_seconds, max_seconds))


def build_voice_input_path(filename: str | None = None) -> Path:
    input_dir = ensure_voice_input_storage()
    candidate = input_dir / (filename or safe_wav_filename())

    if candidate.parent.resolve() != input_dir.resolve():
        candidate = input_dir / safe_wav_filename()

    if candidate.suffix.lower() != ".wav":
        candidate = candidate.with_suffix(".wav")

    counter = 1
    while candidate.exists():
        candidate = input_dir / f"{candidate.stem}-{counter}.wav"
        counter += 1

    return candidate


def validate_audio_extension(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_AUDIO_EXTENSIONS


def save_upload_file(file_obj: BinaryIO, filename: str) -> dict[str, str | None]:
    if not validate_audio_extension(filename):
        return {
            "path": None,
            "error": "Extension de audio no permitida.",
        }

    ensure_voice_storage()
    extension = Path(filename).suffix.lower()
    destination = VOICE_INPUT_DIR / safe_audio_filename(filename, extension)

    counter = 1
    while destination.exists():
        destination = VOICE_INPUT_DIR / f"{destination.stem}-{counter}{extension}"
        counter += 1

    with destination.open("wb") as output:
        shutil.copyfileobj(file_obj, output)

    return {
        "path": str(destination),
        "error": None,
    }


def cleanup_old_voice_files(days: int = 7) -> int:
    ensure_voice_storage()
    cutoff = datetime.now() - timedelta(days=max(1, days))
    deleted = 0

    for directory in (VOICE_INPUT_DIR, VOICE_OUTPUT_DIR, VOICE_TTS_DIR):
        for path in directory.iterdir():
            if not path.is_file():
                continue

            modified_at = datetime.fromtimestamp(path.stat().st_mtime)
            if modified_at < cutoff:
                path.unlink()
                deleted += 1

    return deleted
