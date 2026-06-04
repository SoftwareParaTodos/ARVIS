from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DESKTOP_VERSION = "0.4.4.1"
DESKTOP_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = DESKTOP_DIR.parent
SETTINGS_PATH = DESKTOP_DIR / "config" / "desktop_settings.json"

DEFAULT_DESKTOP_SETTINGS: dict[str, Any] = {
    "backend_base_url": "http://127.0.0.1:8000",
    "request_timeout_seconds": 5,
    "auto_refresh_status": True,
    "auto_refresh_interval_seconds": 15,
    "compact_mode_enabled": False,
    "always_on_top": False,
    "minimize_to_tray": True,
    "ui_mode": "easy",
}


def load_desktop_settings() -> dict[str, Any]:
    settings = DEFAULT_DESKTOP_SETTINGS.copy()

    if SETTINGS_PATH.exists():
        try:
            loaded = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                settings.update(_sanitize_settings(loaded))
        except Exception:
            pass

    save_desktop_settings(settings)
    return settings


def save_desktop_settings(data: dict[str, Any]) -> dict[str, Any]:
    settings = DEFAULT_DESKTOP_SETTINGS.copy()
    settings.update(_sanitize_settings(data))
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return settings


def _sanitize_settings(data: dict[str, Any]) -> dict[str, Any]:
    clean: dict[str, Any] = {}

    backend_base_url = data.get("backend_base_url")
    if isinstance(backend_base_url, str) and backend_base_url.strip():
        clean["backend_base_url"] = backend_base_url.strip().rstrip("/")

    timeout = data.get("request_timeout_seconds")
    if isinstance(timeout, (int, float)) and timeout > 0:
        clean["request_timeout_seconds"] = int(timeout)

    auto_refresh = data.get("auto_refresh_status")
    if isinstance(auto_refresh, bool):
        clean["auto_refresh_status"] = auto_refresh

    interval = data.get("auto_refresh_interval_seconds")
    if isinstance(interval, (int, float)) and interval >= 3:
        clean["auto_refresh_interval_seconds"] = int(interval)

    compact_mode = data.get("compact_mode_enabled")
    if isinstance(compact_mode, bool):
        clean["compact_mode_enabled"] = compact_mode

    always_on_top = data.get("always_on_top")
    if isinstance(always_on_top, bool):
        clean["always_on_top"] = always_on_top

    minimize_to_tray = data.get("minimize_to_tray")
    if isinstance(minimize_to_tray, bool):
        clean["minimize_to_tray"] = minimize_to_tray

    ui_mode = data.get("ui_mode")
    if ui_mode in {"easy", "advanced"}:
        clean["ui_mode"] = ui_mode

    return clean
