from __future__ import annotations

import base64
import io
import mimetypes
import re
import tempfile
import uuid
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Literal
from datetime import datetime
from html import escape
from pathlib import Path
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup
from jinja2 import Environment, StrictUndefined
from PIL import Image
from playwright.sync_api import sync_playwright

from config import get_settings
from models import Client
from services.v4_shape_assets import apply_v4_corner_asset_urls

_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"


def _digits(s: str) -> str:
    return "".join(ch for ch in (s or "") if ch.isdigit())


def _format_phone_display_nbsp(phone: str | None) -> str:
    raw = (phone or "").strip()
    d = _digits(raw)
    if len(d) == 10 and d.startswith("0"):
        pairs = [d[i : i + 2] for i in range(0, 10, 2)]
        return "&nbsp;".join(pairs)
    return escape(raw)


def _format_phone_tel(phone: str | None) -> str:
    raw = (phone or "").strip()
    d = _digits(raw)
    if len(d) == 10 and d.startswith("0"):
        return "+33" + d[1:]
    if raw.startswith("+") and len(_digits(raw)) >= 8:
        return raw.replace(" ", "").replace("\xa0", "")
    return raw.replace(" ", "").replace("\xa0", "")


def _url_path_segments(url: str | None) -> list[str]:
    """Segments de chemin décodés (Unicode dans les slugs LinkedIn, etc.)."""
    u = (url or "").strip()
    if not u:
        return []
    if not u.startswith(("http://", "https://")):
        u = "https://" + u
    path = urlparse(u).path.strip("/")
    if not path:
        return []
    return [unquote(p) for p in path.split("/") if p]


def _slug_linkedin(url: str | None) -> str:
    parts = _url_path_segments(url)
    for i, p in enumerate(parts):
        if p == "in" and i + 1 < len(parts):
            return parts[i + 1]
        if p == "company" and i + 1 < len(parts):
            return parts[i + 1]
    return ""


def _slug_instagram(url: str | None) -> str:
    parts = _url_path_segments(url)
    skip = {"p", "reel", "reels", "stories", "tv", "explore", "accounts"}
    for p in parts:
        if p in skip:
            continue
        return p
    return ""


def _slug_youtube(url: str | None) -> str:
    parts = _url_path_segments(url)
    if not parts:
        return ""
    if parts[0].startswith("@"):
        return parts[0].lstrip("@")
    for i, p in enumerate(parts):
        if p in ("c", "user") and i + 1 < len(parts):
            return parts[i + 1]
        if p == "channel" and i + 1 < len(parts):
            return parts[i + 1]
    return parts[0]


def _slug_facebook(url: str | None) -> str:
    parts = _url_path_segments(url)
    if not parts:
        return ""
    skip = {"share", "sharer", "watch", "photo.php", "groups", "people"}
    for i, p in enumerate(parts):
        if p in skip:
            continue
        if p == "pages" and i + 2 < len(parts):
            return parts[i + 1]
        if not p.isdigit():
            return p
    return ""


def _slug_tiktok(url: str | None) -> str:
    parts = _url_path_segments(url)
    for p in parts:
        if p.startswith("@"):
            return p.lstrip("@")
    return parts[-1] if parts else ""


def _social_slug_labels(client: Client) -> tuple[int, bool, dict[str, str]]:
    """Nombre de réseaux renseignés ; si 1 ou 2 → libellés extraits des URLs (template v1)."""
    urls = [
        client.youtube_url,
        client.linkedin_url,
        client.instagram_url,
        client.facebook_url,
        client.tiktok_url,
    ]
    n = sum(1 for u in urls if u and str(u).strip())
    show = n in (1, 2)
    labels = {
        "youtube_slug": _slug_youtube(client.youtube_url),
        "linkedin_slug": _slug_linkedin(client.linkedin_url),
        "instagram_slug": _slug_instagram(client.instagram_url),
        "facebook_slug": _slug_facebook(client.facebook_url),
        "tiktok_slug": _slug_tiktok(client.tiktok_url),
    }
    return n, show, labels


def _to_jinja(html: str) -> str:
    # Valeurs textuelles (HelloPropre)
    html = html.replace("HelloPropre", "{{ client.name }}")
    html = html.replace("Service de nettoyage professionnel", "{{ client.subtitle or '' }}")
    html = html.replace("contact@hellopropre.com", "{{ client.email or '' }}")
    html = html.replace("www.hellopropre.com", "{{ client.website_label or client.website_url or '' }}")

    # Template "carte magenta"
    html = html.replace("NAME SURNAME", "{{ client.name }}")
    html = html.replace("CHIEF EXECUTIVE OFFICER", "{{ client.subtitle or '' }}")
    html = html.replace("name@company.com", "{{ client.email or '' }}")
    html = html.replace("www.namecompany.com", "{{ client.website_label or client.website_url or '' }}")

    # URLs
    html = html.replace("https://www.hellopropre.com", "{{ client.website_url or '' }}")
    html = html.replace("mailto:contact@hellopropre.com", "mailto:{{ client.email or '' }}")
    html = html.replace("https://www.linkedin.com/company/hellopropre", "{{ client.linkedin_url or '' }}")
    html = html.replace("https://www.instagram.com/hellopropre/", "{{ client.instagram_url or '' }}")
    html = html.replace("https://www.facebook.com/hellopropre", "{{ client.facebook_url or '' }}")
    html = html.replace("https://www.tiktok.com/@hellopropre", "{{ client.tiktok_url or '' }}")
    html = html.replace("https://www.youtube.com/@hellopropre", "{{ client.youtube_url or '' }}")

    # URL générique du template magenta
    html = html.replace("https://www.namecompany.com", "{{ client.website_url or '' }}")
    html = html.replace("mailto:name@company.com", "mailto:{{ client.email or '' }}")

    # Images logo (2 variantes vues dans tes templates)
    html = html.replace(
        "https://static.wixstatic.com/media/0cac82_78c3516305364c279b12e172e84f7a0d~mv2.jpg",
        "{{ client.logo_url or '' }}",
    )
    html = html.replace(
        "https://lp.hellopropre.com/wp-content/uploads/2024/03/logo-hello-propre.jpeg",
        "{{ client.photo2_url or client.logo_url or '' }}",
    )

    # Photo (template magenta)
    html = html.replace(
        "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?auto=format&fit=crop&w=200&h=200&q=80",
        "{{ client.photo1_url or client.logo_url or '' }}",
    )

    # Signature v2 : vignette optionnelle à droite (photo 1 fiche client)
    html = html.replace(
        "https://signdex.placeholder.invalid/v2-optional-right-photo.jpg",
        "{{ client.photo1_url or '' }}",
    )

    # Signature v4 : photo 2 en haut à droite
    html = html.replace(
        "https://signdex.placeholder.invalid/v4-photo2-top-right.jpg",
        "{{ client.photo2_url or '' }}",
    )

    # Téléphones HelloPropre (on garde 2 champs)
    html = html.replace("+33756902818", "{{ client.phone_primary_raw or '' }}")
    html = html.replace("07&nbsp;56&nbsp;90&nbsp;28&nbsp;18", "{{ client.phone_primary_display or '' }}")
    html = html.replace("+33756968210", "{{ client.phone_secondary_raw or '' }}")
    html = html.replace("07&nbsp;56&nbsp;96&nbsp;82&nbsp;10", "{{ client.phone_secondary_display or '' }}")

    # Signature v1 : textes et sous-textes (anciennement bleus HelloPropre) → couleurs client
    html = re.sub(r"#2a4a5e\b", "{{ client.color_primary or '#2a4a5e' }}", html, flags=re.IGNORECASE)
    html = re.sub(r"#7a9aaa\b", "{{ client.color_secondary or '#7a9aaa' }}", html, flags=re.IGNORECASE)
    html = re.sub(r"#4a6a7a\b", "{{ client.color_secondary or '#4a6a7a' }}", html, flags=re.IGNORECASE)

    # Icônes Icons8 : la couleur est dans l’URL (/48/RRGGBB/) sans « # », donc hors des regex ci-dessous
    html = html.replace(
        "https://img.icons8.com/ios-filled/48/5a9cbf/",
        "https://img.icons8.com/ios-filled/48/{{ (client.color_secondary or '5a9cbf')|replace('#', '') }}/",
    )

    # Couleurs dominantes (accents / liens)
    # HelloPropre: v1 barre + liens #5a9abf ; v2/v3 bandeau + liens #4e8baa ; pictos #5a9cbf
    html = re.sub(r"#4e8baa", "{{ client.color_primary or '#4e8baa' }}", html, flags=re.IGNORECASE)
    html = re.sub(r"#5a9abf", "{{ client.color_secondary or '#5a9abf' }}", html, flags=re.IGNORECASE)
    html = re.sub(r"#5a9cbf", "{{ client.color_secondary or '#5a9cbf' }}", html, flags=re.IGNORECASE)
    # Template magenta / signature-v4
    html = re.sub(r"#e6189d", "{{ client.color_primary or '#e6189d' }}", html, flags=re.IGNORECASE)

    return html


@dataclass(frozen=True)
class RenderOverrides:
    """Valeurs None = ne pas modifier par rapport à la fiche client.

    `color_primary` / `color_secondary` sont **appliquées avant** `swap_colors` :
    on remplace d'abord les couleurs effectives par les overrides utilisateur, puis on permute si demandé.
    Cela permet à l'utilisateur de saisir ses 2 couleurs voulues *et* d'utiliser le swap dessus.
    """

    swap_colors: bool = False
    logo_url: str | None = None
    photo1_url: str | None = None
    photo2_url: str | None = None
    show_side_photo: bool = True
    show_right_logo: bool = True
    show_notes: bool = False
    title: str | None = None
    subtitle: str | None = None
    color_primary: str | None = None
    color_secondary: str | None = None


def _address_first_line(notes: str | None) -> str:
    """Première ligne non vide de `notes` — convention : on stocke l'adresse là pour les flyers / cartes."""
    if not notes:
        return ""
    for line in notes.splitlines():
        s = line.strip()
        if s:
            return s
    return ""


def build_client_render_dict(client: Client) -> dict[str, Any]:
    phone_primary_raw = _format_phone_tel(client.phone_primary)
    phone_secondary_raw = _format_phone_tel(client.phone_secondary)
    phone_primary_display = _format_phone_display_nbsp(client.phone_primary)
    phone_secondary_display = _format_phone_display_nbsp(client.phone_secondary)
    _, social_show_slug_labels, social_slugs = _social_slug_labels(client)

    def _sx(slug: str) -> str:
        s = (slug or "").strip()
        return escape(s) if s else ""

    firstname = (client.firstname or "").strip()
    lastname = (client.lastname or "").strip()
    full_name = " ".join(p for p in (firstname, lastname) if p)
    title = (client.title or "").strip()
    subtitle = (client.subtitle or "").strip()
    role_line = title or subtitle

    return {
        "name": client.name,
        "title": title or None,
        "subtitle": subtitle or None,
        "role_line": role_line or None,
        "firstname": firstname,
        "lastname": lastname,
        # `full_name` = "Prénom Nom" si renseignés ; sinon vide. Les templates qui veulent le contact humain
        # peuvent utiliser : `{{ client.full_name or client.name }}` pour garder un fallback propre.
        "full_name": full_name,
        "website_url": client.website_url,
        "website_label": (client.website_url or "").replace("https://", "").replace("http://", ""),
        "email": client.email,
        "phone_primary_raw": phone_primary_raw,
        "phone_secondary_raw": phone_secondary_raw,
        "phone_primary_display": phone_primary_display,
        "phone_secondary_display": phone_secondary_display,
        "linkedin_url": client.linkedin_url,
        "instagram_url": client.instagram_url,
        "facebook_url": client.facebook_url,
        "tiktok_url": client.tiktok_url,
        "youtube_url": client.youtube_url,
        "social_show_slug_labels": social_show_slug_labels,
        "youtube_slug": _sx(social_slugs["youtube_slug"]),
        "linkedin_slug": _sx(social_slugs["linkedin_slug"]),
        "instagram_slug": _sx(social_slugs["instagram_slug"]),
        "facebook_slug": _sx(social_slugs["facebook_slug"]),
        "tiktok_slug": _sx(social_slugs["tiktok_slug"]),
        "color_primary": client.color_primary,
        "color_secondary": client.color_secondary,
        "logo_url": client.logo_url,
        "photo1_url": client.photo1_url,
        "photo2_url": client.photo2_url,
        "show_side_photo": True,
        "show_right_logo": True,
        "show_notes": False,
        "notes": client.notes,
        "address": _address_first_line(client.notes),
    }


def apply_render_overrides(data: dict[str, Any], overrides: RenderOverrides | None) -> dict[str, Any]:
    if overrides is None:
        return data
    out = dict(data)
    # 1) Override couleurs avant swap : l'utilisateur saisit les 2 couleurs voulues, swap permute ensuite.
    if overrides.color_primary is not None:
        out["color_primary"] = overrides.color_primary or None
    if overrides.color_secondary is not None:
        out["color_secondary"] = overrides.color_secondary or None
    if overrides.swap_colors:
        p, s = out.get("color_primary"), out.get("color_secondary")
        out["color_primary"], out["color_secondary"] = s, p
    if overrides.logo_url is not None:
        out["logo_url"] = overrides.logo_url or None
    if overrides.photo1_url is not None:
        out["photo1_url"] = overrides.photo1_url or None
    if overrides.photo2_url is not None:
        out["photo2_url"] = overrides.photo2_url or None
    out["show_side_photo"] = overrides.show_side_photo
    out["show_right_logo"] = overrides.show_right_logo
    out["show_notes"] = overrides.show_notes
    if overrides.title is not None:
        out["title"] = (overrides.title or "").strip() or None
    if overrides.subtitle is not None:
        out["subtitle"] = (overrides.subtitle or "").strip() or None
    if overrides.title is not None or overrides.subtitle is not None:
        t = (out.get("title") or "").strip()
        s = (out.get("subtitle") or "").strip()
        out["role_line"] = t or s or None
    return out


def render_signature_html(
    *,
    template_html: str,
    client: Client,
    overrides: RenderOverrides | None = None,
    extra: dict[str, Any] | None = None,
) -> str:
    """`extra` = variables Jinja de premier niveau (ex. `chambers_visible` pour les templates LEXIAL)."""
    jinja_src = _to_jinja(template_html)
    ctx = apply_render_overrides(build_client_render_dict(client), overrides)
    apply_v4_corner_asset_urls(ctx)
    env = Environment(undefined=StrictUndefined, autoescape=False)
    tpl = env.from_string(jinja_src)
    return tpl.render(client=ctx, **(extra or {}))


def render_jinja_html(
    *,
    template_html: str,
    client: Client,
    overrides: RenderOverrides | None = None,
) -> str:
    """Rendu direct d'un template déjà écrit en Jinja.

    À utiliser pour les nouveaux services (flyers, bannières, cartes) : leurs templates contiennent déjà
    des expressions `{{ ... }}`. Ne PAS passer par `_to_jinja()` (réservé aux signatures historiques),
    sinon on risque de modifier des `#xxxxxx` à l'intérieur des expressions Jinja et casser la syntaxe.
    """
    ctx = apply_render_overrides(build_client_render_dict(client), overrides)
    apply_v4_corner_asset_urls(ctx)
    env = Environment(undefined=StrictUndefined, autoescape=False)
    tpl = env.from_string(template_html)
    return tpl.render(client=ctx)


ImageSlotSource = Literal["default", "logo", "photo1", "photo2"]


def _normalize_color_override(value: str | None, current: str | None) -> str | None:
    """Renvoie la valeur d'override seulement si l'utilisateur a réellement modifié la couleur.

    - `None` ou chaîne vide → pas d'override (utilise la couleur de la fiche client).
    - identique (insensible à la casse) à la couleur courante → pas d'override.
    """
    if value is None:
        return None
    s = value.strip()
    if not s:
        return None
    if current and s.lower() == current.strip().lower():
        return None
    return s


def render_overrides_from_image_slots(
    *,
    client: Client,
    swap_colors: bool,
    logo_slot: ImageSlotSource = "default",
    photo1_slot: ImageSlotSource = "default",
    photo2_slot: ImageSlotSource = "default",
    show_side_photo: bool = True,
    show_right_logo: bool = True,
    show_notes: bool = False,
    title: str | None = None,
    subtitle: str | None = None,
    color_primary: str | None = None,
    color_secondary: str | None = None,
) -> RenderOverrides | None:
    """Réassigne logo / photo1 / photo2 et couleurs de la signature à partir des choix éditeur."""
    bucket: dict[str, str | None] = {
        "logo": client.logo_url,
        "photo1": client.photo1_url,
        "photo2": client.photo2_url,
    }

    def pick_override(field: ImageSlotSource, choice: ImageSlotSource) -> str | None:
        if choice == "default" or choice == field:
            return None
        return bucket.get(choice)

    o_logo = pick_override("logo", logo_slot)
    o_p1 = pick_override("photo1", photo1_slot)
    o_p2 = pick_override("photo2", photo2_slot)
    o_c1 = _normalize_color_override(color_primary, client.color_primary)
    o_c2 = _normalize_color_override(color_secondary, client.color_secondary)
    has_img = any(x is not None for x in (o_logo, o_p1, o_p2))
    has_color = o_c1 is not None or o_c2 is not None
    has_text = title is not None or subtitle is not None
    if (
        not swap_colors
        and not has_img
        and not has_color
        and show_side_photo
        and show_right_logo
        and not show_notes
        and not has_text
    ):
        return None
    return RenderOverrides(
        swap_colors=swap_colors,
        logo_url=o_logo,
        photo1_url=o_p1,
        photo2_url=o_p2,
        show_side_photo=show_side_photo,
        show_right_logo=show_right_logo,
        show_notes=show_notes,
        title=title,
        subtitle=subtitle,
        color_primary=o_c1,
        color_secondary=o_c2,
    )


def _signature_document_body_inner_html(rendered_full_document: str) -> str:
    soup = BeautifulSoup(rendered_full_document, "html.parser")
    body = soup.body
    if body:
        inner = body.decode_contents()
        if inner and inner.strip():
            return inner
    return rendered_full_document


def _mime_type_for_image_url(url: str, content_type: str | None) -> str:
    ct = (content_type or "").split(";")[0].strip().lower()
    if ct.startswith("image/"):
        return ct
    guessed, _ = mimetypes.guess_type(urlparse(url).path)
    if guessed and guessed.startswith("image/"):
        return guessed
    return "image/png"


def _fetch_image_bytes(url: str, *, timeout_s: float = 25.0) -> tuple[bytes, str] | None:
    if not url or url.startswith("data:") or not url.startswith(("http://", "https://")):
        return None
    headers = {"User-Agent": "SignDex/1.0 (Apple Mail signature embed)"}
    try:
        req = urllib.request.Request(url, method="GET", headers=headers)
        with urllib.request.urlopen(req, timeout=timeout_s) as r:
            data = r.read()
            mime = _mime_type_for_image_url(url, r.headers.get("Content-Type"))
        if data:
            return data, mime
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError):
        pass
    return None


def _int_img_dimension(value: object) -> int | None:
    if value is None:
        return None
    s = str(value).strip().lower().removesuffix("px")
    try:
        n = int(float(s))
        return n if n > 0 else None
    except ValueError:
        return None


def _img_display_dimensions(img) -> tuple[int | None, int | None]:
    w = _int_img_dimension(img.get("width"))
    h = _int_img_dimension(img.get("height"))
    if w or h:
        return w, h
    style = img.get("style") or ""
    m_w = re.search(r"width:\s*(\d+(?:\.\d+)?)\s*px", style, re.IGNORECASE)
    m_h = re.search(r"height:\s*(\d+(?:\.\d+)?)\s*px", style, re.IGNORECASE)
    if m_w:
        w = int(float(m_w.group(1)))
    if m_h:
        h = int(float(m_h.group(1)))
    return w, h


def _img_thumbnail_max_size(
    img,
    *,
    retina: int = 2,
    abs_cap: int = 256,
    default_edge: int = 128,
) -> tuple[int, int]:
    """Taille max de redimensionnement (px) dérivée des attributs width/height du template."""
    w, h = _img_display_dimensions(img)
    if w or h:
        base_w = w or h or default_edge
        base_h = h or w or default_edge
        max_w = min(max(base_w * retina, 24), abs_cap)
        max_h = min(max(base_h * retina, 24), abs_cap)
        return max_w, max_h
    return min(default_edge * retina, abs_cap), min(default_edge * retina, abs_cap)


def _image_has_visible_alpha(img: Image.Image) -> bool:
    if img.mode != "RGBA":
        return False
    alpha = img.getchannel("A")
    lo, hi = alpha.getextrema()
    return lo < 255


def _optimize_image_bytes_for_signature(
    raw: bytes,
    mime: str,
    *,
    max_w: int,
    max_h: int,
) -> tuple[bytes, str]:
    """Réduit poids et dimensions pour un `.mailsignature` léger (< ~300 Ko total visé)."""
    img = Image.open(io.BytesIO(raw))
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA" if "A" in img.getbands() else "RGB")
    img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)

    out = io.BytesIO()
    if _image_has_visible_alpha(img):
        img.save(out, format="PNG", optimize=True)
        return out.getvalue(), "image/png"

    rgb = img.convert("RGB")
    rgb.save(out, format="JPEG", quality=85, optimize=True, progressive=True)
    return out.getvalue(), "image/jpeg"


def embed_remote_images_as_base64_html(html: str, *, timeout_s: float = 25.0) -> str:
    """Remplace les `src` http(s) des `<img>` par des data URI optimisées pour Apple Mail."""
    if not html or "<img" not in html.lower():
        return html
    wrap = BeautifulSoup(f'<div data-signdex-root="1">{html}</div>', "html.parser")
    root = wrap.find(attrs={"data-signdex-root": "1"})
    if root is None:
        return html
    cache: dict[str, str] = {}
    for img in root.find_all("img"):
        src = (img.get("src") or "").strip()
        if not src or src.startswith("data:"):
            continue
        max_w, max_h = _img_thumbnail_max_size(img)
        cache_key = f"{src}|{max_w}x{max_h}"
        if cache_key in cache:
            img["src"] = cache[cache_key]
            continue
        fetched = _fetch_image_bytes(src, timeout_s=timeout_s)
        if not fetched:
            continue
        raw, mime = fetched
        try:
            raw, mime = _optimize_image_bytes_for_signature(raw, mime, max_w=max_w, max_h=max_h)
        except OSError:
            continue
        data_uri = f"data:{mime};base64,{base64.b64encode(raw).decode('ascii')}"
        cache[cache_key] = data_uri
        img["src"] = data_uri
    return root.decode_contents()


def build_mailsignature_document(rendered_signature_full_html: str) -> str:
    """Fichier `.mailsignature` pour Apple Mail : en-têtes MIME + corps HTML de la signature.

    Apple Mail stocke chaque signature comme un fragment MIME. On encode le corps en 8bit (UTF-8 brut,
    lisible et copiable tel quel) plutôt qu'en quoted-printable, et on garde un Message-Id unique.
    Le client remplace l'intégralité du contenu du fichier UUID existant par celui-ci (voir LISEZMOI).

    Les images distantes (logo, portrait, icônes) sont intégrées en base64 pour un affichage fiable
    sans dépendre de Supabase ou d'Internet au moment de l'aperçu signature.
    """
    inner = _signature_document_body_inner_html(rendered_signature_full_html)
    inner = embed_remote_images_as_base64_html(inner)
    message_id = f"<{uuid.uuid4()}@signdex>"
    headers = (
        "Content-Transfer-Encoding: 8bit\n"
        "Content-Type: text/html;\n"
        "\tcharset=utf-8\n"
        f"Message-Id: {message_id}\n"
        "Mime-Version: 1.0\n"
    )
    body = (
        '<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"></head>'
        f"<body>{inner}</body></html>"
    )
    return f"{headers}\n{body}"


def encode_mailsignature_document(document: str) -> bytes:
    """UTF-8 avec fins de ligne LF uniquement (requis par Apple Mail sur macOS)."""
    return document.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def write_mailsignature_file(path: Path, document: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encode_mailsignature_document(document))


def _sender_initials(name: str) -> str:
    parts = [p for p in (name or "").strip().split() if p]
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    if parts:
        p0 = parts[0]
        return (p0[:2] if len(p0) >= 2 else p0 + p0).upper()
    return "?"


def fake_mail_preview_to_png_bytes(
    *,
    rendered_signature_full_html: str,
    sender_name: str,
    sender_email: str | None = None,
    subject_line: str | None = None,
    viewport_width: int = 920,
    viewport_height: int = 1120,
    device_scale_factor: int | None = None,
) -> bytes:
    """PNG « faux lecteur de mail » + corps + signature (aperçu livrable, pas Gmail réel)."""
    wrap_path = _ASSETS_DIR / "fake_mail_preview.html"
    if not wrap_path.exists():
        raise FileNotFoundError(f"Gabarit aperçu mail manquant: {wrap_path}")

    inner_sig = _signature_document_body_inner_html(rendered_signature_full_html)
    email_display = (sender_email or "vous@exemple.fr").strip() or "vous@exemple.fr"
    subject = (subject_line or "Point sur le projet — suite à notre échange").strip()
    now = datetime.now()
    months_fr = (
        "janv.",
        "févr.",
        "mars",
        "avr.",
        "mai",
        "juin",
        "juil.",
        "août",
        "sept.",
        "oct.",
        "nov.",
        "déc.",
    )
    weekdays_fr = ("lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim.")
    date_hint = (
        f"{weekdays_fr[now.weekday()]} {now.day} {months_fr[now.month - 1]} {now.year}, "
        f"{now.hour}:{now.minute:02d}"
    )

    doc = wrap_path.read_text(encoding="utf-8")
    doc = doc.replace("%%SIGNATURE_INNER_HTML%%", inner_sig)
    doc = doc.replace("%%SENDER_INITIALS%%", escape(_sender_initials(sender_name)))
    doc = doc.replace("%%SENDER_NAME%%", escape((sender_name or "").strip() or "Expéditeur"))
    doc = doc.replace("%%SENDER_EMAIL%%", escape(email_display))
    doc = doc.replace("%%DATE_HINT%%", escape(date_hint))
    doc = doc.replace("%%SUBJECT_LINE%%", escape(subject))

    settings = get_settings()
    dpr = device_scale_factor if device_scale_factor is not None else settings.signdex_export_device_scale

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "preview.html"
        p.write_text(doc, encoding="utf-8")
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(
                viewport={"width": viewport_width, "height": viewport_height},
                device_scale_factor=dpr,
            )
            try:
                page.goto(p.as_uri(), wait_until="networkidle")
                try:
                    page.evaluate(
                        "async () => { if (document.fonts) await document.fonts.ready; }",
                    )
                except Exception:
                    pass
                page.add_style_tag(content="html,body{margin:0;}")
                root = page.locator("#signdex-fake-mail-root")
                root.wait_for(state="visible", timeout=30_000)
                png = root.screenshot(type="png")
            finally:
                browser.close()
            return _png_downscale_from_device_scale(png, dpr)


def _png_downscale_from_device_scale(png_bytes: bytes, device_scale: int) -> bytes:
    """Ramène les dimensions CSS (évite un PNG 2× trop grand pour Gmail tout en gardant un rendu plus net)."""
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


def html_to_png_bytes(
    *,
    html: str,
    viewport_width: int = 960,
    viewport_height: int = 640,
    device_scale_factor: int | None = None,
) -> bytes:
    """PNG du bloc signature (table racine). Même famille moteur que la plupart des libs « html→image »
    Python (Chromium) ; la qualité vient surtout du DPR + LANCZOS, comme beaucoup d’outils cloud."""
    settings = get_settings()
    dpr = device_scale_factor if device_scale_factor is not None else settings.signdex_export_device_scale

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "sig.html"
        p.write_text(html, encoding="utf-8")
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(
                viewport={"width": viewport_width, "height": viewport_height},
                device_scale_factor=dpr,
            )
            try:
                page.goto(p.as_uri(), wait_until="networkidle")
                try:
                    page.evaluate(
                        "async () => { if (document.fonts) await document.fonts.ready; }",
                    )
                except Exception:
                    pass
                page.add_style_tag(content="html,body{margin:0;padding:0;}")
                pres = page.locator("body > table[role='presentation']")
                if pres.count() > 0:
                    target = pres.first
                else:
                    tabs = page.locator("body > table")
                    target = tabs.first if tabs.count() > 0 else page.locator("body")
                target.wait_for(state="visible", timeout=30_000)
                png = target.screenshot(type="png")
            finally:
                browser.close()
            return _png_downscale_from_device_scale(png, dpr)


def png_to_jpg_bytes(*, png_bytes: bytes, quality: int | None = None) -> bytes:
    settings = get_settings()
    q = quality if quality is not None else settings.signdex_export_jpeg_quality
    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    out = io.BytesIO()
    img.save(
        out,
        format="JPEG",
        quality=q,
        optimize=True,
        subsampling=0 if q >= 90 else 2,
    )
    return out.getvalue()


@dataclass(frozen=True)
class OrgSigJob:
    """Un rendu à produire pour le livrable organisation (1 membre × 1 bureau)."""

    rendered_html: str
    sender_name: str
    sender_email: str | None = None


def _fr_date_hint(now: datetime) -> str:
    months_fr = (
        "janv.", "févr.", "mars", "avr.", "mai", "juin",
        "juil.", "août", "sept.", "oct.", "nov.", "déc.",
    )
    weekdays_fr = ("lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim.")
    return (
        f"{weekdays_fr[now.weekday()]} {now.day} {months_fr[now.month - 1]} {now.year}, "
        f"{now.hour}:{now.minute:02d}"
    )


def render_org_assets(jobs: list[OrgSigJob]) -> list[tuple[bytes, bytes]]:
    """Pour chaque job : (PNG signature, PNG aperçu « faux mail »).

    Réutilise UN SEUL navigateur Chromium pour tous les rendus : indispensable pour générer
    en un clic des dizaines de signatures (sinon 1 lancement de navigateur par image → minutes).
    """
    if not jobs:
        return []
    settings = get_settings()
    dpr = settings.signdex_export_device_scale
    wrap_path = _ASSETS_DIR / "fake_mail_preview.html"
    if not wrap_path.exists():
        raise FileNotFoundError(f"Gabarit aperçu mail manquant: {wrap_path}")
    wrap_doc = wrap_path.read_text(encoding="utf-8")
    date_hint = _fr_date_hint(datetime.now())
    subject = "Point sur le projet — suite à notre échange"

    results: list[tuple[bytes, bytes]] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            for job in jobs:
                # --- PNG signature (table racine) ---
                page = browser.new_page(viewport={"width": 960, "height": 640}, device_scale_factor=dpr)
                try:
                    page.set_content(job.rendered_html, wait_until="networkidle")
                    try:
                        page.evaluate("async () => { if (document.fonts) await document.fonts.ready; }")
                    except Exception:
                        pass
                    page.add_style_tag(content="html,body{margin:0;padding:0;}")
                    pres = page.locator("body > table[role='presentation']")
                    if pres.count() > 0:
                        target = pres.first
                    else:
                        tabs = page.locator("body > table")
                        target = tabs.first if tabs.count() > 0 else page.locator("body")
                    target.wait_for(state="visible", timeout=30_000)
                    sig_png = _png_downscale_from_device_scale(target.screenshot(type="png"), dpr)
                finally:
                    page.close()

                # --- PNG aperçu « faux mail » ---
                inner_sig = _signature_document_body_inner_html(job.rendered_html)
                email_display = (job.sender_email or "vous@exemple.fr").strip() or "vous@exemple.fr"
                doc = wrap_doc
                doc = doc.replace("%%SIGNATURE_INNER_HTML%%", inner_sig)
                doc = doc.replace("%%SENDER_INITIALS%%", escape(_sender_initials(job.sender_name)))
                doc = doc.replace("%%SENDER_NAME%%", escape((job.sender_name or "").strip() or "Expéditeur"))
                doc = doc.replace("%%SENDER_EMAIL%%", escape(email_display))
                doc = doc.replace("%%DATE_HINT%%", escape(date_hint))
                doc = doc.replace("%%SUBJECT_LINE%%", escape(subject))
                page = browser.new_page(viewport={"width": 920, "height": 1120}, device_scale_factor=dpr)
                try:
                    page.set_content(doc, wait_until="networkidle")
                    try:
                        page.evaluate("async () => { if (document.fonts) await document.fonts.ready; }")
                    except Exception:
                        pass
                    page.add_style_tag(content="html,body{margin:0;}")
                    root = page.locator("#signdex-fake-mail-root")
                    root.wait_for(state="visible", timeout=30_000)
                    mail_png = _png_downscale_from_device_scale(root.screenshot(type="png"), dpr)
                finally:
                    page.close()

                results.append((sig_png, mail_png))
        finally:
            browser.close()
    return results

