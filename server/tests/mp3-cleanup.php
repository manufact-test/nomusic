<?php

declare(strict_types=1);
require dirname(__DIR__) . '/bootstrap.php';
use Celikom\Application\Mp3Normalizer;
use Celikom\Application\Mp3DecodeValidator;
function check(bool $ok, string $label): void { if (!$ok) throw new RuntimeException($label); }
$frame = hex2bin('fffb9064') . str_repeat("\0", 413);
$info = substr_replace($frame, 'Info', 36, 4);
$audio = str_repeat($frame, 100);
$tag = "ID3\x04\x00\x00\x00\x00\x00\x10" . str_repeat("x", 16);
$cases = [
    'plain' => [$audio, $audio],
    'leading-tags' => [$tag . $tag . $audio, $audio],
    'interleaved-info' => [$tag . $info . $tag . $info . $audio, $info . $audio],
    'utf8-tag' => [$audio . 'TAG' . str_repeat('Ж', 27) . str_repeat('x', 97) . chr(7), $audio],
    'standard-tag' => [$audio . 'TAG' . str_repeat("\0", 125), $audio],
    'truncated' => [substr($audio, 0, -1), null],
    'broken-middle' => [substr_replace($audio, 'xxxx', 417 * 50, 4), null],
    'id3-in-audio' => [substr($audio, 0, 417 * 50) . $tag . substr($audio, 417 * 50), null],
    'info-in-audio' => [$audio . $info, null],
    'tail-junk' => [$audio . '<?php evil ?>', null],
    'too-many-tags' => [str_repeat($tag, 5) . $audio, null],
    'bad-id3' => ["ID3\x04\x00\x00\xff\xff\xff\xff" . $audio, null],
];
foreach ($cases as $name => [$input, $expected]) {
    $path = tempnam(sys_get_temp_dir(), 'cleanup-test-'); $prepared = null;
    try {
        file_put_contents($path, $input);
        try { $prepared = (new Mp3Normalizer())->prepare($path); }
        catch (DomainException $e) { check($expected === null && $e->getMessage() === 'invalid_mp3', $name); continue; }
        check($expected !== null && file_get_contents($prepared['path']) === $expected, $name);
        check(file_get_contents($path) === $input, 'input untouched');
    } finally { unlink($path); if ($prepared !== null) unlink($prepared['path']); }
}
if ($argc > 1) {
    $prepared = (new Mp3Normalizer())->prepare($argv[1]);
    try {
        (new Mp3DecodeValidator())->check($prepared['path']);
        copy($prepared['path'], $argv[1] . '.clean.mp3');
    } finally { unlink($prepared['path']); }
}
echo "MP3_CLEANUP_PASS\n";
