<?php
declare(strict_types=1);
namespace Celikom\Website;

use InvalidArgumentException;
use RuntimeException;

/**
 * Stage 4 technical editor preview only; not a public CMS.
 * The approved v10 HTML and its two original JS files remain unchanged.
 */
final class FirstScreenDraft
{
    private const SECTIONS = ['header' => true, 'top' => true, 'sound' => true];
    private const DYNAMIC_KEY = 'sound.result.restored';
    private const RESTORED_DEFAULT = 'Играет знакомая версия — если она доступна';
    private const ADAPTER = '<script src="/assets/js/v10/demo-editorial-preview.js"></script>';

    /** @param array<string,mixed> $overrides */
    public static function render(string $trustedTemplate, string $schemaJson, array $overrides): string
    {
        $schema = json_decode($schemaJson, true, 512, JSON_THROW_ON_ERROR);
        if (!is_array($schema) || ($schema['version'] ?? null) !== 1) {
            throw new RuntimeException('Invalid v10 content registry');
        }
        $allowed = [];
        $linkKeys = [];
        $serviceDefault = null;
        foreach (['text_fields', 'link_fields'] as $bucket) {
            if (!is_array($schema[$bucket] ?? null)) {
                throw new RuntimeException('Missing typed content fields');
            }
            foreach ($schema[$bucket] as $field) {
                if (!is_array($field) || !is_string($field['key'] ?? null) ||
                    !is_string($field['section'] ?? null)) {
                    throw new RuntimeException('Invalid editorial field');
                }
                if (isset(self::SECTIONS[$field['section']])) {
                    $allowed[$field['key']] = true;
                    if ($bucket === 'link_fields') {
                        $linkKeys[$field['key']] = true;
                    }
                }
                if ($bucket === 'text_fields' && ($field['key'] ?? null) === 'sound.text.07') {
                    $serviceDefault = $field['default'] ?? null;
                }
            }
        }
        if (!is_string($serviceDefault) || $serviceDefault === '') {
            throw new RuntimeException('Missing approved demo service label');
        }
        $contentOverrides = [];
        $restoredOverride = null;
        $hasRestoredOverride = false;
        foreach ($overrides as $key => $value) {
            if (!is_string($key) ||
                ($key !== self::DYNAMIC_KEY && !isset($allowed[$key]))) {
                throw new InvalidArgumentException('Field outside first-screen editor');
            }
            if (!is_string($value)) {
                throw new InvalidArgumentException('Only plain string edits are supported');
            }
            if ($key === self::DYNAMIC_KEY) {
                $restoredOverride = self::validModeResult($value);
                $hasRestoredOverride = true;
            } else {
                // Internal navigation cannot point to an absent on-page ID.
                // This is extra UX validation atop canonical safeHref/XSS rules.
                if (isset($linkKeys[$key]) && str_starts_with($value, '#') &&
                    !str_contains($trustedTemplate, 'id="' . substr($value, 1) . '"')) {
                    throw new InvalidArgumentException('Unknown local navigation target');
                }
                $contentOverrides[$key] = $value;
            }
        }
        // Verify canonical template SHA, slot positions, URL rules and escaping.
        $html = V10Renderer::render($trustedTemplate, $schemaJson, $contentOverrides);
        if (!array_key_exists('sound.text.07', $contentOverrides) && !$hasRestoredOverride) {
            return $html;
        }

        // The original v10 script contains fixed mode descriptions.
        // Stage 4 preview adds a trusted external adapter only for edited states.
        $service = array_key_exists('sound.text.07', $contentOverrides)
            ? trim($contentOverrides['sound.text.07']) : $serviceDefault;
        $restored = $restoredOverride ?? self::RESTORED_DEFAULT;
        $trustedTag = '<div aria-label="Визуальная схема принципа замены звука" class="demo-board" data-mode="service" id="sound-panel">';
        if (substr_count($html, $trustedTag) !== 1 || substr_count($html, '</body>') !== 1 ||
            str_contains($html, self::ADAPTER)) {
            throw new RuntimeException('Approved v10 demo markup changed');
        }
        $attrs = ' data-editorial-service="' . Content::escape($service) .
            '" data-editorial-restored="' . Content::escape($restored) . '"';
        $html = str_replace($trustedTag, substr($trustedTag, 0, -1) . $attrs . '>', $html);
        return str_replace('</body>', self::ADAPTER . '</body>', $html);
    }

    private static function validModeResult(string $value): string
    {
        if (preg_match('//u', $value) !== 1 ||
            preg_match('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/', $value)) {
            throw new InvalidArgumentException('Invalid encoding or control characters in demo result');
        }
        $value = trim($value);
        $count = preg_match_all('/./us', $value);
        if ($value === '' || $count === false || $count > 120 || strlen($value) > 480) {
            throw new InvalidArgumentException('Invalid length of demo result');
        }
        return $value;
    }
}
