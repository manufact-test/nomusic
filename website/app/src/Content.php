<?php
declare(strict_types=1);
namespace Celikom\Website;

use InvalidArgumentException;

/**
 * Stage 3 typed content rules. Layout stays in trusted templates.
 * The full 12-topic registry and MySQL publication store are Stage 9 work.
 */
final class Content
{
    /** @var array<string, array{type:string,max:int}> */
    public const FIELDS = [
        'seo.title' => ['type' => 'text', 'max' => 140],
        'seo.description' => ['type' => 'text', 'max' => 320],
        'hero.eyebrow' => ['type' => 'text', 'max' => 100],
        'hero.title.first' => ['type' => 'text', 'max' => 150],
        'hero.title.accent' => ['type' => 'text', 'max' => 150],
        'hero.lead' => ['type' => 'text', 'max' => 1100],
        'hero.primary.label' => ['type' => 'text', 'max' => 80],
        'hero.primary.href' => ['type' => 'url', 'max' => 1000],
        'hero.secondary.label' => ['type' => 'text', 'max' => 80],
        'hero.secondary.href' => ['type' => 'url', 'max' => 1000],
        'how.title' => ['type' => 'text', 'max' => 150],
        'sound.title' => ['type' => 'text', 'max' => 180],
        'player.title' => ['type' => 'text', 'max' => 180],
        'contribute.title' => ['type' => 'text', 'max' => 180],
        'transparency.title' => ['type' => 'text', 'max' => 180],
        'faq.title' => ['type' => 'text', 'max' => 180],
        'rewards.title' => ['type' => 'text', 'max' => 180],
        'install.title' => ['type' => 'text', 'max' => 180],
        'install.status' => ['type' => 'text', 'max' => 100],
        'closing.title' => ['type' => 'text', 'max' => 180],
        'closing.cta.label' => ['type' => 'text', 'max' => 80],
        'closing.cta.href' => ['type' => 'url', 'max' => 1000],
    ];

    public static function escape(string $value): string
    {
        return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE | ENT_HTML5, 'UTF-8');
    }

    /**
     * Validate an allowlisted CMS field. No arbitrary JS/CSS/HTML can be
     * injected as a content key or a URL. Output still MUST be escaped.
     */
    public static function validate(string $key, mixed $value): string
    {
        $rule = self::FIELDS[$key] ?? null;
        if ($rule === null) {
            throw new InvalidArgumentException('Unknown content field');
        }
        if (!is_string($value) || preg_match('//u', $value) !== 1) {
            throw new InvalidArgumentException('Content must be UTF-8 text');
        }
        $value = trim($value);
        if (strlen($value) > $rule['max'] * 4) {
            throw new InvalidArgumentException('Content exceeds maximum length');
        }
        $charCount = preg_match_all('/./us', $value);
        if ($charCount === false || $charCount > $rule['max']) {
            throw new InvalidArgumentException('Content exceeds maximum length');
        }
        if (preg_match('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/', $value)) {
            throw new InvalidArgumentException('Forbidden control character');
        }
        if ($rule['type'] === 'url' && !self::safeHref($value)) {
            throw new InvalidArgumentException('Unsafe content link');
        }
        return $value;
    }

    public static function safeHref(string $href): bool
    {
        if ($href === '' || preg_match('/[\x00-\x20\x7F\\\\]/', $href)) {
            return false;
        }
        if (preg_match('/^#[a-zA-Z][\w-]*$/D', $href)) {
            return true;
        }
        if ($href === '/' || preg_match('~^/(?:[a-z0-9-]+/)*(?:[a-z0-9-]+/?)?(?:#[a-zA-Z][\w-]*)?$~Di', $href)) {
            return true;
        }
        $parts = parse_url($href);
        if ($parts === false || !is_array($parts) || ($parts['scheme'] ?? null) !== 'https') {
            return false;
        }
        if (!isset($parts['host']) || isset($parts['user']) || isset($parts['pass'])) {
            return false;
        }
        $host = $parts['host'];
        // No localhost, intranet, IP literals or port-addressable unknown backends.
        if (!preg_match('/^(?=.{4,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$/Di', $host)) {
            return false;
        }
        if (isset($parts['port'])) {
            return false;
        }
        return true;
    }
}
