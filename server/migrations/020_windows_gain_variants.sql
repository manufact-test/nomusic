-- W91: prepared Windows-only MP3 artifacts. Never change shared audio_assets.
-- OFFLINE, no transcoding in PHP requests. Requires one explicit gated migration.
CREATE TABLE IF NOT EXISTS windows_gain_variants (
    replacement_id BIGINT UNSIGNED NOT NULL PRIMARY KEY,
    source_sha256 CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    source_version INT UNSIGNED NOT NULL,
    gain_db DECIMAL(4,1) NOT NULL,
    storage_key VARCHAR(241) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    sha256 CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    mime_type VARCHAR(80) NOT NULL DEFAULT 'audio/mpeg',
    size_bytes BIGINT UNSIGNED NOT NULL,
    duration_ms INT UNSIGNED NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CONSTRAINT windows_gain_variant_replacement_fk
        FOREIGN KEY (replacement_id) REFERENCES track_replacements (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
