-- Reconcile the owner-only bulk moderation tombstone schema for clean installations.
-- Existing databases may already have the original 019 migration applied; IF NOT EXISTS
-- preserves that table and its history while making the schema reproducible from source.
CREATE TABLE IF NOT EXISTS bulk_moderation_tombstones (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    batch_id CHAR(24) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    replacement_id BIGINT UNSIGNED NOT NULL,
    service VARCHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    service_track_id VARCHAR(24) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    sha256 CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    asset_id BIGINT UNSIGNED NOT NULL,
    storage_key VARCHAR(241) CHARACTER SET ascii COLLATE ascii_bin DEFAULT NULL,
    cleanup_status VARCHAR(16) NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY tombstone_replacement (replacement_id),
    KEY tombstone_track (service, service_track_id),
    KEY tombstone_cleanup (cleanup_status, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
