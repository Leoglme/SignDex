"""Endpoints de l'espace client (« Mon espace »).

Scoping implicite : l'organisation du compte connecté (`current.organization_id`).
Aucun `org_id` dans l'URL → un client ne peut jamais toucher une autre organisation.
"""

from __future__ import annotations

import asyncio
import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import get_current_user
from models import GeneratedDeliverable, Organization, OrganizationMember, OrganizationOffice, User
from routes.generate import _safe_slug
from routes.organizations import (
    _build_deliverable_zip,
    _member_client,
    _member_full_name,
    _office_extra,
    _org_common_extra,
    _resolve_offices,
    _signature_count,
)
from schemas.organizations import (
    MemberIn,
    MemberOut,
    MemberPreviewOut,
    MemberUpdate,
    OfficeOut,
    OfficeUpdate,
    PortalDeliverableOut,
    PortalOrganizationOut,
    PortalOverviewOut,
    PortalSettingsUpdate,
    SignaturePreview,
)
from services.render_service import render_signature_html
from services.supabase_storage_service import is_configured, upload_template_asset_bytes_sync
from services.template_service import load_template_html

router = APIRouter()


def _current_org(current: User, db: Session) -> Organization:
    if not current.organization_id:
        raise HTTPException(status_code=403, detail="Aucune organisation associée à ce compte")
    org = db.get(Organization, current.organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organisation introuvable")
    return org


def _tel_from_display(display: str | None) -> str | None:
    """Construit le lien `tel:` à partir du téléphone affiché (garde chiffres + un « + » initial)."""
    s = (display or "").strip()
    if not s:
        return None
    digits = re.sub(r"\D", "", s)
    if not digits:
        return None
    return ("+" + digits) if s.startswith("+") else digits


def _member_or_404(db: Session, org: Organization, member_id: int) -> OrganizationMember:
    member = db.get(OrganizationMember, member_id)
    if not member or member.organization_id != org.id:
        raise HTTPException(status_code=404, detail="Collaborateur introuvable")
    return member


def _build_overview(org: Organization) -> PortalOverviewOut:
    return PortalOverviewOut(
        organization=PortalOrganizationOut(
            id=org.id,
            name=org.name,
            brand_logo_url=org.brand_logo_url,
            brand_color=org.brand_color,
            sig_logo_url=org.sig_logo_url,
            sig_chambers_url=org.sig_chambers_url,
            show_chambers=org.show_chambers,
            show_phone=org.show_phone,
            member_count=len(org.members),
            signature_count=_signature_count(org),
        ),
        members=[MemberOut.model_validate(m) for m in org.members],
        offices=[OfficeOut.model_validate(o) for o in org.offices],
    )


@router.get("/overview", response_model=PortalOverviewOut)
def overview(current: User = Depends(get_current_user), db: Session = Depends(get_db)) -> PortalOverviewOut:
    return _build_overview(_current_org(current, db))


# --------------------------------------------------------------------------- #
#  Collaborateurs (ajouter un stagiaire, modifier, déplacer entre bureaux, retirer)
# --------------------------------------------------------------------------- #
@router.post("/members", response_model=MemberOut)
def add_member(
    payload: MemberIn,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrganizationMember:
    org = _current_org(current, db)
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


@router.put("/members/{member_id}", response_model=MemberOut)
def update_member(
    member_id: int,
    payload: MemberUpdate,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrganizationMember:
    org = _current_org(current, db)
    member = _member_or_404(db, org, member_id)
    data = payload.model_dump(exclude_unset=True)
    for field in ("firstname", "lastname", "title", "sort_order"):
        if field in data:
            setattr(member, field, data[field])
    if "office_ids" in data and data["office_ids"] is not None:
        member.offices = _resolve_offices(db, org.id, data["office_ids"])
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@router.delete("/members/{member_id}")
def delete_member(
    member_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    org = _current_org(current, db)
    member = _member_or_404(db, org, member_id)
    db.delete(member)
    db.commit()
    return {"status": "ok"}


# --------------------------------------------------------------------------- #
#  Bureaux (modifier une adresse = déménagement ; ajouter un bureau)
# --------------------------------------------------------------------------- #
@router.put("/offices/{office_id}", response_model=OfficeOut)
def update_office(
    office_id: int,
    payload: OfficeUpdate,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrganizationOffice:
    org = _current_org(current, db)
    office = db.get(OrganizationOffice, office_id)
    if not office or office.organization_id != org.id:
        raise HTTPException(status_code=404, detail="Bureau introuvable")
    data = payload.model_dump(exclude_unset=True)
    for field in ("label", "city_url", "address_street", "address_cp_city", "phone_display", "phone_tel", "sort_order"):
        if field in data and data[field] is not None:
            setattr(office, field, data[field])
    # Le lien tel: est toujours dérivé du téléphone affiché (un seul champ côté client).
    if "phone_display" in data:
        office.phone_tel = _tel_from_display(office.phone_display)
    db.add(office)
    db.commit()
    db.refresh(office)
    return office


@router.put("/settings", response_model=PortalOverviewOut)
def update_settings(
    payload: PortalSettingsUpdate,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PortalOverviewOut:
    """Options de signature pilotables par le client (afficher/masquer le téléphone, le logo Chambers)."""
    org = _current_org(current, db)
    data = payload.model_dump(exclude_unset=True)
    if "show_phone" in data and data["show_phone"] is not None:
        org.show_phone = data["show_phone"]
    if "show_chambers" in data and data["show_chambers"] is not None:
        org.show_chambers = data["show_chambers"]
    db.add(org)
    db.commit()
    db.refresh(org)
    return _build_overview(org)


@router.post("/offices", response_model=OfficeOut)
def add_office(
    payload: OfficeUpdate,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrganizationOffice:
    org = _current_org(current, db)
    if not payload.label:
        raise HTTPException(status_code=400, detail="Le nom du bureau est requis")
    # Le modèle de design est dérivé d'un bureau existant : les templates ne diffèrent plus
    # que par l'adresse (désormais en données), donc n'importe lequel convient.
    base = org.offices[0] if org.offices else None
    if base is None:
        raise HTTPException(status_code=400, detail="Impossible de déterminer le modèle du bureau")
    office = OrganizationOffice(
        organization_id=org.id,
        label=payload.label,
        template_key=base.template_key,
        sort_order=payload.sort_order if payload.sort_order is not None else len(org.offices),
        city_url=payload.city_url,
        address_street=payload.address_street,
        address_cp_city=payload.address_cp_city,
        phone_display=payload.phone_display,
        phone_tel=_tel_from_display(payload.phone_display),
    )
    db.add(office)
    db.commit()
    db.refresh(office)
    return office


# --------------------------------------------------------------------------- #
#  Images de la signature (logo + Chambers) — upload / réinitialisation
# --------------------------------------------------------------------------- #
@router.post("/signature-image")
async def upload_signature_image(
    field: str = Query(pattern="^(logo|chambers)$"),
    file: UploadFile = File(...),
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str | None]:
    org = _current_org(current, db)
    if not is_configured():
        raise HTTPException(status_code=400, detail="Stockage d'images non configuré")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Fichier vide")
    ext = Path(file.filename or "img.png").suffix or ".png"
    object_path = f"organizations/{org.id}/sig-{field}-{uuid.uuid4().hex}{ext}"
    url = await asyncio.to_thread(
        upload_template_asset_bytes_sync,
        object_path=object_path,
        data=data,
        content_type=file.content_type or "image/png",
    )
    if field == "logo":
        org.sig_logo_url = url
    else:
        org.sig_chambers_url = url
    db.add(org)
    db.commit()
    return {"field": field, "url": url}


@router.delete("/signature-image")
def reset_signature_image(
    field: str = Query(pattern="^(logo|chambers)$"),
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str | None]:
    org = _current_org(current, db)
    if field == "logo":
        org.sig_logo_url = None
    else:
        org.sig_chambers_url = None
    db.add(org)
    db.commit()
    return {"field": field, "url": None}


# --------------------------------------------------------------------------- #
#  Téléchargements + historique
# --------------------------------------------------------------------------- #
def _record(db: Session, org: Organization, current: User, *, scope: str, member: OrganizationMember | None, label: str, count: int) -> None:
    db.add(
        GeneratedDeliverable(
            organization_id=org.id,
            created_by_user_id=current.id,
            scope=scope,
            member_id=member.id if member else None,
            label=label,
            file_url="",
            signature_count=count,
        ),
    )
    db.commit()


@router.post("/deliverable")
def deliverable(
    _: dict | None = Body(default=None),
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Livrable complet (toutes les signatures) + enregistrement dans l'historique."""
    org = _current_org(current, db)
    resp = _build_deliverable_zip(org, list(org.members), org.slug, include_blank_template=True)
    _record(db, org, current, scope="all", member=None, label="Toutes les signatures", count=_signature_count(org))
    return resp


@router.post("/members/{member_id}/deliverable")
def member_deliverable(
    member_id: int,
    _: dict | None = Body(default=None),
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Livrable d'un seul collaborateur (ses signatures) + historique."""
    org = _current_org(current, db)
    member = _member_or_404(db, org, member_id)
    resp = _build_deliverable_zip(org, [member], f"{org.slug}_{_safe_slug(_member_full_name(member))}")
    _record(db, org, current, scope="member", member=member, label=_member_full_name(member), count=len(member.offices))
    return resp


@router.get("/members/{member_id}/preview", response_model=MemberPreviewOut)
def member_preview(
    member_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MemberPreviewOut:
    """Aperçu (HTML rendu) des signatures d'un collaborateur — une par bureau."""
    org = _current_org(current, db)
    member = _member_or_404(db, org, member_id)
    client = _member_client(member)
    common_extra = _org_common_extra(org)
    previews: list[SignaturePreview] = []
    for office in member.offices:
        raw = load_template_html(office.template_key)
        html = render_signature_html(
            template_html=raw,
            client=client,
            extra={**common_extra, "office": _office_extra(office)},
        )
        previews.append(SignaturePreview(office_label=office.label, html=html))
    return MemberPreviewOut(member_name=_member_full_name(member), signatures=previews)


@router.get("/deliverables", response_model=list[PortalDeliverableOut])
def deliverables_history(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[GeneratedDeliverable]:
    org = _current_org(current, db)
    return list(
        db.execute(
            select(GeneratedDeliverable)
            .where(GeneratedDeliverable.organization_id == org.id)
            .order_by(GeneratedDeliverable.created_at.desc())
            .limit(50),
        ).scalars().all(),
    )
