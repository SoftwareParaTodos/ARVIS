import sqlite3
from datetime import datetime, timedelta, timezone

from assistant import pending_actions


def _patch_connection(monkeypatch, db_path):
    def get_test_connection():
        return sqlite3.connect(db_path)

    monkeypatch.setattr(pending_actions, "get_connection", get_test_connection)


def test_create_and_list_pending_action(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "pending.sqlite3"
    _patch_connection(monkeypatch, db_path)

    action = pending_actions.create_pending_action(
        original_message="borrar archivos",
        detected_intent="chat",
        requested_tool=None,
        parameters={},
        risk_level="confirmation_required",
    )

    actions = pending_actions.list_pending_actions()

    assert action["id"] == 1
    assert len(actions) == 1
    assert actions[0]["status"] == "pending"


def test_cancel_pending_action(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "pending.sqlite3"
    _patch_connection(monkeypatch, db_path)

    action = pending_actions.create_pending_action(
        original_message="mover archivos",
        detected_intent="chat",
        requested_tool=None,
        parameters={},
        risk_level="confirmation_required",
    )
    cancelled = pending_actions.cancel_pending_action(action["id"])

    assert cancelled["status"] == "cancelled"
    assert cancelled["resolved_at"] is not None


def test_expired_action_is_not_pending(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "pending.sqlite3"
    _patch_connection(monkeypatch, db_path)
    monkeypatch.setattr(
        pending_actions,
        "get_settings",
        lambda: {"pending_action_expiration_minutes": 10},
    )

    action = pending_actions.create_pending_action(
        original_message="enviar mensaje",
        detected_intent="chat",
        requested_tool=None,
        parameters={},
        risk_level="confirmation_required",
    )
    old_created_at = (datetime.now(timezone.utc) - timedelta(minutes=11)).isoformat()
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "UPDATE pending_actions SET created_at = ? WHERE id = ?",
            (old_created_at, action["id"]),
        )
        connection.commit()

    expired_count = pending_actions.expire_old_pending_actions()
    expired = pending_actions.get_pending_action(action["id"])

    assert expired_count == 1
    assert expired["status"] == "expired"
