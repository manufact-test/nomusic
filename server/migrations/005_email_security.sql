-- Stage 9 email identity: additive only. Old users start unverified and cannot be silently trusted.
CREATE TABLE IF NOT EXISTS user_email_security (
  user_id BIGINT UNSIGNED NOT NULL PRIMARY KEY,
  verified_at DATETIME(6) NULL,
  verification_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NULL,
  verification_expires_at DATETIME(6) NULL,
  verification_attempts TINYINT UNSIGNED NOT NULL DEFAULT 0,
  verification_sent_at DATETIME(6) NULL,
  reset_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NULL,
  reset_expires_at DATETIME(6) NULL,
  reset_attempts TINYINT UNSIGNED NOT NULL DEFAULT 0,
  reset_sent_at DATETIME(6) NULL,
  CONSTRAINT user_email_security_fk FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
