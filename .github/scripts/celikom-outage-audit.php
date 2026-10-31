<?php
declare(strict_types=1);
/* Read-only CLI audit. Never print raw log lines, configuration or user data. */
ini_set('display_errors', '0');
if (PHP_SAPI !== 'cli') exit(2);
$site = '/home/u235811320/domains/darkred-camel-588676.hostingersite.com';
$app = $site . '/celikom';
$release = realpath($app . '/current');
$report = ['at_utc'=>gmdate('c'), 'read_only'=>true, 'php'=>PHP_VERSION,
    'release'=>$release !== false ? basename($release) : null,
    'disk_free_bytes'=>disk_free_space($site), 'logs'=>[]];
/* Only this website's bounded PHP log tails; other domains are excluded. */
$paths = array_unique(array_merge([$site.'/public_html/error_log', $site.'/error_log'],
    glob($site.'/.logs/*error*') ?: [], glob($site.'/.logs/*php*') ?: [],
    glob($site.'/logs/*error*') ?: [], glob($site.'/logs/*php*') ?: [],
    glob('/home/u235811320/.logs/*darkred-camel-588676*') ?: []));
foreach (array_slice($paths, 0, 12) as $path) {
    if (!is_file($path) || is_link($path) || !is_readable($path)) continue;
    $stream=fopen($path, 'rb'); if ($stream===false) continue;
    $size=filesize($path); $offset=max(0, $size-262144); fseek($stream, $offset);
    if ($offset>0) fgets($stream);
    $tail=stream_get_contents($stream, 262144); fclose($stream);
    $groups=[];
    foreach (explode("\n", (string)$tail) as $line) {
        $category=null;
        foreach (['missing_required_file'=>'/Failed opening required|Failed to open stream/i',
            'php_parse'=>'/Parse error|syntax error/i', 'php_memory'=>'/Allowed memory size/i',
            'database_connections'=>'/Too many connections|max_user_connections/i',
            'database_resource_limit'=>'/max_questions|max_updates|max_connections|exceeded.*resource/i',
            'database_unavailable'=>'/SQLSTATE\[08|Connection refused|server has gone away/i',
            'database_error'=>'/PDOException|SQLSTATE/i', 'php_timeout'=>'/Maximum execution time/i',
            'disk_full'=>'/No space left on device/i', 'php_fatal'=>'/Fatal error|Uncaught /i',
            'service_unavailable'=>'/CELIKOM service_unavailable/i'] as $name=>$pattern) {
            if (preg_match($pattern,$line)) { $category=$name; break; }
        }
        if ($category===null) continue;
        $time=null;
        if (preg_match('/^\[([0-9]{2}-[A-Za-z]{3}-[0-9]{4} [0-9:]{8}(?: [A-Za-z_\/+-]+)?)\]/', $line, $m)) $time=$m[1];
        $sql='';
        /* Application logs deliberately store only underscore-delimited SQL codes. */
        if (preg_match('/_sqlstate_([A-Z0-9]{5})_driver_([0-9]{1,5})/i', $line, $m)) {
            $sql=' SQLSTATE='.strtoupper($m[1]).' driver_code='.$m[2];
            $category=match ((int)$m[2]) {
                1040,1203=>'database_connections',
                1226=>'database_resource_limit',
                2002,2003,2006,2013=>'database_unavailable',
                default=>'database_error'
            };
        }
        if (preg_match('/SQLSTATE\[([A-Z0-9]{5})\](?:\s*\[([0-9]{3,5})\])?/', $line, $m)) {
            $sql=' SQLSTATE='.$m[1];
            if (isset($m[2])) $sql.=' driver_code='.$m[2];
        }
        if (preg_match('/(?:General error|Syntax error or access violation): ([0-9]{3,5})/', $line, $m)) $sql.=' driver_code='.$m[1];
        $key=($time ?? 'unknown_time').' '.$category.$sql;
        $groups[$key]=($groups[$key] ?? 0)+1;
    }
    $report['logs'][]=['path'=>str_starts_with($path,$site.'/')?substr($path,strlen($site)+1):'account-logs/'.basename($path),'modified_utc'=>gmdate('c',filemtime($path)),
        'tail_bytes'=>strlen((string)$tail),'classified_errors'=>array_slice($groups,-100,null,true)];
}
try {
    if ($release===false || !str_starts_with($release,$app.'/releases/')) throw new RuntimeException('layout');
    $report['entry_files']=[];
    foreach (['index.php','.htaccess','.user.ini'] as $name) {
        $file=$site.'/public_html/'.$name;
        $report['entry_files'][$name]=['exists'=>is_file($file),'modified_utc'=>is_file($file)?gmdate('c',filemtime($file)):null];
    }
    require $release.'/bootstrap.php';
    $config=require $release.'/config/app.php';
    $started=microtime(true);
    $pdo=Celikom\Database\Connection::open($config); $pdo->query('SELECT 1')->fetchColumn();
    $report['database']=['ok'=>true,'elapsed_ms'=>round((microtime(true)-$started)*1000)];
} catch (Throwable $error) {
    $report['database']=['ok'=>false,'error_class'=>get_class($error)];
}
echo json_encode($report,JSON_THROW_ON_ERROR|JSON_PRETTY_PRINT),"\n";
