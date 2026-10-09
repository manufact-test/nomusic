-- Stage 9: additive customer identity. No changes to admins, catalog, audio or uploads.
CREATE TABLE IF NOT EXISTS users (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(254) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  status ENUM('active','restricted','disabled') NOT NULL DEFAULT 'active',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  last_login_at DATETIME(6) NULL,
  first_activated_at DATETIME(6) NULL,
  UNIQUE KEY users_email_unique (email),
  KEY users_created (created_at),
  KEY users_activation (first_activated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS user_devices (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  installation_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  last_seen_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  UNIQUE KEY user_installation_unique (user_id, installation_id),
  KEY devices_installation (installation_id),
  CONSTRAINT devices_user_fk FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS user_sessions (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  device_id BIGINT UNSIGNED NOT NULL,
  access_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  refresh_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  previous_refresh_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NULL,
  access_expires_at DATETIME(6) NOT NULL,
  refresh_expires_at DATETIME(6) NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  last_refreshed_at DATETIME(6) NULL,
  revoked_at DATETIME(6) NULL,
  UNIQUE KEY sessions_access_hash (access_hash),
  UNIQUE KEY sessions_refresh_hash (refresh_hash),
  KEY sessions_previous_hash (previous_refresh_hash),
  KEY sessions_owner (user_id, revoked_at),
  KEY sessions_expiry (refresh_expires_at),
  CONSTRAINT sessions_customer_fk FOREIGN KEY (user_id) REFERENCES users(id),
  CONSTRAINT sessions_device_fk FOREIGN KEY (device_id) REFERENCES user_devices(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS user_auth_attempts (
  identity_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  window_start BIGINT UNSIGNED NOT NULL,
  attempts INT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (identity_hash, window_start)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS user_auth_events (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  event_name ENUM('user_registered','first_activation','login','account_disabled') NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  KEY auth_event_name_date (event_name, created_at),
  KEY auth_event_user_date (user_id, created_at),
  CONSTRAINT auth_events_user_fk FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
