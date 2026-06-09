-- Option : afficher / masquer le logo Chambers (2e image) dans les signatures de l'organisation.

ALTER TABLE organizations
  ADD COLUMN show_chambers TINYINT(1) NOT NULL DEFAULT 1;
