from assistant.permissions import PermissionLevel, classify_permission


def test_permissions_safe() -> None:
    permission = classify_permission("system_info", "info del sistema")

    assert permission == PermissionLevel.SAFE


def test_permissions_blocked() -> None:
    permission = classify_permission("chat", "formatear disco")

    assert permission == PermissionLevel.BLOCKED


def test_permissions_confirmation_required() -> None:
    permission = classify_permission("chat", "borrar archivos")

    assert permission == PermissionLevel.CONFIRMATION_REQUIRED
