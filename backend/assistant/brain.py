import re
from typing import Any

from assistant.local_ai import ask_ollama
from assistant.memory import get_recent_interactions, save_interaction
from assistant.pending_actions import (
    BLOCKED,
    CANCELLED,
    CONFIRMED,
    EXPIRED,
    PENDING,
    block_pending_action,
    cancel_pending_action,
    confirm_pending_action,
    create_pending_action,
    expire_old_pending_actions,
    get_pending_action,
    list_pending_actions,
)
from assistant.permissions import PermissionLevel, classify_permission
from assistant.router import detect_intent
from assistant.prompts import ARVIS_SYSTEM_PROMPT, HELP_RESPONSE, UNKNOWN_INTENT_RESPONSE
from assistant.settings import get_settings
from tools.notes import create_note
from tools.open_folder import open_allowed_folder
from tools.open_program import open_allowed_program
from tools.system_info import get_system_info


def handle_message(message: str) -> dict[str, Any]:
    clean_message = message.strip()
    pending_resolution = _handle_pending_resolution(clean_message)
    if pending_resolution is not None:
        return pending_resolution

    intent = detect_intent(clean_message)
    permission = classify_permission(intent.name, clean_message)

    tool_used: str | None = intent.tool
    status = "response"
    response: dict[str, Any]

    if permission == PermissionLevel.BLOCKED:
        status = "blocked"
        response = {
            "message": (
                "Accion bloqueada por seguridad. ARVIS no borra, mueve archivos, "
                "instala programas ni ejecuta comandos libres del sistema."
            ),
            "status": status,
        }
    elif permission == PermissionLevel.CONFIRMATION_REQUIRED:
        status = "confirmation_required"
        pending_action = create_pending_action(
            original_message=clean_message,
            detected_intent=intent.name,
            requested_tool=tool_used,
            parameters={},
            risk_level=permission.value,
        )
        response = {
            "message": (
                "Esta accion puede afectar el sistema y requiere confirmacion. "
                f"Cree la accion pendiente #{pending_action.get('id')}. "
                "Para continuar, escribi por ejemplo: confirmar accion "
                f"{pending_action.get('id')}. Para cancelarla: cancelar accion "
                f"{pending_action.get('id')}."
            ),
            "status": status,
            "data": {"pending_action": pending_action},
        }
    elif intent.name == "help":
        tool_used = None
        response = {
            "message": HELP_RESPONSE,
            "status": "response",
        }
    else:
        try:
            if intent.name == "open_notepad":
                response = open_allowed_program("notepad")
            elif intent.name == "open_calculator":
                response = open_allowed_program("calculator")
            elif intent.name == "open_downloads":
                response = open_allowed_folder("downloads")
            elif intent.name == "create_note":
                response = create_note(clean_message)
            elif intent.name == "system_info":
                response = get_system_info()
            else:
                tool_used = None
                ai_response = ask_ollama(
                    clean_message,
                    ARVIS_SYSTEM_PROMPT,
                    _build_conversation_context(),
                )
                if ai_response["available"] and ai_response["response"]:
                    response = {
                        "message": ai_response["response"],
                        "status": "response",
                        "data": {"ai": ai_response},
                    }
                else:
                    response = {
                        "message": UNKNOWN_INTENT_RESPONSE,
                        "status": "response",
                        "data": {"ai": ai_response},
                    }
        except Exception as error:
            response = {
                "message": f"La herramienta fallo de forma controlada: {error}",
                "status": "error",
            }

        status = response.get("status", "response")

    assistant_response = response.get("message", str(response))
    save_interaction(
        user_message=clean_message,
        detected_intent=intent.name,
        tool_used=tool_used,
        assistant_response=assistant_response,
        action_status=status,
    )

    return {
        "status": status,
        "message": assistant_response,
        "intent": intent.name,
        "tool": tool_used,
        "requires_confirmation": permission == PermissionLevel.CONFIRMATION_REQUIRED,
        "risk_level": permission.value,
        "details": response.get("data", {}),
    }


def confirm_action_by_id(action_id: int) -> dict[str, Any]:
    expire_old_pending_actions()
    action = get_pending_action(action_id)
    if action is None:
        return _action_response(
            status="error",
            message=f"No encontre una accion pendiente con ID {action_id}.",
            intent="confirm_pending_action",
            details={"action_id": action_id},
        )

    if action["status"] == EXPIRED:
        return _action_response(
            status="error",
            message=(
                f"La accion pendiente #{action_id} vencio. Pedila nuevamente si "
                "todavia la necesitas."
            ),
            intent="confirm_pending_action",
            details={"pending_action": action},
        )

    if action["status"] != PENDING:
        return _action_response(
            status="error",
            message=(
                f"La accion #{action_id} ya no esta pendiente. Estado actual: "
                f"{action['status']}."
            ),
            intent="confirm_pending_action",
            details={"pending_action": action},
        )

    permission = classify_permission(
        action["detected_intent"],
        action["original_message"],
    )
    if permission == PermissionLevel.BLOCKED:
        block_pending_action(action_id)
        message = "La accion quedo bloqueada al revalidar permisos."
        _audit_action(action["original_message"], action["detected_intent"], action["requested_tool"], message, "blocked")
        return _action_response(
            status="blocked",
            message=message,
            intent=action["detected_intent"],
            tool=action["requested_tool"],
            risk_level=permission.value,
            details={"pending_action": get_pending_action(action_id)},
        )

    if action["requested_tool"] is None:
        confirmed = confirm_pending_action(action_id)
        message = (
            "La accion fue confirmada, pero no existe una herramienta segura "
            "implementada para ejecutarla."
        )
        _audit_action(action["original_message"], action["detected_intent"], None, message, "error")
        return _action_response(
            status="error",
            message=message,
            intent=action["detected_intent"],
            tool=None,
            risk_level=permission.value,
            details={"pending_action": confirmed},
        )

    if permission != PermissionLevel.SAFE:
        confirmed = confirm_pending_action(action_id)
        message = (
            "La accion fue confirmada, pero no se ejecuta porque no hay una "
            "herramienta segura habilitada para este riesgo."
        )
        _audit_action(action["original_message"], action["detected_intent"], action["requested_tool"], message, "error")
        return _action_response(
            status="error",
            message=message,
            intent=action["detected_intent"],
            tool=action["requested_tool"],
            risk_level=permission.value,
            details={"pending_action": confirmed},
        )

    try:
        tool_response = _run_tool(action["detected_intent"], action["original_message"])
        confirmed = confirm_pending_action(action_id)
        status = tool_response.get("status", "response")
        message = tool_response.get("message", str(tool_response))
        _audit_action(action["original_message"], action["detected_intent"], action["requested_tool"], message, status)
        return _action_response(
            status=status,
            message=message,
            intent=action["detected_intent"],
            tool=action["requested_tool"],
            risk_level=permission.value,
            details={"pending_action": confirmed, "tool": tool_response.get("data", {})},
        )
    except Exception as error:
        message = f"La herramienta fallo de forma controlada: {error}"
        _audit_action(action["original_message"], action["detected_intent"], action["requested_tool"], message, "error")
        return _action_response(
            status="error",
            message=message,
            intent=action["detected_intent"],
            tool=action["requested_tool"],
            risk_level=permission.value,
            details={"pending_action": action},
        )


def cancel_action_by_id(action_id: int) -> dict[str, Any]:
    expire_old_pending_actions()
    action = get_pending_action(action_id)
    if action is None:
        return _action_response(
            status="error",
            message=f"No encontre una accion pendiente con ID {action_id}.",
            intent="cancel_pending_action",
            details={"action_id": action_id},
        )

    if action["status"] != PENDING:
        return _action_response(
            status="error",
            message=(
                f"La accion #{action_id} no se puede cancelar porque su estado "
                f"actual es {action['status']}."
            ),
            intent="cancel_pending_action",
            details={"pending_action": action},
        )

    cancelled = cancel_pending_action(action_id)
    message = f"Accion pendiente #{action_id} cancelada."
    _audit_action(action["original_message"], action["detected_intent"], action["requested_tool"], message, CANCELLED)
    return _action_response(
        status="response",
        message=message,
        intent="cancel_pending_action",
        details={"pending_action": cancelled},
    )


def _handle_pending_resolution(message: str) -> dict[str, Any] | None:
    normalized = _normalize_text(message)
    action_id = _extract_action_id(normalized)

    if _is_confirmation_message(normalized):
        return _resolve_from_message(action_id, confirm=True)

    if _is_cancellation_message(normalized):
        return _resolve_from_message(action_id, confirm=False)

    return None


def _resolve_from_message(action_id: int | None, *, confirm: bool) -> dict[str, Any]:
    expire_old_pending_actions()
    if action_id is not None:
        return confirm_action_by_id(action_id) if confirm else cancel_action_by_id(action_id)

    pending = list_pending_actions(limit=2)
    if not pending:
        verb = "confirmar" if confirm else "cancelar"
        return _action_response(
            status="response",
            message=f"No hay acciones pendientes para {verb}.",
            intent="confirm_pending_action" if confirm else "cancel_pending_action",
        )

    if len(pending) > 1:
        ids = ", ".join(str(action["id"]) for action in pending)
        return _action_response(
            status="response",
            message=f"Hay varias acciones pendientes ({ids}). Indicame el ID.",
            intent="confirm_pending_action" if confirm else "cancel_pending_action",
            details={"pending_actions": pending},
        )

    target_id = int(pending[0]["id"])
    return confirm_action_by_id(target_id) if confirm else cancel_action_by_id(target_id)


def _run_tool(intent_name: str, message: str) -> dict[str, Any]:
    if intent_name == "open_notepad":
        return open_allowed_program("notepad")
    if intent_name == "open_calculator":
        return open_allowed_program("calculator")
    if intent_name == "open_downloads":
        return open_allowed_folder("downloads")
    if intent_name == "create_note":
        return create_note(message)
    if intent_name == "system_info":
        return get_system_info()

    return {
        "message": "No existe una herramienta segura implementada para esta accion.",
        "status": "error",
    }


def _action_response(
    *,
    status: str,
    message: str,
    intent: str,
    tool: str | None = None,
    requires_confirmation: bool = False,
    risk_level: str = "safe",
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "message": message,
        "intent": intent,
        "tool": tool,
        "requires_confirmation": requires_confirmation,
        "risk_level": risk_level,
        "details": details or {},
    }


def _audit_action(
    user_message: str,
    detected_intent: str,
    tool_used: str | None,
    assistant_response: str,
    action_status: str,
) -> None:
    save_interaction(
        user_message=user_message,
        detected_intent=detected_intent,
        tool_used=tool_used,
        assistant_response=assistant_response,
        action_status=action_status,
    )


def _normalize_text(message: str) -> str:
    normalized = message.lower().strip()
    replacements = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "¿": "",
        "?": "",
        ",": "",
        ".": "",
    }
    for source, target in replacements.items():
        normalized = normalized.replace(source, target)
    return " ".join(normalized.split())


def _extract_action_id(message: str) -> int | None:
    match = re.search(r"\b(\d+)\b", message)
    return int(match.group(1)) if match else None


def _is_confirmation_message(message: str) -> bool:
    return message in {"confirmo", "si confirmar", "confirmar accion"} or (
        "confirmar accion" in message
        or "ejecutar accion pendiente" in message
    )


def _is_cancellation_message(message: str) -> bool:
    return message in {"cancelar", "cancelar accion", "no cancelar"} or (
        "cancelar accion" in message or "cancelar pendiente" in message
    )


def _build_conversation_context() -> str | None:
    try:
        settings = get_settings()
        if not settings["conversation_history_enabled"]:
            return None

        limit = settings["conversation_history_limit"]
        if limit <= 0:
            return None

        interactions = get_recent_interactions(limit)
    except Exception:
        return None

    lines: list[str] = []
    for interaction in reversed(interactions):
        user_message = interaction.get("user_message")
        assistant_response = interaction.get("assistant_response")
        if not user_message or not assistant_response:
            continue

        lines.append(f"Usuario: {user_message}")
        lines.append(f"ARVIS: {assistant_response}")

    return "\n".join(lines) if lines else None
