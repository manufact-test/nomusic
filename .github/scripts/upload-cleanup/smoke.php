<?php

declare(strict_types=1);
ini_set('display_errors', '0');
if (PHP_SAPI !== 'cli' || $argc !== 3) throw new RuntimeException('arguments');
$release = realpath($argv[1]); $payload = realpath($argv[2]);
$root = '/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
if ($release === false || $payload === false || !str_starts_with($release, $root . '/releases/upload-cleanup-') || !str_starts_with($payload, $root . '/incoming/')) throw new RuntimeException('paths');
$nonce = bin2hex(random_bytes(32));
$name = 'celikom-qa-' . bin2hex(random_bytes(16)) . '.php';
$public = dirname($root) . '/public_html/' . $name;
$code = '<?php declare(strict_types=1); ini_set("display_errors","0");'
    . 'if(!hash_equals(' . var_export(hash('sha256', $nonce), true) . ',hash("sha256",$_SERVER["HTTP_X_CELIKOM_QA"]??""))){http_response_code(404);exit;}'
    . 'header("Cache-Control: no-store");header("Content-Type: text/plain");require ' . var_export($payload . '/probe.php', true) . ';'
    . 'cleanupProbe(' . var_export($release, true) . ',' . var_export($payload, true) . ');';
$file = fopen($public, 'xb');
if ($file === false) throw new RuntimeException('probe_create');
try {
    if (fwrite($file, $code) !== strlen($code)) throw new RuntimeException('probe_write');
    fclose($file); $file = null; chmod($public, 0644);
    $ch = curl_init('https://darkred-camel-588676.hostingersite.com/' . $name);
    curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_FOLLOWLOCATION => false,
        CURLOPT_HTTPHEADER => ['X-Celikom-QA: ' . $nonce, 'Cache-Control: no-store'],
        CURLOPT_SSL_VERIFYPEER => true, CURLOPT_SSL_VERIFYHOST => 2, CURLOPT_CONNECTTIMEOUT => 8, CURLOPT_TIMEOUT => 40]);
    $body = curl_exec($ch); $status = curl_getinfo($ch, CURLINFO_RESPONSE_CODE); curl_close($ch);
    if ($status !== 200 || $body !== "UPLOAD_CLEANUP_PROBE_PASS\n") throw new RuntimeException('fpm_probe_failed');
    echo "UPLOAD_CLEANUP_HTTPS_FPM_PASS\n";
} finally {
    if (is_resource($file)) fclose($file);
    if (is_file($public)) unlink($public);
}
