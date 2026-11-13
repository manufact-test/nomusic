-- Account-level invitations only. No payment qualification, discounts or rewards enabled.
CREATE TABLE IF NOT EXISTS referral_codes (
  user_id BIGINT UNSIGNED PRIMARY KEY,
  code CHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  UNIQUE KEY referral_code_unique (code),
  CONSTRAINT referral_code_user_fk FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS referrals (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  referrer_user_id BIGINT UNSIGNED NOT NULL,
  invited_user_id BIGINT UNSIGNED NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  UNIQUE KEY referral_invited_once (invited_user_id),
  KEY referral_owner (referrer_user_id,id),
  CONSTRAINT referral_referrer_fk FOREIGN KEY (referrer_user_id) REFERENCES users(id),
  CONSTRAINT referral_invited_fk FOREIGN KEY (invited_user_id) REFERENCES users(id),
  CONSTRAINT referral_not_self CHECK (referrer_user_id <> invited_user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
