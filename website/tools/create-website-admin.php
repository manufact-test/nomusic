<?php
declare(strict_types=1);
/**
 * Provision ONE authorized website-only CMS owner, CLI and stdin only.
 *
 * Usage on the server (outside public_html, with website DB env populated):
 *   php website/tools/create-website-admin.php owner < /secure/private/password-file
 *
 * Never type the password as a command argument or store it in this repo.
 */
if (PHP_SAPI !== 'cli' || $argc !== 2 ||
    !preg_match('/^[A-Za-z0-9_.-]{3,80}$/D',$argv[1])) {
    fwrite(STDERR,"Usage: php create-website-admin.php USERNAME < PRIVATE_PASSWORD_FILE\n");
    exit(2);
}
if (function_exists('stream_isatty') && stream_isatty(STDIN)) {
    fwrite(STDERR,"Read password from redirected protected stdin, not an interactive echo.\n");
    exit(2);
}
require dirname(__DIR__).'/app/bootstrap.php';
try {
    $password=stream_get_contents(STDIN,4097);
    if (!is_string($password)) throw new RuntimeException('Password not received');
    $password=rtrim($password,"\r\n");
    if (strlen($password)<16 || strlen($password)>256) {
        throw new RuntimeException('Owner password length invalid');
    }
    $websiteRoot=dirname(__DIR__).'/public';
    $lease=\Celikom\Website\CmsWriteQuiescence::writer($websiteRoot);
    $pdo=\Celikom\Website\Database::connect(\Celikom\Website\CmsConfig::databaseSettings());
    // Provisioning is additive, never reset or overwrite existing accounts.
    $hash=password_hash($password, defined('PASSWORD_ARGON2ID') ? PASSWORD_ARGON2ID : PASSWORD_DEFAULT);
    unset($password);
    $stmt=$pdo->prepare('INSERT INTO admin_users (username,password_hash,is_active) VALUES (?,?,1)');
    $stmt->execute([$argv[1],$hash]);
    fwrite(STDOUT,"Website CMS owner created; change the private password source securely.\n");
} catch (\Throwable $e) {
    fwrite(STDERR,"Owner provisioning rejected; account may exist or database is unavailable.\n");
    exit(1);
}
