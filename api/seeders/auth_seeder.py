"""Crée le compte super-admin (bootstrap) s'il n'existe pas. Idempotent.

Alimenté par les variables d'env ADMIN_EMAIL / ADMIN_PASSWORD. Sans elles, ne fait rien
(utile en prod : on définit les identifiants admin via l'environnement).
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

logger = logging.getLogger("signdex.seeders")


def ensure_admin_user(db: Session) -> None:
    from config import get_settings
    from core.security import hash_password
    from models import ROLE_ADMIN, User

    settings = get_settings()
    email = (settings.admin_email or "").lower().strip()
    password = settings.admin_password or ""
    if not email or not password:
        logger.info("ADMIN_EMAIL / ADMIN_PASSWORD non définis : pas de compte admin bootstrap")
        return

    existing = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if existing:
        return

    db.add(
        User(
            email=email,
            password_hash=hash_password(password),
            role=ROLE_ADMIN,
            full_name="Administrateur",
            is_active=True,
        ),
    )
    db.commit()
    logger.info("Compte admin créé : %s", email)
