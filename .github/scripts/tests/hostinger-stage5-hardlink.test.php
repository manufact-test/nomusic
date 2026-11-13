<?php
declare(strict_types=1);

$root = sys_get_temp_dir() . '/celikom-stage5-hardlink-' . bin2hex(random_bytes(8));
$sourceDir = $root . '/source';
$backupDir = $root . '/backup';
$restoreDir = $root . '/restore';
foreach ([$sourceDir, $backupDir, $restoreDir] as $dir) {
    if (!mkdir($dir, 0700, true)) {
        throw new RuntimeException('test_directory_create_failed');
    }
}

try {
    $source = $sourceDir . '/immutable-audio.mp3';
    $backup = $backupDir . '/immutable-audio.mp3';
    $restored = $restoreDir . '/immutable-audio.mp3';
    $temporary = $sourceDir . '/.tmp-replacement';

    file_put_contents($source, 'original-audio-bytes');
    if (!link($source, $backup)) {
        throw new RuntimeException('same_filesystem_hardlink_unavailable');
    }

    $sourceStat = stat($source);
    $backupStat = stat($backup);
    if ($sourceStat === false || $backupStat === false ||
        $sourceStat['dev'] !== $backupStat['dev'] ||
        $sourceStat['ino'] !== $backupStat['ino']) {
        throw new RuntimeException('snapshot_is_not_a_hardlink');
    }

    // Match LocalStorageAdapter::put(): write a fresh inode, then atomic rename.
    file_put_contents($temporary, 'new-audio-version');
    if (!rename($temporary, $source)) {
        throw new RuntimeException('atomic_replace_failed');
    }
    if (file_get_contents($backup) !== 'original-audio-bytes') {
        throw new RuntimeException('snapshot_changed_after_atomic_replace');
    }

    // Match LocalStorageAdapter::delete(): unlink only the source pathname.
    if (!unlink($source) || file_get_contents($backup) !== 'original-audio-bytes') {
        throw new RuntimeException('snapshot_lost_after_source_unlink');
    }

    if (!link($backup, $restored) || file_get_contents($restored) !== 'original-audio-bytes') {
        throw new RuntimeException('restore_hardlink_failed');
    }

    echo "Stage 5 immutable audio hard-link rollback contract PASS\n";
} finally {
    foreach ([$sourceDir, $backupDir, $restoreDir] as $dir) {
        foreach (glob($dir . '/.*') ?: [] as $file) {
            if (is_file($file)) unlink($file);
        }
        foreach (glob($dir . '/*') ?: [] as $file) {
            if (is_file($file)) unlink($file);
        }
        if (is_dir($dir)) rmdir($dir);
    }
    if (is_dir($root)) rmdir($root);
}
