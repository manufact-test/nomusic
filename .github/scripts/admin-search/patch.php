<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' || $argc !== 3) exit(1);
$source = file_get_contents($argv[1]);
$manifest = json_decode(file_get_contents($argv[2]),true,32,JSON_THROW_ON_ERROR);
if (hash('sha256',$source) !== $manifest['before']) throw new RuntimeException('live_admin_changed_abort');
foreach ($manifest['replace'] as $pair) {
    if (substr_count($source,$pair['old']) !== 1) throw new RuntimeException('anchor_mismatch');
    $source = str_replace($pair['old'],$pair['new'],$source);
}
if (hash('sha256',$source) !== $manifest['after']) throw new RuntimeException('patched_hash_mismatch');
if (file_put_contents($argv[1],$source) !== strlen($source)) throw new RuntimeException('write_failed');
echo "ADMIN_SEARCH_EXACT_PATCH_PASS\n";
