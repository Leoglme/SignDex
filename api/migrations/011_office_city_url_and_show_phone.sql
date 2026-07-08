-- Villes cliquables + téléphone optionnel dans la signature.
-- LEXIAL a retiré l'adresse au profit des noms de ville cliquables (→ page Offices), et retiré
-- le téléphone (désormais une simple option). On ajoute donc :
--   - organization_offices.city_url : le lien de la ville (éditable par le client) ;
--   - organizations.show_phone : toggle d'affichage du téléphone (off par défaut).
ALTER TABLE organization_offices ADD COLUMN city_url VARCHAR(1024) NULL;
ALTER TABLE organizations ADD COLUMN show_phone TINYINT(1) NOT NULL DEFAULT 0;

-- LEXIAL : les 3 villes pointent vers la page Offices ; téléphone masqué ; ordre Paris, Brussels, Geneva.
UPDATE organization_offices SET city_url='https://lexial.eu/offices/' WHERE template_key IN ('signature-lexial-paris','signature-lexial-geneva','signature-lexial-brussels');
UPDATE organization_offices SET sort_order=0 WHERE template_key='signature-lexial-paris';
UPDATE organization_offices SET sort_order=1 WHERE template_key='signature-lexial-brussels';
UPDATE organization_offices SET sort_order=2 WHERE template_key='signature-lexial-geneva';
UPDATE organizations SET show_phone=0 WHERE slug='lexial';
