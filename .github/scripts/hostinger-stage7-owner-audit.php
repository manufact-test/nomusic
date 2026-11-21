<?php
declare(strict_types=1);
ini_set('display_errors', '0');
if (PHP_SAPI !== 'cli') exit(2);

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
    $marker = substr($data, $infoAt, 4);
    $metadata = ($marker === 'Info' || $marker === 'Xing') &&
        $infoAt + 8 <= $at + $bytes && substr($data, $sideAt, $side) === str_repeat("\0", $side);
    return ['bytes'=>$bytes, 'rate'=>(int)$rate, 'version'=>$version, 'metadata'=>$metadata];
}

function inspectMp3Bytes(string $data): array
{
    $size = strlen($data);
    $position = 0;
    $tags = [];
    $tagFooterCount = 0;
    $tagError = false;
    $tagBytes = 0;
    while (substr($data, $position, 3) === 'ID3') {
        if ($position + 10 > $size || count($tags) >= 4) { $tagError = true; break; }
        $version = ord($data[$position + 3]);
        $revision = ord($data[$position + 4]);
        $flags = ord($data[$position + 5]);
        if (!in_array($version, [2,3,4], true) || $revision === 255 ||
            ($flags & ($version === 2 ? 0x3f : ($version === 3 ? 0x1f : 0x0f))) !== 0) {
            $tagError = true; break;
        }
        $header = substr($data, $position, 10);
        for ($i=6; $i<10; $i++) if ((ord($header[$i]) & 0x80) !== 0) $tagError = true;
        if ($tagError) break;
        $payload = (ord($header[6]) << 21) | (ord($header[7]) << 14) |
            (ord($header[8]) << 7) | ord($header[9]);
        $length = 10 + $payload + ($version === 4 && ($flags & 0x10) ? 10 : 0);
        if ($length < 10 || $position + $length > $size - 1024 || $tagBytes + $length > 8*1024*1024) {
            $tagError = true; break;
        }
        if ($version === 4 && ($flags & 0x10)) {
            $tagFooterCount++;
            if (substr($data, $position + $length - 10, 3) !== '3DI') { $tagError = true; break; }
        }
        $tags[] = $version . '.' . $revision;
        $tagBytes += $length;
        $position += $length;
    }

    $infoFrames = 0;
    $interleavedId3 = false;
    $interleavedId3Count = 0;
    if (!$tagError) {
        while (true) {
            $frame = mp3FrameAt($data, $position);
            if ($frame === null || !$frame['metadata']) break;
            $infoFrames++;
            $position += $frame['bytes'];
            while (substr($data, $position, 3) === 'ID3') {
                $interleavedId3 = true;
                $interleavedId3Count++;
                if ($position + 10 > $size || count($tags) >= 4) { $tagError = true; break 2; }
                $h = substr($data, $position, 10);
                $v = ord($h[3]); $rev = ord($h[4]); $fl = ord($h[5]);
                if (!in_array($v,[2,3,4],true) || $rev===255 ||
                    ($fl & ($v===2?0x3f:($v===3?0x1f:0x0f)))!==0) { $tagError=true; break 2; }
                for($i=6;$i<10;$i++) if((ord($h[$i])&0x80)!==0) $tagError=true;
                if($tagError) break 2;
                $p=(ord($h[6])<<21)|(ord($h[7])<<14)|(ord($h[8])<<7)|ord($h[9]);
                $len=10+$p+($v===4&&($fl&0x10)?10:0);
                if($position+$len>$size-1024 || $tagBytes+$len>8*1024*1024){$tagError=true;break 2;}
                if($v===4&&($fl&0x10)){ $tagFooterCount++; if(substr($data,$position+$len-10,3)!=='3DI'){$tagError=true;break 2;} }
                $tags[]=$v.'.'.$rev; $tagBytes+=$len; $position+=$len;
            }
        }
    }

    $audioStart = $position;
    $audioFrames = 0;
    $sampleRate = 0;
    $mpegVersion = -1;
    $unexpectedInfoAfterAudio = false;
    while (!$tagError && $position + 4 <= $size) {
        $frame = mp3FrameAt($data, $position);
        if ($frame === null) break;
        if ($frame['metadata']) { $unexpectedInfoAfterAudio = true; break; }
        if ($sampleRate !== 0 && ($sampleRate !== $frame['rate'] || $mpegVersion !== $frame['version'])) break;
        $sampleRate = $frame['rate'];
        $mpegVersion = $frame['version'];
        $position += $frame['bytes'];
        if (++$audioFrames > 500000) break;
    }

    $end = $size;
    $id3v1 = false;
    if ($end - $position >= 128 && substr($data, $end - 128, 3) === 'TAG') {
        $id3v1 = true; $end -= 128;
    }
    $apev2 = false;
    if ($end - $position >= 32 && substr($data, $end - 32, 8) === 'APETAGEX') {
        $footer = $end - 32;
        $apeVersion = unpack('V', substr($data, $footer + 8, 4))[1];
        $apeBytes = unpack('V', substr($data, $footer + 12, 4))[1];
        $apeItems = unpack('V', substr($data, $footer + 16, 4))[1];
        if ($apeVersion === 2000 && $apeBytes >= 32 && $apeBytes <= 1048576 &&
            $apeItems <= 128 && $apeBytes <= $end - $position) {
            $apev2 = true; $end -= $apeBytes;
            if ($end - $position >= 32 && substr($data, $end - 32, 8) === 'APETAGEX') $end -= 32;
        }
    }
    if ($end - $position >= 128 && substr($data, $end - 128, 3) === 'TAG') {
        $id3v1 = true; $end -= 128;
    }
    $utf8Id3v1Variant = false;
    $tailLength = $end - $position;
    if ($tailLength > 128 && $tailLength <= 512 && substr($data, $position, 3) === 'TAG') {
        $utf8Id3v1Variant = true;
    }
    $zeroPadding = 0;
    if ($tailLength > 0 && $tailLength <= 4096 && trim(substr($data, $position, $tailLength), "\0") === '') {
        $zeroPadding = $tailLength;
    }

    $newPatterns = [];
    if ($infoFrames > 1 && $interleavedId3) $newPatterns[] = 'duplicate_info_xing_with_interleaved_id3';
    if ($utf8Id3v1Variant) $newPatterns[] = 'extended_utf8_id3v1_tail';
    return [
        'id3v2_count'=>count($tags), 'id3v2_versions'=>$tags,
        'id3v24_footer_count'=>$tagFooterCount, 'id3v2_parse_error'=>$tagError,
        'info_xing_frames'=>$infoFrames, 'info_xing_interleaved_id3_count'=>$interleavedId3Count,
        'apev2_tail'=>$apev2, 'id3v1_tail'=>$id3v1,
        'extended_utf8_id3v1_candidate'=>$utf8Id3v1Variant,
        'zero_padding_bytes'=>$zeroPadding, 'mpeg_audio_frames'=>$audioFrames,
        'unexpected_info_after_audio'=>$unexpectedInfoAfterAudio,
        'w170_newly_supported_patterns'=>$newPatterns
    ];
}

try {
    $site='/home/u235811320/domains/darkred-camel-588676.hostingersite.com';
    $root=$site.'/celikom';
    $release=realpath($root.'/current');
    if (!$release || !is_link($root.'/current') || !str_starts_with($release,$root.'/releases/')) throw new RuntimeException('release');
    require $release.'/bootstrap.php';
    $config=require $release.'/config/app.php';
    if (($config['db_name'] ?? null) !== 'u235811320_celikom') throw new RuntimeException('db');
    $pdo=Celikom\Database\Connection::open($config);

    $sql="SELECT t.service_track_id,t.artist,t.title,t.duration_ms track_duration_ms,
        r.id replacement_id,r.status,r.is_active,r.created_at,
        a.mime_type,a.size_bytes,a.duration_ms asset_duration_ms,a.sha256,a.storage_key,
        COUNT(u.id) submission_count,MAX(u.created_at) last_submission_at
      FROM track_replacements r
      JOIN tracks t ON t.id=r.track_id
      JOIN audio_assets a ON a.id=r.audio_asset_id
      LEFT JOIN upload_submissions u ON u.replacement_id=r.id
      WHERE t.service='yandex' AND r.status='pending' AND r.is_active=0
      GROUP BY t.service_track_id,t.artist,t.title,t.duration_ms,r.id,r.status,r.is_active,r.created_at,
        a.mime_type,a.size_bytes,a.duration_ms,a.sha256,a.storage_key
      ORDER BY r.id DESC LIMIT 20";
    $rows=$pdo->query($sql)->fetchAll(PDO::FETCH_ASSOC);
    $items=[];
    foreach($rows as $row) {
        $key=(string)$row['storage_key'];
        if (!str_starts_with($key,'audio/') || str_contains($key,'..')) throw new RuntimeException('unsafe_storage_key');
        $path=$root.'/shared/audio/'.$key;
        $real=realpath($path);
        $audioRoot=realpath($root.'/shared/audio');
        $size=(int)$row['size_bytes'];
        $hashOk=$real && $audioRoot && str_starts_with($real,$audioRoot.DIRECTORY_SEPARATOR) &&
            is_file($real) && filesize($real)===$size &&
            hash_equals((string)$row['sha256'],(string)hash_file('sha256',$real));
        $analysis=[];
        $serverDuration=null;
        if($hashOk && $size>=1024 && $size<=31457280 && $row['mime_type']==='audio/mpeg') {
            $bytes=file_get_contents($real);
            if(is_string($bytes)) $analysis=inspectMp3Bytes($bytes);
            if(class_exists(Celikom\Application\Mp3Inspector::class))
                $serverDuration=(new Celikom\Application\Mp3Inspector())->durationMs($real);
        }
        $items[]=[
            'replacement_id'=>(int)$row['replacement_id'],
            'track_id'=>(string)$row['service_track_id'],
            'artist'=>(string)$row['artist'],'title'=>(string)$row['title'],
            'status'=>(string)$row['status'],'active'=>(bool)$row['is_active'],
            'created_at'=>(string)$row['created_at'],
            'submission_count'=>(int)$row['submission_count'],
            'last_submission_at'=>$row['last_submission_at'],
            'mime_type'=>(string)$row['mime_type'],'size_bytes'=>$size,
            'asset_duration_ms'=>(int)$row['asset_duration_ms'],
            'track_duration_ms'=>(int)$row['track_duration_ms'],
            'server_mp3_inspector_duration_ms'=>$serverDuration,
            'duration_delta_ms'=>$serverDuration===null?null:abs($serverDuration-(int)$row['track_duration_ms']),
            'private_file_hash_valid'=>(bool)$hashOk,
            'mp3_metadata'=>$analysis
        ];
    }

    $approved=$pdo->query("SELECT r.status,r.is_active,a.sha256,a.size_bytes,a.storage_key
        FROM track_replacements r JOIN audio_assets a ON a.id=r.audio_asset_id WHERE r.id=1")->fetch(PDO::FETCH_ASSOC);
    $approvedPath=$approved ? $root.'/shared/audio/'.$approved['storage_key'] : '';
    $approvedOk=$approved && $approved['status']==='approved' && (int)$approved['is_active']===1 &&
        is_file($approvedPath) && (int)filesize($approvedPath)===(int)$approved['size_bytes'] &&
        hash_equals($approved['sha256'],hash_file('sha256',$approvedPath));
    $pendingCount=(int)$pdo->query("SELECT COUNT(*) FROM track_replacements WHERE status='pending' AND is_active=0")->fetchColumn();
    echo json_encode([
        'read_only'=>true,'release'=>basename($release),
        'owner_uploads_enabled'=>(bool)$config['owner_uploads_enabled'],
        'pending_total'=>$pendingCount,'recent_pending'=>$items,
        'original_approved_audio_intact'=>(bool)$approvedOk
    ],JSON_THROW_ON_ERROR|JSON_UNESCAPED_SLASHES|JSON_UNESCAPED_UNICODE),"\n";
    if(!$approvedOk) exit(1);
} catch(Throwable $e) {
    fwrite(STDERR,"Read-only upload audit failed; private details suppressed.\n");
    exit(1);
}
