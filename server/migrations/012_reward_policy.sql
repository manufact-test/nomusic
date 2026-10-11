-- Owner-configured upload discount credits. No seeded financial values or access.
CREATE TABLE IF NOT EXISTS reward_policy (
    id TINYINT UNSIGNED PRIMARY KEY,
    enabled TINYINT UNSIGNED NOT NULL DEFAULT 0,
    upload_discount_percent TINYINT UNSIGNED NOT NULL DEFAULT 0,
    max_discount_percent TINYINT UNSIGNED NOT NULL DEFAULT 0,
    max_reward_per_month INT UNSIGNED NOT NULL DEFAULT 0,
    validity_days SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    CONSTRAINT reward_policy_singleton CHECK (id=1),
    CONSTRAINT reward_policy_bounds CHECK (enabled IN (0,1) AND upload_discount_percent<=100
        AND max_discount_percent<=100 AND max_reward_per_month<=10000 AND validity_days<=3660),
    CONSTRAINT reward_policy_enabled CHECK (enabled=0 OR (upload_discount_percent>0
        AND upload_discount_percent<=max_discount_percent AND max_reward_per_month>0 AND validity_days>0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT IGNORE INTO reward_policy (id) VALUES (1);
SET @celikom_reward_columns = (SELECT IF(COUNT(*)=0, 'ALTER TABLE reward_ledger
    ADD COLUMN discount_percent TINYINT UNSIGNED NULL,
    ADD COLUMN granted_at DATETIME(6) NULL,
    ADD COLUMN expires_at DATETIME(6) NULL,
    ADD COLUMN policy_version INT UNSIGNED NULL,
    ADD COLUMN decided_by_admin_id BIGINT UNSIGNED NULL,
    ADD COLUMN version INT UNSIGNED NOT NULL DEFAULT 1,
    ADD KEY reward_monthly_grants (user_id,granted_at),
    ADD CONSTRAINT reward_deciding_admin_fk FOREIGN KEY (decided_by_admin_id) REFERENCES admins(id),
    ADD CONSTRAINT reward_discount_bounds CHECK (discount_percent IS NULL OR discount_percent BETWEEN 1 AND 100),
    ADD CONSTRAINT reward_grant_dates CHECK (granted_at IS NULL OR (expires_at IS NOT NULL AND expires_at>granted_at AND discount_percent IS NOT NULL AND policy_version IS NOT NULL)),
    ADD CONSTRAINT reward_approved_has_grant CHECK (status NOT IN (''approved'',''used'',''expired'') OR (granted_at IS NOT NULL AND decided_by_admin_id IS NOT NULL))', 'SELECT 1') FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='reward_ledger' AND column_name='discount_percent');
PREPARE celikom_reward_columns_statement FROM @celikom_reward_columns;
EXECUTE celikom_reward_columns_statement;
DEALLOCATE PREPARE celikom_reward_columns_statement;
