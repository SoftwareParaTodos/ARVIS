from api.routes_actions import pending_actions
from assistant.brain import confirm_action_by_id


def test_actions_pending_route(monkeypatch) -> None:
    monkeypatch.setattr(
        "api.routes_actions.list_pending_actions",
        lambda limit=20: [
            {
                "id": 1,
                "status": "pending",
                "original_message": "borrar archivos",
            }
        ],
    )

    response = pending_actions()

    assert response["status"] == "ok"
    assert response["actions"][0]["id"] == 1


def test_confirm_nonexistent_action_returns_controlled_error() -> None:
    response = confirm_action_by_id(999999)

    assert response["status"] == "error"
    assert "No encontre" in response["message"]
