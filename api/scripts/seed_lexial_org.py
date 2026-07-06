"""Crée l'organisation LEXIAL : 3 bureaux + 10 membres (avec leurs bureaux).

Permet de générer TOUTES les signatures en un clic depuis la page Organisation.
Idempotent : supprime puis recrée l'organisation « LEXIAL », et nettoie les anciennes
fiches client autonomes « LEXIAL — … » (remplacées par l'organisation).

Noms récupérés sur lexial.eu (prénoms complets). Fanny Brossard n'apparaît pas sur le site.

    docker exec signdex-api sh -c 'cd /app && PYTHONPATH=/app python scripts/seed_lexial_org.py'
"""

from __future__ import annotations

from sqlalchemy import select

from core.database import SessionLocal
from models import Client, Organization, OrganizationMember, OrganizationOffice

# (libellé bureau, template, rue, CP+ville, téléphone affiché, téléphone lien)
OFFICES = [
    ("Paris", "signature-lexial-paris", "30 rue Jouffroy d’Abbans", "F-75017 Paris", "+33 1 84 60 60 16", "+33184606016"),
    ("Geneva", "signature-lexial-geneva", "Chemin de la Milice", "CH-1228 Plan-les-Ouates, Geneva", "+41 22 595 59 26", "+41225955926"),
    ("Brussels", "signature-lexial-brussels", "Rue de la Loi 155/99", "BE-1040 Brussels", "+32 2 511 23 33", "+3225112333"),
]

LEXIAL_LOGO_URL = "https://aapjpybdkzqtgxavjjem.supabase.co/storage/v1/object/public/GoupixDex/template-assets/lexial/lexial-logo-transparent.png"

# (prénom, nom, titre, [bureaux])
MEMBERS = [
    ("Emmanuel", "Ruchat", "Avocat associé – Partner", ["Paris", "Geneva", "Brussels"]),
    ("Pierre", "Langlois de Bazillac", "Avocat associé – Partner", ["Paris", "Brussels"]),
    ("Sander", "Van Hulle", "Of Counsel", ["Brussels"]),
    ("François", "Ziegler", "Of Counsel", ["Paris", "Geneva", "Brussels"]),
    ("Corentin", "Brisseau", "Paralegal", ["Paris", "Geneva", "Brussels"]),
    ("Maewenn", "le Golvan", "Paralegal", ["Paris", "Geneva", "Brussels"]),
    ("Théau", "Guillerm", "Paralegal", ["Paris", "Geneva", "Brussels"]),
    ("Nola", "Tanguy", "Paralegal", ["Paris", "Geneva", "Brussels"]),
    ("Katell", "Rosec", "Paralegal", ["Paris", "Geneva", "Brussels"]),
    ("Fanny", "Brossard", "Assistante de Me Ruchat", ["Paris", "Geneva", "Brussels"]),
]


def main() -> None:
    db = SessionLocal()
    try:
        # 1) Nettoyer les anciennes fiches client LEXIAL autonomes.
        old = list(db.execute(select(Client).where(Client.name.like("LEXIAL — %"))).scalars().all())
        for c in old:
            db.delete(c)
        if old:
            db.commit()
            print(f"Supprimé {len(old)} ancienne(s) fiche(s) client LEXIAL.")

        # 2) (Re)créer l'organisation.
        existing = db.execute(select(Organization).where(Organization.name == "LEXIAL")).scalar_one_or_none()
        if existing:
            db.delete(existing)
            db.commit()

        # show_chambers=True : l'image Chambers définitive (chambers-2026.png) est en place et affichée.
        org = Organization(
            name="LEXIAL",
            slug="lexial",
            notes="Cabinet d'avocats — lexial.eu",
            show_chambers=True,
            brand_color="#d1080c",
            brand_logo_url=LEXIAL_LOGO_URL,
            default_theme="light",
        )
        offices_by_label: dict[str, OrganizationOffice] = {}
        for i, (label, template_key, street, cp_city, phone_display, phone_tel) in enumerate(OFFICES):
            office = OrganizationOffice(
                label=label,
                template_key=template_key,
                sort_order=i,
                address_street=street,
                address_cp_city=cp_city,
                phone_display=phone_display,
                phone_tel=phone_tel,
            )
            org.offices.append(office)
            offices_by_label[label] = office

        for i, (firstname, lastname, title, labels) in enumerate(MEMBERS):
            member = OrganizationMember(firstname=firstname, lastname=lastname, title=title, sort_order=i)
            member.offices = [offices_by_label[label] for label in labels]
            org.members.append(member)

        db.add(org)
        db.commit()
        db.refresh(org)

        total = sum(len(m.offices) for m in org.members)
        print(f"Organisation LEXIAL id={org.id} | {len(org.offices)} bureaux | {len(org.members)} membres | {total} signatures")
        for m in org.members:
            full = " ".join(p for p in (m.firstname, m.lastname) if p)
            print(f"  - {full} | {m.title} | {', '.join(o.label for o in m.offices)}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
