from fastapi import APIRouter, Query

from assistant.brain import cancel_action_by_id, confirm_action_by_id
from assistant.pending_actions import clear_resolved_pending_actions, list_pending_actions


router = APIRouter(prefix="/actions", tags=["actions"])


@router.get("/pending")
def pending_actions(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, object]:
    return {
        "status": "ok",
        "actions": list_pending_actions(limit),
    }


@router.post("/{action_id}/confirm")
def confirm_action(action_id: int) -> dict[str, object]:
    return confirm_action_by_id(action_id)


@router.post("/{action_id}/cancel")
def cancel_action(action_id: int) -> dict[str, object]:
    return cancel_action_by_id(action_id)


@router.post("/clear-resolved")
def clear_resolved_actions() -> dict[str, object]:
    deleted_count = clear_resolved_pending_actions()
    return {
        "status": "ok",
        "deleted_count": deleted_count,
    }
