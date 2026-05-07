"""Formes décoratives signature-v4 : PNG hébergés Supabase (Gmail ne gère pas data:image/svg+xml)."""

from __future__ import annotations

import io
import urllib.error
import urllib.request
from urllib.parse import quote
from PIL import Image
from playwright.sync_api import sync_playwright

from config import get_settings
from services.supabase_storage_service import (
    is_configured,
    storage_public_url,
    upload_template_asset_bytes_sync,
)

_V4_PREFIX = "template-assets/v4"
# Bump quand la génération PNG change (ex. viewport) pour forcer un nouvel upload Supabase.
_V4_ASSET_SUFFIX = "-v2"

V4_TL_CSS_W = 145
V4_TL_CSS_H = 105
V4_BR_CSS_W = 121
V4_BR_CSS_H = 81

# Cache processus : évite HEAD / uploads répétés pour une même teinte.
_url_pair_cache: dict[str, tuple[str, str]] = {}


def normalize_hex_color(color: str | None, *, default: str = "e6189d") -> str:
    s = (color or "").strip().lstrip("#")
    if len(s) == 3 and all(c in "0123456789abcdefABCDEF" for c in s):
        s = "".join(c * 2 for c in s)
    if len(s) != 6 or not all(c in "0123456789abcdefABCDEF" for c in s):
        return default
    return s.lower()


def _object_paths(hex6: str) -> tuple[str, str]:
    return (
        f"{_V4_PREFIX}/corner-tl-{hex6}{_V4_ASSET_SUFFIX}.png",
        f"{_V4_PREFIX}/corner-br-{hex6}{_V4_ASSET_SUFFIX}.png",
    )


def _public_url_ok(url: str, timeout_s: float = 6.0) -> bool:
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout_s) as r:
            code = r.getcode()
            return 200 <= code < 400
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError):
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=timeout_s) as r:
                code = r.getcode()
                return 200 <= code < 400
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError):
            return False


def _png_downscale(png_bytes: bytes, device_scale: int) -> bytes:
    if device_scale <= 1:
        return png_bytes
    img = Image.open(io.BytesIO(png_bytes))
    if img.mode not in ("RGBA", "RGB"):
        img = img.convert("RGBA")
    w, h = img.size
    new_w = max(1, round(w / device_scale))
    new_h = max(1, round(h / device_scale))
    if new_w == w and new_h == h:
        return png_bytes
    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    out = io.BytesIO()
    resized.save(out, format="PNG", optimize=True)
    return out.getvalue()


def _html_corner_tl(fill_css: str) -> str:
    w, h = V4_TL_CSS_W, V4_TL_CSS_H
    return f"""<!DOCTYPE html><html><head>
<meta charset="utf-8"><style>
html,body{{margin:0;padding:0;background:transparent;overflow:hidden;width:{w}px;height:{h}px;}}
body{{display:block;line-height:0;font-size:0;}}
</style></head><body>
<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 180 130" style="display:block;">
<path d="M 24 0 L 180 0 A 180 130 0 0 1 0 130 L 0 24 A 24 24 0 0 1 24 0 Z" fill="{fill_css}"/>
</svg>
</body></html>"""


def _html_corner_br(fill_css: str) -> str:
    w, h = V4_BR_CSS_W, V4_BR_CSS_H
    return f"""<!DOCTYPE html><html><head>
<meta charset="utf-8"><style>
html,body{{margin:0;padding:0;background:transparent;overflow:hidden;width:{w}px;height:{h}px;}}
body{{display:block;line-height:0;font-size:0;}}
</style></head><body>
<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 150 100" style="display:block;">
<path d="M 150 0 A 150 100 0 0 0 0 100 L 126 100 A 24 24 0 0 0 150 76 Z" fill="{fill_css}"/>
</svg>
</body></html>"""


def _screenshot_corner_png(
    html: str,
    *,
    css_width: int,
    css_height: int,
    device_scale_factor: int,
) -> bytes:
    """Capture viewport = boîte exacte (pas full_page sur 320×320) pour garder l’échelle des formes."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(
            viewport={"width": css_width, "height": css_height},
            device_scale_factor=device_scale_factor,
        )
        try:
            page.set_content(html, wait_until="networkidle")
            raw = page.screenshot(omit_background=True)
        finally:
            browser.close()
    return _png_downscale(raw, device_scale_factor)


def _generate_corner_pngs(hex6: str) -> tuple[bytes, bytes]:
    fill = f"#{hex6}"
    settings = get_settings()
    dpr = settings.signdex_export_device_scale
    png_tl = _screenshot_corner_png(
        _html_corner_tl(fill),
        css_width=V4_TL_CSS_W,
        css_height=V4_TL_CSS_H,
        device_scale_factor=dpr,
    )
    png_br = _screenshot_corner_png(
        _html_corner_br(fill),
        css_width=V4_BR_CSS_W,
        css_height=V4_BR_CSS_H,
        device_scale_factor=dpr,
    )
    return png_tl, png_br


def _data_uri_svg_tl(hex6: str) -> str:
    fill = f"%23{hex6}"
    body = (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='180' height='130' viewBox='0 0 180 130'>"
        f"<path d='M 24 0 L 180 0 A 180 130 0 0 1 0 130 L 0 24 A 24 24 0 0 1 24 0 Z' fill='{fill}'/>"
        f"</svg>"
    )
    return "data:image/svg+xml;utf8," + quote(body)


def _data_uri_svg_br(hex6: str) -> str:
    fill = f"%23{hex6}"
    body = (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='150' height='100' viewBox='0 0 150 100'>"
        f"<path d='M 150 0 A 150 100 0 0 0 0 100 L 126 100 A 24 24 0 0 0 150 76 Z' fill='{fill}'/>"
        f"</svg>"
    )
    return "data:image/svg+xml;utf8," + quote(body)


def ensure_v4_corner_image_urls(color_primary: str | None) -> tuple[str, str]:
    """Retourne (url_tl, url_br) pour les coins décoratifs v4, teinte = color_primary."""
    hex6 = normalize_hex_color(color_primary)
    if hex6 in _url_pair_cache:
        return _url_pair_cache[hex6]

    if not is_configured():
        pair = (_data_uri_svg_tl(hex6), _data_uri_svg_br(hex6))
        _url_pair_cache[hex6] = pair
        return pair

    path_tl, path_br = _object_paths(hex6)
    url_tl = storage_public_url(path_tl)
    url_br = storage_public_url(path_br)

    if _public_url_ok(url_tl) and _public_url_ok(url_br):
        _url_pair_cache[hex6] = (url_tl, url_br)
        return url_tl, url_br

    png_tl, png_br = _generate_corner_pngs(hex6)
    upload_template_asset_bytes_sync(object_path=path_tl, data=png_tl, content_type="image/png")
    upload_template_asset_bytes_sync(object_path=path_br, data=png_br, content_type="image/png")

    _url_pair_cache[hex6] = (url_tl, url_br)
    return url_tl, url_br


def apply_v4_corner_asset_urls(ctx: dict) -> None:
    """Mut ctx : ajoute v4_corner_tl_url / v4_corner_br_url selon color_primary (après overrides)."""
    primary = ctx.get("color_primary")
    tl, br = ensure_v4_corner_image_urls(str(primary) if primary else None)
    ctx["v4_corner_tl_url"] = tl
    ctx["v4_corner_br_url"] = br
