from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from core.database import get_db
from models import Client
from schemas.deliverable import RenderPreviewIn
from services.render_service import render_overrides_from_image_slots, render_signature_html
from services.template_service import load_template_html

router = APIRouter()


def _placeholder_client() -> Client:
    # Client "fictif" uniquement pour l’aperçu quand aucun client n’est sélectionné.
    return Client(
        name="Nom du client",
        subtitle="Sous-titre / slogan",
        website_url="https://example.com",
        email="contact@example.com",
        phone_primary="06 12 34 56 78",
        phone_secondary="07 98 76 54 32",
        linkedin_url="https://www.linkedin.com/company/example",
        instagram_url="https://www.instagram.com/example/",
        facebook_url="https://www.facebook.com/example",
        tiktok_url="https://www.tiktok.com/@example",
        youtube_url="https://www.youtube.com/@example",
        color_primary="#4e8baa",
        color_secondary="#5a9abf",
        # Images placeholders: volontairement vides (l’utilisateur verra un “trou” propre)
        logo_url="",
        photo1_url="",
        photo2_url="",
        notes="Ville / pays",
    )


@router.get("/render/{template_key}.html")
def render_template_html(
    template_key: str,
    client_id: int | None = Query(default=None, description="Si absent: placeholder"),
    db: Session = Depends(get_db),
) -> Response:
    raw = load_template_html(template_key)
    if client_id is None:
        client = _placeholder_client()
    else:
        client = db.get(Client, client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client introuvable")

    html = render_signature_html(template_html=raw, client=client)
    return Response(content=html, media_type="text/html; charset=utf-8")


@router.post("/render/preview")
def render_preview(
    payload: RenderPreviewIn = Body(...),
    db: Session = Depends(get_db),
) -> Response:
    """Aperçu HTML avec overrides (swap couleurs, URLs images) sans modifier la fiche client."""
    raw = load_template_html(payload.template_key)
    client = db.get(Client, payload.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client introuvable")

    overrides = render_overrides_from_image_slots(
        client=client,
        swap_colors=payload.swap_colors,
        logo_slot=payload.logo_slot,
        photo1_slot=payload.photo1_slot,
        photo2_slot=payload.photo2_slot,
        show_side_photo=payload.show_side_photo,
    )
    html = render_signature_html(template_html=raw, client=client, overrides=overrides)
    return Response(content=html, media_type="text/html; charset=utf-8")

