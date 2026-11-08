-- Persistent private delete history: never let a later importer silently recreate deleted versions.
-- The audio key is PRIVATE and must never be exposed in a public API/CSV.
CREATE TABLE IF NOT EXISTS bulk_moderation_tombstones (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    batch_id CHAR(24) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    replacement_id BIGINT UNSIGNED NOT NULL,
    service VARCHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    service_track_id VARCHAR(24) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    sha256 CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    asset_id BIGINT UNSIGNED NOT NULL,
    storage_key VARCHAR(241) CHARACTER SET ascii COLLATE ascii_bin NULL,
    cleanup_status VARCHAR(16) NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    UNIQUE KEY tombstone_replacement (replacement_id),
    KEY tombstone_track (service,service_track_id),
    KEY tombstone_cleanup (cleanup_status,created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
