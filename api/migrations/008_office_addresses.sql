-- Adresses de bureau éditables (déménagement) : sorties des templates vers les données.
ALTER TABLE organization_offices
  ADD COLUMN address_street VARCHAR(255) NULL,
  ADD COLUMN address_cp_city VARCHAR(255) NULL,
  ADD COLUMN phone_display VARCHAR(64) NULL,
  ADD COLUMN phone_tel VARCHAR(64) NULL;

-- Pré-remplit les bureaux LEXIAL existants avec leurs adresses actuelles (= valeurs figées dans les templates).
UPDATE organization_offices SET address_street='30 rue Jouffroy d’Abbans', address_cp_city='F-75017 Paris', phone_display='+33 1 84 60 60 16', phone_tel='+33184606016' WHERE template_key='signature-lexial-paris';
UPDATE organization_offices SET address_street='Chemin de la Milice', address_cp_city='CH-1228 Plan-les-Ouates, Geneva', phone_display='+41 22 595 59 26', phone_tel='+41225955926' WHERE template_key='signature-lexial-geneva';
UPDATE organization_offices SET address_street='Rue de la Loi 155/99', address_cp_city='BE-1040 Brussels', phone_display='+32 2 511 23 33', phone_tel='+3225112333' WHERE template_key='signature-lexial-brussels';
