from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class GeneratedDeliverable(Base):
    """Historique des livrables générés depuis le portail (téléchargeables à nouveau)."""

    __tablename__ = "generated_deliverables"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False,
    )
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    #: 'all' (toutes les signatures) ou 'member' (une personne).
    scope: Mapped[str] = mapped_column(String(16), default="all", nullable=False)
    member_id: Mapped[int | None] = mapped_column(
        ForeignKey("organization_members.id", ondelete="SET NULL"), nullable=True,
    )
    label: Mapped[str] = mapped_column(String(255))
    file_url: Mapped[str] = mapped_column(String(1024))
    signature_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), default=datetime.utcnow, nullable=False)
