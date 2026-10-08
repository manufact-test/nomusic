<?php

declare(strict_types=1);

namespace Celikom\Database;

final class MigrationRunner
{
    public function __construct(private readonly \PDO $pdo, private readonly string $directory)
    {
    }

    public function run(): array
    {
        if ((int) $this->pdo->query("SELECT GET_LOCK('celikom_schema_migration', 10)")->fetchColumn() !== 1) {
            throw new \RuntimeException('migration_lock_unavailable');
        }
        $applied = [];
        try {
            $this->pdo->exec('CREATE TABLE IF NOT EXISTS schema_migrations (version VARCHAR(120) PRIMARY KEY, sha256 CHAR(64) NOT NULL, applied_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)) ENGINE=InnoDB');
            $files = glob($this->directory . '/*.sql') ?: [];
            sort($files);
            foreach ($files as $file) {
                $version = basename($file);
                $sql = file_get_contents($file);
                if ($sql === false) {
                    throw new \RuntimeException('migration_unreadable');
                }
                $hash = hash('sha256', $sql);
                $select = $this->pdo->prepare('SELECT sha256 FROM schema_migrations WHERE version = ?');
                $select->execute([$version]);
                $oldHash = $select->fetchColumn();
                if ($oldHash !== false) {
                    if (!hash_equals($oldHash, $hash)) {
                        throw new \RuntimeException('applied_migration_changed');
                    }
                    continue;
                }
                // DDL auto-commits: restartable statements, mark only after success.
                foreach (explode(';', $sql) as $statement) {
                    if (trim($statement) !== '') {
                        $this->pdo->exec($statement);
                    }
                }
                $insert = $this->pdo->prepare('INSERT INTO schema_migrations (version, sha256) VALUES (?, ?)');
                $insert->execute([$version, $hash]);
                $applied[] = $version;
            }
        } finally {
            $this->pdo->query("SELECT RELEASE_LOCK('celikom_schema_migration')");
        }
        return $applied;
    }
}
