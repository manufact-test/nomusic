#!/bin/bash
# W178 temporary owner-authorized read-only post-cutover audit.
# No credentials, rows, content, URLs with secrets, mutations or configuration changes.
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
echo CELIKOM_W178_AUDIO_READONLY_START
nginx -t >/dev/null 2>&1 && echo W178_NGINX_SYNTAX_OK
runuser -u www-data -- php <<'PHP_W178'
<?php
declare(strict_types=1);
ini_set('display_errors','0');
ini_set('log_errors','0');
function reportFlag(string $k, bool $v): void { echo $k,'=',($v?'YES':'NO'),PHP_EOL; }
try {
    require '/srv/celikom/app/staging-20261122/bootstrap.php';
    $cfg = require '/srv/celikom/app/staging-20261122/config/app.php';
    $pdo = \Celikom\Database\Connection::open($cfg);
    $pdo->exec('SET TRANSACTION READ ONLY');
    $pdo->beginTransaction();
    reportFlag('W178_EXPECTED_DATABASE', (string)$pdo->query('SELECT DATABASE()')->fetchColumn() === 'celikom_cutover_20261124');
    reportFlag('W178_AUTH_ENABLED', (bool)($cfg['auth_enabled'] ?? false));
    reportFlag('W178_REPLACEMENTS_ENABLED', (bool)($cfg['api_enabled'] ?? false));
    reportFlag('W178_ENTITLEMENT_ENABLED', (bool)($cfg['entitlement_enabled'] ?? false));
    reportFlag('W178_ADMIN_ENABLED', (bool)($cfg['admin_enabled'] ?? false));
    $catalog = new \Celikom\Repositories\PdoCatalogRepository($pdo);
    $storage = new \Celikom\Storage\LocalStorageAdapter($cfg['storage_path']);
    foreach (['18697033','144530503'] as $id) {
        $row = $catalog->findActive('yandex',$id);
        reportFlag('W178_TRACK_'.$id.'_MAPPED', is_array($row));
        reportFlag('W178_TRACK_'.$id.'_FILE', is_array($row) && $row['storage_driver'] === 'local' && $storage->exists($row['storage_key']));
    }
    reportFlag('W178_ADMIN_EXISTS', (int)$pdo->query('SELECT COUNT(*) FROM admins WHERE enabled=1')->fetchColumn() > 0);
    reportFlag('W178_ACTIVE_USER_SESSIONS', (int)$pdo->query('SELECT COUNT(*) FROM user_sessions WHERE revoked_at IS NULL AND refresh_expires_at > UTC_TIMESTAMP(6)')->fetchColumn() > 0);
    $pdo->rollBack();
    echo 'W178_SQL_READ_ONLY_COMPLETED',PHP_EOL;
} catch (Throwable $error) {
    echo 'W178_SQL_READ_ONLY_FAILED',PHP_EOL;
    exit(1);
}
PHP_W178
for entry in   'https://api.celikom.com/api/v1/health'   'https://api.celikom.com/api/v1/config'   'https://api.celikom.com/admin/login'   'https://celikom.com/'; do
  status=$(curl -sS --fail-with-body --connect-timeout 4 --max-time 12     --resolve "$(echo "$entry" | sed -n 's#https://\([^/]*\)/.*#\1#p'):443:127.0.0.1"     -o /dev/null -w '%{http_code}' "$entry" 2>/dev/null) || status="HTTP_ERROR"
  case "$entry" in
    */health) echo "W178_PUBLIC_API_HEALTH=$status" ;;
    */config) echo "W178_PUBLIC_API_CONFIG=$status" ;;
    */admin/login) echo "W178_API_ADMIN_LOGIN=$status" ;;
    */) echo "W178_OWNER_WEBSITE=$status" ;;
  esac
done
echo CELIKOM_W178_AUDIO_READONLY_END
