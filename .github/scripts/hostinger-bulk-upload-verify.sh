#!/usr/bin/env bash
set -euo pipefail
umask 077
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
printf '%s\n' "$HOSTINGER_SSH_KEY" | tr -d '\r' > "$work/key"
ssh-keygen -y -P '' -f "$work/key" > "$work/public"
test "$(ssh-keygen -lf "$work/public" -E sha256 | awk '{print $2}')" = 'SHA256:Q6FyifXRq6garceQdIIjBmXhkk81Ic1p/x9JTSYHWUk'
printf '%s\n' '[92.113.19.189]:65002 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAf8M2EVwq0oJI8I9KZ0NFE8P8yDOvDATEhkQti/Kk/0' > "$work/known_hosts"
ssh -T -p 65002 -i "$work/key" -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o "UserKnownHostsFile=$work/known_hosts" -o GlobalKnownHostsFile=/dev/null -o ConnectTimeout=15 u235811320@92.113.19.189 /opt/alt/php83/usr/bin/php <<'PHP'
<?php
ini_set('display_errors','0');
try {
    $root='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom/current';
    require $root.'/bootstrap.php'; $config=require $root.'/config/app.php';
    $pdo=Celikom\Database\Connection::open($config);
    $rows=$pdo->query("SELECT u.id FROM users u JOIN user_email_security e ON e.user_id=u.id WHERE u.status='active' AND e.verified_at IS NOT NULL")->fetchAll(PDO::FETCH_COLUMN);
    $bulk=0; $ordinary=0;
    foreach($rows as $id) {
        $limits=Celikom\Application\UploadRatePolicy::forAccount($pdo,(int)$id);
        if($limits['bulk']) {
            if($limits!==['account'=>500,'device'=>1000,'ip'=>3000,'bulk'=>true])throw new RuntimeException('invalid_bulk_limits');
            $bulk++;
        } else {
            if($limits!==['account'=>10,'device'=>20,'ip'=>60,'bulk'=>false])throw new RuntimeException('invalid_ordinary_limits');
            $ordinary++;
        }
    }
    if($bulk<1 || $bulk>2)throw new RuntimeException('unexpected_bulk_identity_count');
    echo json_encode(['read_only'=>true,'release'=>basename(realpath($root)),'verified_bulk_accounts'=>$bulk,'bulk_attempts_per_hour'=>500,'ordinary_accounts_unchanged'=>true]),"\n";
} catch(Throwable $e) {fwrite(STDERR,"Bulk quota verification failed; private details suppressed.\n");exit(1);}
PHP
