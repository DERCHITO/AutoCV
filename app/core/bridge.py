"""Lógica compartida del puente n8n ↔ Python."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select

from app.core.config import (
    ROOT_DIR,
    get_bridge_host,
    get_bridge_port,
    get_database_url,
    get_ollama_base_url,
    get_ollama_model,
)
from app.database.connection import check_database, get_session_factory, init_database
from app.database.models import Application


def health_payload() -> dict[str, Any]:
    db_ok = False
    db_error: str | None = None
    try:
        db_ok = check_database()
    except Exception as exc:  # noqa: BLE001 — respuesta operativa para n8n
        db_error = str(exc)

    return {
        "status": "ok" if db_ok else "degraded",
        "service": "autocv-bridge",
        "database": {"ok": db_ok, "url": get_database_url(), "error": db_error},
        "paths": {"root": str(ROOT_DIR)},
        "bridge": {
            "host": get_bridge_host(),
            "port": get_bridge_port(),
        },
        "ollama": {
            "base_url": get_ollama_base_url(),
            "model": get_ollama_model(),
        },
    }


def list_applications(limit: int = 50) -> list[dict[str, Any]]:
    factory = get_session_factory()
    with factory() as session:
        rows = session.scalars(
            select(Application).order_by(Application.created_at.desc()).limit(limit)
        ).all()
        return [
            {
                "id": r.id,
                "company": r.company,
                "title": r.title,
                "url": r.url,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]


def setup_database() -> dict[str, Any]:
    init_database()
    return {"ok": True, "message": "Tablas SQLite creadas o ya existentes."}


def json_response(payload: dict[str, Any], status: int = 200) -> tuple[int, str]:
    return status, json.dumps(payload, ensure_ascii=False)
