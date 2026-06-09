"""Aperçu local des templates LEXIAL via le VRAI pipeline de rendu/export.

Génère, pour quelques personas et chaque template signature-lexial-*, le PNG de la
signature (crop table racine) + un aperçu « faux mail », dans assets/lexial/_preview/.

    docker exec signdex-api sh -c 'cd /app && PYTHONPATH=/app python scripts/preview_lexial.py'
"""

from __future__ import annotations

from pathlib import Path

from models import Client
from services.render_service import (
    fake_mail_preview_to_png_bytes,
    html_to_png_bytes,
    render_signature_html,
)
from services.template_service import load_template_html

_OUT = Path("/app/assets/lexial/_preview")

_TEMPLATES = [
    "signature-lexial-paris",
    "signature-lexial-geneva",
    "signature-lexial-brussels",
]

# (label, prénom, nom, titre) — name sert d'identifiant ; full_name = prénom+nom.
_PERSONAS = [
    ("emmanuel", "Emmanuel", "Ruchat", "Associé – Partner"),
    ("pierre", "Pierre", "Langlois de Bazillac", "Avocat associé – Partner"),
    ("sander", "Sander", "Van Hulle", "Of Counsel"),
    ("brisseau", None, "Brisseau", "Paralegal"),
]


def _client(firstname: str | None, lastname: str, title: str) -> Client:
    full = " ".join(p for p in (firstname, lastname) if p)
    return Client(name=full, firstname=firstname, lastname=lastname, title=title, email=None)


def main() -> None:
    _OUT.mkdir(parents=True, exist_ok=True)
    for key in _TEMPLATES:
        try:
            raw = load_template_html(key)
        except FileNotFoundError:
            print(f"skip (absent): {key}")
            continue
        for label, fn, ln, title in _PERSONAS:
            client = _client(fn, ln, title)
            html = render_signature_html(template_html=raw, client=client)
            png = html_to_png_bytes(html=html)
            (_OUT / f"{key}__{label}.png").write_bytes(png)
            print(f"ok: {key} / {label} ({len(png)} bytes)")
        # Un seul aperçu « faux mail » par template (persona = emmanuel) pour le contexte.
        client = _client("Emmanuel", "Ruchat", "Associé – Partner")
        html = render_signature_html(template_html=raw, client=client)
        mail = fake_mail_preview_to_png_bytes(
            rendered_signature_full_html=html,
            sender_name="Emmanuel Ruchat",
            sender_email="eruc@lexial.eu",
        )
        (_OUT / f"{key}__mail.png").write_bytes(mail)
        print(f"ok: {key} / mail ({len(mail)} bytes)")


if __name__ == "__main__":
    main()
