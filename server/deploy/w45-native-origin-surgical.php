<?php

declare(strict_types=1);

/**
 * W45 candidate-only surgical patch.
 * Never call on the live current symlink or any existing release.
 * Runs ONLY against a fresh, immutable, separately cloned release candidate
 * whose unmodified Application.php SHA256 equals the approved W43 live source.
 *
 * No authentication, audio, user data, database or runtime configuration read.
 */
if ($argc !== 2 || !is_file($argv[1]) || is_link($argv[1])) {
    fwrite(STDERR, "W45_CANDIDATE_REQUIRED\n");
    exit(2);
}
$real = realpath($argv[1]);
if (!is_string($real) ||
    preg_match('~/releases/w45-native-cors-[a-f0-9]{12}/src/Application\.php$~D', $real) !== 1) {
    fwrite(STDERR, "W45_NOT_AN_ISOLATED_RELEASE_CANDIDATE\n");
    exit(2);
}
$source = file_get_contents($real);
if (!is_string($source) ||
    hash('sha256', $source) !== 'ec7f5d0d87978c823ece2dcfa2e76a021d4e2af09eb4f5c4d5fe52b6ab6c897e') {
    fwrite(STDERR, "W45_LIVE_BASELINE_SHA_MISMATCH\n");
    exit(3);
}
$needle = "                'musicapplication://desktop',\n";
$addition =
    "                // Genuine native Yandex 5.126.1 uses the hyphenated protocol.\n" .
    "                // Only signed numeric audio routes; never auth/admin/resolve.\n" .
    "                'music-application://desktop',\n";
if (substr_count($source, $needle) !== 1 ||
    str_contains($source, "'music-application://desktop'")) {
    fwrite(STDERR, "W45_ORIGIN_ANCHOR_NOT_UNIQUE\n");
    exit(3);
}
$patched = str_replace($needle, $needle . $addition, $source);
if (hash('sha256', $patched) !== '920a4fa28357a3e61d6af64085448eacc76ea8c3c3c1946597b6428e61b506e0') {
    fwrite(STDERR, "W45_PATCHED_SHA_MISMATCH\n");
    exit(3);
}
$mode = fileperms($real) & 0777;
$temp = tempnam(dirname($real), '.w45-');
if ($temp === false) {
    fwrite(STDERR, "W45_TEMP_CREATE_FAILED\n");
    exit(4);
}
try {
    if (file_put_contents($temp, $patched, LOCK_EX) !== strlen($patched) ||
        !chmod($temp, $mode) ||
        !rename($temp, $real)) {
        fwrite(STDERR, "W45_CANDIDATE_WRITE_FAILED\n");
        exit(4);
    }
} finally {
    if (is_file($temp)) unlink($temp);
}
echo "W45_EXACT_ONE_HUNK_APPLIED_TO_ISOLATED_CANDIDATE\n";
