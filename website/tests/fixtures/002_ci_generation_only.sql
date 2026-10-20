-- Stage 10 CI-only schema evolution rehearsal: NEVER apply to live CMS.
-- Version 2 is tested on a freshly restored disposable MySQL database only.
CREATE TABLE cms_schema_versions (
  version INT UNSIGNED NOT NULL PRIMARY KEY,
  migration_name VARCHAR(80) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
ALTER TABLE site_settings ADD COLUMN release_generation VARCHAR(16) NOT NULL DEFAULT 'v2';
INSERT INTO cms_schema_versions(version,migration_name) VALUES(2,'ci-offline-generation-v2');
