<?php

declare(strict_types=1);

require dirname(__DIR__) . '/deploy/private-test-env.php';
$password = '  quotes" and $dollars `literal` \\ slash #hash  ';
$settings = Celikom\Deployment\privateTestSettings(['db_name' => 'celikom_test', 'db_user' => 'root', 'db_password' => $password], '/tmp/celikom-private');
$encoded = Celikom\Deployment\privateTestDotenv($settings);
$decoded = [];
$directory = sys_get_temp_dir() . '/celikom-env-test-' . bin2hex(random_bytes(8));
mkdir($directory, 0700);
copy(dirname(__DIR__) . '/bootstrap.php', $directory . '/bootstrap.php');
file_put_contents($directory . '/.env', $encoded);
$original = [];
try {
    foreach ($settings as $name => $value) {
        $original[$name] = getenv($name);
        putenv($name);
    }
    require $directory . '/bootstrap.php';
    foreach ($settings as $name => $value) {
        $decoded[$name] = getenv($name);
    }
} finally {
    foreach ($original as $name => $value) {
        putenv($value === false ? $name : $name . '=' . $value);
    }
    unlink($directory . '/.env');
    unlink($directory . '/bootstrap.php');
    rmdir($directory);
}
if ($decoded['DB_PASSWORD'] !== $password || $decoded['FEATURE_REPLACEMENTS'] !== '0' || $decoded['FEATURE_ANALYTICS'] !== '0' || count(array_unique([$decoded['AUDIO_SIGNING_KEY'], $decoded['API_TEST_TOKEN'], $decoded['ANALYTICS_PRIVACY_KEY']])) !== 3) {
    throw new RuntimeException('private_configuration_roundtrip_failed');
}
foreach (["password\nFEATURE_REPLACEMENTS=1", "password\rvalue", "password\0value"] as $invalid) {
    try {
        Celikom\Deployment\privateTestSettings(['db_name' => 'celikom_test', 'db_user' => 'root', 'db_password' => $invalid], '/tmp/celikom-private');
        throw new RuntimeException('unsafe_password_accepted');
    } catch (InvalidArgumentException) {
    }
}
fwrite(STDOUT, "Private deployment configuration: special-character round trip, separate keys and newline rejection passed.\n");
