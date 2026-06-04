from pathlib import Path

from services.diagnostics import build_diagnostic_report


def test_diagnostic_report_excludes_full_chat_content() -> None:
    report = build_diagnostic_report(
        desktop_version="0.4.4",
        backend_url="http://127.0.0.1:8000",
        backend_online=False,
        health={"version": "0.4.4"},
        ai_status={"available": False, "model": "llama3.2"},
        voice_status={"voice_enabled": True},
        mic_status={"available": False},
        pending_count=0,
        project_dir=Path("C:/ARVIS"),
        storage_dir=Path("C:/ARVIS/backend/storage"),
        desktop_config_path=Path("C:/ARVIS/desktop_app/config/desktop_settings.json"),
        log_entries=["<b>chat</b> enviado: ayuda"],
        last_error="Backend no disponible.",
    )

    assert "Desktop version: 0.4.4" in report
    assert "Backend no disponible." in report
    assert "<b>" not in report
    assert "contenido completo del chat" not in report
