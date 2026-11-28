<?php

declare(strict_types=1);

// Input is generated from extension/tests/fixtures/mp3-metadata-fixtures.mjs.
// This isolated test uses no database, credentials or user-supplied audio.
require dirname(__DIR__) . '/bootstrap.php';
$cases = json_decode(file_get_contents($argv[1]), true, 32, JSON_THROW_ON_ERROR);
$count = 0;
foreach ($cases as $case) {
    $input = tempnam(sys_get_temp_dir(), 'celikom-metadata-test-');
    $prepared = null;
    try {
        file_put_contents($input, base64_decode($case['source'], true));
        try {
            $prepared = (new Celikom\Application\Mp3Normalizer())->prepare($input);
        } catch (DomainException $error) {
            if ($case['sha256'] !== null || $error->getMessage() !== 'invalid_mp3') {
                throw new RuntimeException('Unexpected rejection: ' . $case['name'], 0, $error);
            }
        }
        if ($prepared !== null && ($case['sha256'] === null ||
            hash_file('sha256', $prepared['path']) !== $case['sha256'] ||
            $prepared['duration_ms'] !== $case['duration_ms'])) {
            throw new RuntimeException('Different normalization: ' . $case['name']);
        }
        ++$count;
    } finally {
        if ($prepared !== null) unlink($prepared['path']);
        unlink($input);
    }
}
echo 'MP3_JS_PHP_PARITY_PASS ' . $count . "\n";
