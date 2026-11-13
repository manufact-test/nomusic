<?php
declare(strict_types=1);
// W73: read-only lookup of numeric IDs and protected configuration equality.
// JSON is passed to an ephemeral CI file, never printed in Actions logs.
ini_set('display_errors','0');
try {
    if (PHP_SAPI!=='cli') throw new RuntimeException();
    $request=json_decode((string)stream_get_contents(STDIN,2048),true,8,JSON_THROW_ON_ERROR);
    if (!is_array($request) || array_keys($request)!==['host','from','user']) throw new RuntimeException();
    $base='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
    if (!is_link($base.'/current')) throw new RuntimeException();
    $release=realpath($base.'/current');
    if ($release===false || !str_starts_with($release,$base.'/releases/')) throw new RuntimeException();
    require $release.'/bootstrap.php';
    $config=require $release.'/config/app.php';
    if (($config['environment']??'')!=='production') throw new RuntimeException();
    $equals=static fn(string $a,string $b):bool => hash_equals(strtolower(trim($a)),strtolower(trim($b)));
    $match=$equals((string)$config['mail_host'],(string)$request['host'])
        && $equals((string)$config['mail_from'],(string)$request['from'])
        && $equals((string)$config['mail_user'],(string)$request['user']);
    if (!$match) { echo '{"matched":false,"tickets":[]}'; exit(0); }
    $pdo=\Celikom\Database\Connection::open($config);
    $q=$pdo->query("SELECT t.id FROM support_tickets t
        INNER JOIN support_messages m ON m.ticket_id=t.id
        WHERE t.kind='general' AND m.admin_id IS NULL
        AND m.mail_required=1 AND m.delivery='sent'
        AND t.created_at>=UTC_TIMESTAMP()-INTERVAL 48 HOUR
        ORDER BY t.id DESC LIMIT 12");
    $ids=array_map('intval',$q->fetchAll(\PDO::FETCH_COLUMN));
    echo json_encode(['matched'=>true,'tickets'=>$ids],JSON_THROW_ON_ERROR);
} catch(\Throwable) {
    fwrite(STDERR,"W73_MAILBOX_MATCH_REMOTE_FAILED\n");
    exit(1);
}
