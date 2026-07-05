"""QA rapide : rend UNE signature (Emmanuel / Bruxelles) en PNG pour comparer à la cible client.

    docker exec signdex-api sh -c 'cd /app && PYTHONPATH=/app python scripts/qa_render.py'
"""

from __future__ import annotations

from pathlib import Path

from models import Client
from services.render_service import html_to_png_bytes, render_signature_html
from services.template_service import load_template_html

KEY = "signature-lexial-brussels"
FIRSTNAME = "Emmanuel"
LASTNAME = "Ruchat"
TITLE = "Avocat associé – Partner"

client = Client(name=f"{FIRSTNAME} {LASTNAME}", firstname=FIRSTNAME, lastname=LASTNAME, title=TITLE)
html = render_signature_html(template_html=load_template_html(KEY), client=client)
Path("/app/assets/lexial/_qa.png").write_bytes(html_to_png_bytes(html=html))
print("ok:", KEY, FIRSTNAME, LASTNAME, "|", TITLE)
