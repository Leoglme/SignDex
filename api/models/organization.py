from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table, Text
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

# Association membre <-> bureau (un membre est rattaché à 1..N bureaux de l'organisation).
organization_member_offices = Table(
    "organization_member_offices",
    Base.metadata,
    Column(
        "member_id",
        ForeignKey("organization_members.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "office_id",
        ForeignKey("organization_offices.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Organization(Base):
    """Une organisation (ex. cabinet LEXIAL) regroupe des bureaux + des membres.

    Permet de générer en un clic TOUTES les signatures (chaque membre × ses bureaux).
    """

    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    slug: Mapped[str] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Affiche/masque le logo Chambers (2e image) dans les signatures. Off tant que le
    # logo définitif n'est pas reçu ; activer puis régénérer le livrable.
    show_chambers: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Branding du portail « Mon espace » (défini par l'admin) : logo + couleur d'accent du client.
    brand_logo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    brand_color: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # Images DANS la signature, éditables par le client (pré-remplies). Fallback = URLs hébergées.
    sig_logo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    sig_chambers_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    # Thème par défaut du portail client ('light' | 'dark' | NULL = système/au choix).
    default_theme: Mapped[str | None] = mapped_column(String(16), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False,
    )

    offices: Mapped[list[OrganizationOffice]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan",
        order_by="OrganizationOffice.sort_order, OrganizationOffice.id",
    )
    members: Mapped[list[OrganizationMember]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan",
        order_by="OrganizationMember.sort_order, OrganizationMember.id",
    )
    users: Mapped[list[User]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan",
        order_by="User.created_at",
    )


class OrganizationOffice(Base):
    """Un bureau de l'organisation = un libellé (ex. « Paris ») + le template à utiliser.

    L'adresse / téléphone du bureau est figé dans le template (signature-lexial-paris, etc.).
    """

    __tablename__ = "organization_offices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False,
    )
    label: Mapped[str] = mapped_column(String(255))
    template_key: Mapped[str] = mapped_column(String(128))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Adresse du bureau (éditable par le client — déménagement). Fallback = valeurs figées du template.
    address_street: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_cp_city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone_display: Mapped[str | None] = mapped_column(String(64), nullable=True)
    phone_tel: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), default=datetime.utcnow, nullable=False)

    organization: Mapped[Organization] = relationship(back_populates="offices")
    members: Mapped[list[OrganizationMember]] = relationship(
        secondary=organization_member_offices,
        back_populates="offices",
    )


class OrganizationMember(Base):
    """Un membre de l'organisation : nom + titre + ses bureaux. Léger (pas une fiche client)."""

    __tablename__ = "organization_members"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False,
    )
    firstname: Mapped[str | None] = mapped_column(String(128), nullable=True)
    lastname: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False,
    )

    organization: Mapped[Organization] = relationship(back_populates="members")
    offices: Mapped[list[OrganizationOffice]] = relationship(
        secondary=organization_member_offices,
        back_populates="members",
        order_by="OrganizationOffice.sort_order, OrganizationOffice.id",
    )
