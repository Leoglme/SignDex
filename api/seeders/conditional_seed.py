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


def _ensure_lexial_org(db) -> None:
    """Seed l'organisation LEXIAL UNE SEULE FOIS (si absente).

    Ne réécrase jamais une organisation existante → les modifications faites par le
    client depuis le portail (ajout de collaborateurs, déménagements…) sont préservées
    à chaque déploiement.
    """
    from sqlalchemy import select

    from models import Organization

    # Garde robuste : si une orga LEXIAL existe déjà (par slug OU par nom), on ne touche à RIEN.
    # `slug='lexial'` est la clé multi-tenant (sous-domaine) → immuable en pratique. `.first()`
    # (et non `scalar_one_or_none`) pour ne jamais lever si plusieurs lignes correspondent.
    already_exists = db.execute(
        select(Organization.id).where(
            (Organization.slug == "lexial") | (Organization.name == "LEXIAL"),
        ),
    ).first()
    if already_exists:
        return
    from scripts.seed_lexial_org import main as seed_lexial

    seed_lexial()
    logger.info("Organisation LEXIAL seedée (première fois, base vide)")


def run() -> None:
    _load_dotenv()
    from config import get_settings
    from core.database import SessionLocal
    from seeders.initial_clients_seeder import seed_if_database_empty

    from seeders.auth_seeder import ensure_admin_user

    settings = get_settings()
    db = SessionLocal()
    try:
        # Compte admin bootstrap : toujours tenté (idempotent), indépendant du seed de démo.
        ensure_admin_user(db)
        # Organisation LEXIAL : créée une seule fois si absente (jamais réécrasée).
        _ensure_lexial_org(db)
        if int(settings.signdex_seed_if_empty or 0) == 1:
            seed_if_database_empty(db)
        else:
            logger.info("SIGNDEX_SEED_IF_EMPTY=0 : aucun seed automatique")
    finally:
        db.close()
    logger.info("Seeders OK")


if __name__ == "__main__":
    run()
