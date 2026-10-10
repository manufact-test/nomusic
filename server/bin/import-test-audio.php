<?php

declare(strict_types=1);

require dirname(__DIR__) . '/bootstrap.php';
$options = getopt('', ['file:', 'track-id:', 'duration-ms:', 'artist::', 'title::', 'album::', 'confirm-reviewed']);
if (!array_key_exists('confirm-reviewed', $options) || !isset($options['file'], $options['track-id'], $options['duration-ms']) || !ctype_digit($options['duration-ms'])) {
    fwrite(STDERR, "Usage: php bin/import-test-audio.php --file=/private/file.mp3 --track-id=123 --duration-ms=201000 --confirm-reviewed\nOnly owner-reviewed authorized test files; duration must be measured from the file.\n");
    exit(2);
}
$config = require dirname(__DIR__) . '/config/app.php';
$storage = new Celikom\Storage\LocalStorageAdapter($config['storage_path']);
$service = new Celikom\Application\TestAudioImporter(Celikom\Database\Connection::open($config), $storage, $config['max_audio_size']);
$id = $service->import($options['file'], 'yandex', $options['track-id'], (int) $options['duration-ms'], $options);
fwrite(STDOUT, 'Reviewed test mapping ready: ' . $id . "\n");
