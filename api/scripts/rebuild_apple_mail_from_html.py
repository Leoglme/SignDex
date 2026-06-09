"""Regénère les fichiers apple-mail/*/signature.mailsignature depuis le dossier HTML/ d'un livrable."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# api/ sur sys.path
_API_ROOT = Path(__file__).resolve().parent.parent
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

from services.render_service import (  # noqa: E402
    build_mailsignature_document,
    write_mailsignature_file,
)


def rebuild(deliverable_dir: Path) -> int:
    html_dir = deliverable_dir / "HTML"
    apple_dir = deliverable_dir / "apple-mail"
    if not html_dir.is_dir():
        print(f"Dossier HTML introuvable : {html_dir}", file=sys.stderr)
        return 1
    apple_dir.mkdir(parents=True, exist_ok=True)

    n = 0
    for html_path in sorted(html_dir.glob("*.html")):
        stem = html_path.stem
        out_dir = apple_dir / stem
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "signature.mailsignature"
        full_html = html_path.read_text(encoding="utf-8")
        write_mailsignature_file(out_file, build_mailsignature_document(full_html))
        print(f"OK  {out_file.relative_to(deliverable_dir)}")
        n += 1
    if not n:
        print(f"Aucun .html dans {html_dir}", file=sys.stderr)
        return 1
    return 0


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "deliverable_dir",
        type=Path,
        help="Dossier livrable (contient HTML/ et apple-mail/)",
    )
    args = p.parse_args()
    raise SystemExit(rebuild(args.deliverable_dir.resolve()))


if __name__ == "__main__":
    main()
