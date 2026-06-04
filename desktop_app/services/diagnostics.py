from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any


TAG_RE = re.compile(r"<[^>]+>")


def build_diagnostic_report(
    *,
    desktop_version: str,
    backend_url: str,
    backend_online: bool,
    health: dict[str, Any] | None,
    ai_status: dict[str, Any] | None,
    voice_status: dict[str, Any] | None,
    mic_status: dict[str, Any] | None,
    pending_count: int,
    project_dir: Path,
    storage_dir: Path,
    desktop_config_path: Path,
    log_entries: list[str],
    last_error: str | None = None,
) -> str:
    health = health or {}
    ai_status = ai_status or {}
    voice_status = voice_status or {}
    mic_status = mic_status or {}
    recent_logs = [_clean_log_entry(entry) for entry in log_entries[-10:]]

    lines = [
        "ARVIS - Diagnostico de escritorio",
        f"Fecha/hora: {datetime.now().isoformat(timespec='seconds')}",
        f"Desktop version: {desktop_version}",
        f"Backend version: {health.get('version', '--')}",
        f"Backend URL: {backend_url}",
        f"Backend estado: {'conectado' if backend_online else 'desconectado'}",
        f"IA disponible: {ai_status.get('available', health.get('ai_available', '--'))}",
        f"Modelo actual: {ai_status.get('model', health.get('ai_model', '--'))}",
        f"Voz habilitada: {voice_status.get('voice_enabled', health.get('voice_enabled', '--'))}",
        f"STT disponible: {_nested_available(voice_status, 'stt', health.get('stt_available', '--'))}",
        f"TTS disponible: {_nested_available(voice_status, 'tts', health.get('tts_available', '--'))}",
        f"Microfono disponible: {mic_status.get('available', health.get('mic_available', '--'))}",
        f"Acciones pendientes: {pending_count}",
        f"Proyecto: {project_dir}",
        f"Storage: {storage_dir}",
        f"Config desktop: {desktop_config_path}",
        f"Ultimo error: {last_error or '--'}",
        "Ultimos eventos:",
    ]

    if recent_logs:
        lines.extend(f"- {entry}" for entry in recent_logs)
    else:
        lines.append("- sin eventos")

    return "\n".join(lines)


def _nested_available(data: dict[str, Any], key: str, fallback: Any) -> Any:
    item = data.get(key)
    if isinstance(item, dict):
        return item.get("available", fallback)
    return fallback


def _clean_log_entry(entry: str) -> str:
    without_tags = TAG_RE.sub("", entry)
    return " ".join(without_tags.split())[:180]
