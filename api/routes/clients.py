from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import get_db
from models import Client
from schemas.clients import ClientCreate, ClientOut, ClientUpdate
from services.supabase_storage_service import is_configured, upload_image_bytes

router = APIRouter()


@router.get("", response_model=list[ClientOut])
def list_clients(db: Session = Depends(get_db)) -> list[Client]:
    return list(db.execute(select(Client).order_by(Client.created_at.desc())).scalars().all())


@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: int, db: Session = Depends(get_db)) -> Client:
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client introuvable")
    return client


@router.post("", response_model=ClientOut)
def create_client(payload: ClientCreate, db: Session = Depends(get_db)) -> Client:
    client = Client(**payload.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.put("/{client_id}", response_model=ClientOut)
def update_client(client_id: int, payload: ClientUpdate, db: Session = Depends(get_db)) -> Client:
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client introuvable")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(client, k, v)
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client introuvable")
    db.delete(client)
    db.commit()
    return {"status": "ok"}


@router.post("/{client_id}/upload")
async def upload_client_image(
    client_id: int,
    field: str = Query(
        description="Champ à mettre à jour: logo_url | photo1_url | photo2_url",
        pattern="^(logo_url|photo1_url|photo2_url)$",
    ),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client introuvable")
    if not is_configured():
        raise HTTPException(
            status_code=400,
            detail="Supabase n'est pas configuré (SUPABASE_URL / SUPABASE_API_KEY / SUPABASE_STORAGE_BUCKET)",
        )
    data = await file.read()
    url = await upload_image_bytes(client_id=client_id, data=data, original_filename=file.filename)
    setattr(client, field, url)
    db.add(client)
    db.commit()
    db.refresh(client)
    return {"url": url}

