<?php
declare(strict_types=1);
namespace Celikom\Website;
use InvalidArgumentException;

/** Developer-only Stage 6 draft, not an authenticated CMS or policy engine. */
final class CommunityDraft
{
    /** @param array<string,mixed> $overrides */
    public static function render(string $approvedHtml, string $schemaJson, array $overrides): string
    {
        $fields = CommunityFieldCatalog::fields($schemaJson);
        foreach ($overrides as $key => $value) {
            if (!is_string($key) || !isset($fields[$key]) || !is_string($value)) {
                throw new InvalidArgumentException('Stage 6 editable field not allowed');
            }
            CommunityFieldCatalog::check($key, $value, $fields[$key]);
        }
        return V10Renderer::render($approvedHtml, $schemaJson, $overrides);
    }
}
