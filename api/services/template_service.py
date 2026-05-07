from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bs4 import BeautifulSoup

from config import get_settings


@dataclass(frozen=True)
class TemplateInfo:
    key: str
    filename: str
    title: str


def _extract_title(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    t = soup.find("title")
    if t and t.text and t.text.strip():
        return t.text.strip()
    return "Signature"


def list_templates() -> list[TemplateInfo]:
    settings = get_settings()
    base = Path(settings.signdex_templates_dir)
    items: list[TemplateInfo] = []
    for p in sorted(base.glob("*.html")):
        raw = p.read_text(encoding="utf-8", errors="ignore")
        title = _extract_title(raw)
        items.append(TemplateInfo(key=p.stem, filename=p.name, title=title))
    return items


def load_template_html(template_key: str) -> str:
    settings = get_settings()
    base = Path(settings.signdex_templates_dir)
    p = base / f"{template_key}.html"
    if not p.exists():
        raise FileNotFoundError(f"Template introuvable: {template_key}")
    return p.read_text(encoding="utf-8", errors="strict")

