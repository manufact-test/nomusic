<?php

declare(strict_types=1);

// Only the local test server uses this router; excluded from deployment packages.
$fixturePath = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH);
if ($fixturePath === '/stage7-browser-mp3') {
    $file = getenv('CELIKOM_STAGE7_TEST_MP3');
    if (!$file || !is_file($file)) { http_response_code(404); return; }
    $length = filesize($file);
    if ($length === false || $length < 1) { http_response_code(404); return; }
    $first = 0;
    $last = $length - 1;
    $requestedRange = $_SERVER['HTTP_RANGE'] ?? '';
    if ($requestedRange !== '') {
        if (!preg_match('/^bytes=(\\d+)-(\\d*)$/D', $requestedRange, $parts) ||
            strlen($parts[1]) > 12 || strlen($parts[2]) > 12) {
            http_response_code(416); header('Content-Range: bytes */' . $length); return;
        }
        $first = (int) $parts[1];
        $last = $parts[2] === '' ? $length - 1 : min($length - 1, (int) $parts[2]);
        if ($first > $last || $first >= $length) {
            http_response_code(416); header('Content-Range: bytes */' . $length); return;
        }
        http_response_code(206);
        header('Content-Range: bytes ' . $first . '-' . $last . '/' . $length);
    }
    header('Content-Type: audio/mpeg');
    header('Cache-Control: no-store');
    header('X-Content-Type-Options: nosniff');
    header('Accept-Ranges: bytes');
    header('Content-Length: ' . ($last - $first + 1));
    $stream = fopen($file, 'rb');
    if ($stream === false) { http_response_code(500); return; }
    try {
        fseek($stream, $first);
        $remaining = $last - $first + 1;
        while ($remaining > 0 && !feof($stream)) {
            $chunk = fread($stream, min(65536, $remaining));
            if ($chunk === false || $chunk === '') break;
            echo $chunk;
            $remaining -= strlen($chunk);
        }
    } finally { fclose($stream); }
    return;
}
if ($fixturePath === '/stage7-browser-mp3-play') {
    header('Content-Type: text/html; charset=utf-8');
    echo '<!doctype html><html><body data-audio-result="pending"><script>
const audio = new Audio(); audio.preload = "auto";
audio.onerror = () => { document.body.dataset.audioResult = "decode-error"; };
audio.addEventListener("loadedmetadata", () => {
  if (!Number.isFinite(audio.duration) || audio.duration < 2 || audio.duration > 3) {
    document.body.dataset.audioResult = "duration-error"; return;
  }
  audio.currentTime = 0.5;
});
audio.addEventListener("seeked", async () => {
  try { await audio.play(); audio.pause();
    document.body.dataset.audioResult = audio.paused && audio.currentTime >= 0.4 ? "ok" : "seek-error";
  } catch (_) { document.body.dataset.audioResult = "play-error"; }
}, {once: true});
audio.src = "/stage7-browser-mp3"; audio.load();
</script></body></html>';
    return;
}
if ($fixturePath !== '/browser-fixture') {
    require dirname(__DIR__) . '/public/index.php';
    return;
}
require dirname(__DIR__) . '/bootstrap.php';
$config = require dirname(__DIR__) . '/config/app.php';
$app = new Celikom\Application($config);
$response = $app->handle('GET', '/api/v1/resolve', ['service' => 'yandex', 'track_id' => '1944599'], ['Authorization' => 'Bearer ' . $config['test_api_token']]);
$asset = json_decode($response->body, true, flags: JSON_THROW_ON_ERROR);
$url = json_encode($asset['audio_url'] ?? '', JSON_THROW_ON_ERROR | JSON_HEX_TAG);
header('Content-Type: text/html; charset=utf-8');
echo '<!doctype html><html><body data-audio-result="pending"><script>
const audio = new Audio(); audio.crossOrigin = "anonymous"; audio.preload = "auto";
audio.addEventListener("error", () => document.body.dataset.audioResult = "media-error");
audio.addEventListener("loadedmetadata", () => {
  if (!Number.isFinite(audio.duration) || audio.duration < 0.9 || audio.duration > 1.1) { document.body.dataset.audioResult = "duration-error"; return; }
  audio.currentTime = 0.5;
});
audio.addEventListener("seeked", async () => {
  try { await audio.play(); audio.pause(); document.body.dataset.audioResult = audio.paused && audio.currentTime >= 0.4 ? "ok" : "seek-error"; }
  catch (_) { document.body.dataset.audioResult = "play-error"; }
}, {once: true});
audio.src = ' . $url . '; audio.load();
</script></body></html>';
