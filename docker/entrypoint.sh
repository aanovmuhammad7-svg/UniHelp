#!/bin/sh
set -e

python - <<'PY'
import socket
import time
from urllib.parse import urlparse

from app.core.config import settings


def wait_for_service(host: str, port: int, name: str, timeout: int = 60) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=2):
                print(f"{name} is available at {host}:{port}")
                return
        except OSError:
            time.sleep(2)
    raise RuntimeError(f"Timed out waiting for {name} at {host}:{port}")


db = urlparse(settings.database_url.unicode_string())
redis = urlparse(settings.redis_url.unicode_string())

wait_for_service(db.hostname or "postgres", db.port or 5432, "PostgreSQL")
wait_for_service(redis.hostname or "redis", redis.port or 6379, "Redis")
PY

alembic upgrade head
python -m app.bot.runner
