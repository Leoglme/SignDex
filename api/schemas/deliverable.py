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
        description="signature-v2 : vignette à droite ; v6/v8 : portrait à gauche.",
    )
    show_right_logo: bool = Field(
        default=True,
        description="signature-v6 / v8 : logo à droite quand portrait actif (masque aussi le filet).",
    )
    show_notes: bool = Field(
        default=False,
        description="signature-v1 / v2 : afficher la 1re ligne des notes (ex. adresse).",
    )
    color_primary: str | None = Field(
        default=None,
        max_length=32,
        description="Surcharge couleur 1 (#hex ou tout CSS color) ; vide / null = couleur de la fiche client.",
    )
    color_secondary: str | None = Field(default=None, max_length=32)
    title: str | None = Field(
        default=None,
        max_length=255,
        description="Titre figé au moment « Ajouter au livrable » (aperçu / v1-v2).",
    )
    subtitle: str | None = Field(default=None, max_length=255)


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
        description="signature-v2 : vignette à droite ; v6/v8 : portrait à gauche.",
    )
    show_right_logo: bool = Field(
        default=True,
        description="signature-v6 / v8 : logo à droite quand portrait actif.",
    )
    show_notes: bool = Field(
        default=False,
        description="signature-v1 / v2 : afficher la 1re ligne des notes (ex. adresse).",
    )
    color_primary: str | None = Field(default=None, max_length=32)
    color_secondary: str | None = Field(default=None, max_length=32)
    title: str | None = Field(default=None, max_length=255)
    subtitle: str | None = Field(default=None, max_length=255)
