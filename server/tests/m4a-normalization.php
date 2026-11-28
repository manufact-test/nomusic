<?php

declare(strict_types=1);
require dirname(__DIR__) . '/bootstrap.php';
$cases = json_decode(file_get_contents($argv[1]), true, 32, JSON_THROW_ON_ERROR);
$count = 0;
foreach ($cases as $case) {
    $input = tempnam(sys_get_temp_dir(), 'celikom-m4a-test-'); $prepared = null;
    try {
        file_put_contents($input, base64_decode($case['source'], true));
        try {
            $prepared = (new Celikom\Application\M4aNormalizer())->prepare($input);
        } catch (DomainException $error) {
            if ($case['valid'] || $error->getMessage() !== 'invalid_m4a') throw new RuntimeException('Unexpected rejection: ' . $case['name'], 0, $error);
        }
        if ($prepared !== null && (!$case['valid'] || hash_file('sha256', $prepared['path']) !== $case['sha256'] || $prepared['duration_ms'] !== $case['duration_ms'])) {
            throw new RuntimeException('Unexpected preparation: ' . $case['name']);
        }
        ++$count;
    } finally {
        if ($prepared !== null) unlink($prepared['path']);
        unlink($input);
    }
}
echo 'M4A_NORMALIZATION_MATRIX_PASS ' . $count . "\n";
