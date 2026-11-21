<?php

declare(strict_types=1);

function cleanupProbe(string $release, string $payload): void
{
    require $release . '/bootstrap.php';
    $normalizer = new Celikom\Application\Mp3Normalizer();
    foreach (['fixture.mp3' => true, 'corrupt.mp3' => false] as $name => $valid) {
        $prepared = $normalizer->prepare($payload . '/' . $name);
        try {
            if ($valid && file_get_contents($prepared['path']) !== file_get_contents($payload . '/expected.mp3')) throw new RuntimeException('cleaned_audio_mismatch');
            try { (new Celikom\Application\Mp3DecodeValidator())->check($prepared['path']); }
            catch (DomainException $e) {
                if ($valid || $e->getMessage() !== 'invalid_mp3') throw $e;
                continue;
            }
            if (!$valid) throw new RuntimeException('corrupt_audio_accepted');
        } finally { unlink($prepared['path']); }
    }
    echo "UPLOAD_CLEANUP_PROBE_PASS\n";
}
