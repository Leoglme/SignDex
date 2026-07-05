"""Gestion des accès d'un espace client (page admin « Espaces clients » + délégation au propriétaire).

Monté sous le préfixe /organizations (paths : /{org_id}/users…).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import (
    build_invite_url,
    ensure_org_access,
    generate_invite_token,
    get_current_user,
    invite_expiry,
)
from models import ROLE_ADMIN, ROLE_OWNER, Organization, User
from schemas.auth import AccessUserOut, InviteLinkOut, UserCreateIn

router = APIRouter()


def _can_manage_users(user: User, org_id: int) -> bool:
    """Admin (partout) ou Propriétaire de CET espace."""
    if user.role == ROLE_ADMIN:
        return True
    return user.role == ROLE_OWNER and user.organization_id == org_id


def _require_manage(user: User, org_id: int) -> None:
    if not _can_manage_users(user, org_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Gestion des accès réservée au propriétaire")


@router.get("/{org_id}/users", response_model=list[AccessUserOut])
def list_users(org_id: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[User]:
    ensure_org_access(current, org_id)
    return list(
        db.execute(select(User).where(User.organization_id == org_id).order_by(User.created_at)).scalars().all(),
    )


@router.post("/{org_id}/users", response_model=InviteLinkOut)
def create_user(
    org_id: int,
    payload: UserCreateIn,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InviteLinkOut:
    org = db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organisation introuvable")
    _require_manage(current, org_id)
    # Un propriétaire ne peut créer que des éditeurs ; seul l'admin peut créer un propriétaire.
    if current.role != ROLE_ADMIN and payload.role == ROLE_OWNER:
        raise HTTPException(status_code=403, detail="Seul l'administrateur peut créer un propriétaire")

    email = str(payload.email).lower().strip()
    if db.execute(select(User).where(User.email == email)).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Un compte existe déjà avec cet email")

    user = User(
        email=email,
        full_name=(payload.full_name or "").strip() or None,
        role=payload.role,
        organization_id=org_id,
        is_active=False,
        invite_token=generate_invite_token(),
        invite_expires_at=invite_expiry(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return InviteLinkOut(user=AccessUserOut.model_validate(user), invite_url=build_invite_url(org, user.invite_token))


@router.post("/{org_id}/users/{user_id}/reinvite", response_model=InviteLinkOut)
def reinvite_user(
    org_id: int,
    user_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InviteLinkOut:
    _require_manage(current, org_id)
    user = db.get(User, user_id)
    if not user or user.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Accès introuvable")
    # Régénère un lien (réinitialise aussi l'activation : le compte redevient « invité »).
    user.invite_token = generate_invite_token()
    user.invite_expires_at = invite_expiry()
    user.is_active = False
    user.password_hash = None
    db.add(user)
    db.commit()
    db.refresh(user)
    return InviteLinkOut(user=AccessUserOut.model_validate(user), invite_url=build_invite_url(user.organization, user.invite_token))


@router.delete("/{org_id}/users/{user_id}")
def delete_user(
    org_id: int,
    user_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    _require_manage(current, org_id)
    if user_id == current.id:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas supprimer votre propre accès")
    user = db.get(User, user_id)
    if not user or user.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Accès introuvable")
    db.delete(user)
    db.commit()
    return {"status": "ok"}
