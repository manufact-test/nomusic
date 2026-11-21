-- Additive Stage11 foundation. No live provider or HTTP billing is enabled.
CREATE TABLE IF NOT EXISTS subscriptions (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  provider VARCHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  provider_subscription_id VARCHAR(191) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  plan_key VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  currency CHAR(3) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  amount_minor BIGINT UNSIGNED NOT NULL,
  status ENUM('pending','active','past_due') NOT NULL DEFAULT 'pending',
  cancel_at_period_end BOOLEAN NOT NULL DEFAULT FALSE,
  payment_event_at DATETIME(6) NULL,
  renewal_event_at DATETIME(6) NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  UNIQUE KEY subscription_provider_ref (provider,provider_subscription_id),
  KEY subscription_user (user_id,id),
  CONSTRAINT subscription_user_fk FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS billing_events (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  subscription_id BIGINT UNSIGNED NOT NULL,
  provider VARCHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  provider_event_id VARCHAR(191) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  payload_sha256 CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  event_sha256 CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  event_type VARCHAR(32) NOT NULL,
  occurred_at DATETIME(6) NOT NULL,
  received_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  UNIQUE KEY billing_provider_event (provider,provider_event_id),
  KEY billing_subscription (subscription_id,id),
  CONSTRAINT billing_event_subscription_fk FOREIGN KEY (subscription_id) REFERENCES subscriptions(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS billing_payments (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  subscription_id BIGINT UNSIGNED NOT NULL,
  event_id BIGINT UNSIGNED NOT NULL,
  ledger_id BIGINT UNSIGNED NOT NULL,
  provider VARCHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  provider_payment_id VARCHAR(191) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  amount_minor BIGINT UNSIGNED NOT NULL,
  currency CHAR(3) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  valid_from DATETIME(6) NOT NULL,
  valid_until DATETIME(6) NOT NULL,
  revoked_at DATETIME(6) NULL,
  UNIQUE KEY billing_provider_payment (provider,provider_payment_id),
  UNIQUE KEY billing_payment_ledger (ledger_id),
  KEY billing_payment_access (subscription_id,revoked_at,valid_until),
  CONSTRAINT billing_payment_subscription_fk FOREIGN KEY (subscription_id) REFERENCES subscriptions(id),
  CONSTRAINT billing_payment_event_fk FOREIGN KEY (event_id) REFERENCES billing_events(id),
  CONSTRAINT billing_payment_ledger_fk FOREIGN KEY (ledger_id) REFERENCES entitlement_ledger(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS billing_adjustments (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  payment_id BIGINT UNSIGNED NOT NULL,
  event_id BIGINT UNSIGNED NOT NULL,
  provider VARCHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  provider_adjustment_id VARCHAR(191) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  kind ENUM('refund','chargeback') NOT NULL,
  amount_minor BIGINT UNSIGNED NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  UNIQUE KEY billing_provider_adjustment (provider,provider_adjustment_id),
  CONSTRAINT billing_adjustment_payment_fk FOREIGN KEY (payment_id) REFERENCES billing_payments(id),
  CONSTRAINT billing_adjustment_event_fk FOREIGN KEY (event_id) REFERENCES billing_events(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
