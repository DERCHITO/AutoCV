"""CLI del puente — usable desde terminal o nodo Execute Command de n8n."""

from __future__ import annotations

import argparse
import json
import sys

from app.core.bridge import health_payload, list_applications, setup_database
from app.core.server import run_server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AutoCV — puente Python para n8n")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("health", help="Estado del servicio y SQLite")
    sub.add_parser("db-init", help="Crear tablas en SQLite")
    sub.add_parser("applications", help="Listar postulaciones (JSON)")
    sub.add_parser("serve", help="Levantar API HTTP para n8n")

    args = parser.parse_args(argv)

    if args.command == "health":
        print(json.dumps(health_payload(), ensure_ascii=False, indent=2))
        return 0
    if args.command == "db-init":
        print(json.dumps(setup_database(), ensure_ascii=False, indent=2))
        return 0
    if args.command == "applications":
        print(json.dumps({"items": list_applications()}, ensure_ascii=False, indent=2))
        return 0
    if args.command == "serve":
        run_server()
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
