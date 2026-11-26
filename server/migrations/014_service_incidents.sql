-- Base trial/payment grants remain immutable. Compensation is service-specific.
CREATE TABLE IF NOT EXISTS service_incident_locks (
    service VARCHAR(40) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE IF NOT EXISTS service_incidents (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    service VARCHAR(40) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    request_key CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL UNIQUE,
    reason VARCHAR(500) NOT NULL,
    started_at DATETIME(6) NOT NULL,
    ended_at DATETIME(6) NULL,
    created_by BIGINT UNSIGNED NOT NULL,
    resolved_by BIGINT UNSIGNED NULL,
    freeze_entitlements BOOLEAN NOT NULL DEFAULT TRUE,
    KEY incident_intervals (service, started_at, ended_at),
    CONSTRAINT incident_actor_fk FOREIGN KEY (created_by) REFERENCES admins(id),
    CONSTRAINT incident_resolver_fk FOREIGN KEY (resolved_by) REFERENCES admins(id),
    CONSTRAINT incident_window CHECK (ended_at IS NULL OR ended_at >= started_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE IF NOT EXISTS incident_compensations (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    incident_id BIGINT UNSIGNED NOT NULL,
    ledger_id BIGINT UNSIGNED NOT NULL,
    microseconds BIGINT UNSIGNED NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    UNIQUE KEY incident_grant (incident_id, ledger_id),
    CONSTRAINT compensation_incident_fk FOREIGN KEY (incident_id) REFERENCES service_incidents(id),
    CONSTRAINT compensation_grant_fk FOREIGN KEY (ledger_id) REFERENCES entitlement_ledger(id),
    CONSTRAINT positive_compensation CHECK (microseconds > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
