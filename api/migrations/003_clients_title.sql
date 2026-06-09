-- Titre / fonction explicite pour les signatures (sous-titre historique = fallback)

ALTER TABLE clients
  ADD COLUMN title VARCHAR(255) NULL AFTER subtitle;
