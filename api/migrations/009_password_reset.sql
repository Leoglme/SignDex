-- Réinitialisation de mot de passe (« mot de passe oublié ») : token dédié + expiration.
-- Distinct de invite_token (activation) pour ne pas mélanger les deux flux.
ALTER TABLE users
  ADD COLUMN reset_token VARCHAR(128) NULL,
  ADD COLUMN reset_expires_at DATETIME(6) NULL;

CREATE INDEX ix_users_reset_token ON users (reset_token);
