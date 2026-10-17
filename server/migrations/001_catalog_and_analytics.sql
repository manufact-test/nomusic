CREATE TABLE IF NOT EXISTS tracks (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    service VARCHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    service_track_id VARCHAR(24) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    artist VARCHAR(240) NOT NULL DEFAULT '',
    title VARCHAR(240) NOT NULL DEFAULT '',
    album VARCHAR(240) NOT NULL DEFAULT '',
    duration_ms INT UNSIGNED NOT NULL,
    isrc VARCHAR(16) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    UNIQUE KEY track_service_identity (service, service_track_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS audio_assets (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    storage_driver VARCHAR(32) NOT NULL,
    storage_key VARCHAR(241) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    sha256 CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    audio_fingerprint VARCHAR(255) NULL,
    mime_type VARCHAR(80) NOT NULL,
    size_bytes BIGINT UNSIGNED NOT NULL,
    duration_ms INT UNSIGNED NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    UNIQUE KEY audio_exact_hash (sha256),
    UNIQUE KEY audio_storage_object (storage_driver, storage_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS track_replacements (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    track_id BIGINT UNSIGNED NOT NULL,
    audio_asset_id BIGINT UNSIGNED NOT NULL,
    status ENUM('pending', 'approved', 'rejected', 'disabled') NOT NULL DEFAULT 'pending',
    is_active TINYINT(1) NOT NULL DEFAULT 0,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    uploaded_by_user_id BIGINT UNSIGNED NULL,
    approved_by_admin_id BIGINT UNSIGNED NULL,
    approved_at DATETIME(6) NULL,
    disabled_at DATETIME(6) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    active_track_id BIGINT UNSIGNED GENERATED ALWAYS AS
        (CASE WHEN status = 'approved' AND is_active = 1 AND disabled_at IS NULL THEN track_id ELSE NULL END) STORED,
    UNIQUE KEY one_active_approved_mapping (active_track_id),
    KEY replacements_by_track_status (track_id, status),
    CONSTRAINT replacement_track_fk FOREIGN KEY (track_id) REFERENCES tracks (id),
    CONSTRAINT replacement_asset_fk FOREIGN KEY (audio_asset_id) REFERENCES audio_assets (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS analytics_events (
    event_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL PRIMARY KEY,
    schema_version SMALLINT UNSIGNED NOT NULL,
    event_name VARCHAR(40) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    installation_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    client_version VARCHAR(24) NOT NULL,
    platform VARCHAR(24) NOT NULL,
    occurred_at DATETIME(6) NOT NULL,
    received_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    properties_json JSON NOT NULL,
    KEY events_daily (occurred_at, event_name, platform)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS analytics_daily_aggregates (
    aggregate_date DATE NOT NULL,
    schema_version SMALLINT UNSIGNED NOT NULL,
    metric VARCHAR(40) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    platform VARCHAR(24) NOT NULL,
    event_count BIGINT UNSIGNED NOT NULL,
    installation_count BIGINT UNSIGNED NOT NULL,
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (aggregate_date, schema_version, metric, platform)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
