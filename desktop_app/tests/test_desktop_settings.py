from services import desktop_settings


def test_load_desktop_settings_creates_file(tmp_path, monkeypatch) -> None:
    settings_path = tmp_path / "desktop_settings.json"
    monkeypatch.setattr(desktop_settings, "SETTINGS_PATH", settings_path)

    settings = desktop_settings.load_desktop_settings()

    assert settings_path.exists()
    assert settings["backend_base_url"] == "http://127.0.0.1:8000"
    assert settings["request_timeout_seconds"] == 5
    assert settings["compact_mode_enabled"] is False
    assert settings["always_on_top"] is False
    assert settings["minimize_to_tray"] is True
    assert settings["ui_mode"] == "easy"


def test_save_desktop_settings_sanitizes_values(tmp_path, monkeypatch) -> None:
    settings_path = tmp_path / "desktop_settings.json"
    monkeypatch.setattr(desktop_settings, "SETTINGS_PATH", settings_path)

    settings = desktop_settings.save_desktop_settings(
        {
            "backend_base_url": "http://127.0.0.1:9000/",
            "request_timeout_seconds": 2,
            "auto_refresh_status": False,
            "auto_refresh_interval_seconds": 20,
            "compact_mode_enabled": True,
            "always_on_top": True,
            "minimize_to_tray": False,
            "ui_mode": "advanced",
        }
    )

    assert settings["backend_base_url"] == "http://127.0.0.1:9000"
    assert settings["request_timeout_seconds"] == 2
    assert settings["auto_refresh_status"] is False
    assert settings["auto_refresh_interval_seconds"] == 20
    assert settings["compact_mode_enabled"] is True
    assert settings["always_on_top"] is True
    assert settings["minimize_to_tray"] is False
    assert settings["ui_mode"] == "advanced"
