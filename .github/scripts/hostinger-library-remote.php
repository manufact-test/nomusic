<?php

declare(strict_types=1);

/**
 * Stage 6 owner-only Actions entrypoint, executed solely via pinned SSH under
 * /celikom/incoming; never a public PHP/HTTP endpoint.
 */
if (PHP_SAPI !== 'cli' || count($argv) !== 2) {
    exit(2);
}
ini_set('display_errors', '0');
try {
    $site = '/home/u235811320/domains/darkred-camel-588676.hostingersite.com';
    $app = $site . '/celikom';
    $incoming = __DIR__;
    $sha = getenv('CELIKOM_LIBRARY_COMMIT');
    if (!is_string($sha) || !preg_match('/^[a-f0-9]{40}$/D', $sha)
        || realpath(dirname(__DIR__, 2)) !== $app || is_link($app)
        || !is_dir($site . '/public_html')
        || $incoming !== $app . '/incoming/library-operation-' . $sha) {
        throw new RuntimeException('invalid_private_context');
    }
    if (realpath($argv[1]) !== $incoming . '/hostinger-library-request.json'
        || !is_file($argv[1]) || filesize($argv[1]) > 2048) {
        throw new RuntimeException('invalid_private_request');
    }
    $request = json_decode((string) file_get_contents($argv[1]), true, 8, JSON_THROW_ON_ERROR);
    $schema = [
        'inspect' => ['operation'],
        'add-track' => ['operation', 'track_id', 'duration_ms', 'confirm_owner'],
        'add-asset' => ['operation', 'duration_ms', 'confirm_owner', 'confirm_reviewed'],
        'link' => ['operation', 'track_db_id', 'asset_id', 'confirm_owner'],
        'approve' => ['operation', 'replacement_id', 'confirm_owner', 'confirm_reviewed'],
        'activate' => ['operation', 'replacement_id', 'expected_active_replacement_id', 'confirm_owner', 'confirm_activate'],
        'disable' => ['operation', 'replacement_id', 'expected_active_replacement_id', 'confirm_owner', 'confirm_disable'],
    ];
    if (!is_array($request) || array_is_list($request)
        || !is_string($request['operation'] ?? null) || !isset($schema[$request['operation']])) {
        throw new InvalidArgumentException('invalid_library_request');
    }
    $operation = $request['operation'];
    $actualKeys = array_keys($request);
    $expectedKeys = $schema[$operation];
    sort($actualKeys);
    sort($expectedKeys);
    if ($actualKeys !== $expectedKeys) {
        throw new InvalidArgumentException('invalid_library_request');
    }
    if (isset($request['track_id']) && (!is_string($request['track_id'])
        || !preg_match('/^[1-9][0-9]{0,23}$/D', $request['track_id']))) {
        throw new InvalidArgumentException('invalid_track');
    }
    foreach (['track_db_id', 'asset_id', 'replacement_id'] as $key) {
        if (isset($request[$key]) && (!is_string($request[$key])
            || !preg_match('/^[1-9][0-9]{0,17}$/D', $request[$key]))) {
            throw new InvalidArgumentException('invalid_library_id');
        }
    }
    if (isset($request['expected_active_replacement_id'])
        && (!is_string($request['expected_active_replacement_id'])
        || !preg_match('/^(0|[1-9][0-9]{0,17})$/D', $request['expected_active_replacement_id']))) {
        throw new InvalidArgumentException('invalid_expected_mapping');
    }
    if (isset($request['duration_ms']) && (!is_int($request['duration_ms'])
        || $request['duration_ms'] < 1000 || $request['duration_ms'] > 86400000)) {
        throw new InvalidArgumentException('invalid_duration');
    }
    foreach (['confirm_owner', 'confirm_reviewed', 'confirm_activate', 'confirm_disable'] as $field) {
        if (array_key_exists($field, $request) && $request[$field] !== true) {
            throw new InvalidArgumentException('explicit_review_required');
        }
    }

    $release = realpath($app . '/current');
    $shared = $app . '/shared';
    $env = $shared . '/env';
    if (!is_link($app . '/current') || !is_string($release)
        || !str_starts_with($release, $app . '/releases/')
        || is_link($shared) || is_link($env) || !is_file($env)
        || filesize($env) > 16384 || !is_dir($shared . '/audio')) {
        throw new RuntimeException('unexpected_private_layout');
    }
    require $release . '/bootstrap.php';
    $config = require $release . '/config/app.php';
    if ($config['environment'] !== 'production' || $config['storage_driver'] !== 'local'
        || realpath($config['storage_path']) !== $shared . '/audio'
        || !$config['api_enabled'] || $config['analytics_enabled']) {
        throw new RuntimeException('unexpected_runtime_config');
    }
    $pdo = Celikom\Database\Connection::open($config);
    // Read-only inspection prints counts, never secrets, names, hashes or URLs.
    if ($operation === 'inspect') {
        $counts = [];
        foreach (['tracks', 'audio_assets', 'track_replacements'] as $table) {
            $counts[] = (int) $pdo->query('SELECT COUNT(*) FROM ' . $table)->fetchColumn();
        }
        echo 'Stage 6 private library inspection: ', $counts[0], ' tracks, ',
            $counts[1], ' assets, ', $counts[2], " mappings.\n";
        exit(0);
    }

    // One-time claim is created BEFORE any mutation. Ambiguous outcomes require
    // a newly reviewed commit; an old GitHub Action can never replay its write.
    $ledger = $shared . '/library-operation-claims';
    if (is_link($ledger) || (!is_dir($ledger) && !mkdir($ledger, 0700))) {
        throw new RuntimeException('library_claim_unavailable');
    }
    $claim = $ledger . '/' . $sha;
    $claimHandle = @fopen($claim, 'x');
    if ($claimHandle === false) {
        throw new RuntimeException('library_operation_already_claimed');
    }
    chmod($claim, 0600);
    fwrite($claimHandle, "claimed\n");
    fclose($claimHandle);

    require $incoming . '/LibraryManagementService.php';
    $storage = new Celikom\Storage\LocalStorageAdapter($config['storage_path']);
    $manager = new Celikom\Application\LibraryManagementService($pdo, $storage, $config['max_audio_size']);
    switch ($operation) {
        case 'add-track':
            $id = $manager->addTrack('yandex', $request['track_id'], $request['duration_ms']);
            echo 'Library Track registered, internal ID ', $id, ".\n";
            break;
        case 'add-asset':
            $directory = $shared . '/staging';
            if (is_link($directory) || realpath($directory) !== $directory) {
                throw new RuntimeException('staging_unavailable');
            }
            $eligible = [];
            foreach (scandir($directory) ?: [] as $basename) {
                if (!preg_match('/^[A-Za-z0-9][A-Za-z0-9._-]{0,119}\.(?:mp3|wav)$/iD', $basename)) {
                    continue;
                }
                $file = $directory . '/' . $basename;
                if (is_link($file)) {
                    throw new RuntimeException('staging_symlink_forbidden');
                }
                if (is_file($file) && realpath($file) === $file) {
                    $eligible[] = $file;
                }
            }
            if (count($eligible) !== 1) {
                throw new RuntimeException('staging_requires_one_reviewed_file');
            }
            $id = $manager->addReviewedAsset($eligible[0], $request['duration_ms'], $request['confirm_reviewed']);
            echo 'Reviewed AudioAsset registered, ID ', $id, ".\n";
            break;
        case 'link':
            $id = $manager->link((int) $request['track_db_id'], (int) $request['asset_id']);
            echo 'Pending TrackReplacement registered, ID ', $id, ".\n";
            break;
        case 'approve':
            $manager->approve((int) $request['replacement_id'], $request['confirm_reviewed']);
            echo "Candidate approved, but not active.\n";
            break;
        case 'activate':
            $manager->activate((int) $request['replacement_id'], $request['confirm_activate'],
                (int) $request['expected_active_replacement_id']);
            echo "Approved candidate activated after expected-active check.\n";
            break;
        case 'disable':
            $manager->disable((int) $request['replacement_id'], $request['confirm_disable'],
                (int) $request['expected_active_replacement_id']);
            echo "Candidate disabled after expected-active check.\n";
            break;
        default:
            throw new InvalidArgumentException('unrecognized_library_operation');
    }
} catch (Throwable) {
    fwrite(STDERR, "Stage 6 library operation refused; verify private state and one-time claim. Details withheld.\n");
    exit(1);
}
