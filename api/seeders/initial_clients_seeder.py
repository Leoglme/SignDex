"""Seed clients initiaux si la table `clients` est vide (prod / première install)."""

from __future__ import annotations

import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import Client

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("signdex.seeder.initial_clients")

# Données alignées sur l’export phpMyAdmin / fiches clients SignDex.
# Les `id` SQL sont laissés à l’auto-increment.
_INITIAL_ROWS: list[dict[str, object | None]] = [
    {
        "name": "HelloPropre",
        "subtitle": "Service de nettoyage professionnel",
        "website_url": "https://www.hellopropre.com",
        "email": "contact@hellopropre.com",
        "phone_primary": "07 56 90 28 18",
        "phone_secondary": "07 56 96 82 10",
        "linkedin_url": "https://www.linkedin.com/company/hellopropre",
        "instagram_url": "https://www.instagram.com/hellopropre/",
        "facebook_url": "https://www.facebook.com/hellopropre",
        "tiktok_url": "https://www.tiktok.com/@hellopropre",
        "youtube_url": "https://www.youtube.com/@hellopropre",
        "color_primary": "#4e8baa",
        "color_secondary": "#5a9abf",
        "logo_url": "https://static.wixstatic.com/media/0cac82_78c3516305364c279b12e172e84f7a0d~mv2.jpg",
        "photo1_url": None,
        "photo2_url": "https://lp.hellopropre.com/wp-content/uploads/2024/03/logo-hello-propre.jpeg",
        "notes": "Seeder auto depuis tes 3 signatures HelloPropre (v1/v2/v3).",
    },
    {
        "name": "Aihaht EDANH",
        "subtitle": "Fondatrice - RESPONYX",
        "website_url": "https://www.responyx.fr",
        "email": "aihaht.edanh@responyx.fr",
        # Export phpMyAdmin : espaces à normaliser pour affichage téléphone FR
        "phone_primary": "09 72 12 65 09",
        "phone_secondary": None,
        "linkedin_url": "https://linkedin.com/in/aïhaht-edanh",
        "instagram_url": None,
        "facebook_url": None,
        "tiktok_url": None,
        "youtube_url": None,
        "color_primary": "#5f5bff",
        "color_secondary": "#14243e",
        "logo_url": "https://aapjpybdkzqtgxavjjem.supabase.co/storage/v1/object/public/GoupixDex/clients/2/00aadb70af424c3da1c516564ece9fa3.png",
        "photo1_url": "https://aapjpybdkzqtgxavjjem.supabase.co/storage/v1/object/public/GoupixDex/clients/2/500e5f987ede4d2f83f4403b77df8131.jpg",
        "photo2_url": "https://aapjpybdkzqtgxavjjem.supabase.co/storage/v1/object/public/GoupixDex/clients/2/765a5c82d231428287a3e88377e27589.png",
        "notes": None,
    },
]


def seed_if_database_empty(db: Session) -> int:
    """
    Insère les clients initiaux uniquement si `clients` n’a aucune ligne.
    Retourne le nombre de lignes insérées (0 si skip).
    """
    n = db.scalar(select(func.count()).select_from(Client))
    if n:
        logger.info("Table clients non vide (%s ligne(s)), seed initial ignoré", n)
        return 0

    inserted = 0
    for row in _INITIAL_ROWS:
        c = Client(**row)
        db.add(c)
        inserted += 1
    db.commit()
    logger.info("Seed initial : %s client(s) créé(s)", inserted)
    return inserted


def run() -> None:
    from core.database import SessionLocal

    db = SessionLocal()
    try:
        seed_if_database_empty(db)
    finally:
        db.close()


if __name__ == "__main__":
    run()
