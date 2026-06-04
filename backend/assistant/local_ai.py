from typing import Any

import requests

from assistant.settings import get_settings, update_settings


def _empty_response(
    available: bool,
    error: str | None = None,
    settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    settings = settings or get_settings()
    return {
        "available": available,
        "model": settings["ollama_model"],
        "response": None,
        "error": error,
    }


def is_ollama_available(timeout_seconds: float = 1.0) -> bool:
    settings = get_settings()
    if not settings["ollama_enabled"]:
        return False

    try:
        response = requests.get(
            f"{settings['ollama_base_url']}/api/tags",
            timeout=timeout_seconds,
        )
        return response.status_code == 200
    except requests.RequestException:
        return False


def get_ollama_status(timeout_seconds: float = 1.0) -> dict[str, Any]:
    settings = get_settings()
    if not settings["ollama_enabled"]:
        return {
            "enabled": False,
            "available": False,
            "base_url": settings["ollama_base_url"],
            "model": settings["ollama_model"],
            "timeout_seconds": settings["ollama_timeout_seconds"],
            "error": "IA local desactivada en configuracion",
        }

    try:
        response = requests.get(
            f"{settings['ollama_base_url']}/api/tags",
            timeout=timeout_seconds,
        )
        if response.status_code != 200:
            return {
                "enabled": True,
                "available": False,
                "base_url": settings["ollama_base_url"],
                "model": settings["ollama_model"],
                "timeout_seconds": settings["ollama_timeout_seconds"],
                "error": f"Ollama respondio con estado HTTP {response.status_code}.",
            }

        return {
            "enabled": True,
            "available": True,
            "base_url": settings["ollama_base_url"],
            "model": settings["ollama_model"],
            "timeout_seconds": settings["ollama_timeout_seconds"],
            "error": None,
        }
    except requests.Timeout:
        return {
            "enabled": True,
            "available": False,
            "base_url": settings["ollama_base_url"],
            "model": settings["ollama_model"],
            "timeout_seconds": settings["ollama_timeout_seconds"],
            "error": "Timeout al consultar Ollama.",
        }
    except requests.RequestException as error:
        return {
            "enabled": True,
            "available": False,
            "base_url": settings["ollama_base_url"],
            "model": settings["ollama_model"],
            "timeout_seconds": settings["ollama_timeout_seconds"],
            "error": str(error),
        }


def get_ollama_models(timeout_seconds: float = 3.0) -> dict[str, Any]:
    settings = get_settings()
    if not settings["ollama_enabled"]:
        return {
            "available": False,
            "current_model": settings["ollama_model"],
            "models": [],
            "error": "IA local desactivada en configuracion",
        }

    try:
        response = requests.get(
            f"{settings['ollama_base_url']}/api/tags",
            timeout=timeout_seconds,
        )
        if response.status_code != 200:
            return {
                "available": False,
                "current_model": settings["ollama_model"],
                "models": [],
                "error": f"Ollama respondio con estado HTTP {response.status_code}.",
            }

        data = response.json()
        models = [
            item["name"]
            for item in data.get("models", [])
            if isinstance(item, dict) and isinstance(item.get("name"), str)
        ]
        return {
            "available": True,
            "current_model": settings["ollama_model"],
            "models": models,
            "error": None,
        }
    except requests.Timeout:
        return {
            "available": False,
            "current_model": settings["ollama_model"],
            "models": [],
            "error": "Timeout al consultar Ollama.",
        }
    except requests.RequestException as error:
        return {
            "available": False,
            "current_model": settings["ollama_model"],
            "models": [],
            "error": str(error),
        }
    except ValueError:
        return {
            "available": False,
            "current_model": settings["ollama_model"],
            "models": [],
            "error": "Ollama devolvio una respuesta invalida.",
        }


def set_ollama_model(model: str) -> dict[str, Any]:
    model = model.strip()
    settings = update_settings({"ollama_model": model})
    models_status = get_ollama_models()
    details: dict[str, Any] = {
        "verified": False,
        "warning": None,
        "models": models_status["models"],
    }

    if models_status["available"]:
        details["verified"] = model in models_status["models"]
        if not details["verified"]:
            details["warning"] = (
                "Ollama esta disponible, pero el modelo no aparece instalado. "
                "No se descargara automaticamente en esta version."
            )
    else:
        details["warning"] = (
            "Modelo guardado, pero no se pudo verificar porque Ollama no esta disponible."
        )

    return {
        "settings": settings,
        "ai_status": get_ollama_status(),
        "details": details,
    }


def ask_ollama(
    message: str,
    system_prompt: str | None = None,
    conversation_context: str | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    if not settings["ollama_enabled"]:
        return _empty_response(
            available=False,
            error="IA local desactivada en configuracion",
            settings=settings,
        )

    prompt = message
    if conversation_context:
        prompt = f"Contexto reciente:\n{conversation_context}\n\nMensaje actual:\n{message}"

    payload: dict[str, Any] = {
        "model": settings["ollama_model"],
        "prompt": prompt,
        "stream": False,
    }
    if system_prompt:
        payload["system"] = system_prompt

    try:
        response = requests.post(
            f"{settings['ollama_base_url']}/api/generate",
            json=payload,
            timeout=settings["ollama_timeout_seconds"],
        )
        if response.status_code != 200:
            return _empty_response(
                available=False,
                error=f"Ollama respondio con estado HTTP {response.status_code}.",
                settings=settings,
            )

        data = response.json()
        generated_text = data.get("response")
        if not isinstance(generated_text, str) or not generated_text.strip():
            return _empty_response(
                available=True,
                error="Ollama no devolvio una respuesta de texto.",
                settings=settings,
            )

        return {
            "available": True,
            "model": settings["ollama_model"],
            "response": generated_text.strip(),
            "error": None,
        }
    except requests.Timeout:
        return _empty_response(
            available=False,
            error="Timeout al consultar Ollama.",
            settings=settings,
        )
    except requests.RequestException as error:
        return _empty_response(available=False, error=str(error), settings=settings)
    except ValueError:
        return _empty_response(
            available=False,
            error="Ollama devolvio una respuesta invalida.",
            settings=settings,
        )
