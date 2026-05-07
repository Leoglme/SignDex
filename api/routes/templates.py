from __future__ import annotations

from fastapi import APIRouter

from services.template_service import list_templates

router = APIRouter()


@router.get("")
def get_templates() -> list[dict[str, str]]:
    return [{"key": t.key, "filename": t.filename, "title": t.title} for t in list_templates()]

