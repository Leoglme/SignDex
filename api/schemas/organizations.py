from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class OfficeIn(BaseModel):
    label: str = Field(min_length=1, max_length=255, description="Libellé du bureau (ex. Paris).")
    template_key: str = Field(min_length=1, max_length=128, description="Template à utiliser (ex. signature-lexial-paris).")
    sort_order: int = 0
    address_street: str | None = Field(default=None, max_length=255)
    address_cp_city: str | None = Field(default=None, max_length=255)
    phone_display: str | None = Field(default=None, max_length=64)
    phone_tel: str | None = Field(default=None, max_length=64)


class OfficeUpdate(BaseModel):
    """Édition d'un bureau (déménagement) : libellé + adresse."""

    label: str | None = Field(default=None, min_length=1, max_length=255)
    address_street: str | None = Field(default=None, max_length=255)
    address_cp_city: str | None = Field(default=None, max_length=255)
    phone_display: str | None = Field(default=None, max_length=64)
    phone_tel: str | None = Field(default=None, max_length=64)
    sort_order: int | None = None


class OfficeOut(BaseModel):
    id: int
    label: str
    template_key: str
    sort_order: int
    address_street: str | None = None
    address_cp_city: str | None = None
    phone_display: str | None = None
    phone_tel: str | None = None

    class Config:
        from_attributes = True


class MemberIn(BaseModel):
    firstname: str | None = Field(default=None, max_length=128)
    lastname: str | None = Field(default=None, max_length=128)
    title: str | None = Field(default=None, max_length=255)
    sort_order: int = 0
    office_ids: list[int] = Field(default_factory=list, description="Bureaux auxquels le membre est rattaché.")


class MemberUpdate(BaseModel):
    firstname: str | None = Field(default=None, max_length=128)
    lastname: str | None = Field(default=None, max_length=128)
    title: str | None = Field(default=None, max_length=255)
    sort_order: int | None = None
    office_ids: list[int] | None = None


class MemberOut(BaseModel):
    id: int
    firstname: str | None
    lastname: str | None
    title: str | None
    sort_order: int
    offices: list[OfficeOut]

    class Config:
        from_attributes = True


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    notes: str | None = None
    show_chambers: bool = True
    brand_logo_url: str | None = Field(default=None, max_length=1024)
    brand_color: str | None = Field(default=None, max_length=32)
    offices: list[OfficeIn] = Field(default_factory=list)


class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    notes: str | None = None
    show_chambers: bool | None = None
    brand_logo_url: str | None = Field(default=None, max_length=1024)
    brand_color: str | None = Field(default=None, max_length=32)
    sig_logo_url: str | None = Field(default=None, max_length=1024)
    sig_chambers_url: str | None = Field(default=None, max_length=1024)
    default_theme: str | None = Field(default=None, max_length=16)


class OrganizationOut(BaseModel):
    id: int
    name: str
    slug: str
    notes: str | None
    show_chambers: bool
    brand_logo_url: str | None = None
    brand_color: str | None = None
    sig_logo_url: str | None = None
    sig_chambers_url: str | None = None
    default_theme: str | None = None
    offices: list[OfficeOut]
    members: list[MemberOut]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrganizationSummary(BaseModel):
    """Vue liste : compteurs sans charger tout le détail."""

    id: int
    name: str
    slug: str
    notes: str | None
    show_chambers: bool
    brand_logo_url: str | None = None
    brand_color: str | None = None
    default_theme: str | None = None
    office_count: int
    member_count: int
    signature_count: int
    created_at: datetime
    updated_at: datetime


class PortalOrganizationOut(BaseModel):
    id: int
    name: str
    brand_logo_url: str | None = None
    brand_color: str | None = None
    sig_logo_url: str | None = None
    sig_chambers_url: str | None = None
    show_chambers: bool = True
    member_count: int
    signature_count: int


class PortalOverviewOut(BaseModel):
    organization: PortalOrganizationOut
    members: list[MemberOut]
    offices: list[OfficeOut]


class PortalDeliverableOut(BaseModel):
    """Ligne d'historique : une génération de livrable depuis le portail."""

    id: int
    scope: str
    label: str
    signature_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class SignaturePreview(BaseModel):
    office_label: str
    html: str


class MemberPreviewOut(BaseModel):
    """Aperçu des signatures d'un collaborateur (une par bureau), HTML rendu."""

    member_name: str
    signatures: list[SignaturePreview]
