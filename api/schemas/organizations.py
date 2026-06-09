from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class OfficeIn(BaseModel):
    label: str = Field(min_length=1, max_length=255, description="Libellé du bureau (ex. Paris).")
    template_key: str = Field(min_length=1, max_length=128, description="Template à utiliser (ex. signature-lexial-paris).")
    sort_order: int = 0


class OfficeOut(BaseModel):
    id: int
    label: str
    template_key: str
    sort_order: int

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
    offices: list[OfficeIn] = Field(default_factory=list)


class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    notes: str | None = None
    show_chambers: bool | None = None


class OrganizationOut(BaseModel):
    id: int
    name: str
    slug: str
    notes: str | None
    show_chambers: bool
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
    office_count: int
    member_count: int
    signature_count: int
    created_at: datetime
    updated_at: datetime
