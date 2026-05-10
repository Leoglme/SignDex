from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ImageSlotSource = Literal["default", "logo", "photo1", "photo2"]


class ServiceDeliverableVariantIn(BaseModel):
    template_key: str = Field(min_length=1, max_length=128)
    swap_colors: bool = False
    logo_slot: ImageSlotSource = "default"
    photo1_slot: ImageSlotSource = "default"
    photo2_slot: ImageSlotSource = "default"
    color_primary: str | None = Field(
        default=None,
        max_length=32,
        description="Surcharge couleur 1 (#hex ou tout CSS color) ; vide / null = couleur de la fiche client.",
    )
    color_secondary: str | None = Field(default=None, max_length=32)


class ServiceDeliverableRequest(BaseModel):
    variants: list[ServiceDeliverableVariantIn] | None = None


class ServiceRenderPreviewIn(BaseModel):
    template_key: str = Field(min_length=1, max_length=128)
    client_id: int = Field(ge=1)
    swap_colors: bool = False
    logo_slot: ImageSlotSource = "default"
    photo1_slot: ImageSlotSource = "default"
    photo2_slot: ImageSlotSource = "default"
    color_primary: str | None = Field(default=None, max_length=32)
    color_secondary: str | None = Field(default=None, max_length=32)

