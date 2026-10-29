-- Additive per-admin read watermark for incoming user promo activations.
-- Pending moderation and support counts remain derived from their real statuses.
CREATE TABLE IF NOT EXISTS admin_navigation_seen (
 admin_id BIGINT UNSIGNED NOT NULL,
 section VARCHAR(24) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 last_seen_id BIGINT UNSIGNED NOT NULL DEFAULT 0,
 updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
 PRIMARY KEY(admin_id,section),
 CONSTRAINT admin_navigation_seen_admin_fk FOREIGN KEY(admin_id) REFERENCES admins(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
