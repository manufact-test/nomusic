<?php

declare(strict_types=1);

/** Strict, owner-only internal CLI. Never included in the public HTTP router. */

function celikomLibraryParse(string $operation, array $argv): array
{
    $specs = [
        'add-track' => [['track-id', 'duration-ms'], ['artist', 'title', 'album'], []],
        'add-asset' => [['staging-file', 'duration-ms'], [], ['confirm-reviewed']],
        'link' => [['track-db-id', 'asset-id'], [], []],
        'approve' => [['replacement-id'], [], ['confirm-reviewed']],
        'activate' => [['replacement-id'], [], ['confirm-activate']],
        'disable' => [['replacement-id'], [], ['confirm-disable']],
    ];
    if (!isset($specs[$operation])) {
        throw new InvalidArgumentException('invalid_library_operation');
    }
    [$required, $optional, $flags] = $specs[$operation];
    $allowed = array_merge($required, $optional, $flags);
    $parsed = [];
    foreach (array_slice($argv, 1) as $arg) {
        if (!is_string($arg) || !preg_match('/^--([a-z][a-z-]*)(?:=(.*))?$/Ds', $arg, $parts)) {
            throw new InvalidArgumentException('invalid_library_arguments');
        }
        $key = $parts[1];
        if (!in_array($key, $allowed, true) || array_key_exists($key, $parsed)) {
            throw new InvalidArgumentException('invalid_library_arguments');
        }
        if (in_array($key, $flags, true)) {
            if (array_key_exists(2, $parts)) {
                throw new InvalidArgumentException('invalid_library_confirmation');
            }
            $parsed[$key] = true;
        } else {
            if (!array_key_exists(2, $parts) || $parts[2] === '') {
                throw new InvalidArgumentException('invalid_library_arguments');
            }
            $parsed[$key] = $parts[2];
        }
    }
    foreach (array_merge($required, $flags) as $key) {
        if (!array_key_exists($key, $parsed)) {
            throw new InvalidArgumentException('missing_library_argument');
        }
    }
    if (isset($parsed['track-id']) && !preg_match('/^[1-9]\d{0,23}$/D', $parsed['track-id'])) {
        throw new InvalidArgumentException('invalid_library_track_id');
    }
    foreach (['track-db-id', 'asset-id', 'replacement-id'] as $key) {
        if (isset($parsed[$key]) && !preg_match('/^[1-9]\d{0,17}$/D', $parsed[$key])) {
            throw new InvalidArgumentException('invalid_library_numeric_id');
        }
    }
    if (isset($parsed['duration-ms']) && (!preg_match('/^[1-9]\d{0,7}$/D', $parsed['duration-ms'])
        || (int) $parsed['duration-ms'] < 1000 || (int) $parsed['duration-ms'] > 86400000)) {
        throw new InvalidArgumentException('invalid_library_duration');
    }
    if (isset($parsed['staging-file']) && !preg_match('/^[A-Za-z0-9][A-Za-z0-9._-]{0,119}$/D', $parsed['staging-file'])) {
        throw new InvalidArgumentException('invalid_library_staging_name');
    }
    foreach (['artist', 'title', 'album'] as $key) {
        if (isset($parsed[$key]) && (strlen($parsed[$key]) > 240 || strpbrk($parsed[$key], "\r\n\0") !== false)) {
            throw new InvalidArgumentException('invalid_library_metadata');
        }
    }
    return $parsed;
}

function celikomLibraryStagedFile(string $storagePath, string $basename): string
{
    if (!preg_match('/^[A-Za-z0-9][A-Za-z0-9._-]{0,119}$/D', $basename)) {
        throw new InvalidArgumentException('invalid_library_staging_name');
    }
    $directory = dirname($storagePath) . '/staging';
    $staging = realpath($directory);
    if ($staging === false || !is_dir($staging) || is_link($directory)) {
        throw new RuntimeException('library_staging_unavailable');
    }
    $file = $staging . '/' . $basename;
    $resolved = realpath($file);
    if ($resolved === false || dirname($resolved) !== $staging || is_link($file) || !is_file($file)) {
        throw new InvalidArgumentException('invalid_library_staging_file');
    }
    return $resolved;
}

function celikomLibraryRun(string $operation, array $argv): int
{
    if (PHP_SAPI !== 'cli') {
        return 2;
    }
    try {
        $args = celikomLibraryParse($operation, $argv);
    } catch (Throwable) {
        fwrite(STDERR, "Invalid library command arguments. Use documented --name=value parameters and confirmations.\n");
        return 2;
    }
    try {
        require_once dirname(__DIR__) . '/bootstrap.php';
        $config = require dirname(__DIR__) . '/config/app.php';
        if ($config['storage_driver'] !== 'local') {
            throw new RuntimeException('unsupported_library_storage');
        }
        $storage = new Celikom\Storage\LocalStorageAdapter($config['storage_path']);
        $manager = new Celikom\Application\LibraryManagementService(
            Celikom\Database\Connection::open($config), $storage, $config['max_audio_size']
        );
        switch ($operation) {
            case 'add-track':
                $id = $manager->addTrack('yandex', $args['track-id'], (int) $args['duration-ms'], [
                    'artist' => $args['artist'] ?? '', 'title' => $args['title'] ?? '', 'album' => $args['album'] ?? '',
                ]);
                fwrite(STDOUT, "Track ID: $id\n");
                break;
            case 'add-asset':
                $file = celikomLibraryStagedFile($config['storage_path'], $args['staging-file']);
                $id = $manager->addReviewedAsset($file, (int) $args['duration-ms'], $args['confirm-reviewed']);
                fwrite(STDOUT, "AudioAsset ID: $id\n");
                break;
            case 'link':
                $id = $manager->link((int) $args['track-db-id'], (int) $args['asset-id']);
                fwrite(STDOUT, "Pending TrackReplacement ID: $id\n");
                break;
            case 'approve':
                $manager->approve((int) $args['replacement-id'], $args['confirm-reviewed']);
                fwrite(STDOUT, "Reviewed candidate approved, still inactive.\n");
                break;
            case 'activate':
                $manager->activate((int) $args['replacement-id'], $args['confirm-activate']);
                fwrite(STDOUT, "Approved replacement activated.\n");
                break;
            case 'disable':
                $manager->disable((int) $args['replacement-id'], $args['confirm-disable']);
                fwrite(STDOUT, "Replacement disabled.\n");
                break;
        }
        return 0;
    } catch (Throwable) {
        // Database errors and private paths must never appear in CI or CLI logs.
        fwrite(STDERR, "Library operation rejected. Verify the private database, reviewed input and candidate state.\n");
        return 1;
    }
}
