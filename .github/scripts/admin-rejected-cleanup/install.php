<?php

declare(strict_types=1);
if (PHP_SAPI !== 'cli' || $argc !== 3) throw new RuntimeException('arguments');
$release = $argv[1]; $payload = $argv[2];
$manifest = json_decode(file_get_contents($payload . '/manifest.json'), true, 16, JSON_THROW_ON_ERROR);
foreach ($manifest as $name => $hashes) {
    if (!in_array($name, ['AdminPanel.php','ModerationService.php','BulkModerationService.php','BulkModerationView.php','bulk-moderation.js','admin-style.css'], true)) throw new RuntimeException('path');
    $target = $release . '/src/Admin/' . $name;
    $old = is_file($target) ? hash_file('sha256', $target) : null;
    if (!in_array($old, $hashes['before'], true) || hash_file('sha256', $payload . '/' . $name) !== $hashes['after']) throw new RuntimeException('source_changed');
}
foreach ($manifest as $name => $hashes) {
    $target = $release . '/src/Admin/' . $name;
    if (!copy($payload . '/' . $name, $target) || hash_file('sha256', $target) !== $hashes['after']) throw new RuntimeException('copy_failed');
}
echo "ADMIN_REJECTED_CLEANUP_PATCH_PASS\n";
