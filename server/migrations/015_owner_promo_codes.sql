-- Independent owner promos; no changes to existing grants or financial journals.
CREATE TABLE IF NOT EXISTS promo_codes (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 code VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 title VARCHAR(120) NOT NULL,
 discount_percent TINYINT UNSIGNED NOT NULL,
 duration_days SMALLINT UNSIGNED NULL,
 forever TINYINT UNSIGNED NOT NULL DEFAULT 0,
 max_activations INT UNSIGNED NOT NULL DEFAULT 1,
 used_activations INT UNSIGNED NOT NULL DEFAULT 0,
 activation_deadline DATETIME(6) NULL,
 request_key CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 created_by BIGINT UNSIGNED NOT NULL,
 created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
 revoked_at DATETIME(6) NULL,
 UNIQUE KEY promo_code_unique(code), UNIQUE KEY promo_create_request(request_key),
 CONSTRAINT promo_creator_fk FOREIGN KEY(created_by) REFERENCES admins(id),
 CONSTRAINT promo_percent_check CHECK(discount_percent BETWEEN 1 AND 100),
 CONSTRAINT promo_days_check CHECK((forever=0 AND duration_days IS NOT NULL AND duration_days BETWEEN 1 AND 3660) OR (forever=1 AND duration_days IS NULL AND discount_percent=100)),
 CONSTRAINT promo_forever_check CHECK(forever IN (0,1)),
 CONSTRAINT promo_cap_check CHECK(max_activations BETWEEN 1 AND 1000000 AND used_activations<=max_activations)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE IF NOT EXISTS promo_redemptions (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 promo_id BIGINT UNSIGNED NOT NULL,
 user_id BIGINT UNSIGNED NOT NULL,
 ledger_id BIGINT UNSIGNED NOT NULL,
 parent_ledger_id BIGINT UNSIGNED NULL,
 duration_days SMALLINT UNSIGNED NULL,
 forever TINYINT UNSIGNED NOT NULL DEFAULT 0,
 valid_from DATETIME(6) NOT NULL,
 valid_until DATETIME(6) NULL,
 activated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
 revoked_at DATETIME(6) NULL,
 UNIQUE KEY promo_once_per_account(promo_id,user_id), UNIQUE KEY promo_grant_unique(ledger_id),
 KEY promo_account(user_id,id),
 CONSTRAINT promo_redemption_code_fk FOREIGN KEY(promo_id) REFERENCES promo_codes(id),
 CONSTRAINT promo_redemption_user_fk FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
 CONSTRAINT promo_redemption_grant_fk FOREIGN KEY(ledger_id) REFERENCES entitlement_ledger(id),
 CONSTRAINT promo_redemption_parent_fk FOREIGN KEY(parent_ledger_id) REFERENCES entitlement_ledger(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE IF NOT EXISTS promo_attempt_buckets (
 identity_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 window_start BIGINT UNSIGNED NOT NULL,
 attempts INT UNSIGNED NOT NULL,
 PRIMARY KEY(identity_hash,window_start)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
