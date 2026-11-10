<?php
declare(strict_types=1);
// Read-only release/config metadata. No database connection or credential output.
ini_set('display_errors','0');
try {
    if (PHP_SAPI !== 'cli') throw new RuntimeException('cli_only');
    $root='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
    $release=realpath($root.'/current');
    if (!$release || !str_starts_with($release,$root.'/releases/')) throw new RuntimeException('release');
    require $release.'/bootstrap.php';
    $config=require $release.'/config/app.php';
    $public=realpath(dirname($root).'/public_html');
    $storage=realpath((string)($config['storage_path']??''));
    $env=realpath($release.'/.env');
    $hashes=[];
    foreach (['src/Application.php','src/Entitlement/TrialService.php','src/Entitlement/EntitlementService.php',
        'src/Entitlement/AudioAccessService.php','src/Http/AudioController.php','src/Application/AudioTokenService.php',
        'src/Application/ResolveService.php','src/Billing/BillingAdapter.php','src/Billing/WebhookService.php',
        'src/Billing/PaidAccessService.php','src/Auth/AuthService.php','config/app.php'] as $path) {
        $hashes[$path]=is_file($release.'/'.$path)?hash_file('sha256',$release.'/'.$path):null;
    }
    $flags=[];
    foreach (['api_enabled','auth_enabled','entitlement_enabled','billing_enabled','billing_views_enabled','debug'] as $key)
        $flags[$key]=(bool)($config[$key]??false);
    echo json_encode(['read_only'=>true,'database_opened'=>false,'release'=>basename($release),'flags'=>$flags,
        'legacy_test_bearer_configured'=>strlen((string)($config['test_api_token']??''))>=24,
        'private_env_outside_webroot'=>$env && $public && !str_starts_with($env,$public.'/'),
        'private_env_permissions'=>$env && (fileperms($env)&0077)===0,
        'audio_outside_webroot'=>$storage && $public && !str_starts_with($storage,$public.'/'),
        'source_sha256'=>$hashes],JSON_THROW_ON_ERROR|JSON_UNESCAPED_SLASHES),"\n";
} catch (Throwable $error) {
    fwrite(STDERR,"Read-only release/config check failed; no configuration values emitted.\n");
    exit(1);
}
