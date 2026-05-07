from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ImageSlotSource = Literal["default", "logo", "photo1", "photo2"]


class DeliverableVariantIn(BaseModel):
    template_key: str = Field(min_length=1, max_length=128)
    swap_colors: bool = False
    logo_slot: ImageSlotSource = "default"
    photo1_slot: ImageSlotSource = "default"
    photo2_slot: ImageSlotSource = "default"
    show_side_photo: bool = Field(
        default=True,
        description="Template moderne (signature-v2) : afficher la vignette à droite (photo 1).",
    )


class DeliverableRequest(BaseModel):
    """Si `variants` est absent ou null : une entrée par template (comportement historique)."""

    variants: list[DeliverableVariantIn] | None = None


class RenderPreviewIn(BaseModel):
    template_key: str = Field(min_length=1, max_length=128)
    client_id: int = Field(ge=1)
    swap_colors: bool = False
    logo_slot: ImageSlotSource = "default"
    photo1_slot: ImageSlotSource = "default"
    photo2_slot: ImageSlotSource = "default"
    show_side_photo: bool = Field(
        default=True,
        description="Template moderne (signature-v2) : afficher la vignette à droite (photo 1).",
    )
