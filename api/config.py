from __future__ import annotations

from functools import lru_cache

from pydantic import Field

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "mysql+pymysql://signdex:signdex@127.0.0.1:3307/signdex"
    cors_origins: str = "*"

    supabase_url: str | None = None
    supabase_api_key: str | None = None
    supabase_storage_bucket: str | None = "SignDex"

    # Templates:
    # - signatures: `${signdex_templates_dir}/` (comportement historique)
    # - autres services: `${signdex_templates_dir}/{service}/`
    signdex_templates_dir: str = "templates"

    #: Si 1 (défaut), exécuter le seed initial uniquement quand la table `clients` est vide. Mettre 0 pour désactiver.
    signdex_seed_if_empty: int = Field(default=1, ge=0, le=1)

    # Export HTML → PNG/JPG : facteur de résolution Chromium (2 = suréchantillonnage puis
    # réduction LANCZOS, proche des services type CloudConvert pour texte et bords nets).
    signdex_export_device_scale: int = Field(default=2, ge=1, le=4)
    signdex_export_jpeg_quality: int = Field(default=95, ge=70, le=100)

    # --- Auth / portail client ---
    #: Secret de signature JWT. DOIT être défini en prod (variable d'env JWT_SECRET).
    jwt_secret: str = "dev-insecure-change-me-in-prod"
    #: Durée de validité du token de session (heures).
    jwt_expire_hours: int = Field(default=168, ge=1)
    #: Durée de validité d'un lien d'invitation (heures).
    invite_ttl_hours: int = Field(default=168, ge=1)
    #: Compte admin bootstrap créé au seed s'il n'existe pas (prod : ADMIN_EMAIL / ADMIN_PASSWORD).
    admin_email: str | None = None
    admin_password: str | None = None
    #: Base publique pour construire les liens d'invitation (front). Prod : https://signdex.dibodev.fr
    public_base_url: str = "http://localhost:3000"

    # --- Resend (emails transactionnels : mot de passe oublié) ---
    #: Clé API Resend. Vide = envoi désactivé (l'endpoint reste OK, sans email).
    resend_api_key: str = ""
    resend_webhook_secret: str = ""
    #: Adresse d'envoi (doit être sur un domaine vérifié dans Resend, ex. mail.dibodev.fr).
    resend_from_email: str = "noreply@mail.dibodev.fr"
    #: Nom d'expéditeur par défaut (remplacé par le nom de l'organisation quand disponible).
    resend_from_name: str = "SignDex"
    #: Domaine racine des sous-domaines clients → liens email https://<slug>.<domaine>/reset/<token>.
    portal_base_domain: str = "dibodev.fr"
    #: Durée de validité d'un lien de réinitialisation de mot de passe (heures).
    reset_ttl_hours: int = Field(default=2, ge=1)


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()

