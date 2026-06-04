from services.api_client import ApiClient


def test_api_client_builds_urls_without_double_slashes() -> None:
    client = ApiClient("http://127.0.0.1:8000/")

    assert client._build_url("/health") == "http://127.0.0.1:8000/health"
    assert client._build_url("tools") == "http://127.0.0.1:8000/tools"


def test_send_chat_message_uses_consistent_response(monkeypatch) -> None:
    client = ApiClient()
    calls = []

    def fake_request(method, path, payload=None, **kwargs):
        calls.append((method, path, payload))
        return {"ok": True, "data": {"status": "response"}, "error": None}

    monkeypatch.setattr(client, "_request", fake_request)

    result = client.send_chat_message("info del sistema")

    assert result["ok"] is True
    assert result["error"] is None
    assert calls == [("POST", "/chat", {"message": "info del sistema"})]


def test_voice_and_mic_helpers_use_consistent_response(monkeypatch) -> None:
    client = ApiClient()
    calls = []

    def fake_request(method, path, payload=None, **kwargs):
        calls.append((method, path, payload))
        return {"ok": True, "data": {}, "error": None}

    monkeypatch.setattr(client, "_request", fake_request)

    assert client.get_mic_devices()["ok"] is True
    assert client.generate_tts("Hola")["ok"] is True
    assert calls == [
        ("GET", "/voice/mic/devices", None),
        ("POST", "/voice/tts", {"text": "Hola", "speak_now": False}),
    ]


def test_api_client_handles_backend_down() -> None:
    client = ApiClient("http://127.0.0.1:9", timeout_seconds=0.5)

    result = client.get_health()

    assert result["ok"] is False
    assert result["data"] == {}
    assert result["error"]
