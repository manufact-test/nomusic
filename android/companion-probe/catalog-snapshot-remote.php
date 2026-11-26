<?php
declare(strict_types=1);
// Owner diagnostic only: metadata SELECT in a read-only transaction, no public endpoint.
ini_set('display_errors', '0');
if (PHP_SAPI !== 'cli') exit(2);
try {
    $app = '/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
    $release = realpath($app . '/current');
    if (!$release || !is_link($app . '/current') || !str_starts_with($release, $app . '/releases/')) throw new RuntimeException();
    require $release . '/bootstrap.php';
    $config = require $release . '/config/app.php';
    if ($config['db_name'] !== 'u235811320_celikom') throw new RuntimeException();
    $pdo = Celikom\Database\Connection::open($config);
    $pdo->exec('SET TRANSACTION READ ONLY');
    $pdo->beginTransaction();
    $count = (int)$pdo->query("SELECT COUNT(*) FROM tracks WHERE service='yandex'")->fetchColumn();
    $rows = $pdo->query("SELECT service_track_id AS track_id,title,artist,album,duration_ms,
        EXISTS(SELECT 1 FROM track_replacements r WHERE r.track_id=t.id AND r.status='approved' AND r.is_active=1 AND r.disabled_at IS NULL) AS replacement_available
        FROM tracks t WHERE service='yandex' ORDER BY t.id LIMIT 5000")->fetchAll(PDO::FETCH_ASSOC);
    $pdo->commit();
    $items = [];
    foreach ($rows as $r) {
        if (!preg_match('/^[1-9][0-9]{0,23}$/D', (string)$r['track_id'])) throw new RuntimeException();
        $items[] = ['track_id'=>(string)$r['track_id'], 'title'=>(string)$r['title'], 'artist'=>(string)$r['artist'],
            'album'=>(string)$r['album'], 'duration_ms'=>(int)$r['duration_ms'], 'replacement_available'=>(bool)$r['replacement_available']];
    }
    echo json_encode(['schema'=>1,'source'=>'celikom_owner_catalog_snapshot','generated_at_ms'=>(int)round(microtime(true)*1000),
        'complete'=>$count<=5000,'total_tracks'=>$count,'tracks'=>$items], JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR);
} catch (Throwable) { fwrite(STDERR,"Read-only catalog snapshot failed.\n"); exit(1); }
