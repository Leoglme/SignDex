-- SignDex: colonnes contact (firstname, lastname). name = nom d entreprise.
-- Idempotence: si la migration est deja dans schema_migrations, ce fichier ne sera pas rejoue.

ALTER TABLE clients ADD COLUMN firstname VARCHAR(128) NULL AFTER subtitle;
ALTER TABLE clients ADD COLUMN lastname VARCHAR(128) NULL AFTER firstname;
