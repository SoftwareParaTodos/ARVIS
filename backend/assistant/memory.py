import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from config import DATABASE_PATH, STORAGE_DIR


def get_connection() -> sqlite3.Connection:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DATABASE_PATH)


def init_db() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                user_message TEXT NOT NULL,
                detected_intent TEXT NOT NULL,
                tool_used TEXT,
                assistant_response TEXT NOT NULL,
                action_status TEXT NOT NULL
            )
            """
        )
        connection.commit()


def save_interaction(
    *,
    user_message: str,
    detected_intent: str,
    tool_used: str | None,
    assistant_response: str,
    action_status: str,
) -> None:
    init_db()
    created_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO interactions (
                created_at,
                user_message,
                detected_intent,
                tool_used,
                assistant_response,
                action_status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                user_message,
                detected_intent,
                tool_used,
                assistant_response,
                action_status,
            ),
        )
        connection.commit()


def get_recent_interactions(limit: int = 10) -> list[dict[str, str | None]]:
    init_db()
    safe_limit = max(1, min(limit, 100))

    with get_connection() as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT
                created_at,
                user_message,
                detected_intent,
                tool_used,
                assistant_response,
                action_status
            FROM interactions
            ORDER BY id DESC
            LIMIT ?
            """,
            (safe_limit,),
        ).fetchall()

    return [
        {
            "created_at": row["created_at"],
            "user_message": row["user_message"],
            "detected_intent": row["detected_intent"],
            "tool_used": row["tool_used"],
            "assistant_response": row["assistant_response"],
            "action_status": row["action_status"],
        }
        for row in rows
    ]


def database_location() -> Path:
    return DATABASE_PATH
