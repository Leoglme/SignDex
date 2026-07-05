-- Portail client : comptes de connexion (users), branding + images de signature par organisation,
-- et historique des livrables générés.

ALTER TABLE organizations
  ADD COLUMN brand_logo_url VARCHAR(1024) NULL,
  ADD COLUMN brand_color VARCHAR(32) NULL,
  ADD COLUMN sig_logo_url VARCHAR(1024) NULL,
  ADD COLUMN sig_chambers_url VARCHAR(1024) NULL;

CREATE TABLE IF NOT EXISTS users (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NULL,
  role VARCHAR(16) NOT NULL DEFAULT 'editor',
  organization_id INT NULL,
  full_name VARCHAR(255) NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 0,
  invite_token VARCHAR(128) NULL,
  invite_expires_at DATETIME(6) NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  INDEX idx_users_invite_token (invite_token),
  CONSTRAINT fk_user_org FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS generated_deliverables (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  organization_id INT NOT NULL,
  created_by_user_id INT NULL,
  scope VARCHAR(16) NOT NULL DEFAULT 'all',
  member_id INT NULL,
  label VARCHAR(255) NOT NULL,
  file_url VARCHAR(1024) NOT NULL,
  signature_count INT NOT NULL DEFAULT 0,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  CONSTRAINT fk_gd_org FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
  CONSTRAINT fk_gd_user FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
  CONSTRAINT fk_gd_member FOREIGN KEY (member_id) REFERENCES organization_members(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
