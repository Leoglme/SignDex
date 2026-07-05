from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

# Rôles :
#   admin  → super-admin global (Léo), organization_id = NULL, voit tout.
#   owner  → propriétaire d'un espace client (ex. Emmanuel) : édite tout + invite/supprime des users.
#   editor → membre d'un espace client : édite les signatures, ne gère pas les users.
ROLE_ADMIN = "admin"
ROLE_OWNER = "owner"
ROLE_EDITOR = "editor"


class User(Base):
    """Compte de connexion au portail. DISTINCT d'un OrganizationMember (sujet de signature)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(16), default=ROLE_EDITOR, nullable=False)
    organization_id: Mapped[int | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True,
    )
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    invite_token: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    invite_expires_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)
    # Réinitialisation de mot de passe (« mot de passe oublié »), distinct de l'invitation.
    reset_token: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    reset_expires_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False,
    )

    organization: Mapped[Organization | None] = relationship(back_populates="users")

    @property
    def status(self) -> str:
        """'active' si le compte a défini son mot de passe, sinon 'invited'."""
        return "active" if self.is_active else "invited"
