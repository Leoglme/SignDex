from __future__ import annotations

import logging

from config import get_settings
from core.database import SessionLocal
from seeders.initial_clients_seeder import seed_if_database_empty

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("signdex.seeders")


def run() -> None:
    settings = get_settings()
    db = SessionLocal()
    try:
        if int(settings.signdex_seed_if_empty or 0) == 1:
            seed_if_database_empty(db)
        else:
            logger.info("SIGNDEX_SEED_IF_EMPTY=0 : aucun seed automatique")
    finally:
        db.close()
    logger.info("Seeders OK")


if __name__ == "__main__":
    run()
