from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlencode


DEFAULT_BACKEND_URL = "http://127.0.0.1:8000"
DEFAULT_TIMEOUT_SECONDS = 5


class ApiClient:
    """Small stdlib HTTP client used by the desktop app."""

    def __init__(
        self,
        base_url: str = DEFAULT_BACKEND_URL,
        timeout_seconds: int | float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.base_url = self._normalize_base_url(base_url)
        self.timeout_seconds = max(float(timeout_seconds), 0.5)

    def get_health(self) -> dict[str, Any]:
        return self._request("GET", "/health", timeout_seconds=2)

    def send_chat_message(self, message: str) -> dict[str, Any]:
        return self._request("POST", "/chat", {"message": message})

    def get_tools(self) -> dict[str, Any]:
        return self._request("GET", "/tools")

    def get_settings(self) -> dict[str, Any]:
        return self._request("GET", "/settings")

    def update_settings(self, data: dict[str, Any]) -> dict[str, Any]:
        return self._request("PATCH", "/settings", data)

    def get_ai_status(self) -> dict[str, Any]:
        return self._request("GET", "/ai/status")

    def get_ai_models(self) -> dict[str, Any]:
        return self._request("GET", "/ai/models", timeout_seconds=min(self.timeout_seconds, 5))

    def set_ai_model(self, model: str) -> dict[str, Any]:
        return self._request("POST", "/ai/model", {"model": model})

    def get_voice_status(self) -> dict[str, Any]:
        return self._request("GET", "/voice/status")

    def get_mic_status(self) -> dict[str, Any]:
        return self._request("GET", "/voice/mic/status")

    def get_mic_devices(self) -> dict[str, Any]:
        return self._request(
            "GET",
            "/voice/mic/devices",
            timeout_seconds=min(self.timeout_seconds, 5),
        )

    def generate_tts(self, text: str, speak_now: bool = False) -> dict[str, Any]:
        return self._request(
            "POST",
            "/voice/tts",
            {"text": text, "speak_now": speak_now},
        )

    def get_pending_actions(self, limit: int = 20) -> dict[str, Any]:
        query = urlencode({"limit": max(int(limit), 1)})
        return self._request("GET", f"/actions/pending?{query}")

    def confirm_action(self, action_id: int | str) -> dict[str, Any]:
        normalized_id = self._normalize_action_id(action_id)
        if normalized_id is None:
            return self._error("ID de accion invalido.")
        return self._request("POST", f"/actions/{normalized_id}/confirm")

    def cancel_action(self, action_id: int | str) -> dict[str, Any]:
        normalized_id = self._normalize_action_id(action_id)
        if normalized_id is None:
            return self._error("ID de accion invalido.")
        return self._request("POST", f"/actions/{normalized_id}/cancel")

    def record_mic_chat(
        self,
        duration_seconds: int = 5,
        speak_response: bool = False,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/voice/mic/chat",
            {
                "duration_seconds": duration_seconds,
                "speak_response": speak_response,
            },
        )

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        timeout_seconds: int | float | None = None,
    ) -> dict[str, Any]:
        data = None
        headers = {"Accept": "application/json"}

        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = urllib.request.Request(
            self._build_url(path),
            data=data,
            headers=headers,
            method=method,
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=timeout_seconds or self.timeout_seconds,
            ) as response:
                body = response.read().decode("utf-8")
                parsed = self._parse_json(body)
                if parsed["error"]:
                    return self._error(parsed["error"])
                return {"ok": True, "data": parsed["data"], "error": None}
        except urllib.error.HTTPError as error:
            return self._handle_http_error(error)
        except urllib.error.URLError as error:
            reason = getattr(error, "reason", error)
            if isinstance(reason, socket.timeout):
                return self._error("Timeout consultando backend")
            return self._error(f"Backend no disponible: {reason}")
        except TimeoutError:
            return self._error("Timeout consultando backend")
        except socket.timeout:
            return self._error("Timeout consultando backend")
        except Exception as error:
            return self._error(f"Error inesperado de conexion: {error}")

    def _handle_http_error(self, error: urllib.error.HTTPError) -> dict[str, Any]:
        try:
            body = error.read().decode("utf-8")
            parsed = self._parse_json(body)
            details = parsed["data"] if parsed["error"] is None else body
        except Exception:
            details = error.reason
        return self._error(f"HTTP {error.code}: {details}")

    def _build_url(self, path: str) -> str:
        normalized_path = path if path.startswith("/") else f"/{path}"
        return f"{self.base_url}{normalized_path}"

    @staticmethod
    def _parse_json(body: str) -> dict[str, Any]:
        if not body.strip():
            return {"data": {}, "error": None}
        try:
            return {"data": json.loads(body), "error": None}
        except json.JSONDecodeError as error:
            return {"data": {}, "error": f"JSON invalido recibido del backend: {error}"}

    @staticmethod
    def _normalize_base_url(base_url: str) -> str:
        candidate = (base_url or DEFAULT_BACKEND_URL).strip().rstrip("/")
        if not candidate:
            return DEFAULT_BACKEND_URL
        return candidate

    @staticmethod
    def _normalize_action_id(action_id: int | str) -> int | None:
        try:
            normalized = int(action_id)
        except (TypeError, ValueError):
            return None
        return normalized if normalized > 0 else None

    @staticmethod
    def _error(message: str) -> dict[str, Any]:
        return {"ok": False, "data": {}, "error": message}
