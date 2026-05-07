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

    signdex_templates_dir: str = "templates"

    #: Si 1 (défaut), exécuter le seed initial uniquement quand la table `clients` est vide. Mettre 0 pour désactiver.
    signdex_seed_if_empty: int = Field(default=1, ge=0, le=1)

    # Export HTML → PNG/JPG : facteur de résolution Chromium (2 = suréchantillonnage puis
    # réduction LANCZOS, proche des services type CloudConvert pour texte et bords nets).
    signdex_export_device_scale: int = Field(default=2, ge=1, le=4)
    signdex_export_jpeg_quality: int = Field(default=95, ge=70, le=100)


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()

