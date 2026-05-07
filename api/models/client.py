from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, Text
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(255), unique=True)
    subtitle: Mapped[str | None] = mapped_column(String(255), nullable=True)

    website_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone_primary: Mapped[str | None] = mapped_column(String(64), nullable=True)
    phone_secondary: Mapped[str | None] = mapped_column(String(64), nullable=True)

    linkedin_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    instagram_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    facebook_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    tiktok_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    youtube_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    color_primary: Mapped[str | None] = mapped_column(String(32), nullable=True)
    color_secondary: Mapped[str | None] = mapped_column(String(32), nullable=True)

    logo_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    photo1_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    photo2_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

