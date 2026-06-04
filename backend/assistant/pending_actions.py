import json
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any

from assistant.memory import get_connection
from assistant.settings import get_settings


PENDING = "pending"
CONFIRMED = "confirmed"
CANCELLED = "cancelled"
EXPIRED = "expired"
BLOCKED = "blocked"
RESOLVED_STATUSES = {CONFIRMED, CANCELLED, EXPIRED, BLOCKED}


def init_pending_actions_db() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS pending_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                original_message TEXT NOT NULL,
                detected_intent TEXT NOT NULL,
                requested_tool TEXT,
                parameters TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                status TEXT NOT NULL,
                resolved_at TEXT
            )
            """
        )
        connection.commit()


def create_pending_action(
    *,
    original_message: str,
    detected_intent: str,
    requested_tool: str | None,
    parameters: dict[str, Any] | None,
    risk_level: str,
) -> dict[str, Any]:
    init_pending_actions_db()
    created_at = _now().isoformat()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO pending_actions (
                created_at,
                original_message,
                detected_intent,
                requested_tool,
                parameters,
                risk_level,
                status,
                resolved_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                original_message,
                detected_intent,
                requested_tool,
                json.dumps(parameters or {}, ensure_ascii=True),
                risk_level,
                PENDING,
                None,
            ),
        )
        connection.commit()
        action_id = int(cursor.lastrowid)

    action = get_pending_action(action_id)
    return action or {}


def get_pending_action(action_id: int) -> dict[str, Any] | None:
    init_pending_actions_db()

    with get_connection() as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT
                id,
                created_at,
                original_message,
                detected_intent,
                requested_tool,
                parameters,
                risk_level,
                status,
                resolved_at
            FROM pending_actions
            WHERE id = ?
            """,
            (action_id,),
        ).fetchone()

    return _row_to_action(row) if row else None


def list_pending_actions(limit: int = 20) -> list[dict[str, Any]]:
    init_pending_actions_db()
    expire_old_pending_actions()
    safe_limit = max(1, min(limit, 100))

    with get_connection() as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT
                id,
                created_at,
                original_message,
                detected_intent,
                requested_tool,
                parameters,
                risk_level,
                status,
                resolved_at
            FROM pending_actions
            WHERE status = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (PENDING, safe_limit),
        ).fetchall()

    return [_row_to_action(row) for row in rows]


def list_actions(limit: int = 20) -> list[dict[str, Any]]:
    init_pending_actions_db()
    expire_old_pending_actions()
    safe_limit = max(1, min(limit, 100))

    with get_connection() as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT
                id,
                created_at,
                original_message,
                detected_intent,
                requested_tool,
                parameters,
                risk_level,
                status,
                resolved_at
            FROM pending_actions
            ORDER BY id DESC
            LIMIT ?
            """,
            (safe_limit,),
        ).fetchall()

    return [_row_to_action(row) for row in rows]


def confirm_pending_action(action_id: int) -> dict[str, Any] | None:
    return _resolve_action(action_id, CONFIRMED)


def cancel_pending_action(action_id: int) -> dict[str, Any] | None:
    return _resolve_action(action_id, CANCELLED)


def block_pending_action(action_id: int) -> dict[str, Any] | None:
    return _resolve_action(action_id, BLOCKED)


def expire_old_pending_actions() -> int:
    init_pending_actions_db()
    settings = get_settings()
    expiration_minutes = settings["pending_action_expiration_minutes"]
    cutoff = _now() - timedelta(minutes=expiration_minutes)

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE pending_actions
            SET status = ?, resolved_at = ?
            WHERE status = ? AND created_at < ?
            """,
            (EXPIRED, _now().isoformat(), PENDING, cutoff.isoformat()),
        )
        connection.commit()
        return int(cursor.rowcount)


def clear_resolved_pending_actions() -> int:
    init_pending_actions_db()

    with get_connection() as connection:
        cursor = connection.execute(
            f"""
            DELETE FROM pending_actions
            WHERE status IN ({",".join("?" for _ in RESOLVED_STATUSES)})
            """,
            tuple(RESOLVED_STATUSES),
        )
        connection.commit()
        return int(cursor.rowcount)


def count_pending_actions() -> int:
    init_pending_actions_db()
    expire_old_pending_actions()

    with get_connection() as connection:
        row = connection.execute(
            "SELECT COUNT(*) FROM pending_actions WHERE status = ?",
            (PENDING,),
        ).fetchone()

    return int(row[0]) if row else 0


def _resolve_action(action_id: int, status: str) -> dict[str, Any] | None:
    init_pending_actions_db()

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE pending_actions
            SET status = ?, resolved_at = ?
            WHERE id = ?
            """,
            (status, _now().isoformat(), action_id),
        )
        connection.commit()

    return get_pending_action(action_id)


def _row_to_action(row: sqlite3.Row) -> dict[str, Any]:
    try:
        parameters = json.loads(row["parameters"])
    except (TypeError, json.JSONDecodeError):
        parameters = {}

    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "original_message": row["original_message"],
        "detected_intent": row["detected_intent"],
        "requested_tool": row["requested_tool"],
        "parameters": parameters if isinstance(parameters, dict) else {},
        "risk_level": row["risk_level"],
        "status": row["status"],
        "resolved_at": row["resolved_at"],
    }


def _now() -> datetime:
    return datetime.now(timezone.utc)
