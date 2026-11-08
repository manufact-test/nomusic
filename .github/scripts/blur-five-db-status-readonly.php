<?php

declare(strict_types=1);

// CELIKOM Blur 5: no side effects, SELECT-only from the currently active API release.
// Execute on the verified existing Hostinger API host via php stdin.
ini_set('display_errors', '0');
try {
    $base = '/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
    $release = realpath($base . '/current');
    $releases = realpath($base . '/releases');
    if ($release === false || $releases === false || !str_starts_with($release, $releases . DIRECTORY_SEPARATOR)) {
        throw new RuntimeException('unexpected_live_release');
    }
    if (!is_file($release . '/bootstrap.php') || !is_file($release . '/config/app.php')) {
        throw new RuntimeException('unexpected_api_layout');
    }
    require_once $release . '/bootstrap.php';
    $config = require $release . '/config/app.php';
    $pdo = Celikom\Database\Connection::open($config);
    $pdo->exec('START TRANSACTION READ ONLY');
    $ids = ['17198343', '24442524', '27323567', '29851850', '32988400', '25168288', '17198411', '21220262', '30212997'];
    $in = implode(',', array_fill(0, count($ids), '?'));
    $st = $pdo->prepare("SELECT t.service_track_id AS yandex_id, t.id AS local_id, t.artist, t.title, r.status, r.is_active, r.disabled_at
        FROM tracks t LEFT JOIN track_replacements r ON r.track_id = t.id
        WHERE t.service = 'yandex' AND t.service_track_id IN ($in)
        ORDER BY t.service_track_id, r.id");
    $st->execute($ids);
    $rows = $st->fetchAll(PDO::FETCH_ASSOC);
    $out = [];
    foreach ($ids as $id) {
        $out[$id] = ['track_found' => false, 'mapping_statuses' => [], 'active' => false];
    }
    foreach ($rows as $row) {
        $id = (string) $row['yandex_id'];
        $out[$id]['track_found'] = true;
        if ($row['status'] !== null) {
            $out[$id]['mapping_statuses'][] = (string) $row['status'];
            if ($row['status'] === 'approved' && (int) $row['is_active'] === 1 && $row['disabled_at'] === null) {
                $out[$id]['active'] = true;
            }
        }
    }
    // Potential alternate Yandex ID with the same title: informational only.
    $sample = [['Сектор Газа', 'Опять сегодня'], ['Агата Кристи', 'Моряк'], ['GUF', 'Ice Baby'], ['PHARAOH', 'Black Siemens'], ['Найк Борзов', 'Лошадка'], ['ЛСП', 'Уровни'], ['Сектор Газа', 'Наркоман'], ['Anacondaz', 'Радуга'], ['Yanix', 'Трэп хата']];
    $alt = [];
    $similar = $pdo->prepare("SELECT service_track_id AS yandex_id, artist, title
        FROM tracks WHERE service = 'yandex' AND title = ? LIMIT 20");
    foreach ($sample as [$artist, $title]) {
        $similar->execute([$title]);
        $alt[$title] = array_map(static fn($x) => ['track_id' => (string) $x['yandex_id'], 'artist' => (string) $x['artist']], $similar->fetchAll(PDO::FETCH_ASSOC));
    }
    $requestStmt = $pdo->prepare("SELECT service_track_id, status FROM track_requests WHERE service = 'yandex' AND service_track_id IN ($in) ORDER BY id");
    $requestStmt->execute($ids);
    foreach ($out as $id => $_row) { $out[$id]['track_request_statuses'] = []; }
    foreach ($requestStmt->fetchAll(PDO::FETCH_ASSOC) as $rq) {
        $out[(string) $rq['service_track_id']]['track_request_statuses'][] = (string) $rq['status'];
    }
    $pdo->rollBack();
    echo json_encode(['source' => 'live_approved_and_pending_readonly', 'candidate_count' => count($ids), 'results' => $out, 'same_title_records' => $alt, 'writes' => 0], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT) . "\n";
} catch (Throwable $e) {
    fwrite(STDERR, "READONLY_DB_CHECK_FAILED: verify server location, active release, PHP/PDO and permissions\n");
    exit(1);
}