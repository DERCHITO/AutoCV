"""Tests mínimos para CI — imports y lógica sin red ni Playwright."""

from app.core.bridge import health_payload, setup_database


def test_import_app_package() -> None:
    import app  # noqa: F401
    import app.core.config  # noqa: F401
    import app.database.connection  # noqa: F401


def test_health_payload_structure() -> None:
    payload = health_payload()
    assert "status" in payload
    assert "database" in payload
    assert payload["service"] == "autocv-bridge"


def test_database_init() -> None:
    result = setup_database()
    assert result["ok"] is True
