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
from schemas.deliverable import DeliverableRequest, DeliverableVariantIn
from services.render_service import (
    fake_mail_preview_to_png_bytes,
    html_to_png_bytes,
    png_to_jpg_bytes,
    render_overrides_from_image_slots,
    render_signature_html,
)
from services.template_service import list_templates, load_template_html

router = APIRouter()


def _lisezmoi_intro(*, n_templates: int) -> str:
    if n_templates <= 0:
        return "Ce dossier ne contient aucune version de signature.\n"
    if n_templates == 1:
        return (
            "Ce dossier contient une version de signature pour Gmail. Vous pouvez\n"
            "l’utiliser telle quelle ou l’adapter selon vos besoins.\n"
        )
    return (
        f"Ce dossier contient {n_templates} versions différentes de signature pour Gmail. Vous\n"
        "pouvez choisir celle que vous préférez visuellement.\n"
    )


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


def _variant_zip_stems(slug: str, variants: list[DeliverableVariantIn]) -> list[tuple[DeliverableVariantIn, str]]:
    """Première occurrence d’un template : `{slug}_{key}` ; suivantes : `_variant-2`, `_variant-3`, …"""
    per_key_count: dict[str, int] = {}
    out: list[tuple[DeliverableVariantIn, str]] = []
    for v in variants:
        per_key_count[v.template_key] = per_key_count.get(v.template_key, 0) + 1
        n = per_key_count[v.template_key]
        base = f"{slug}_{v.template_key}"
        stem = base if n == 1 else f"{base}_variant-{n}"
        out.append((v, stem))
    return out


@router.post("/clients/{client_id}/deliverable")
def generate_deliverable(
    client_id: int,
    payload: DeliverableRequest | None = Body(default=None),
    db: Session = Depends(get_db),
) -> Response:
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client introuvable")

    templates_all = list_templates()
    if not templates_all:
        raise HTTPException(status_code=500, detail="Aucun template trouvé côté API")

    known_keys = {t.key for t in templates_all}
    if payload and payload.variants is not None:
        variants_in = payload.variants
    else:
        variants_in = [DeliverableVariantIn(template_key=t.key) for t in templates_all]

    if not variants_in:
        raise HTTPException(status_code=400, detail="Au moins une variante dans le livrable")

    for v in variants_in:
        if v.template_key not in known_keys:
            raise HTTPException(status_code=400, detail=f"Template inconnu: {v.template_key}")

    readme_path = Path(__file__).resolve().parent.parent / "assets" / "LISEZMOI-signatures.txt"
    if not readme_path.exists():
        raise HTTPException(status_code=500, detail="LISEZMOI-signatures.txt manquant côté API")
    readme_txt = readme_path.read_text(encoding="utf-8").replace(
        "%%INTRO%%",
        _lisezmoi_intro(n_templates=len(variants_in)),
    )

    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    slug = _safe_slug(client.name)
    zip_name = f"signdex_{slug}_{now}.zip"

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("LISEZMOI-signatures.txt", readme_txt)

        for v, stem in _variant_zip_stems(slug, variants_in):
            raw_template = load_template_html(v.template_key)
            overrides = render_overrides_from_image_slots(
                client=client,
                swap_colors=v.swap_colors,
                logo_slot=v.logo_slot,
                photo1_slot=v.photo1_slot,
                photo2_slot=v.photo2_slot,
                show_side_photo=v.show_side_photo,
            )
            rendered_html = render_signature_html(template_html=raw_template, client=client, overrides=overrides)

            z.writestr(f"HTML/{stem}.html", rendered_html)

            png = html_to_png_bytes(html=rendered_html)
            jpg = png_to_jpg_bytes(png_bytes=png)

            z.writestr(f"PNG/{stem}.png", png)
            z.writestr(f"JPG/{stem}.jpg", jpg)

            exemple_mail_png = fake_mail_preview_to_png_bytes(
                rendered_signature_full_html=rendered_html,
                sender_name=client.name,
                sender_email=client.email,
            )
            z.writestr(
                f"EXEMPLES/{stem}_apercu-mail.jpg",
                png_to_jpg_bytes(png_bytes=exemple_mail_png),
            )

    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{zip_name}"'},
    )

