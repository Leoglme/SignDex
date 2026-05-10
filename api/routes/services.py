from __future__ import annotations

import io
import zipfile
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from core.database import get_db
from models import Client
from schemas.service_deliverable import ServiceDeliverableRequest, ServiceDeliverableVariantIn, ServiceRenderPreviewIn
from services.render_service import (
    html_to_png_bytes,
    png_to_jpg_bytes,
    render_overrides_from_image_slots,
    render_jinja_html,
)
from services.template_service import list_service_templates, load_service_template_html

router = APIRouter(prefix="/services")


_KNOWN_SERVICES = {
    "flyer": "Flyer",
    "banners": "Bannières réseaux",
    "cards-visite": "Cartes de visite",
    "cards-fidelite": "Cartes de fidélité",
}


def _ensure_service(service: str) -> str:
    s = (service or "").strip().lower()
    if s not in _KNOWN_SERVICES:
        raise HTTPException(status_code=404, detail=f"Service inconnu: {service}")
    return s


def _safe_slug(name: str) -> str:
    keep = []
    for ch in name.strip():
        if ch.isalnum():
            keep.append(ch.lower())
        elif ch in (" ", "-", "_"):
            keep.append("-")
    s = "".join(keep)
    while "--" in s:
        s = s.replace("--", "-")
    return s.strip("-") or "client"


def _variant_zip_stems(slug: str, variants: list[ServiceDeliverableVariantIn]) -> list[tuple[ServiceDeliverableVariantIn, str]]:
    per_key_count: dict[str, int] = {}
    out: list[tuple[ServiceDeliverableVariantIn, str]] = []
    for v in variants:
        per_key_count[v.template_key] = per_key_count.get(v.template_key, 0) + 1
        n = per_key_count[v.template_key]
        base = f"{slug}_{v.template_key}"
        stem = base if n == 1 else f"{base}_variant-{n}"
        out.append((v, stem))
    return out


def _viewport_for(service: str, template_key: str) -> tuple[int, int]:
    """Viewport par défaut pour le screenshot Chromium.

    On reste volontairement simple: les templates doivent définir une taille fixe via CSS (width/height),
    et on donne un viewport assez grand pour éviter un crop.
    """
    # Flyers: A4 portrait → viewport généreux pour ne pas couper le bas (page = 794×1123 @96dpi).
    if service == "flyer":
        return 900, 1300
    # Cartes (visite et fidélité): format imprimable type VistaPrint (3.5"×2" = 1050×600 @300dpi).
    # Les templates rendent recto+verso côte à côte (chaque carte = 1050×600, gap 60px → total 2160×620).
    if service in ("cards-visite", "cards-fidelite"):
        return 2240, 700
    if service == "banners":
        key = (template_key or "").lower()
        if "linkedin" in key:
            return 1700, 600
        if "youtube" in key:
            return 2800, 1700
        if key.startswith("x-") or "twitter" in key or "xheader" in key or "x_header" in key or "xheader" in key:
            return 1700, 700
        if "facebook" in key:
            return 1900, 800
        return 2000, 900
    return 1600, 900


@router.get("/{service}/templates")
def get_service_templates(service: str) -> list[dict[str, str]]:
    svc = _ensure_service(service)
    return [{"key": t.key, "filename": t.filename, "title": t.title} for t in list_service_templates(svc)]


@router.post("/{service}/render/preview")
def render_service_preview(
    service: str,
    payload: ServiceRenderPreviewIn = Body(...),
    db: Session = Depends(get_db),
) -> Response:
    svc = _ensure_service(service)
    raw = load_service_template_html(svc, payload.template_key)
    client = db.get(Client, payload.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client introuvable")
    overrides = render_overrides_from_image_slots(
        client=client,
        swap_colors=payload.swap_colors,
        logo_slot=payload.logo_slot,
        photo1_slot=payload.photo1_slot,
        photo2_slot=payload.photo2_slot,
        show_side_photo=True,
        color_primary=payload.color_primary,
        color_secondary=payload.color_secondary,
    )
    html = render_jinja_html(template_html=raw, client=client, overrides=overrides)
    return Response(content=html, media_type="text/html; charset=utf-8")


@router.post("/{service}/clients/{client_id}/deliverable")
def generate_service_deliverable(
    service: str,
    client_id: int,
    payload: ServiceDeliverableRequest | None = Body(default=None),
    db: Session = Depends(get_db),
) -> Response:
    svc = _ensure_service(service)

    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client introuvable")

    templates_all = list_service_templates(svc)
    if not templates_all:
        raise HTTPException(status_code=500, detail=f"Aucun template trouvé côté API pour le service: {svc}")

    known_keys = {t.key for t in templates_all}
    if payload and payload.variants is not None:
        variants_in = payload.variants
    else:
        variants_in = [ServiceDeliverableVariantIn(template_key=t.key) for t in templates_all]

    if not variants_in:
        raise HTTPException(status_code=400, detail="Au moins une variante dans le livrable")

    for v in variants_in:
        if v.template_key not in known_keys:
            raise HTTPException(status_code=400, detail=f"Template inconnu ({svc}): {v.template_key}")

    readme_txt = (
        f"SignDex — Livrable { _KNOWN_SERVICES[svc] }\n"
        f"Client : {client.name}\n\n"
        "Contenu:\n"
        "- HTML/ : versions HTML (si applicable)\n"
        "- PNG/  : exports PNG\n"
        "- JPG/  : exports JPG\n"
    )

    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    slug = _safe_slug(client.name)
    zip_name = f"signdex_{svc}_{slug}_{now}.zip"

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("LISEZMOI.txt", readme_txt)

        for v, stem in _variant_zip_stems(slug, variants_in):
            raw_template = load_service_template_html(svc, v.template_key)
            overrides = render_overrides_from_image_slots(
                client=client,
                swap_colors=v.swap_colors,
                logo_slot=v.logo_slot,
                photo1_slot=v.photo1_slot,
                photo2_slot=v.photo2_slot,
                show_side_photo=True,
                color_primary=v.color_primary,
                color_secondary=v.color_secondary,
            )
            rendered_html = render_jinja_html(template_html=raw_template, client=client, overrides=overrides)
            z.writestr(f"HTML/{stem}.html", rendered_html)

            vw, vh = _viewport_for(svc, v.template_key)
            png = html_to_png_bytes(html=rendered_html, viewport_width=vw, viewport_height=vh)
            jpg = png_to_jpg_bytes(png_bytes=png)

            z.writestr(f"PNG/{stem}.png", png)
            z.writestr(f"JPG/{stem}.jpg", jpg)

    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{zip_name}"'},
    )

