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
    private const ADAPTER = '<script src="/assets/js/v10/demo-editorial-preview.js"></script>';
    private const EDITOR_CSS = '<link rel="stylesheet" href="/assets/css/v10/editor-copy-safety.css"/>';

    /** @param array<string,mixed> $overrides */
    public static function render(string $trustedTemplate, string $schemaJson, array $overrides): string
    {
        $fields = FirstScreenFieldCatalog::fields($schemaJson);
        $serviceDefault = $fields['sound.text.07']['default'];
        $contentOverrides = [];
        $restoredOverride = null;
        $hasRestoredOverride = false;
        foreach ($overrides as $key => $value) {
            if (!is_string($key) || !isset($fields[$key]) || !is_string($value)) {
                throw new InvalidArgumentException('Field outside first-screen editor');
            }
            FirstScreenFieldCatalog::check($key, $value, $fields[$key]);
            if ($key === self::DYNAMIC_KEY) {
                $restoredOverride = trim($value);
                $hasRestoredOverride = true;
            } else {
                // Prevent dead local CTA targets in the approved v10 markup.
                if ($fields[$key]['type'] === 'url' && str_starts_with($value, '#') &&
                    !str_contains($trustedTemplate, 'id="' . substr($value, 1) . '"')) {
                    throw new InvalidArgumentException('Unknown local navigation target');
                }
                $contentOverrides[$key] = $value;
            }
        }
        // Verify canonical template SHA, slot positions, URL rules and escaping.
        $html = V10Renderer::render($trustedTemplate, $schemaJson, $contentOverrides);
        if ($overrides !== []) {
            // Additive wrapping rules are scoped to edited previews only.
            // Without edits, the original HTML remains byte-for-byte equal.
            if (substr_count($html, '</head>') !== 1 ||
                str_contains($html, self::EDITOR_CSS)) {
                throw new RuntimeException('Unexpected editor preview HTML head');
            }
            $html = str_replace('</head>', self::EDITOR_CSS . '</head>', $html);
        }
        if (!array_key_exists('sound.text.07', $contentOverrides) && !$hasRestoredOverride) {
            return $html;
        }

        // The original v10 script contains fixed mode descriptions.
        // Stage 4 preview adds a trusted external adapter only for edited states.
        $service = array_key_exists('sound.text.07', $contentOverrides)
            ? trim($contentOverrides['sound.text.07']) : $serviceDefault;
        $restored = $restoredOverride ?? FirstScreenFieldCatalog::RESTORED_DEFAULT;
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

}
