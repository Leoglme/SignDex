from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ClientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    subtitle: str | None = None

    website_url: str | None = None
    email: str | None = None
    phone_primary: str | None = None
    phone_secondary: str | None = None

    linkedin_url: str | None = None
    instagram_url: str | None = None
    facebook_url: str | None = None
    tiktok_url: str | None = None
    youtube_url: str | None = None

    color_primary: str | None = None
    color_secondary: str | None = None

    logo_url: str | None = None
    photo1_url: str | None = None
    photo2_url: str | None = None

    notes: str | None = None


class ClientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    subtitle: str | None = None
    website_url: str | None = None
    email: str | None = None
    phone_primary: str | None = None
    phone_secondary: str | None = None
    linkedin_url: str | None = None
    instagram_url: str | None = None
    facebook_url: str | None = None
    tiktok_url: str | None = None
    youtube_url: str | None = None
    color_primary: str | None = None
    color_secondary: str | None = None
    logo_url: str | None = None
    photo1_url: str | None = None
    photo2_url: str | None = None
    notes: str | None = None


class ClientOut(BaseModel):
    id: int
    name: str
    subtitle: str | None
    website_url: str | None
    email: str | None
    phone_primary: str | None
    phone_secondary: str | None
    linkedin_url: str | None
    instagram_url: str | None
    facebook_url: str | None
    tiktok_url: str | None
    youtube_url: str | None
    color_primary: str | None
    color_secondary: str | None
    logo_url: str | None
    photo1_url: str | None
    photo2_url: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

