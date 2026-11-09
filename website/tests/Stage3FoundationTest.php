<?php
declare(strict_types=1);
require dirname(__DIR__) . '/app/bootstrap.php';

use Celikom\Website\Content;
use Celikom\Website\Security;

function check(bool $condition, string $message): void
{
    if (!$condition) {
        throw new RuntimeException($message);
    }
}
function mustReject(callable $callback, string $message): void
{
    try {
        $callback();
    } catch (InvalidArgumentException|RuntimeException $expected) {
        return;
    }
    throw new RuntimeException($message);
}

check(Content::validate('hero.title.first', 'Те самые песни.') === 'Те самые песни.', 'Cyrillic content validation');
check(Content::validate('hero.primary.href', '#how') === '#how', 'Approved anchor rejected');
check(Content::validate('hero.secondary.href', '/privacy/') === '/privacy/', 'Relative route rejected');
check(Content::validate('hero.primary.href', 'https://example.org/path') === 'https://example.org/path', 'HTTPS rejected');
check(Content::escape('<script>') === '&lt;script&gt;', 'HTML escape failed');

foreach (['javascript:alert(1)', 'data:text/html,hello', '//evil.example', 'http://example.org', 'https://user:pass@example.org', "https://example.org/\n<script>", 'https://127.0.0.1/', 'https://example.com:8443'] as $bad) {
    mustReject(static fn() => Content::validate('hero.primary.href', $bad), 'Unsafe href accepted: ' . $bad);
}
mustReject(static fn() => Content::validate('unknown.field', 'Value'), 'Unknown field accepted');
mustReject(static fn() => Content::validate('hero.title.first', str_repeat('A', 151)), 'Oversized content accepted');
mustReject(static fn() => Content::validate('hero.title.first', "bad\0value"), 'Control byte accepted');
mustReject(static fn() => Security::startAdminSession(false), 'Insecure session accepted');

print "CELIKOM Stage 3 content/security checks passed\n";
