<?php
declare(strict_types=1);
/** Read-only, fixed-scope fingerprint check for owner supplied original "Ау". */
if (PHP_SAPI!=='cli') exit(2);
ini_set('display_errors','0');
try {
    $app='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
    $release=realpath($app.'/current');
    if (!is_string($release) || !str_starts_with($release,$app.'/releases/')) {
        throw new RuntimeException('Invalid release');
    }
    require $release.'/bootstrap.php';
    $config=require $release.'/config/app.php';
    $pdo=\Celikom\Database\Connection::open($config);
    $pdo->exec('SET TRANSACTION READ ONLY');
    $pdo->beginTransaction();
    $id='144530503';
    $q=$pdo->prepare("SELECT t.service_track_id,t.title,t.artist,t.duration_ms original_ms,r.id replacement_id,r.version,a.sha256,a.size_bytes,a.duration_ms replacement_ms FROM tracks t JOIN track_replacements r ON r.track_id=t.id JOIN audio_assets a ON a.id=r.audio_asset_id WHERE t.service='yandex' AND t.service_track_id=? AND r.status='approved' AND r.is_active=1 AND r.disabled_at IS NULL");
    $q->execute([$id]);
    $found=$q->fetchAll(PDO::FETCH_ASSOC);
    $all=$pdo->prepare("SELECT t.service_track_id,t.title,r.id replacement_id,r.version,r.status,r.is_active,r.disabled_at,a.sha256,a.size_bytes FROM tracks t JOIN track_replacements r ON r.track_id=t.id JOIN audio_assets a ON a.id=r.audio_asset_id WHERE t.service='yandex' AND t.service_track_id=? ORDER BY r.version DESC LIMIT 25");
    $all->execute([$id]);$allRows=$all->fetchAll(PDO::FETCH_ASSOC);
    $originalHash='5dfdfaa97ee6f1168964a1a49a101bebb20bd5dca7147c41c1d2df366a2a00d8';
    $q=$pdo->prepare("SELECT COUNT(*) FROM audio_assets WHERE sha256=?");
    $q->execute([$originalHash]);$matchedAssets=(int)$q->fetchColumn();
    $pdo->commit();
    $staging=$app.'/shared/staging';
    $sameNameOrSha=false;
    $stagingFiles=0;
    if (is_dir($staging)) {
        foreach(scandir($staging)?:[] as $basename) {
            if($basename==='.'||$basename==='..'||!preg_match('/\\.(mp3|wav)$/iD',$basename))continue;
            $path=$staging.'/'.$basename;
            if(!is_file($path)||is_link($path))continue;
            $stagingFiles++;
            if(filesize($path)===4345176 && hash_file('sha256',$path)===$originalHash)$sameNameOrSha=true;
        }
    }
    echo json_encode([
      'candidate_track'=>$found,
      'all_replacement_versions'=>$allRows,
      'exact_user_original_present_in_audio_assets'=>$matchedAssets>0,
      'exact_user_original_present_in_staging'=>$sameNameOrSha,
      'staging_audio_count'=>$stagingFiles,
    ],JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR)."\n";
} catch(Throwable $error) {
    fwrite(STDERR,"CELIKOM read-only Au inventory unavailable.\n");
    exit(1);
}
