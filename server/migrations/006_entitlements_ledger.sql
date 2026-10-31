CREATE TABLE IF NOT EXISTS entitlement_ledger (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    source VARCHAR(32) NOT NULL,
    reason VARCHAR(64) NOT NULL,
    valid_from DATETIME(6) NOT NULL,
    valid_until DATETIME(6) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    INDEX idx_entitlement_user_valid (user_id, valid_until),
    CONSTRAINT fk_entitlement_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
