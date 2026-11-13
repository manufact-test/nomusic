-- Additive exact native Yandex identity for CELIKOM Android A1.
-- NULL means unverified: the Android source contract must keep the original source.
ALTER TABLE tracks
    ADD COLUMN service_album_id VARCHAR(24) CHARACTER SET ascii COLLATE ascii_bin NULL AFTER service_track_id,
    ADD COLUMN service_edition_id VARCHAR(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL AFTER service_album_id;
