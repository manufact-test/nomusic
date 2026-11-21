<?php
declare(strict_types=1);
namespace Celikom\Website;

use InvalidArgumentException;

/**
 * Independent Stage 5 private CLI-only content draft. This is not a CMS and
 * cannot publish, persist or accept any media/FAQ/payment/user data.
 */
final class PrincipleDraft
{
    /** @param array<string,mixed> $overrides */
    public static function render(string $trustedTemplate, string $manifestJson, array $overrides): string
    {
        $fields = PrincipleFieldCatalog::fields($manifestJson);
        foreach ($overrides as $key => $value) {
            if (!is_string($key) || !isset($fields[$key]) || !is_string($value)) {
                throw new InvalidArgumentException('Stage 5 field outside approved copy scope');
            }
            PrincipleFieldCatalog::check($key, $value, $fields[$key]);
        }
        return V10Renderer::render($trustedTemplate, $manifestJson, $overrides);
    }
}
