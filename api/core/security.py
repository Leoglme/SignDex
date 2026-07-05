"""Sécurité du portail : hachage de mot de passe (bcrypt), JWT, tokens d'invitation, dépendances FastAPI."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from config import get_settings
from core.database import get_db
from models import ROLE_ADMIN, Organization, User

_ALGO = "HS256"


# --------------------------------------------------------------------------- #
#  Mots de passe
# --------------------------------------------------------------------------- #
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# --------------------------------------------------------------------------- #
#  JWT de session
# --------------------------------------------------------------------------- #
def create_access_token(user: User) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "role": user.role,
        "org": user.organization_id,
        "iat": now,
        "exp": now + timedelta(hours=settings.jwt_expire_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=_ALGO)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, get_settings().jwt_secret, algorithms=[_ALGO])
    except jwt.PyJWTError:
        return None


# --------------------------------------------------------------------------- #
#  Invitations
# --------------------------------------------------------------------------- #
def generate_invite_token() -> str:
    return secrets.token_urlsafe(32)


def invite_expiry() -> datetime:
    return datetime.utcnow() + timedelta(hours=get_settings().invite_ttl_hours)


def invite_is_valid(user: User) -> bool:
    return bool(user.invite_token) and user.invite_expires_at is not None and user.invite_expires_at > datetime.utcnow()


def _portal_url(org: Organization | None, path: str, token: str) -> str:
    """URL du portail sur le sous-domaine du client (ex. https://lexial.dibodev.fr/<path>/<token>).

    Fallback sur `public_base_url` si l'orga n'a pas de slug ou si le domaine racine n'est pas configuré.
    """
    settings = get_settings()
    base_domain = settings.portal_base_domain.strip()
    if org and org.slug and base_domain:
        return f"https://{org.slug}.{base_domain}/{path}/{token}"
    return f"{settings.public_base_url.rstrip('/')}/{path}/{token}"


def build_invite_url(org: Organization | None, token: str) -> str:
    """Lien d'invitation sur le sous-domaine du client (ex. https://lexial.dibodev.fr/invitation/<token>)."""
    return _portal_url(org, "invitation", token)


# --------------------------------------------------------------------------- #
#  Réinitialisation de mot de passe (« mot de passe oublié »)
# --------------------------------------------------------------------------- #
def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)


def reset_expiry() -> datetime:
    return datetime.utcnow() + timedelta(hours=get_settings().reset_ttl_hours)


def reset_is_valid(user: User) -> bool:
    return bool(user.reset_token) and user.reset_expires_at is not None and user.reset_expires_at > datetime.utcnow()


def build_reset_url(org: Organization | None, token: str) -> str:
    """Lien de réinitialisation sur le sous-domaine du client (ex. https://lexial.dibodev.fr/reset/<token>)."""
    return _portal_url(org, "reset", token)


# --------------------------------------------------------------------------- #
#  Dépendances FastAPI
# --------------------------------------------------------------------------- #
def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Non authentifié")
    payload = decode_access_token(authorization.split(" ", 1)[1].strip())
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide ou expiré")
    try:
        user = db.get(User, int(payload.get("sub")))
    except (TypeError, ValueError):
        user = None
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Compte inconnu ou inactif")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != ROLE_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Réservé à l'administrateur")
    return user


def ensure_org_access(user: User, organization_id: int) -> None:
    """Un admin accède à tout ; un utilisateur d'espace uniquement à SON organisation."""
    if user.role == ROLE_ADMIN:
        return
    if user.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé à cette organisation")
