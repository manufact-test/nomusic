<?php
declare(strict_types=1);
ini_set('display_errors', '0');
if (PHP_SAPI !== 'cli') exit(2);

function marker(string $data, int $at, string $text): bool
{
    return $at >= 0 && $at + strlen($text) <= strlen($data) &&
        substr($data, $at, strlen($text)) === $text;
}

function mp3FrameAt(string $data, int $at): ?array
{
    $size = strlen($data);
    if ($at < 0 || $at + 4 > $size) return null;
    $header = unpack('Nvalue', substr($data, $at, 4))['value'];
    if (($header >> 21) !== 0x7ff) return null;
    $version = ($header >> 19) & 3;
    $layer = ($header >> 17) & 3;
    $bitrateIndex = ($header >> 12) & 15;
    $rateIndex = ($header >> 10) & 3;
    if ($version === 1 || $layer !== 1 || $bitrateIndex < 1 || $bitrateIndex > 14 || $rateIndex === 3) return null;
    $bitrates = $version === 3
        ? [0,32,40,48,56,64,80,96,112,128,160,192,224,256,320]
        : [0,8,16,24,32,40,48,56,64,80,96,112,128,144];
    $rate = [44100,48000,32000][$rateIndex] / ($version === 3 ? 1 : ($version === 2 ? 2 : 4));
    $bytes = (int)floor(($version === 3 ? 144 : 72) * $bitrates[$bitrateIndex] * 1000 / $rate) + (($header >> 9) & 1);
    if ($bytes < 24 || $bytes > 1441 || $at + $bytes > $size) return null;
    $crc = (($header >> 16) & 1) === 0 ? 2 : 0;
    $mono = (($header >> 6) & 3) === 3;
    $side = $version === 3 ? ($mono ? 17 : 32) : ($mono ? 9 : 17);
    $sideAt = $at + 4 + $crc;
    $infoAt = $sideAt + $side;
    $info = marker($data, $infoAt, 'Info') || marker($data, $infoAt, 'Xing');
    $zeroSide = $info && $infoAt + 8 <= $at + $bytes &&
        substr($data, $sideAt, $side) === str_repeat("\0", $side);
    return ['bytes'=>$bytes, 'rate'=>(int)$rate, 'version'=>$version,
        'samples'=>$version === 3 ? 1152 : 576, 'metadata'=>$zeroSide];
}

function inspectMp3Bytes(string $data): array
{
    $size = strlen($data);
    $position = 0;
    $tags = [];
    $tagBytes = 0;
    $footerCount = 0;
    $tagError = false;
    $interleavedId3Count = 0;

    $skipId3 = function () use (&$position, &$tags, &$tagBytes, &$footerCount, &$tagError, $data, $size): bool {
        while (marker($data, $position, 'ID3')) {
            if ($position + 10 > $size || count($tags) >= 4) { $tagError = true; return false; }
            $version = ord($data[$position + 3]);
            $revision = ord($data[$position + 4]);
            $flags = ord($data[$position + 5]);
            if (!in_array($version, [2,3,4], true) || $revision === 255 ||
                ($flags & ($version === 2 ? 0x3f : ($version === 3 ? 0x1f : 0x0f))) !== 0) {
                $tagError = true; return false;
            }
            for ($i=6; $i<10; $i++) if ((ord($data[$position + $i]) & 0x80) !== 0) {
                $tagError = true; return false;
            }
            $header = substr($data, $position, 10);
            $payload = (ord($header[6]) << 21) | (ord($header[7]) << 14) |
                (ord($header[8]) << 7) | ord($header[9]);
            $length = 10 + $payload + ($version === 4 && ($flags & 0x10) ? 10 : 0);
            if ($length < 10 || $position + $length > $size - 1024 ||
                $tagBytes + $length > 8 * 1024 * 1024) {
                $tagError = true; return false;
            }
            if ($version === 4 && ($flags & 0x10)) {
                $footerCount++;
                if (!marker($data, $position + $length - 10, '3DI')) {
                    $tagError = true; return false;
                }
            }
            $tags[] = $version . '.' . $revision;
            $tagBytes += $length;
            $position += $length;
        }
        return true;
    };

    if (!$skipId3()) $tagError = true;

    $infoFrames = 0;
    $infoFrameSamples = 0;
    $infoFrameRate = 0;
    $infoFrameVersion = -1;
    while (!$tagError) {
        $frame = mp3FrameAt($data, $position);
        if ($frame === null || !$frame['metadata']) break;
        if (++$infoFrames > 4) { $tagError = true; break; }
        if ($infoFrameRate !== 0 &&
            ($infoFrameRate !== $frame['rate'] || $infoFrameVersion !== $frame['version'])) {
            $tagError = true; break;
        }
        $infoFrameSamples = $frame['samples'];
        $infoFrameRate = $frame['rate'];
        $infoFrameVersion = $frame['version'];
        $position += $frame['bytes'];
        if (marker($data, $position, 'ID3')) {
            $interleavedId3Count++;
            if (!$skipId3()) break;
        }
    }

    $audioFrames = 0;
    $sampleRate = $infoFrameRate;
    $mpegVersion = $infoFrameVersion;
    $samples = $infoFrames > 0 ? $infoFrameSamples : 0;
    $unexpectedInfoAfterAudio = false;
    while (!$tagError && $position + 4 <= $size) {
        $frame = mp3FrameAt($data, $position);
        if ($frame === null) break;
        if ($frame['metadata']) { $unexpectedInfoAfterAudio = true; break; }
        if ($sampleRate !== 0 &&
            ($sampleRate !== $frame['rate'] || $mpegVersion !== $frame['version'])) break;
        $sampleRate = $frame['rate'];
        $mpegVersion = $frame['version'];
        $position += $frame['bytes'];
        $samples += $frame['samples'];
        if (++$audioFrames > 500000) break;
    }

    $end = $size;
    $id3v1 = false;
    if ($end - $position >= 128 && marker($data, $end - 128, 'TAG')) {
        $id3v1 = true;
        $end -= 128;
    }
    $apev2 = false;
    if ($end - $position >= 32 && marker($data, $end - 32, 'APETAGEX')) {
        $footer = $end - 32;
        $ape = unpack('Vversion/Vbytes/Vitems', substr($data, $footer + 8, 12));
        if ($ape['version'] === 2000 && $ape['bytes'] >= 32 &&
            $ape['bytes'] <= 1048576 && $ape['items'] <= 128 &&
            $ape['bytes'] <= $end - $position) {
            $apev2 = true;
            $end -= $ape['bytes'];
            if ($end - $position >= 32 && marker($data, $end - 32, 'APETAGEX')) {
                $header = unpack('Vversion/Vbytes', substr($data, $end - 24, 8));
                if ($header['version'] !== $ape['version'] || $header['bytes'] !== $ape['bytes']) {
                    $tagError = true;
                } else {
                    $end -= 32;
                }
            }
        } else {
            $tagError = true;
        }
    }
    if ($end - $position >= 128 && marker($data, $end - 128, 'TAG')) {
        $id3v1 = true;
        $end -= 128;
    }

    $utf8Id3v1 = false;
    $tailLength = $end - $position;
    if (!$tagError && $tailLength > 128 && $tailLength <= 512 &&
        marker($data, $position, 'TAG')) {
        $text = substr($data, $position + 3, $tailLength - 4);
        if (preg_match('//u', $text) === 1) {
            if (str_starts_with($text, "\xEF\xBB\xBF")) $text = substr($text, 3);
            $characters = preg_match_all('/./us', $text);
            if ($characters === 124 && preg_match('/[\x00-\x1f\x7f]/u', $text) !== 1) {
                $utf8Id3v1 = true;
            }
        }
    }
    $zeroPadding = 0;
    if (!$tagError && $tailLength > 0 && $tailLength <= 4096 &&
        trim(substr($data, $position, $tailLength), "\0") === '') {
        $zeroPadding = $tailLength;
    }

    $parserDuration = null;
    if (!$tagError && !$unexpectedInfoAfterAudio && $audioFrames >= 2 && $sampleRate > 0 &&
        $end >= $position && $end - $position <= 4096 &&
        trim(substr($data, $position, $end - $position), "\0") === '') {
        $parserDuration = (int)round(1000 * $samples / $sampleRate);
    }

    $patterns = [];
    if (count($tags) > 1) $patterns[] = 'multiple_leading_id3v2';
    if ($footerCount > 0) $patterns[] = 'id3v2_footer';
    if ($infoFrames > 1) $patterns[] = 'multiple_info_xing_frames';
    if ($interleavedId3Count > 0) $patterns[] = 'id3_between_info_xing_frames';
    if ($apev2) $patterns[] = 'apev2_tail';
    if ($id3v1) $patterns[] = 'id3v1_tail';
    if ($utf8Id3v1) $patterns[] = 'extended_utf8_id3v1_tail';
    if ($zeroPadding > 0) $patterns[] = 'bounded_zero_padding';
    $newPatterns = [];
    if ($infoFrames > 1 && $interleavedId3Count > 0)
        $newPatterns[] = 'duplicate_info_xing_with_interleaved_id3';
    if ($utf8Id3v1) $newPatterns[] = 'extended_utf8_id3v1_tail';

    return [
        'id3v2_count'=>count($tags),
        'id3v2_versions'=>$tags,
        'id3v24_footer_count'=>$footerCount,
        'info_xing_frames'=>$infoFrames,
        'info_xing_interleaved_id3_count'=>$interleavedId3Count,
        'apev2_tail'=>$apev2,
        'id3v1_tail'=>$id3v1,
        'extended_utf8_id3v1_tail'=>$utf8Id3v1,
        'zero_padding_bytes'=>$zeroPadding,
        'mpeg_audio_frames'=>$audioFrames,
        'parser_duration_ms'=>$parserDuration,
        'unexpected_info_after_audio'=>$unexpectedInfoAfterAudio,
        'metadata_parse_error'=>$tagError,
        'supported_metadata_patterns'=>$patterns,
        'w170_newly_supported_patterns'=>$newPatterns
    ];
}

try {
    $site = '/home/u235811320/domains/darkred-camel-588676.hostingersite.com';
    $root = $site . '/celikom';
    $release = realpath($root . '/current');
    if (!$release || !is_link($root . '/current') ||
        !str_starts_with($release, $root . '/releases/')) throw new RuntimeException('release');
    require $release . '/bootstrap.php';
    $config = require $release . '/config/app.php';
    if (($config['db_name'] ?? null) !== 'u235811320_celikom') throw new RuntimeException('db');
    $pdo = Celikom\Database\Connection::open($config);

    // Previous audit ended at 2026-11-21 09:36:30 UTC and saw replacement IDs 1543–1545.
    // Inspect the latest owner submissions, marking only later submissions as the new batch.
    $cutoff = '2026-11-21 09:36:30';
    $sql = "SELECT t.service_track_id,t.artist,t.title,t.duration_ms track_duration_ms,
        r.id replacement_id,r.status,r.is_active,r.created_at,
        a.mime_type,a.size_bytes,a.duration_ms asset_duration_ms,a.sha256,a.storage_key,
        COUNT(u.id) submission_count,MAX(u.created_at) last_submission_at
      FROM upload_submissions u
      JOIN track_replacements r ON r.id=u.replacement_id
      JOIN tracks t ON t.id=r.track_id
      JOIN audio_assets a ON a.id=r.audio_asset_id
      WHERE t.service='yandex'
      GROUP BY t.service_track_id,t.artist,t.title,t.duration_ms,r.id,r.status,r.is_active,r.created_at,
        a.mime_type,a.size_bytes,a.duration_ms,a.sha256,a.storage_key
      ORDER BY MAX(u.created_at) DESC LIMIT 40";
    $rows = $pdo->query($sql)->fetchAll(PDO::FETCH_ASSOC);
    $items = [];
    foreach ($rows as $row) {
        $key = (string)$row['storage_key'];
        if (!str_starts_with($key, 'audio/') || str_contains($key, '..'))
            throw new RuntimeException('unsafe_storage_key');
        $path = $root . '/shared/audio/' . $key;
        $real = realpath($path);
        $audioRoot = realpath($root . '/shared/audio');
        $size = (int)$row['size_bytes'];
        $hashOk = $real && $audioRoot &&
            str_starts_with($real, $audioRoot . DIRECTORY_SEPARATOR) &&
            is_file($real) && filesize($real) === $size &&
            hash_equals((string)$row['sha256'], (string)hash_file('sha256', $real));
        $metadata = [];
        $serverDuration = null;
        if ($hashOk && $size >= 1024 && $size <= 31457280 &&
            $row['mime_type'] === 'audio/mpeg') {
            $bytes = file_get_contents($real);
            if (is_string($bytes)) $metadata = inspectMp3Bytes($bytes);
            if (class_exists(Celikom\Application\Mp3Inspector::class)) {
                try { $serverDuration = (new Celikom\Application\Mp3Inspector())->durationMs($real); }
                catch (Throwable) { $serverDuration = null; }
            }
        }
        $lastSubmission = (string)$row['last_submission_at'];
        $items[] = [
            'new_since_previous_audit' => $lastSubmission >= $cutoff,
            'last_submission_at' => $lastSubmission,
            'replacement_id' => (int)$row['replacement_id'],
            'track_id' => (string)$row['service_track_id'],
            'artist' => (string)$row['artist'],
            'title' => (string)$row['title'],
            'status' => (string)$row['status'],
            'active' => (bool)$row['is_active'],
            'submission_count' => (int)$row['submission_count'],
            'mime_type' => (string)$row['mime_type'],
            'size_bytes' => $size,
            'asset_duration_ms' => (int)$row['asset_duration_ms'],
            'track_duration_ms' => (int)$row['track_duration_ms'],
            'server_mp3_inspector_duration_ms' => $serverDuration,
            'server_duration_delta_ms' => $serverDuration === null ? null :
                abs($serverDuration - (int)$row['track_duration_ms']),
            'private_file_hash_valid' => (bool)$hashOk,
            'mp3_metadata' => $metadata
        ];
    }

    // One previously reported difficult owner sample: verify it only if an upload is already present.
    $legacyStmt = $pdo->prepare("SELECT t.service_track_id,t.artist,t.title,t.duration_ms track_duration_ms,
        r.id replacement_id,r.status,r.is_active,r.created_at,
        a.mime_type,a.size_bytes,a.duration_ms asset_duration_ms,a.sha256,a.storage_key,
        COUNT(u.id) submission_count
      FROM tracks t
      JOIN track_replacements r ON r.track_id=t.id
      JOIN audio_assets a ON a.id=r.audio_asset_id
      LEFT JOIN upload_submissions u ON u.replacement_id=r.id
      WHERE t.service='yandex' AND t.service_track_id=?
      GROUP BY t.service_track_id,t.artist,t.title,t.duration_ms,r.id,r.status,r.is_active,r.created_at,
        a.mime_type,a.size_bytes,a.duration_ms,a.sha256,a.storage_key
      ORDER BY r.id DESC LIMIT 5");
    $legacyStmt->execute(['48591846']);
    $legacyRows = $legacyStmt->fetchAll(PDO::FETCH_ASSOC);
    $legacyProbe = [];
    foreach ($legacyRows as $row) {
        $key = (string)$row['storage_key'];
        if (!str_starts_with($key, 'audio/') || str_contains($key, '..'))
            throw new RuntimeException('unsafe_legacy_storage_key');
        $path = $root . '/shared/audio/' . $key;
        $real = realpath($path);
        $audioRoot = realpath($root . '/shared/audio');
        $size = (int)$row['size_bytes'];
        $hashOk = $real && $audioRoot &&
            str_starts_with($real, $audioRoot . DIRECTORY_SEPARATOR) &&
            is_file($real) && filesize($real) === $size &&
            hash_equals((string)$row['sha256'], (string)hash_file('sha256', $real));
        $metadata = [];
        $serverDuration = null;
        if ($hashOk && $size >= 1024 && $size <= 31457280 && $row['mime_type'] === 'audio/mpeg') {
            $bytes = file_get_contents($real);
            if (is_string($bytes)) $metadata = inspectMp3Bytes($bytes);
            if (class_exists(Celikom\Application\Mp3Inspector::class)) {
                try { $serverDuration = (new Celikom\Application\Mp3Inspector())->durationMs($real); }
                catch (Throwable) { $serverDuration = null; }
            }
        }
        $legacyProbe[] = [
            'replacement_id' => (int)$row['replacement_id'],
            'track_id' => (string)$row['service_track_id'],
            'artist' => (string)$row['artist'],
            'title' => (string)$row['title'],
            'status' => (string)$row['status'],
            'active' => (bool)$row['is_active'],
            'created_at' => (string)$row['created_at'],
            'submission_count' => (int)$row['submission_count'],
            'size_bytes' => $size,
            'private_file_hash_valid' => (bool)$hashOk,
            'server_mp3_inspector_duration_ms' => $serverDuration,
            'mp3_metadata' => $metadata
        ];
    }

    $approved = $pdo->query("SELECT r.status,r.is_active,a.sha256,a.size_bytes,a.storage_key
        FROM track_replacements r JOIN audio_assets a ON a.id=r.audio_asset_id WHERE r.id=1")
        ->fetch(PDO::FETCH_ASSOC);
    $approvedPath = $approved ? $root . '/shared/audio/' . $approved['storage_key'] : '';
    $approvedOk = $approved && $approved['status'] === 'approved' &&
        (int)$approved['is_active'] === 1 && is_file($approvedPath) &&
        (int)filesize($approvedPath) === (int)$approved['size_bytes'] &&
        hash_equals($approved['sha256'], hash_file('sha256', $approvedPath));
    $pendingCount = (int)$pdo->query(
        "SELECT COUNT(*) FROM track_replacements WHERE status='pending' AND is_active=0"
    )->fetchColumn();
    $newCount = count(array_filter($items, static fn(array $x): bool => $x['new_since_previous_audit']));
    echo json_encode([
        'read_only' => true,
        'release' => basename($release),
        'owner_uploads_enabled' => (bool)$config['owner_uploads_enabled'],
        'previous_audit_cutoff' => $cutoff,
        'latest_owner_uploads' => count($items),
        'new_since_previous_audit' => $newCount,
        'pending_total' => $pendingCount,
        'recent_owner_submissions' => $items,
        'known_legacy_track_48591846' => $legacyProbe,
        'original_approved_audio_intact' => (bool)$approvedOk
    ], JSON_THROW_ON_ERROR | JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE), "\n";
    if (!$approvedOk) exit(1);
} catch (Throwable) {
    fwrite(STDERR, "Stage 7 read-only upload/MP3 audit failed; private details suppressed.\n");
    exit(1);
}
