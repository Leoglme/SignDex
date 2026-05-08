from __future__ import annotations

import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("signdex.seeders")

_ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv() -> None:
    # Les scripts CI/VPS peuvent etre lancés depuis un autre dossier que `api/`.
    # On charge donc explicitement `.env`.
    if str(_ROOT) not in sys.path:
        sys.path.insert(0, str(_ROOT))
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(_ROOT / ".env")


def run() -> None:
    _load_dotenv()
    from config import get_settings
    from core.database import SessionLocal
    from seeders.initial_clients_seeder import seed_if_database_empty

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
