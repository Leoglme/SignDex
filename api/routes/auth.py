from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import (
    build_reset_url,
    create_access_token,
    generate_reset_token,
    get_current_user,
    hash_password,
    invite_is_valid,
    reset_expiry,
    reset_is_valid,
    verify_password,
)
from models import Organization, User
from schemas.auth import (
    BrandingOut,
    ForgotPasswordIn,
    InviteAcceptIn,
    InviteInfoOut,
    LoginIn,
    ResetInfoOut,
    ResetPasswordIn,
    TokenOut,
    UserOut,
)
from services.email_service import send_password_reset_email

logger = logging.getLogger("signdex.auth")

router = APIRouter()


def _user_out(user: User) -> UserOut:
    org = user.organization
    return UserOut(
        id=user.id,
        email=user.email,
        role=user.role,
        organization_id=user.organization_id,
        full_name=user.full_name,
        is_active=user.is_active,
        organization_name=org.name if org else None,
        brand_logo_url=org.brand_logo_url if org else None,
        brand_color=org.brand_color if org else None,
        default_theme=org.default_theme if org else None,
    )


def _token_response(user: User) -> TokenOut:
    return TokenOut(access_token=create_access_token(user), user=_user_out(user))


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)) -> TokenOut:
    email = str(payload.email).lower().strip()
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou mot de passe incorrect")
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte non activé — utilisez votre lien d'invitation pour définir votre mot de passe",
        )
    return _token_response(user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return _user_out(user)


@router.get("/invite/{token}", response_model=InviteInfoOut)
def invite_info(token: str, db: Session = Depends(get_db)) -> InviteInfoOut:
    user = db.execute(select(User).where(User.invite_token == token)).scalar_one_or_none()
    if not user or not invite_is_valid(user):
        return InviteInfoOut(valid=False)
    org = db.get(Organization, user.organization_id) if user.organization_id else None
    return InviteInfoOut(
        valid=True,
        email=user.email,
        organization_name=org.name if org else None,
        brand_logo_url=org.brand_logo_url if org else None,
        brand_color=org.brand_color if org else None,
    )


@router.get("/branding", response_model=BrandingOut | None)
def branding(slug: str = Query(..., max_length=255), db: Session = Depends(get_db)) -> BrandingOut | None:
    """Branding public d'une organisation par son slug (= sous-domaine, ex. `lexial`).

    Permet de teinter la page de connexion aux couleurs du client AVANT toute
    authentification. Renvoie `null` si le slug ne correspond à aucune organisation
    (→ hôte non-client comme `signdex` → thème SignDex par défaut).
    """
    key = slug.strip().lower()
    if not key:
        return None
    org = db.execute(select(Organization).where(Organization.slug == key)).scalar_one_or_none()
    if not org:
        return None
    return BrandingOut(
        slug=org.slug,
        organization_name=org.name,
        brand_logo_url=org.brand_logo_url,
        brand_color=org.brand_color,
        default_theme=org.default_theme,
    )


@router.post("/accept-invite", response_model=TokenOut)
def accept_invite(payload: InviteAcceptIn, db: Session = Depends(get_db)) -> TokenOut:
    user = db.execute(select(User).where(User.invite_token == payload.token)).scalar_one_or_none()
    if not user or not invite_is_valid(user):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lien d'invitation invalide ou expiré")
    user.password_hash = hash_password(payload.password)
    user.is_active = True
    user.invite_token = None
    user.invite_expires_at = None
    db.add(user)
    db.commit()
    db.refresh(user)
    return _token_response(user)


# --------------------------------------------------------------------------- #
#  Mot de passe oublié
# --------------------------------------------------------------------------- #
@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordIn, db: Session = Depends(get_db)) -> dict[str, bool]:
    """Déclenche l'envoi d'un email de réinitialisation.

    Réponse CONSTANTE (`{"ok": true}`) quoi qu'il arrive : ne révèle jamais si un
    compte existe, et n'échoue pas si l'envoi d'email plante (loggé seulement).
    """
    email = str(payload.email).lower().strip()
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user and user.is_active:
        user.reset_token = generate_reset_token()
        user.reset_expires_at = reset_expiry()
        db.add(user)
        db.commit()
        db.refresh(user)
        org = db.get(Organization, user.organization_id) if user.organization_id else None
        try:
            await send_password_reset_email(user, org, build_reset_url(org, user.reset_token))
        except Exception:  # noqa: BLE001 — ne jamais révéler ni planter sur l'email
            logger.exception("Envoi de l'email de réinitialisation échoué pour %s", email)
    return {"ok": True}


@router.get("/reset/{token}", response_model=ResetInfoOut)
def reset_info(token: str, db: Session = Depends(get_db)) -> ResetInfoOut:
    """Infos (validité + branding) pour la page « choisir un nouveau mot de passe »."""
    user = db.execute(select(User).where(User.reset_token == token)).scalar_one_or_none()
    if not user or not reset_is_valid(user):
        return ResetInfoOut(valid=False)
    org = db.get(Organization, user.organization_id) if user.organization_id else None
    return ResetInfoOut(
        valid=True,
        email=user.email,
        organization_name=org.name if org else None,
        brand_logo_url=org.brand_logo_url if org else None,
        brand_color=org.brand_color if org else None,
    )


@router.post("/reset-password", response_model=TokenOut)
def reset_password(payload: ResetPasswordIn, db: Session = Depends(get_db)) -> TokenOut:
    """Applique le nouveau mot de passe puis connecte l'utilisateur."""
    user = db.execute(select(User).where(User.reset_token == payload.token)).scalar_one_or_none()
    if not user or not reset_is_valid(user):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lien de réinitialisation invalide ou expiré")
    user.password_hash = hash_password(payload.password)
    user.reset_token = None
    user.reset_expires_at = None
    user.is_active = True
    db.add(user)
    db.commit()
    db.refresh(user)
    return _token_response(user)
