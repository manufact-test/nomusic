<?php
declare(strict_types=1);
// Private owner-side forensic check. No writes, exports, downloads, or public HTTP endpoint.
ini_set('display_errors', '0');
if (PHP_SAPI !== 'cli') exit(2);
try {
    $app = '/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
    $release = realpath($app . '/current');
    if (!$release || !is_link($app . '/current') || !str_starts_with($release, $app . '/releases/')) throw new RuntimeException();
    require $release . '/bootstrap.php';
    $config = require $release . '/config/app.php';
    if ($config['db_name'] !== 'u235811320_celikom' || $config['storage_driver'] !== 'local') throw new RuntimeException();
    $pdo = Celikom\Database\Connection::open($config);
    $pdo->exec('SET TRANSACTION READ ONLY');
    $pdo->beginTransaction();
    $counts = [];
    foreach (['tracks', 'track_replacements', 'audio_assets', 'upload_submissions'] as $table) {
        $counts[$table] = (int)$pdo->query('SELECT COUNT(*) FROM ' . $table)->fetchColumn();
    }
    $assets = $pdo->query('SELECT storage_key FROM audio_assets WHERE storage_driver = \'local\'')->fetchAll(PDO::FETCH_COLUMN);
    $pdo->commit();
    $known = array_fill_keys(array_map('strval', $assets), true);
    $root = realpath((string)$config['storage_path']);
    if (!$root || !is_dir($root) || !str_starts_with($root, '/home/u235811320/')) throw new RuntimeException();
    $fileCount = 0;
    $unknown = [];
    $knownFiles = 0;
    $scan = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($root, FilesystemIterator::SKIP_DOTS));
    foreach ($scan as $file) {
        if (++$fileCount > 15000) throw new RuntimeException();
        if (!$file->isFile() || $file->isLink()) continue;
        $relative = str_replace('\\', '/', substr($file->getPathname(), strlen($root) + 1));
        if (isset($known[$relative])) $knownFiles++;
        elseif (preg_match('~^audio/[a-f0-9]{2}/[a-f0-9]{64}\\.(mp3|m4a)$~iD', $relative)) $unknown[] = $file->getPathname();
    }
    // Read ID3v2 titles ONLY from unindexed MP3s. Do not log paths, audio or metadata of unrelated songs.
    $matchNames = ['соната ей', 'порнозвезда', 'гипнозы', 'нас нет'];
    $hits = [];
    foreach (array_slice($unknown, 0, 2000) as $path) {
        if (!str_ends_with(strtolower($path), '.mp3')) continue;
        $in = @fopen($path, 'rb');
        if (!$in) continue;
        $header = fread($in, 10);
        $title = '';
        if (strlen($header) === 10 && substr($header, 0, 3) === 'ID3' && in_array(ord($header[3]), [3, 4], true)) {
            $limit = 0;
            for ($i = 6; $i < 10; $i++) $limit = ($limit << 7) | (ord($header[$i]) & 127);
            $limit = min($limit, 262144);
            $bytes = fread($in, $limit);
            $pos = 0;
            while ($pos + 10 <= strlen($bytes)) {
                $id = substr($bytes, $pos, 4);
                if (!preg_match('/^[A-Z0-9]{4}$/D', $id)) break;
                $size = ord($header[3]) === 4
                    ? ((ord($bytes[$pos + 4]) & 127) << 21) | ((ord($bytes[$pos + 5]) & 127) << 14) | ((ord($bytes[$pos + 6]) & 127) << 7) | (ord($bytes[$pos + 7]) & 127)
                    : unpack('N', substr($bytes, $pos + 4, 4))[1];
                $pos += 10;
                if ($size < 1 || $pos + $size > strlen($bytes)) break;
                if ($id === 'TIT2') {
                    $raw = substr($bytes, $pos, $size);
                    $encoding = ord($raw[0]);
                    $title = $encoding === 3 ? substr($raw, 1) : ($encoding === 1 && strlen($raw) > 3 ? @iconv('UTF-16', 'UTF-8//IGNORE', substr($raw, 1)) : '');
                    break;
                }
                $pos += $size;
            }
        }
        fclose($in);
        $normalized = mb_strtolower((string)$title, 'UTF-8');
        $normalized = str_replace('ё', 'е', $normalized);
        foreach ($matchNames as $name) {
            if ($normalized !== '' && str_contains($normalized, $name)) {
                $hits[] = ['target' => $name, 'size_bytes' => filesize($path)];
                break;
            }
        }
    }
    echo json_encode(['counts' => $counts, 'known_local_assets' => count($known),
        'registered_files' => $knownFiles, 'unindexed_files' => count($unknown),
        'title_hits' => $hits], JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR);
} catch (Throwable) {
    fwrite(STDERR, "Private read-only recovery inventory failed.\n");
    exit(1);
}
