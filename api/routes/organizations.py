from __future__ import annotations

import asyncio
import io
import uuid
import zipfile
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import get_db
from models import Client, Organization, OrganizationMember, OrganizationOffice
from routes.generate import _safe_slug
from schemas.organizations import (
    MemberIn,
    MemberOut,
    MemberUpdate,
    OfficeIn,
    OfficeOut,
    OrganizationCreate,
    OrganizationOut,
    OrganizationSummary,
    OrganizationUpdate,
)
from services.render_service import (
    OrgSigJob,
    build_mailsignature_document,
    encode_mailsignature_document,
    png_to_jpg_bytes,
    render_org_assets,
    render_signature_html,
)
from services.supabase_storage_service import is_configured, upload_template_asset_bytes_sync
from services.template_service import list_templates, load_template_html

router = APIRouter()


def _known_template_keys() -> set[str]:
    return {t.key for t in list_templates()}


def _member_full_name(m: OrganizationMember) -> str:
    return " ".join(p for p in (m.firstname, m.lastname) if p) or "Membre"


def _member_client(m: OrganizationMember) -> Client:
    """Client transitoire (non persisté) pour réutiliser le pipeline de rendu signature."""
    return Client(
        name=_member_full_name(m),
        firstname=m.firstname,
        lastname=m.lastname,
        title=m.title,
    )


# Lien par défaut des villes cliquables (page « Offices » du site) si aucun n'est défini sur le bureau.
_DEFAULT_OFFICE_URL = "https://lexial.eu/offices/"

# Signature « modèle vierge » : nom + fonction laissés VIDES (2 lignes vides que le client remplit
# dans Outlook). Rendu via l'extra `is_blank=True` → le template garde la hauteur des lignes.
_TEMPLATE_SENDER_LABEL = "Modèle à compléter"


def _template_client() -> Client:
    """Client transitoire pour la signature « modèle vierge » (nom + fonction laissés vides)."""
    return Client(name="", firstname="", lastname="", title="")


def _org_common_extra(org: Organization) -> dict:
    """Variables Jinja communes à toutes les signatures de l'organisation (hors bureau courant)."""
    return {
        "chambers_visible": org.show_chambers,
        "phone_visible": org.show_phone,
        "sig_logo_url": org.sig_logo_url,
        "sig_chambers_url": org.sig_chambers_url,
        # Villes cliquables (mêmes sur toutes les signatures), dans l'ordre des bureaux.
        "offices": [{"label": o.label, "url": o.city_url or _DEFAULT_OFFICE_URL} for o in org.offices],
    }


def _office_extra(office: OrganizationOffice) -> dict:
    """Bloc `office` du bureau courant (téléphone optionnel + adresse historique)."""
    return {
        "street": office.address_street,
        "cp_city": office.address_cp_city,
        "phone_display": office.phone_display,
        "phone_tel": office.phone_tel,
    }


def _signature_count(org: Organization) -> int:
    return sum(len(m.offices) for m in org.members)


def _get_org_or_404(db: Session, org_id: int) -> Organization:
    org = db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organisation introuvable")
    return org


# --------------------------------------------------------------------------- #
#  CRUD organisations
# --------------------------------------------------------------------------- #
@router.get("", response_model=list[OrganizationSummary])
def list_organizations(db: Session = Depends(get_db)) -> list[OrganizationSummary]:
    orgs = list(db.execute(select(Organization).order_by(Organization.created_at.desc())).scalars().all())
    return [
        OrganizationSummary(
            id=o.id,
            name=o.name,
            slug=o.slug,
            notes=o.notes,
            show_chambers=o.show_chambers,
            brand_logo_url=o.brand_logo_url,
            brand_color=o.brand_color,
            default_theme=o.default_theme,
            office_count=len(o.offices),
            member_count=len(o.members),
            signature_count=_signature_count(o),
            created_at=o.created_at,
            updated_at=o.updated_at,
        )
        for o in orgs
    ]


@router.post("", response_model=OrganizationOut)
def create_organization(payload: OrganizationCreate, db: Session = Depends(get_db)) -> Organization:
    known = _known_template_keys()
    for off in payload.offices:
        if off.template_key not in known:
            raise HTTPException(status_code=400, detail=f"Template inconnu: {off.template_key}")
    org = Organization(
        name=payload.name,
        slug=_safe_slug(payload.name),
        notes=payload.notes,
        show_chambers=payload.show_chambers,
        show_phone=payload.show_phone,
        brand_logo_url=payload.brand_logo_url,
        brand_color=payload.brand_color,
    )
    for off in payload.offices:
        org.offices.append(
            OrganizationOffice(
                label=off.label,
                template_key=off.template_key,
                sort_order=off.sort_order,
                city_url=off.city_url,
            ),
        )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


@router.get("/{org_id}", response_model=OrganizationOut)
def get_organization(org_id: int, db: Session = Depends(get_db)) -> Organization:
    return _get_org_or_404(db, org_id)


@router.put("/{org_id}", response_model=OrganizationOut)
def update_organization(org_id: int, payload: OrganizationUpdate, db: Session = Depends(get_db)) -> Organization:
    org = _get_org_or_404(db, org_id)
    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"]:
        org.name = data["name"]
        org.slug = _safe_slug(data["name"])
    if "notes" in data:
        org.notes = data["notes"]
    if "show_chambers" in data and data["show_chambers"] is not None:
        org.show_chambers = data["show_chambers"]
    if "show_phone" in data and data["show_phone"] is not None:
        org.show_phone = data["show_phone"]
    for field in ("brand_logo_url", "brand_color", "sig_logo_url", "sig_chambers_url", "default_theme"):
        if field in data:
            setattr(org, field, data[field])
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


@router.post("/{org_id}/brand-logo")
async def upload_brand_logo(
    org_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Téléverse le logo de marque vers Supabase et le persiste sur l'organisation."""
    org = _get_org_or_404(db, org_id)
    if not is_configured():
        raise HTTPException(
            status_code=400,
            detail="Supabase n'est pas configuré (SUPABASE_URL / SUPABASE_API_KEY / SUPABASE_STORAGE_BUCKET)",
        )
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Fichier vide")
    ext = Path(file.filename or "logo.png").suffix or ".png"
    object_path = f"organizations/{org_id}/brand-{uuid.uuid4().hex}{ext}"
    url = await asyncio.to_thread(
        upload_template_asset_bytes_sync,
        object_path=object_path,
        data=data,
        content_type=file.content_type or "image/png",
    )
    org.brand_logo_url = url
    db.add(org)
    db.commit()
    db.refresh(org)
    return {"brand_logo_url": url}


@router.delete("/{org_id}")
def delete_organization(org_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    org = _get_org_or_404(db, org_id)
    db.delete(org)
    db.commit()
    return {"status": "ok"}


# --------------------------------------------------------------------------- #
#  Bureaux
# --------------------------------------------------------------------------- #
@router.post("/{org_id}/offices", response_model=OfficeOut)
def add_office(org_id: int, payload: OfficeIn, db: Session = Depends(get_db)) -> OrganizationOffice:
    org = _get_org_or_404(db, org_id)
    if payload.template_key not in _known_template_keys():
        raise HTTPException(status_code=400, detail=f"Template inconnu: {payload.template_key}")
    office = OrganizationOffice(
        organization_id=org.id,
        label=payload.label,
        template_key=payload.template_key,
        sort_order=payload.sort_order,
        city_url=payload.city_url,
    )
    db.add(office)
    db.commit()
    db.refresh(office)
    return office


@router.delete("/{org_id}/offices/{office_id}")
def delete_office(org_id: int, office_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    office = db.get(OrganizationOffice, office_id)
    if not office or office.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Bureau introuvable")
    db.delete(office)
    db.commit()
    return {"status": "ok"}


# --------------------------------------------------------------------------- #
#  Membres
# --------------------------------------------------------------------------- #
def _resolve_offices(db: Session, org_id: int, office_ids: list[int]) -> list[OrganizationOffice]:
    if not office_ids:
        return []
    offices = list(
        db.execute(
            select(OrganizationOffice).where(
                OrganizationOffice.id.in_(office_ids),
                OrganizationOffice.organization_id == org_id,
            ),
        ).scalars().all(),
    )
    found = {o.id for o in offices}
    missing = [i for i in office_ids if i not in found]
    if missing:
        raise HTTPException(status_code=400, detail=f"Bureau(x) hors organisation: {missing}")
    return offices


@router.post("/{org_id}/members", response_model=MemberOut)
def add_member(org_id: int, payload: MemberIn, db: Session = Depends(get_db)) -> OrganizationMember:
    org = _get_org_or_404(db, org_id)
    member = OrganizationMember(
        organization_id=org.id,
        firstname=payload.firstname,
        lastname=payload.lastname,
        title=payload.title,
        sort_order=payload.sort_order,
    )
    member.offices = _resolve_offices(db, org.id, payload.office_ids)
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@router.put("/{org_id}/members/{member_id}", response_model=MemberOut)
def update_member(
    org_id: int,
    member_id: int,
    payload: MemberUpdate,
    db: Session = Depends(get_db),
) -> OrganizationMember:
    member = db.get(OrganizationMember, member_id)
    if not member or member.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Membre introuvable")
    data = payload.model_dump(exclude_unset=True)
    for field in ("firstname", "lastname", "title", "sort_order"):
        if field in data:
            setattr(member, field, data[field])
    if "office_ids" in data and data["office_ids"] is not None:
        member.offices = _resolve_offices(db, org_id, data["office_ids"])
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@router.delete("/{org_id}/members/{member_id}")
def delete_member(org_id: int, member_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    member = db.get(OrganizationMember, member_id)
    if not member or member.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Membre introuvable")
    db.delete(member)
    db.commit()
    return {"status": "ok"}


# --------------------------------------------------------------------------- #
#  Livrable complet de l'organisation (1 clic)
# --------------------------------------------------------------------------- #
def _org_readme_intro(org_name: str) -> str:
    return (
        f"Ce dossier contient les signatures e-mail de toute l'organisation {org_name}.\n"
        "Les fichiers sont classés par TYPE (HTML, PNG, JPG, EXEMPLES, apple-mail) et nommés\n"
        "« prénom-nom_bureau » (ex. « emmanuel-ruchat_paris »). Chaque personne dispose d'une\n"
        "signature par bureau auquel elle est rattachée.\n"
        "\n"
        "Vous trouverez aussi des signatures « modele-a-completer_<bureau> » : ce sont des MODÈLES\n"
        "VIERGES (mise en forme complète, mais nom et fonction laissés VIDES). Importez-en un dans\n"
        "Outlook comme une signature normale, puis saisissez vos nom et fonction sur les deux lignes\n"
        "vides du haut. Pratique pour créer une signature sans repasser par nous.\n"
    )


def _build_deliverable_zip(
    org: Organization,
    members: list[OrganizationMember],
    zip_stem: str,
    *,
    include_blank_template: bool = False,
) -> Response:
    """Construit le ZIP (HTML / apple-mail / PNG / JPG / EXEMPLES) pour les membres donnés.

    `include_blank_template` : ajoute une signature « modèle vierge » à compléter par bureau
    (nom + fonction en repères) — réservé au livrable COMPLET, pas aux livrables d'un seul membre.
    """
    plan: list[tuple[str, str, str]] = []  # (member_slug, office_slug, rendered_html)
    jobs: list[OrgSigJob] = []
    common_extra = _org_common_extra(org)
    for member in members:
        if not member.offices:
            continue
        client = _member_client(member)
        member_slug = _safe_slug(_member_full_name(member))
        for office in member.offices:
            raw = load_template_html(office.template_key)
            rendered = render_signature_html(
                template_html=raw,
                client=client,
                extra={**common_extra, "office": _office_extra(office)},
            )
            plan.append((member_slug, _safe_slug(office.label), rendered))
            jobs.append(OrgSigJob(rendered_html=rendered, sender_name=_member_full_name(member)))

    # Modèle vierge à compléter (une variante par bureau) — seulement pour le livrable complet.
    if include_blank_template:
        template_client = _template_client()
        for office in org.offices:
            raw = load_template_html(office.template_key)
            rendered = render_signature_html(
                template_html=raw,
                client=template_client,
                extra={**common_extra, "office": _office_extra(office), "is_blank": True},
            )
            plan.append(("modele-a-completer", _safe_slug(office.label), rendered))
            jobs.append(OrgSigJob(rendered_html=rendered, sender_name=_TEMPLATE_SENDER_LABEL))

    if not jobs:
        raise HTTPException(
            status_code=400,
            detail="Aucune signature à générer : assigne au moins un bureau à un membre.",
        )

    assets = render_org_assets(jobs)  # [(sig_png, mail_png), ...] — un seul navigateur Chromium

    assets_dir = Path(__file__).resolve().parent.parent / "assets"
    readme_path = assets_dir / "LISEZMOI-signatures.txt"
    apple_readme_path = assets_dir / "LISEZMOI-apple-mail.txt"
    if not readme_path.exists() or not apple_readme_path.exists():
        raise HTTPException(status_code=500, detail="LISEZMOI manquant côté API")
    readme_txt = readme_path.read_text(encoding="utf-8").replace("%%INTRO%%", _org_readme_intro(org.name))
    apple_readme_txt = apple_readme_path.read_text(encoding="utf-8")

    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    zip_name = f"signdex_{zip_stem}_{now}.zip"
    used: dict[str, int] = {}

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("LISEZMOI-signatures.txt", readme_txt)
        z.writestr("LISEZMOI-apple-mail.txt", apple_readme_txt)
        for (member_slug, office_slug, rendered_html), (sig_png, mail_png) in zip(plan, assets):
            stem = f"{member_slug}_{office_slug}"
            used[stem] = used.get(stem, 0) + 1
            if used[stem] > 1:
                stem = f"{stem}-{used[stem]}"
            z.writestr(f"HTML/{stem}.html", rendered_html)
            z.writestr(
                f"apple-mail/{stem}/signature.mailsignature",
                encode_mailsignature_document(build_mailsignature_document(rendered_html)),
            )
            z.writestr(f"PNG/{stem}.png", sig_png)
            z.writestr(f"JPG/{stem}.jpg", png_to_jpg_bytes(png_bytes=sig_png))
            z.writestr(f"EXEMPLES/{stem}_apercu-mail.jpg", png_to_jpg_bytes(png_bytes=mail_png))

    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{zip_name}"'},
    )


@router.post("/{org_id}/deliverable")
def generate_organization_deliverable(
    org_id: int,
    _: dict | None = Body(default=None),
    db: Session = Depends(get_db),
) -> Response:
    """Livrable COMPLET : toutes les signatures de tous les membres, en un seul ZIP."""
    org = _get_org_or_404(db, org_id)
    return _build_deliverable_zip(org, list(org.members), org.slug, include_blank_template=True)


@router.post("/{org_id}/members/{member_id}/deliverable")
def generate_member_deliverable(
    org_id: int,
    member_id: int,
    _: dict | None = Body(default=None),
    db: Session = Depends(get_db),
) -> Response:
    """Livrable d'UN membre (ex. nouveau stagiaire) : ses signatures seulement."""
    org = _get_org_or_404(db, org_id)
    member = db.get(OrganizationMember, member_id)
    if not member or member.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Membre introuvable")
    return _build_deliverable_zip(org, [member], f"{org.slug}_{_safe_slug(_member_full_name(member))}")
