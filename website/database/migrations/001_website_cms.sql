-- CELIKOM website only / planned Stage 9 schema (Stage 3 technical contract).
-- NEVER run against the existing CELIKOM application database.
-- Apply only to a dedicated website MySQL/MariaDB database, after backup.
-- This file is kept OUTSIDE public_html and is NOT auto-applied on deployment.
-- Hostinger MySQL/MariaDB version compatibility must be verified before use.

CREATE TABLE IF NOT EXISTS admin_users (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(80) COLLATE utf8mb4_bin NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_login_at DATETIME NULL,
  UNIQUE KEY uq_admin_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS media_assets (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  storage_key VARCHAR(255) COLLATE utf8mb4_bin NOT NULL,
  original_filename VARCHAR(255) NOT NULL,
  mime_type VARCHAR(80) NOT NULL,
  sha256 CHAR(64) COLLATE ascii_bin NOT NULL,
  pixel_width INT UNSIGNED NULL,
  pixel_height INT UNSIGNED NULL,
  alt_text VARCHAR(500) NOT NULL DEFAULT '',
  created_by BIGINT UNSIGNED NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  UNIQUE KEY uq_media_storage (storage_key),
  KEY idx_media_sha256 (sha256),
  CONSTRAINT fk_media_user FOREIGN KEY (created_by) REFERENCES admin_users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS faq_categories (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  code VARCHAR(80) COLLATE utf8mb4_bin NOT NULL,
  label VARCHAR(160) NOT NULL,
  position INT NOT NULL DEFAULT 0,
  is_visible TINYINT(1) NOT NULL DEFAULT 1,
  UNIQUE KEY uq_faq_category_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS faq_items (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  slug VARCHAR(160) COLLATE utf8mb4_bin NOT NULL,
  category_id BIGINT UNSIGNED NOT NULL,
  question VARCHAR(400) NOT NULL,
  answer_html MEDIUMTEXT NOT NULL,
  position INT NOT NULL DEFAULT 0,
  is_visible TINYINT(1) NOT NULL DEFAULT 1,
  is_archived TINYINT(1) NOT NULL DEFAULT 0,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_faq_slug (slug),
  KEY idx_faq_position (category_id, position),
  CONSTRAINT fk_faq_category FOREIGN KEY (category_id) REFERENCES faq_categories(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS site_content (
  content_key VARCHAR(160) COLLATE utf8mb4_bin NOT NULL PRIMARY KEY,
  content_type VARCHAR(32) NOT NULL,
  draft_value MEDIUMTEXT NULL,
  updated_by BIGINT UNSIGNED NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_site_content_editor FOREIGN KEY (updated_by) REFERENCES admin_users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS site_settings (
  setting_key VARCHAR(160) COLLATE utf8mb4_bin NOT NULL PRIMARY KEY,
  setting_value MEDIUMTEXT NOT NULL,
  updated_by BIGINT UNSIGNED NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_settings_editor FOREIGN KEY (updated_by) REFERENCES admin_users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Each published page is an immutable full content+FAQ+media-reference snapshot.
-- No visitor ever combines fields from different revisions.
CREATE TABLE IF NOT EXISTS content_revisions (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  snapshot_json LONGTEXT NOT NULL,
  change_note VARCHAR(255) NOT NULL DEFAULT '',
  created_by BIGINT UNSIGNED NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_revision_created (created_at),
  CONSTRAINT fk_revision_author FOREIGN KEY (created_by) REFERENCES admin_users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS site_state (
  id TINYINT UNSIGNED NOT NULL PRIMARY KEY,
  published_revision_id BIGINT UNSIGNED NULL,
  updated_by BIGINT UNSIGNED NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_site_published_revision FOREIGN KEY (published_revision_id) REFERENCES content_revisions(id),
  CONSTRAINT fk_site_publisher FOREIGN KEY (updated_by) REFERENCES admin_users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO site_state (id, published_revision_id) VALUES (1, NULL);

-- One shared editable draft snapshot in MVP; optimistic_version prevents
-- two browser tabs silently overwriting one another's changes.
CREATE TABLE IF NOT EXISTS content_drafts (
  id TINYINT UNSIGNED NOT NULL PRIMARY KEY,
  draft_json LONGTEXT NOT NULL,
  optimistic_version BIGINT UNSIGNED NOT NULL DEFAULT 0,
  updated_by BIGINT UNSIGNED NOT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_draft_author FOREIGN KEY (updated_by) REFERENCES admin_users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS login_rate_limits (
  bucket_hash CHAR(64) COLLATE ascii_bin NOT NULL PRIMARY KEY,
  attempts INT UNSIGNED NOT NULL DEFAULT 0,
  window_started_at DATETIME NOT NULL,
  locked_until DATETIME NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS audit_log (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  actor_admin_id BIGINT UNSIGNED NULL,
  event_name VARCHAR(100) NOT NULL,
  subject_key VARCHAR(200) NULL,
  event_metadata LONGTEXT NULL,
  occurred_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_audit_occurred (occurred_at),
  KEY idx_audit_actor (actor_admin_id),
  CONSTRAINT fk_audit_actor FOREIGN KEY (actor_admin_id) REFERENCES admin_users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Atomic publication contract (application code in Stage 9):
-- BEGIN; SELECT published_revision_id FROM site_state WHERE id=1 FOR UPDATE;
-- INSERT content_revisions(snapshot_json, ...); UPDATE site_state
-- SET published_revision_id=:new_id, updated_by=:admin WHERE id=1; COMMIT;
-- Rollback creates a NEW revision from an earlier snapshot and atomically points
-- site_state to it; never mutates historical revisions.
