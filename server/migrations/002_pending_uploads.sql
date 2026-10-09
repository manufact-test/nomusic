-- Stage 7: additive, restartable schema. Never edits active approved records.
ALTER TABLE audio_assets
  ADD COLUMN fingerprint_status ENUM('not_processed','pending','ready','failed') NOT NULL DEFAULT 'not_processed',
  ADD COLUMN fingerprint_updated_at DATETIME(6) NULL;

CREATE TABLE IF NOT EXISTS upload_submissions (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  uploader_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  request_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  service VARCHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  service_track_id VARCHAR(24) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  sha256 CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  replacement_id BIGINT UNSIGNED NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  UNIQUE KEY upload_retry_identity (uploader_hash, request_id),
  KEY uploads_by_replacement (replacement_id),
  CONSTRAINT upload_replacement_fk FOREIGN KEY (replacement_id) REFERENCES track_replacements(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS track_requests (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  service VARCHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  service_track_id VARCHAR(24) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  uploader_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  artist VARCHAR(240) NOT NULL DEFAULT '',
  title VARCHAR(240) NOT NULL DEFAULT '',
  status ENUM('pending','reviewed','rejected') NOT NULL DEFAULT 'pending',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  UNIQUE KEY unique_owner_track_request (uploader_hash, service, service_track_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS upload_rate_buckets (
  identity_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  window_start BIGINT UNSIGNED NOT NULL,
  operation ENUM('upload','track_request') NOT NULL,
  attempts INT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY(identity_hash, window_start, operation)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;