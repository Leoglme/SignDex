from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    role: str
    organization_id: int | None
    full_name: str | None
    is_active: bool
    organization_name: str | None = None
    brand_logo_url: str | None = None
    brand_color: str | None = None
    default_theme: str | None = None

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class InviteInfoOut(BaseModel):
    """Infos affichées sur la page « définir mon mot de passe » (avant activation)."""

    valid: bool
    email: str | None = None
    organization_name: str | None = None
    brand_logo_url: str | None = None
    brand_color: str | None = None


class BrandingOut(BaseModel):
    """Branding public d'une organisation, déduit du sous-domaine (ex. `lexial`).

    Sert à teinter la page de connexion aux couleurs du client AVANT authentification.
    Ne contient que du public (nom, logo, couleur) — aucune donnée sensible.
    """

    slug: str
    organization_name: str | None = None
    brand_logo_url: str | None = None
    brand_color: str | None = None
    default_theme: str | None = None


class InviteAcceptIn(BaseModel):
    token: str = Field(min_length=8)
    password: str = Field(min_length=8, max_length=128)


class ForgotPasswordIn(BaseModel):
    email: EmailStr


class ResetInfoOut(BaseModel):
    """Infos affichées sur la page « choisir un nouveau mot de passe » (avant validation)."""

    valid: bool
    email: str | None = None
    organization_name: str | None = None
    brand_logo_url: str | None = None
    brand_color: str | None = None


class ResetPasswordIn(BaseModel):
    token: str = Field(min_length=8)
    password: str = Field(min_length=8, max_length=128)


class UserCreateIn(BaseModel):
    """Création d'un accès par l'admin ou le propriétaire d'un espace."""

    email: EmailStr
    full_name: str | None = Field(default=None, max_length=255)
    role: str = Field(default="editor", pattern="^(owner|editor)$")


class AccessUserOut(BaseModel):
    id: int
    email: str
    full_name: str | None
    role: str
    status: str  # 'invited' | 'active'

    class Config:
        from_attributes = True


class InviteLinkOut(BaseModel):
    user: AccessUserOut
    invite_url: str
