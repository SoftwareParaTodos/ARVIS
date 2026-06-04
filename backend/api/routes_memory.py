from fastapi import APIRouter, Query

from assistant.memory import get_recent_interactions


router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/recent")
def recent_memory(limit: int = Query(default=10, ge=1, le=100)) -> dict[str, object]:
    return {
        "limit": limit,
        "items": get_recent_interactions(limit),
    }
