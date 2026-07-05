-- Thème par défaut du portail client, par organisation ('light' | 'dark' | NULL = au choix).
ALTER TABLE organizations
  ADD COLUMN default_theme VARCHAR(16) NULL;
