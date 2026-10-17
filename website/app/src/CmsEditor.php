<?php
declare(strict_types=1);
namespace Celikom\Website;

use InvalidArgumentException;

/**
 * Initial Stage 9 editing surface: non-policy website headings and explanatory
 * copy from the reviewed Stage 7 and Stage 8 catalogs. Other sections and
 * FAQ item operations remain excluded from this first authenticated slice.
 * All new snapshots are re-rendered against the exact approved v10 HTML.
 */
final class CmsEditor
{
    /** @return array<string,array<string,mixed>> */
    public static function fields(string $manifest): array
    {
        $trust = TrustFieldCatalog::fields($manifest);
        $finish = InstallFooterFieldCatalog::fields($manifest);
        return array_merge($trust,$finish['texts']);
    }

    public static function validate(
        string $template,
        string $manifest,
        string $faqSeed,
        array $data
    ): string {
        if (array_keys($data) !== ['content','faq'] ||
            !is_array($data['content']) || !is_array($data['faq']) ||
            $data['faq'] !== []) {
            throw new InvalidArgumentException('Unsupported editor snapshot');
        }
        $fields = self::fields($manifest);
        foreach ($data['content'] as $key=>$value) {
            if (!is_string($key) || !isset($fields[$key]) || !is_string($value)) {
                throw new InvalidArgumentException('Unapproved CMS field');
            }
            if (str_starts_with($key,'faq.') || str_starts_with($key,'transparency.')) {
                TrustFieldCatalog::check($key,$value,$fields[$key]);
            } else {
                InstallFooterFieldCatalog::checkText($key,$value,$fields[$key]);
            }
        }
        // Safe HTML escaping and immutable visual template/token checks.
        return FaqV10Renderer::render(
            V10Renderer::render($template,$manifest,$data['content']),$faqSeed,[]
        );
    }
}
