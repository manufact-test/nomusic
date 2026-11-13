<?php
declare(strict_types=1);

$root = sys_get_temp_dir() . '/celikom-stage5-inventory-' . bin2hex(random_bytes(8));
$audio = $root . '/audio';
if (!mkdir($audio, 0700, true)) {
    throw new RuntimeException('test_directory_create_failed');
}

$inventory = static function (string $dir): array {
    $result = [];
    $iterator = new RecursiveIteratorIterator(
        new RecursiveDirectoryIterator($dir, FilesystemIterator::SKIP_DOTS)
    );
    foreach ($iterator as $entry) {
        if ($entry->isLink() || !$entry->isFile()) {
            throw new RuntimeException('unsafe_test_audio_object');
        }
        $relative = substr($entry->getPathname(), strlen($dir) + 1);
        $result[$relative] = [
            'sha256' => hash_file('sha256', $entry->getPathname()),
            'size' => $entry->getSize(),
        ];
    }
    ksort($result);
    return $result;
};

try {
    $source = $audio . '/original.mp3';
    $temporary = $audio . '/.tmp-replacement';
    file_put_contents($source, 'original-audio-bytes');

    $baseline = $inventory($audio);
    if ($baseline !== $inventory($audio)) {
        throw new RuntimeException('unchanged_inventory_not_stable');
    }

    // Match LocalStorageAdapter::put(): new inode + atomic rename.
    file_put_contents($temporary, 'new-audio-version');
    if (!rename($temporary, $source)) {
        throw new RuntimeException('atomic_replace_failed');
    }
    if ($inventory($audio) === $baseline) {
        throw new RuntimeException('inventory_missed_atomic_replacement');
    }

    $changed = $inventory($audio);
    if (!unlink($source) || $inventory($audio) === $changed) {
        throw new RuntimeException('inventory_missed_deleted_original');
    }

    echo "Stage 5 immutable audio SHA256 inventory contract PASS\n";
} finally {
    foreach (glob($audio . '/.*') ?: [] as $file) {
        if (is_file($file)) unlink($file);
    }
    foreach (glob($audio . '/*') ?: [] as $file) {
        if (is_file($file)) unlink($file);
    }
    if (is_dir($audio)) rmdir($audio);
    if (is_dir($root)) rmdir($root);
}
