-- Stage12 contribution evidence only. No discount value, money or access grant.
CREATE TABLE IF NOT EXISTS reward_ledger (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    audio_asset_id BIGINT UNSIGNED NOT NULL,
    replacement_id BIGINT UNSIGNED NOT NULL,
    approved_by_admin_id BIGINT UNSIGNED NOT NULL,
    status ENUM('pending','approved','rejected','used','expired') NOT NULL DEFAULT 'pending',
    source VARCHAR(32) NOT NULL DEFAULT 'approved_upload',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    UNIQUE KEY reward_asset_once (audio_asset_id),
    UNIQUE KEY reward_replacement_once (replacement_id),
    KEY reward_user_status (user_id,status,id),
    CONSTRAINT reward_user_fk FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT reward_asset_fk FOREIGN KEY (audio_asset_id) REFERENCES audio_assets(id),
    CONSTRAINT reward_replacement_fk FOREIGN KEY (replacement_id) REFERENCES track_replacements(id),
    CONSTRAINT reward_admin_fk FOREIGN KEY (approved_by_admin_id) REFERENCES admins(id),
    CONSTRAINT reward_source CHECK (source = 'approved_upload')
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
