"""Héberge les assets de marque LEXIAL sur Supabase Storage (chemins fixes).

Usage (dans le conteneur API, Supabase configuré) :
    docker exec -e PYTHONPATH=/app -w /app signdex-api python scripts/host_lexial_assets.py

Imprime les URLs publiques à coller dans les templates signature-lexial-*.html.
Les sources sont versionnées dans api/assets/lexial/ pour pouvoir régénérer l'upload.
"""

from __future__ import annotations

from pathlib import Path

from services.supabase_storage_service import is_configured, upload_template_asset_bytes_sync

_SRC = Path(__file__).resolve().parent.parent / "assets" / "lexial"

# (chemin source local, chemin objet Supabase)
_ASSETS = [
    ("lexial-logo.png", "template-assets/lexial/lexial-logo.png"),
    ("chambers-provisional.png", "template-assets/lexial/chambers-provisional.png"),
]


def main() -> None:
    if not is_configured():
        raise SystemExit("Supabase non configuré (SUPABASE_URL / SUPABASE_API_KEY / SUPABASE_STORAGE_BUCKET).")
    for local_name, object_path in _ASSETS:
        src = _SRC / local_name
        if not src.exists():
            raise SystemExit(f"Source manquante: {src}")
        url = upload_template_asset_bytes_sync(
            object_path=object_path,
            data=src.read_bytes(),
            content_type="image/png",
        )
        print(f"{local_name} -> {url}")


if __name__ == "__main__":
    main()
