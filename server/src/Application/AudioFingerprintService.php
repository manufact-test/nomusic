<?php

declare(strict_types=1);

namespace Celikom\Application;

/** Deliberately deferred processing: no fingerprinting binaries on the web request. */
interface AudioFingerprintService
{
    public function schedule(int $assetId): void;
}
