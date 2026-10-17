<?php
declare(strict_types=1);
namespace Celikom\Website;

use InvalidArgumentException;

/**
 * Developer-only v10 Stage 8 preview. Does not enable a real installation
 * CTA, create legal pages, write to storage or publish anything.
 */
final class InstallFooterDraft
{
    /** @param array<string,mixed> $texts @param array<string,mixed> $links */
    public static function render(
        string $trustedTemplate,
        string $manifestJson,
        array $texts = [],
        array $links = []
    ): string {
        $catalog = InstallFooterFieldCatalog::fields($manifestJson);
        foreach ($texts as $key => $value) {
            if (!is_string($key) || !isset($catalog['texts'][$key]) || !is_string($value)) {
                throw new InvalidArgumentException('Unknown Stage 8 text field');
            }
            InstallFooterFieldCatalog::checkText($key, $value, $catalog['texts'][$key]);
        }
        foreach ($links as $key => $value) {
            if (!is_string($key) || !isset($catalog['links'][$key]) || !is_string($value)) {
                throw new InvalidArgumentException('Unknown Stage 8 link field');
            }
            InstallFooterFieldCatalog::checkLink($key, $value, $catalog['links'][$key], $trustedTemplate);
        }
        return V10Renderer::render($trustedTemplate, $manifestJson, array_merge($texts, $links));
    }
}
