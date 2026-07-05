"""Gabarits HTML des emails transactionnels.

Styles 100 % inline + tables : indispensable pour un rendu correct dans les
clients mail (Outlook, Gmail, Apple Mail). Aucun mention SignDex : l'email est
aux couleurs du client.
"""

from __future__ import annotations

from html import escape


def _contrast_text(hex_color: str) -> str:
    """Noir ou blanc lisible sur une couleur de fond hex, selon sa luminance."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except ValueError:
        return "#ffffff"
    return "#111827" if (0.299 * r + 0.587 * g + 0.114 * b) / 255 > 0.6 else "#ffffff"


def render_password_reset_email(
    *,
    org_name: str | None,
    brand_color: str,
    logo_url: str | None,
    reset_url: str,
    expires_hours: int,
) -> str:
    """Email « réinitialisation de mot de passe » aux couleurs de l'organisation."""
    name = escape(org_name or "votre espace")
    color = brand_color if brand_color.startswith("#") else f"#{brand_color}"
    text_on = _contrast_text(color)
    safe_url = escape(reset_url, quote=True)

    header = (
        f'<img src="{escape(logo_url, quote=True)}" alt="{name}" height="44" '
        f'style="height:44px;max-width:220px;object-fit:contain;border:0;outline:none;text-decoration:none;">'
        if logo_url
        else f'<span style="font-size:22px;font-weight:700;color:{color};">{name}</span>'
    )

    return f"""\
<!doctype html>
<html lang="fr">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f4f5;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f5;padding:32px 12px;">
    <tr><td align="center">
      <table role="presentation" width="480" cellpadding="0" cellspacing="0"
             style="width:480px;max-width:100%;background:#ffffff;border:1px solid #e5e7eb;border-radius:16px;overflow:hidden;">
        <tr><td style="padding:28px 32px 8px;text-align:center;">{header}</td></tr>
        <tr><td style="padding:8px 32px 0;">
          <h1 style="margin:0 0 12px;font-family:Arial,Helvetica,sans-serif;font-size:19px;line-height:26px;color:#111827;text-align:center;">
            Réinitialisation de votre mot de passe
          </h1>
          <p style="margin:0 0 20px;font-family:Arial,Helvetica,sans-serif;font-size:14px;line-height:22px;color:#4b5563;text-align:center;">
            Vous avez demandé à réinitialiser le mot de passe de votre espace <strong>{name}</strong>.
            Cliquez sur le bouton ci-dessous pour en choisir un nouveau.
          </p>
        </td></tr>
        <tr><td style="padding:0 32px 8px;" align="center">
          <table role="presentation" cellpadding="0" cellspacing="0"><tr><td
            style="border-radius:10px;background:{color};">
            <a href="{safe_url}" target="_blank"
               style="display:inline-block;padding:13px 26px;font-family:Arial,Helvetica,sans-serif;font-size:15px;
                      font-weight:700;color:{text_on};text-decoration:none;border-radius:10px;">
              Réinitialiser mon mot de passe
            </a>
          </td></tr></table>
        </td></tr>
        <tr><td style="padding:16px 32px 4px;">
          <p style="margin:0;font-family:Arial,Helvetica,sans-serif;font-size:12px;line-height:19px;color:#6b7280;text-align:center;">
            Ce lien expire dans {expires_hours} h. Si le bouton ne fonctionne pas, copiez-collez ce lien :
          </p>
          <p style="margin:6px 0 0;font-family:Arial,Helvetica,sans-serif;font-size:12px;line-height:18px;text-align:center;word-break:break-all;">
            <a href="{safe_url}" target="_blank" style="color:{color};text-decoration:underline;">{safe_url}</a>
          </p>
        </td></tr>
        <tr><td style="padding:20px 32px 28px;">
          <p style="margin:16px 0 0;padding-top:16px;border-top:1px solid #ececed;
                    font-family:Arial,Helvetica,sans-serif;font-size:12px;line-height:18px;color:#9ca3af;text-align:center;">
            Vous n'êtes pas à l'origine de cette demande ? Ignorez cet email, votre mot de passe reste inchangé.
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""
