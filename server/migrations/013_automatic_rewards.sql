-- Automatic upload credits wait for payment without an expiry countdown.
SET @celikom_auto_columns = (SELECT IF(COUNT(*)=0, 'ALTER TABLE reward_ledger
    DROP CHECK reward_grant_dates,
    ADD COLUMN grant_mode ENUM(''manual'',''automatic'') NOT NULL DEFAULT ''manual'',
    ADD CONSTRAINT reward_grant_dates CHECK (granted_at IS NULL OR (discount_percent IS NOT NULL AND policy_version IS NOT NULL AND ((grant_mode=''manual'' AND expires_at IS NOT NULL AND expires_at>granted_at) OR (grant_mode=''automatic'' AND expires_at IS NULL))))', 'UPDATE reward_policy SET id=id WHERE id=1') FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='reward_ledger' AND column_name='grant_mode');
SET @celikom_auto_columns = IF(INSTR(VERSION(),'MariaDB')>0, REPLACE(@celikom_auto_columns,'DROP CHECK reward_grant_dates','DROP CONSTRAINT reward_grant_dates'), @celikom_auto_columns);
PREPARE celikom_auto_statement FROM @celikom_auto_columns;
EXECUTE celikom_auto_statement;
DEALLOCATE PREPARE celikom_auto_statement;
CREATE TABLE IF NOT EXISTS reward_allocations (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    reward_id BIGINT UNSIGNED NOT NULL,
    part_index SMALLINT UNSIGNED NOT NULL,
    available_from DATE NOT NULL,
    discount_percent TINYINT UNSIGNED NOT NULL,
    monthly_cap_percent TINYINT UNSIGNED NOT NULL,
    validity_days SMALLINT UNSIGNED NOT NULL,
    redeemed_at DATETIME(6) NULL,
    expires_at DATETIME(6) NULL,
    UNIQUE KEY reward_allocation_part (reward_id,part_index),
    KEY reward_allocation_month (available_from,reward_id),
    CONSTRAINT reward_allocation_reward_fk FOREIGN KEY (reward_id) REFERENCES reward_ledger(id) ON DELETE CASCADE,
    CONSTRAINT reward_allocation_bounds CHECK (discount_percent BETWEEN 1 AND 100 AND monthly_cap_percent BETWEEN 1 AND 100 AND validity_days BETWEEN 1 AND 3660),
    CONSTRAINT reward_allocation_activation CHECK ((redeemed_at IS NULL AND expires_at IS NULL) OR (redeemed_at IS NOT NULL AND expires_at>redeemed_at))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
