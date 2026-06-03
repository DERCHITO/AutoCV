"""Carga de configuración desde .env (raíz del repositorio)."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


def _resolve_sqlite_url(raw: str) -> str:
    """Convierte sqlite:///database/foo.db en ruta absoluta bajo el repo."""
    prefix = "sqlite:///"
    if not raw.startswith(prefix):
        return raw
    path_part = raw[len(prefix) :]
    if path_part.startswith("/") or (len(path_part) > 1 and path_part[1] == ":"):
        return raw
    db_path = (ROOT_DIR / path_part).resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path.as_posix()}"


def get_database_url() -> str:
    raw = os.getenv("DATABASE_URL", "sqlite:///database/autocv.sqlite")
    return _resolve_sqlite_url(raw)


def get_bridge_host() -> str:
    return os.getenv("BRIDGE_API_HOST", "127.0.0.1")


def get_bridge_port() -> int:
    return int(os.getenv("BRIDGE_API_PORT", "8765"))


def get_bridge_token() -> str | None:
    token = os.getenv("BRIDGE_API_TOKEN", "").strip()
    return token or None


def get_ollama_base_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")


def get_ollama_model() -> str:
    return os.getenv("OLLAMA_MODEL", "llama3")
