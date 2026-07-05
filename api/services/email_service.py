"""Envoi d'emails transactionnels via Resend (ex. réinitialisation de mot de passe).

Domaine d'envoi vérifié dans Resend : `mail.dibodev.fr` (partagé avec devleadhunter).
API : POST https://api.resend.com/emails — https://resend.com/docs/api-reference/emails/send-email
"""

from __future__ import annotations

import logging

import httpx

from config import get_settings
from models import Organization, User
from services.email_templates import render_password_reset_email

logger = logging.getLogger("signdex.email")

_RESEND_SEND_URL = "https://api.resend.com/emails"


async def _resend_send(*, from_field: str, to_email: str, subject: str, html: str) -> None:
    """Envoie un email via l'API Resend. Lève si non configuré ou si Resend répond une erreur."""
    settings = get_settings()
    if not settings.resend_api_key:
        raise RuntimeError("RESEND_API_KEY non configuré")
    payload = {"from": from_field, "to": [to_email], "subject": subject, "html": html}
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(
            _RESEND_SEND_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {settings.resend_api_key}",
                "Content-Type": "application/json",
            },
        )
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Resend {resp.status_code}: {resp.text}")
    logger.info("[Resend] email « %s » envoyé à %s", subject, to_email)


async def send_password_reset_email(user: User, org: Organization | None, reset_url: str) -> None:
    """Envoie l'email « mot de passe oublié » aux couleurs de l'organisation."""
    settings = get_settings()
    org_name = (org.name if org and org.name else "") or settings.resend_from_name
    from_field = f"{org_name} <{settings.resend_from_email}>"
    html = render_password_reset_email(
        org_name=org_name,
        brand_color=(org.brand_color if org else None) or "#111827",
        logo_url=org.brand_logo_url if org else None,
        reset_url=reset_url,
        expires_hours=settings.reset_ttl_hours,
    )
    subject = f"Réinitialisation de votre mot de passe — {org_name}"
    await _resend_send(from_field=from_field, to_email=user.email, subject=subject, html=html)
