from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import text

from core.database import engine

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("signdex.migrations")


def ensure_schema_migrations_table() -> None:
    sql = """
    CREATE TABLE IF NOT EXISTS schema_migrations (
      id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
      filename VARCHAR(255) NOT NULL UNIQUE,
      applied_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    with engine.begin() as conn:
        conn.execute(text(sql))


def is_applied(filename: str) -> bool:
    with engine.begin() as conn:
        res = conn.execute(
            text("SELECT 1 FROM schema_migrations WHERE filename=:f LIMIT 1"),
            {"f": filename},
        ).fetchone()
        return bool(res)


def mark_applied(filename: str) -> None:
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO schema_migrations (filename) VALUES (:f)"),
            {"f": filename},
        )


def apply_file(path: Path) -> None:
    filename = path.name
    if is_applied(filename):
        return
    sql = path.read_text(encoding="utf-8")
    logger.info("Applying migration %s", filename)
    with engine.begin() as conn:
        for statement in [s.strip() for s in sql.split(";") if s.strip()]:
            conn.execute(text(statement))
    mark_applied(filename)


def run() -> None:
    ensure_schema_migrations_table()
    migrations_dir = Path(__file__).parent
    for p in sorted(migrations_dir.glob("*.sql")):
        apply_file(p)
    logger.info("Migrations OK")


if __name__ == "__main__":
    run()

