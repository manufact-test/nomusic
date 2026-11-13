-- Stage 10: one immutable trial per account. No backfill from Stage 9 activation.
CREATE TABLE IF NOT EXISTS account_trials (
    user_id BIGINT UNSIGNED NOT NULL PRIMARY KEY,
    ledger_id BIGINT UNSIGNED NOT NULL UNIQUE,
    valid_from DATETIME(6) NOT NULL,
    valid_until DATETIME(6) NOT NULL,
    CONSTRAINT account_trial_user_fk FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT account_trial_ledger_fk FOREIGN KEY (ledger_id) REFERENCES entitlement_ledger(id),
    CONSTRAINT account_trial_duration CHECK (valid_until = DATE_ADD(valid_from, INTERVAL 432000 SECOND))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
